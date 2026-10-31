import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, ToolMessage

from agent import agent
from tools import get_campaign, get_warnings, get_audit, get_campaign_list


app = FastAPI(title="Campaign AI Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    thread_id: Optional[str] = None


class ConfirmRequest(BaseModel):
    thread_id: str
    answer: str


class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    state: str
    pending_confirmation: bool
    tool_calls: list[dict] = Field(default_factory=list)
    messages: list[dict] = Field(default_factory=list)


def _serialize_messages(messages: list) -> list[dict]:
    out = []
    for m in messages:
        item = {
            "type": type(m).__name__,
            "content": getattr(m, "content", "") or "",
        }
        tc = getattr(m, "tool_calls", None)
        if tc:
            item["tool_calls"] = [
                {"name": t.get("name"), "args": t.get("args"), "id": t.get("id")}
                for t in tc
            ]
        if isinstance(m, ToolMessage):
            item["tool_call_id"] = getattr(m, "tool_call_id", None)
        out.append(item)
    return out


def _pending(snap) -> bool:
    if not snap or not snap.values:
        return False
    return bool(snap.values.get("pending_tool_calls"))


def _current_state(thread_id: str) -> str:
    snap = agent.get_state({"configurable": {"thread_id": thread_id}})
    if not snap or not snap.values:
        return "unknown"
    draft = snap.values.get("draft") or {}
    cid = draft.get("campaign_id")
    if not cid:
        return "draft_not_created"
    try:
        c = get_campaign.invoke({"campaign_id": int(cid)})
        if isinstance(c, dict) and "errors" in c:
            return "unknown"
        return c.get("state", "unknown")
    except Exception:
        return "unknown"


def _run_until_stable(config: dict, max_steps: int = 20) -> dict:
    result = None
    for _ in range(max_steps):
        snap = agent.get_state(config)
        if _pending(snap):
            break
        result = agent.invoke(None, config=config)
        if result is None:
            break
        last = result["messages"][-1]
        if not getattr(last, "tool_calls", None):
            break
    if result is None:
        snap = agent.get_state(config)
        result = {"messages": list(snap.values.get("messages", [])) if snap and snap.values else []}
    return result


def _build_response(thread_id: str, result: dict) -> ChatResponse:
    snap = agent.get_state({"configurable": {"thread_id": thread_id}})
    pending = _pending(snap)
    messages = result.get("messages", [])
    last = messages[-1] if messages else None
    reply = getattr(last, "content", "") or "" if last else ""
    tool_calls = [
        {"name": t.get("name"), "args": t.get("args")}
        for t in (getattr(last, "tool_calls", None) or [])
    ]
    return ChatResponse(
        thread_id=thread_id,
        reply=reply,
        state=_current_state(thread_id),
        pending_confirmation=pending,
        tool_calls=tool_calls,
        messages=_serialize_messages(messages),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=req.message)], "draft": {}},
            config=config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    snap = agent.get_state(config)
    if not _pending(snap):
        last = result["messages"][-1] if result.get("messages") else None
        if last is None or getattr(last, "tool_calls", None):
            result = _run_until_stable(config)

    return _build_response(thread_id, result)


@app.post("/confirm", response_model=ChatResponse)
def confirm(req: ConfirmRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    snap = agent.get_state(config)
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if not _pending(snap):
        raise HTTPException(status_code=400, detail="Нет ожидающих подтверждения действий")

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=req.answer)]},
            config=config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    snap = agent.get_state(config)
    if not _pending(snap):
        last = result["messages"][-1] if result.get("messages") else None
        if last is None or getattr(last, "tool_calls", None):
            result = _run_until_stable(config)

    return _build_response(req.thread_id, result)


@app.get("/state/{thread_id}")
def get_state(thread_id: str):
    snap = agent.get_state({"configurable": {"thread_id": thread_id}})
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    values = dict(snap.values)
    values["messages"] = _serialize_messages(values.get("messages", []))
    return {
        "thread_id": thread_id,
        "values": values,
        "pending_confirmation": _pending(snap),
        "next": list(snap.next) if snap.next else [],
    }


@app.get("/campaigns")
def list_campaigns():
    return get_campaign_list.invoke({})


@app.get("/campaigns/{campaign_id}")
def campaign_details(campaign_id: int):
    c = get_campaign.invoke({"campaign_id": campaign_id})
    if isinstance(c, dict) and "errors" in c:
        raise HTTPException(status_code=404, detail=c["errors"])
    return c


@app.get("/campaigns/{campaign_id}/warnings")
def campaign_warnings(campaign_id: int):
    return get_warnings.invoke({"campaign_id": campaign_id})


@app.get("/campaigns/{campaign_id}/audit")
def campaign_audit(campaign_id: int):
    return get_audit.invoke({"campaign_id": campaign_id})