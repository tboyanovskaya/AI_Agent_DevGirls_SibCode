import base64
import os
import time
import uuid

import requests
import urllib3
from bs4 import BeautifulSoup


AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY", "")
SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
VERIFY_SSL = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() in ("1", "true", "yes")

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://api.giga.chat/v1/chat/completions"
FILES_URL = "https://api.giga.chat/v1/files"

_token_cache: dict = {"token": None, "expires_at": 0.0}


class KandinskyError(RuntimeError):
    pass


def _get_access_token() -> str:
    """Возвращает действующий access_token GigaChat (кэширует на ~25 минут)."""
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now:
        return _token_cache["token"]

    if not AUTH_KEY:
        raise KandinskyError("GIGACHAT_AUTH_KEY не задан в окружении")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {AUTH_KEY}",
    }
    r = requests.post(
        OAUTH_URL,
        data={"scope": SCOPE},
        headers=headers,
        timeout=30,
        verify=VERIFY_SSL,
    )
    if r.status_code != 200:
        raise KandinskyError(f"OAuth error {r.status_code}: {r.text}")
    body = r.json()
    token = body.get("access_token")
    if not token:
        raise KandinskyError(f"Нет access_token в ответе: {body}")

    expires_at = body.get("expires_at")
    if isinstance(expires_at, (int, float)) and expires_at > 10**12:
        expires_at = expires_at / 1000.0  # ms → s
    if not isinstance(expires_at, (int, float)) or expires_at <= now:
        expires_at = now + 25 * 60

    _token_cache["token"] = token
    _token_cache["expires_at"] = expires_at
    return token


def _chat_completion(prompt: str) -> str:
    token = _get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": "Ты — Василий Кандинский"},
            {"role": "user", "content": prompt},
        ],
        "function_call": "auto",
    }
    r = requests.post(CHAT_URL, headers=headers, json=payload, timeout=120, verify=VERIFY_SSL)
    if r.status_code != 200:
        raise KandinskyError(f"Chat error {r.status_code}: {r.text}")
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise KandinskyError(f"Неожиданный ответ chat: {data}")


def _download_image(file_id: str) -> bytes:
    token = _get_access_token()
    r = requests.get(
        f"{FILES_URL}/{file_id}/content",
        headers={
            "Accept": "application/jpeg",
            "Authorization": f"Bearer {token}",
        },
        timeout=60,
        verify=VERIFY_SSL,
    )
    if r.status_code != 200:
        raise KandinskyError(f"Files error {r.status_code}: {r.text[:300]}")
    return r.content


def generate_image(prompt: str, width: int = 1024, height: int = 1024,
                   style: str = "DEFAULT") -> str:
    """Генерирует изображение через GigaChat и возвращает data:image/jpeg;base64,..."""
    content = _chat_completion(prompt)
    img_tag = BeautifulSoup(content, "html.parser").find("img")
    if not img_tag or not img_tag.get("src"):
        raise KandinskyError(f"В ответе нет <img src>: {content[:300]}")
    file_id = img_tag.get("src")
    raw = _download_image(file_id)
    b64 = base64.b64encode(raw).decode()
    return f"data:image/jpeg;base64,{b64}"


def build_prompt(campaign: dict) -> str:
    """Собирает промпт из сущностей кампании."""
    name = campaign.get("name") or "рекламная кампания"
    topic = campaign.get("topic") or "финансы"
    audience = campaign.get("audienceType") or "клиенты банка"

    banners = campaign.get("banners") or []
    banner_text = ""
    for b in banners[:2]:
        c = b.get("content") or {}
        parts = [c.get("title"), c.get("text")]
        banner_text = " ".join(p for p in parts if p)
        if banner_text:
            break

    places = campaign.get("places") or []
    return (
        f"Нарисуй яркую рекламную иллюстрацию для банковской кампании «{name}». "
        f"Тематика: {topic}. Аудитория: {audience}. "
        f"Стиль: современный финтех-баннер, зелёно-синяя палитра Сбера, "
        f"чистый минимализм, крупные элементы, без текста. "
        f"{('Акцент: ' + banner_text + '.') if banner_text else ''} "
        f"Места показа: {len(places)} шт. Квадратный формат."
    )