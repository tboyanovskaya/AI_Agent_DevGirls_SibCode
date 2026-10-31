import os
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = Path("prompts/system_prompt.md").read_text(encoding="utf-8")

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Создайте файл .env и укажите: TOKEN=''")

llm = ChatOpenAI(
    model="qwen3.8-flash-next",
    api_key=TOKEN,
    base_url="https://deepcode.ci.nsu.ru/api",
    temperature=0,
)

llm_tools = llm.bind_tools(ALL_TOOLS)
NAME_TOOLS = {t.name: t for t in ALL_TOOLS}

WRITE_TOOLS = {
    "create_campaign", "update_campaign", "put_segments",
    "create_banner", "create_content", "create_creative",
    "to_moderation", "approve", "decline", "activate", "stop",
}


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    draft: dict
    pending_tool_calls: list
    last_errors: list
    last_warnings: list


def agent_node(state: AgentState) -> dict:
    messages = list(state["messages"])
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    draft = state.get("draft") or {}
    if draft:
        messages.append(
            HumanMessage(
                content=(
                    "Текущий черновик кампании (источник истины):\n"
                    f"{draft}\n\n"
                    "Обновляй его только через инструменты, не выдумывай id."
                )
            )
        )
    response = llm_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "confirm", "end"]:
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return "end"
    if any(tc["name"] in WRITE_TOOLS for tc in last.tool_calls):
        return "confirm"
    return "tools"


def confirm_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    write_calls = [tc for tc in last.tool_calls if tc["name"] in WRITE_TOOLS]
    return {
        "pending_tool_calls": write_calls,
        "messages": [
            AIMessage(
                content=(
                    "Планирую выполнить действия:\n"
                    + "\n".join(
                        f"• {tc['name']}({tc['args']})" for tc in write_calls
                    )
                    + "\n\nПодтвердите (да/нет)."
                )
            )
        ],
    }


def confirm_router(state: AgentState) -> Literal["tools", "agent"]:
    messages = state["messages"]
    user_reply = None
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            user_reply = (m.content or "").strip().lower()
            break
    if user_reply in ("да", "yes", "y", "ок", "ok", "подтверждаю"):
        return "tools"
    return "agent"


def tools_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    tool_messages = []
    last_errors: list = []
    last_warnings: list = []
    new_draft = dict(state.get("draft") or {})

    for tc in last.tool_calls:
        name, args, tid = tc["name"], tc["args"], tc["id"]
        fn = NAME_TOOLS.get(name)
        if fn is None:
            result = f"Инструмент '{name}' не найден."
        else:
            try:
                result = fn.invoke(args)
            except Exception as e:
                result = f"Ошибка при вызове {name}: {e}"

        if isinstance(result, dict):
            if "errors" in result:
                last_errors.extend(result["errors"])
            if "warnings" in result:
                last_warnings.extend(result["warnings"])
            if name == "create_campaign" and "id" in result:
                new_draft["campaign_id"] = result["id"]
            if name == "create_banner" and "id" in result:
                new_draft.setdefault("banner_ids", []).append(result["id"])
            if name == "create_content" and "id" in result:
                new_draft.setdefault("content_ids", []).append(result["id"])
            if name == "create_creative" and "id" in result:
                new_draft.setdefault("creative_ids", []).append(result["id"])
            if name == "put_segments":
                new_draft["included_segments"] = args.get("included", [])
                new_draft["excluded_segments"] = args.get("excluded", [])

        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tid))

    return {
        "messages": tool_messages,
        "pending_tool_calls": [],
        "draft": new_draft,
        "last_errors": last_errors,
        "last_warnings": last_warnings,
    }


workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("confirm", confirm_node)
workflow.add_node("tools", tools_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "confirm": "confirm", "end": END},
)
workflow.add_conditional_edges(
    "confirm",
    confirm_router,
    {"tools": "tools", "agent": "agent"},
)
workflow.add_edge("tools", "agent")

checkpointer = MemorySaver()
agent = workflow.compile(checkpointer=checkpointer)