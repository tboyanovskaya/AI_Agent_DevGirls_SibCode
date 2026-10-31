import json
import logging
import os
import re
import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, ToolMessage

from kandinsky import generate_image, build_prompt, KandinskyError
from tools import get_campaign, get_warnings, get_audit, get_campaign_list
from agent import agent

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("campaign-agent")

RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "50"))


def _log_event(thread_id: str, event: str, payload: dict) -> None:
    """Пишем событие в stdout (Docker сам соберёт)."""
    try:
        line = json.dumps(
            {"ts": time.time(), "thread_id": thread_id, "event": event, "payload": payload},
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        line = f"{event} thread={thread_id} payload=<unserializable>"
    logger.info("%s", line)


# ---------------------------------------------------------------------------
# Очистка ответа агента от «рефлексии» для человекочитаемого reply
# ---------------------------------------------------------------------------
_REFLECTION_PATTERNS = [
    r"^я\s+(понял|подтянул|собрал|выяснил|разобрался)[^\n]*\n?",
    r"^вот\s+что\s+я\s+(понял|выяснил)[^\n]*\n?",
    r"^из\s+брифа\s+я\s+понял[^\n]*\n?",
    r"^справочники\s+подтянул[^\n]*\n?",
]


def _humanize(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    for pat in _REFLECTION_PATTERNS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE).strip()
    return t or "Уточняю данные…"

app = FastAPI(title="Campaign AI Agent API", version="1.2.0")

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


class GenerateImageResponse(BaseModel):
    campaign_id: int
    prompt: str
    image: str  # data:image/jpeg;base64,...


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


def _run_until_stable(thread_id: str, config: dict, max_steps: int = 10) -> dict:
    """
    Дошагивает граф, пока он не остановится на pending-подтверждении
    или не выдаст финальный AIMessage без tool_calls.
    Защищено от бесконечного цикла: не более max_steps вызовов.
    """
    result = None
    for step in range(max_steps):
        snap = agent.get_state(config)
        if _pending(snap):
            break
        try:
            result = agent.invoke(None, config=config)
        except Exception as e:
            _log_event(thread_id, "agent_step_error", {"error": str(e), "step": step})
            logger.exception("Error in _run_until_stable step=%s", step)
            break
        if result is None:
            break

        _log_event(thread_id, "agent_step", {
            "step": step,
            "messages": _serialize_messages(result.get("messages", [])),
        })

        last = result["messages"][-1] if result.get("messages") else None
        if last is None or not getattr(last, "tool_calls", None):
            break

    if result is None:
        snap = agent.get_state(config)
        result = {
            "messages": list(snap.values.get("messages", [])) if snap and snap.values else []
        }
    return result


def _build_response(thread_id: str, result: dict) -> ChatResponse:
    snap = agent.get_state({"configurable": {"thread_id": thread_id}})
    pending = _pending(snap)
    messages = result.get("messages", [])
    last = messages[-1] if messages else None

    if last is None:
        reply = "Уточняю данные…"
    elif getattr(last, "tool_calls", None):
        reply = "Нужно ваше подтверждение…" if pending else "Обрабатываю…"
    else:
        reply = _humanize(getattr(last, "content", "") or "")

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
    # recursion_limit защищает сам граф от бесконечных циклов внутри одного invoke
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": RECURSION_LIMIT,
    }

    _log_event(thread_id, "user_message", {"content": req.message})

    try:
        # ВАЖНО: НЕ передаём "draft": {} — иначе затираем состояние из чекпоинтера
        result = agent.invoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )
    except Exception as e:
        _log_event(thread_id, "agent_error", {"error": str(e)})
        logger.exception("Agent error in /chat thread=%s", thread_id)
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    snap = agent.get_state(config)
    if not _pending(snap):
        last = result["messages"][-1] if result.get("messages") else None
        if last is None or getattr(last, "tool_calls", None):
            result = _run_until_stable(thread_id, config)

    _log_event(thread_id, "agent_result", {
        "messages": _serialize_messages(result.get("messages", [])),
        "state": _current_state(thread_id),
    })

    return _build_response(thread_id, result)


@app.post("/confirm", response_model=ChatResponse)
def confirm(req: ConfirmRequest):
    config = {
        "configurable": {"thread_id": req.thread_id},
        "recursion_limit": RECURSION_LIMIT,
    }
    snap = agent.get_state(config)
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if not _pending(snap):
        raise HTTPException(status_code=400, detail="Нет ожидающих подтверждения действий")

    _log_event(req.thread_id, "user_confirm", {"answer": req.answer})

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=req.answer)]},
            config=config,
        )
    except Exception as e:
        _log_event(req.thread_id, "agent_error", {"error": str(e)})
        logger.exception("Agent error in /confirm thread=%s", req.thread_id)
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    snap = agent.get_state(config)
    if not _pending(snap):
        last = result["messages"][-1] if result.get("messages") else None
        if last is None or getattr(last, "tool_calls", None):
            result = _run_until_stable(req.thread_id, config)

    _log_event(req.thread_id, "agent_result", {
        "messages": _serialize_messages(result.get("messages", [])),
        "state": _current_state(req.thread_id),
    })

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


@app.post("/campaigns/{campaign_id}/generate_image", response_model=GenerateImageResponse)
def campaign_generate_image(campaign_id: int):
    """Собирает сущности кампании, генерирует картинку через GigaChat/Kandinsky."""
    c = get_campaign.invoke({"campaign_id": campaign_id})
    if isinstance(c, dict) and "errors" in c:
        raise HTTPException(status_code=404, detail=c["errors"])

    prompt = build_prompt(c)
    try:
        image_data_url = generate_image(prompt)
    except KandinskyError as e:
        logger.exception("Kandinsky error campaign=%s", campaign_id)
        raise HTTPException(status_code=502, detail=f"Kandinsky: {e}")
    except Exception as e:
        logger.exception("Unexpected error in generate_image")
        raise HTTPException(status_code=500, detail=str(e))

    return GenerateImageResponse(
        campaign_id=campaign_id,
        prompt=prompt,
        image=image_data_url,
    )