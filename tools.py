import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import tool

MOCKS = Path(__file__).parent / "mocks"


def _load(name: str) -> Any:
    return json.loads((MOCKS / name).read_text(encoding="utf-8"))


_TAG_NAMES = {
    1: "Страхование",
    2: "Кэшбэк",
    3: "Путешествия",
    4: "Карта",
    5: "Инвестиции",
    6: "Обучение",
}

_PLACE_CODES = {
    1: "mainScreenStories",
    2: "mainScreenSmartBanner",
    3: "paymentsScreen",
    4: "profileScreen",
    5: "oldPromoBlock",
    6: "cardsScreen",
    7: "mainScreenWidget",
    8: "archiveBlock",
}

_PLACE_DESCRIPTIONS = {
    1: "Сторис на главном экране",
    2: "Смарт-баннер на главном",
    3: "Экран платежей",
    4: "Профиль",
    5: "Устаревший промо-блок",
    6: "Экран карт",
    7: "Виджет на главном",
    8: "Архивный блок",
}

_PLACE_DEFAULT_BANNER = {
    1: "STORY",
    2: "SMART_BANNER",
    3: "SMART_BANNER",
    4: "SMART_BANNER",
    5: "SMART_BANNER",
    6: "SMART_BANNER",
    7: "SMART_BANNER",
    8: "SMART_BANNER",
}

_SEGMENT_LABELS = {
    "AGE_18_25": "Возраст 18–25",
    "AGE_26_45": "Возраст 26–45",
    "CITY_MSK": "Москва",
    "CITY_SPB": "Санкт-Петербург",
    "REGION_MOS_OBL": "Московская область",
    "CHANNEL_VIP": "VIP-клиенты",
    "CHANNEL_MASS": "Массовые",
    "CHANNEL_MID": "Средний сегмент",
    "CHANNEL_NEW_USER": "Новые пользователи",
    "PRODUCT_DC": "Дебетовая карта",
    "PRODUCT_AUTO_LOAN": "Автокредит",
    "PRODUCT_SUBSCRIPTION": "Подписка",
    "INTRS_TRAVEL": "Интерес: путешествия",
    "INTRS_CARS": "Интерес: авто",
    "EXC_UNSUBSCRIBED": "Отписавшиеся",
    "EXC_MORATORIUM": "Мораторий",
    "EXC_OVERCOMMUNICATED": "Перекоммуницированные",
    "EXC_EMPLOYEES": "Сотрудники",
}

_SEGMENT_TYPES = {
    "AGE": "AGE",
    "CITY": "GEO",
    "REGION": "GEO",
    "CHANNEL": "CHANNEL",
    "PRODUCT": "PRODUCT",
    "INTRS": "INTEREST",
    "EXC": "EXCLUSION",
}

_SEGMENT_COUNTS = {
    "AGE_18_25": 2_100_000,
    "AGE_26_45": 1_500_000,
    "CITY_MSK": 800_000,
    "CITY_SPB": 400_000,
    "REGION_MOS_OBL": 350_000,
    "CHANNEL_VIP": 50_000,
    "CHANNEL_MASS": 3_200_000,
    "CHANNEL_MID": 1_100_000,
    "CHANNEL_NEW_USER": 220_000,
    "PRODUCT_DC": 2_700_000,
    "PRODUCT_AUTO_LOAN": 180_000,
    "PRODUCT_SUBSCRIPTION": 640_000,
    "INTRS_TRAVEL": 310_000,
    "INTRS_CARS": 270_000,
    "EXC_UNSUBSCRIBED": 120_000,
    "EXC_MORATORIUM": 30_000,
    "EXC_OVERCOMMUNICATED": 90_000,
    "EXC_EMPLOYEES": 15_000,
}


def _collect_topics() -> list[dict]:
    seen: dict[str, dict] = {}
    for c in _load("campaigns.json"):
        t = c.get("topic")
        if t and t not in seen:
            seen[t] = {"value": t, "label": t}
    return [seen[k] for k in sorted(seen)]


def _collect_tags() -> list[dict]:
    seen: dict[int, dict] = {}
    for c in _load("campaigns.json"):
        for tid in c.get("tags", []) or []:
            if tid not in seen:
                seen[tid] = {"id": tid, "name": _TAG_NAMES.get(tid, f"Тег {tid}")}
    for tid, name in _TAG_NAMES.items():
        seen.setdefault(tid, {"id": tid, "name": name})
    return [seen[k] for k in sorted(seen)]


def _collect_places() -> list[dict]:
    seen: dict[int, dict] = {}
    for row in _load("campaign_places.json"):
        for pid in row.get("placeIds", []) or []:
            if pid in seen:
                continue
            seen[pid] = {
                "id": pid,
                "code": _PLACE_CODES.get(pid, f"place_{pid}"),
                "description": _PLACE_DESCRIPTIONS.get(pid, f"Место показа {pid}"),
                "defaultBanner": _PLACE_DEFAULT_BANNER.get(pid, "SMART_BANNER"),
                "state": "INACTIVE" if pid == 8 else "ACTIVE",
            }
    for pid in _PLACE_CODES:
        seen.setdefault(pid, {
            "id": pid,
            "code": _PLACE_CODES[pid],
            "description": _PLACE_DESCRIPTIONS.get(pid, f"Место показа {pid}"),
            "defaultBanner": _PLACE_DEFAULT_BANNER.get(pid, "SMART_BANNER"),
            "state": "INACTIVE" if pid == 8 else "ACTIVE",
        })
    return [seen[k] for k in sorted(seen)]


def _collect_segments() -> list[dict]:
    seen: dict[str, dict] = {}
    for row in _load("campaign_segments.json"):
        for code in (row.get("included") or []) + (row.get("excluded") or []):
            if code in seen:
                continue
            prefix = code.split("_")[0]
            seen[code] = {
                "code": code,
                "name": _SEGMENT_LABELS.get(code, code.replace("_", " ").title()),
                "type": _SEGMENT_TYPES.get(prefix, "OTHER"),
                "state": "ACTIVE",
                "count": _SEGMENT_COUNTS.get(code, 0),
            }
    for code, name in _SEGMENT_LABELS.items():
        if code in seen:
            continue
        prefix = code.split("_")[0]
        seen[code] = {
            "code": code,
            "name": name,
            "type": _SEGMENT_TYPES.get(prefix, "OTHER"),
            "state": "ACTIVE",
            "count": _SEGMENT_COUNTS.get(code, 0),
        }
    return [seen[k] for k in sorted(seen)]


_CAMPAIGNS: dict[int, dict] = {}
_BANNERS: dict[int, list[dict]] = {}
_CONTENTS: dict[int, list[dict]] = {}
_CREATIVES: dict[int, list[dict]] = {}
_SEGMENTS: dict[int, dict] = {}
_AUDIT: dict[int, list[dict]] = {}
_NEXT_ID = {"campaign": 1000, "banner": 2000, "content": 3000, "creative": 4000}


def _next(kind: str) -> int:
    _NEXT_ID[kind] += 1
    return _NEXT_ID[kind]


def _audit(campaign_id: int, entity: str, entity_id: int, action: str,
           changes: Optional[dict] = None, comment: Optional[str] = None) -> None:
    _AUDIT.setdefault(campaign_id, []).append({
        "entity": entity,
        "entityId": entity_id,
        "action": action,
        "changes": changes,
        "at": datetime.utcnow().isoformat(timespec="seconds"),
        "actor": "campaignManager",
        "comment": comment,
    })


def _error(code: str, message: str, field: str = "") -> dict:
    return {"code": code, "message": message, "field": field}


@tool
def get_topics() -> list[dict]:
    """Справочник тематик кампаний (фиксированный enum)."""
    return _collect_topics()


@tool
def get_tags() -> list[dict]:
    """Справочник тегов."""
    return _collect_tags()


@tool
def get_channels() -> list[dict]:
    """Справочник каналов: iOS, ANDROID, WEB."""
    return _load("channels.json")


@tool
def get_banner_types() -> list[dict]:
    """Типы баннеров: лимиты title/text, допустимые каналы."""
    return _load("banner_types.json")


@tool
def get_segments() -> list[dict]:
    """Сегменты аудитории: code, name, type, state, count."""
    return _collect_segments()


@tool
def get_places() -> list[dict]:
    """Места показа: id, code, description, defaultBanner, state."""
    return _collect_places()


@tool
def get_campaign_list() -> list[dict]:
    """GET /campaigns — список кампаний (CampaignListItemDto)."""
    result = []
    try:
        for c in _load("campaigns.json"):
            result.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "state": c.get("state"),
                "published": c.get("published"),
                "topic": c.get("topic"),
                "startDate": c.get("startDate"),
                "endDate": c.get("endDate"),
            })
    except FileNotFoundError:
        pass
    for cid, c in _CAMPAIGNS.items():
        result.append({
            "id": cid,
            "name": c["name"],
            "state": c["state"],
            "published": c["published"],
            "topic": c["topic"],
            "startDate": c["startDate"],
            "endDate": c.get("endDate"),
        })
    return result


@tool
def validate_json(kind: str, payload: dict) -> dict:
    """Валидирует JSON баннера (kind='banner') или контента (kind='promo')
    по схемам. Возвращает {ok: bool, errors: [...]}."""
    errors: list[dict] = []
    if kind == "banner":
        if "actionType" not in payload:
            errors.append(_error("BANNER_ACTION_TYPE_REQUIRED",
                                 "actionType обязателен", "actionType"))
        elif payload["actionType"] not in (
            "default", "externalLink", "openSmartLink", "closeCampaign", "doneCampaign"
        ):
            errors.append(_error("BANNER_ACTION_TYPE_INVALID",
                                 "Недопустимый actionType", "actionType"))
        if payload.get("actionType") in ("externalLink", "openSmartLink") and not payload.get("link"):
            errors.append(_error("BANNER_LINK_REQUIRED",
                                 "link обязателен при externalLink/openSmartLink", "link"))
        if payload.get("actionType") in ("closeCampaign", "doneCampaign") and payload.get("link"):
            errors.append(_error("BANNER_LINK_FORBIDDEN",
                                 "link запрещён при closeCampaign/doneCampaign", "link"))
    elif kind == "promo":
        if payload.get("role") != "promo":
            errors.append(_error("PROMO_ROLE_INVALID", "role должен быть 'promo'", "role"))
        comp = payload.get("component") or {}
        if comp.get("role") != "linearContainer":
            errors.append(_error("PROMO_CONTAINER_INVALID",
                                 "component.role должен быть 'linearContainer'", "component.role"))
        if comp.get("axis") != "v":
            errors.append(_error("PROMO_AXIS_INVALID", "axis должен быть 'v'", "component.axis"))
        comps = comp.get("components") or []
        if not (1 <= len(comps) <= 6):
            errors.append(_error("PROMO_COMPONENTS_COUNT",
                                 "components: 1..6 элементов", "component.components"))
        for i, c in enumerate(comps):
            role = c.get("role")
            if role == "text" and "format" not in c:
                errors.append(_error("PROMO_TEXT_FORMAT_REQUIRED",
                                     f"components[{i}].format обязателен", f"components[{i}].format"))
            if role == "image" and not c.get("url"):
                errors.append(_error("PROMO_IMAGE_URL_REQUIRED",
                                     f"components[{i}].url обязателен", f"components[{i}].url"))
            if role == "button" and "actionType" not in c:
                errors.append(_error("PROMO_BUTTON_ACTION_REQUIRED",
                                     f"components[{i}].actionType обязателен",
                                     f"components[{i}].actionType"))
    else:
        errors.append(_error("VALIDATE_KIND_INVALID",
                             "kind должен быть 'banner' или 'promo'", "kind"))
    return {"ok": not errors, "errors": errors}


@tool
def create_campaign(payload: dict) -> dict:
    """POST /campaigns. Создаёт DRAFT. Возвращает CampaignInfoDto с id."""
    cid = _next("campaign")
    _CAMPAIGNS[cid] = {
        "id": cid,
        "name": payload.get("name"),
        "marketingName": payload.get("marketingName"),
        "startDate": payload.get("startDate"),
        "startTime": payload.get("startTime"),
        "endDate": payload.get("endDate"),
        "endTime": payload.get("endTime"),
        "topic": (payload.get("topic") or {}).get("value"),
        "tags": [t["value"] for t in payload.get("tags", [])],
        "audienceType": payload.get("audienceType"),
        "weight": payload.get("weight", 0),
        "initialCtr": payload.get("initialCtr", 15),
        "places": [p["value"] for p in payload.get("places", [])],
        "state": "DRAFT",
        "published": False,
        "author": "campaignManager",
    }
    _BANNERS[cid] = []
    _CONTENTS[cid] = []
    _CREATIVES[cid] = []
    _SEGMENTS[cid] = {"included": [], "excluded": []}
    _audit(cid, "CAMPAIGN", cid, "CREATE")
    return {"id": cid, "state": "DRAFT", "published": False}


@tool
def update_campaign(campaign_id: int, payload: dict) -> dict:
    """PUT /campaigns/{id}. Полная замена шапки/мест."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    if c["state"] in ("ON_MODERATION", "STOPPED"):
        return {"errors": [_error("UPDATE_NOT_ALLOWED",
                                  f"Нельзя редактировать в state={c['state']}", "state")]}
    if c["state"] == "APPROVED":
        c["state"] = "DRAFT"
    elif c["state"] in ("ACTIVE", "ACTIVE_EDITING"):
        c["state"] = "ACTIVE_EDITING"
    for k in ("name", "marketingName", "startDate", "startTime",
              "endDate", "endTime", "audienceType", "weight", "initialCtr"):
        if k in payload:
            c[k] = payload[k]
    if "topic" in payload:
        c["topic"] = (payload["topic"] or {}).get("value")
    if "places" in payload:
        c["places"] = [p["value"] for p in payload["places"]]
    _audit(campaign_id, "CAMPAIGN", campaign_id, "UPDATE")
    return {"id": campaign_id, "state": c["state"]}


@tool
def put_segments(campaign_id: int, included: list[str], excluded: list[str]) -> dict:
    """PUT /campaigns/{id}/segments."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    if c["audienceType"] == "ALL_USERS" and (included or excluded):
        return {"errors": [_error("SEGMENTS_FORBIDDEN_FOR_ALL_USERS",
                                  "Сегменты запрещены при ALL_USERS", "segments")]}
    valid = {s["code"] for s in _collect_segments() if s.get("state") == "ACTIVE"}
    bad = [s for s in included + excluded if s not in valid]
    if bad:
        return {"errors": [_error("SEGMENT_INVALID",
                                  f"Неизвестный/неактивный сегмент: {bad}", "segments")]}
    _SEGMENTS[campaign_id] = {"included": included, "excluded": excluded}
    _audit(campaign_id, "SEGMENTS", campaign_id, "UPDATE")
    return {"included": included, "excluded": excluded}


@tool
def create_banner(campaign_id: int, name: str, banner_type_id: int, content: dict) -> dict:
    """POST /campaigns/{id}/banners."""
    if campaign_id not in _CAMPAIGNS:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "campaign_id")]}
    v = validate_json.invoke({"kind": "banner", "payload": content})
    if not v["ok"]:
        return {"errors": v["errors"]}
    bid = _next("banner")
    _BANNERS[campaign_id].append({
        "id": bid, "name": name, "bannerTypeId": banner_type_id, "content": content
    })
    _audit(campaign_id, "BANNER", bid, "CREATE")
    return {"id": bid, "name": name}


@tool
def create_content(campaign_id: int, name: str, content: dict) -> dict:
    """POST /campaigns/{id}/contents (contentType=PROMO)."""
    if campaign_id not in _CAMPAIGNS:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "campaign_id")]}
    v = validate_json.invoke({"kind": "promo", "payload": content})
    if not v["ok"]:
        return {"errors": v["errors"]}
    cid = _next("content")
    _CONTENTS[campaign_id].append({
        "id": cid, "name": name, "contentType": "PROMO", "content": content
    })
    _audit(campaign_id, "CONTENT", cid, "CREATE")
    return {"id": cid, "name": name}


@tool
def create_creative(campaign_id: int, name: str, banner_id: int,
                    channel_code: str, content_id: Optional[int] = None) -> dict:
    """POST /campaigns/{id}/creatives."""
    if campaign_id not in _CAMPAIGNS:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "campaign_id")]}
    channel = next((c for c in _load("channels.json") if c["code"] == channel_code), None)
    if not channel:
        return {"errors": [_error("ENTITY_NOT_FOUND", f"Канал {channel_code} не найден", "channelCode")]}
    banner = next((b for b in _BANNERS[campaign_id] if b["id"] == banner_id), None)
    if not banner:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Баннер не найден", "bannerId")]}
    btype = next((t for t in _load("banner_types.json")
                  if t["id"] == banner["bannerTypeId"]), None)
    if btype and channel_code not in btype.get("channels", []):
        return {"errors": [_error("CREATIVE_CHANNEL_NOT_ALLOWED",
                                  f"Канал {channel_code} не разрешён для {btype['code']}",
                                  "channelCode")]}
    dup = next((c for c in _CREATIVES[campaign_id]
                if c["bannerId"] == banner_id and c["channelCode"] == channel_code), None)
    if dup:
        return {"errors": [_error("CREATIVE_DUPLICATE",
                                  "Креатив с этой парой banner+channel уже есть", "channelCode")]}
    cr = _next("creative")
    _CREATIVES[campaign_id].append({
        "id": cr, "name": name, "bannerId": banner_id,
        "contentId": content_id, "channelCode": channel_code
    })
    _audit(campaign_id, "CREATIVE", cr, "CREATE")
    return {"id": cr, "name": name}


@tool
def get_campaign(campaign_id: int) -> dict:
    """GET /campaigns/{id} — CampaignDetailsDto."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    return {
        **c,
        "banners": _BANNERS.get(campaign_id, []),
        "contents": _CONTENTS.get(campaign_id, []),
        "creatives": _CREATIVES.get(campaign_id, []),
        "segments": _SEGMENTS.get(campaign_id, {"included": [], "excluded": []}),
    }


@tool
def get_warnings(campaign_id: int) -> dict:
    """GET /campaigns/{id}/warnings — {errors, warnings}."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")],
                "warnings": []}
    errors, warnings = [], []
    if not c.get("name"):
        errors.append(_error("NAME_REQUIRED", "Название обязательно", "name"))
    if not c.get("startDate") or not c.get("startTime"):
        errors.append(_error("START_REQUIRED", "Дата/время начала обязательны", "startDate"))
    if c.get("audienceType") == "SEGMENTED" and not _SEGMENTS[campaign_id]["included"]:
        errors.append(_error("SEGMENTS_REQUIRED",
                             "Для SEGMENTED нужен ≥1 включённый сегмент", "segments"))
    if not c.get("places"):
        errors.append(_error("PLACES_REQUIRED", "Нужно ≥1 место показа", "places"))
    if not c.get("tags"):
        warnings.append(_error("TAGS_MISSING", "У кампании отсутствуют теги", "tags"))
    place_ids = set(c.get("places", []))
    places = {p["id"]: p for p in _collect_places()}
    inactive = [pid for pid in place_ids if places.get(pid, {}).get("state") == "INACTIVE"]
    if inactive:
        warnings.append(_error("PLACES_INACTIVE",
                               f"Неактивные места показа: {inactive}", "places"))
    covered = {(cr["bannerId"]) for cr in _CREATIVES[campaign_id]}
    if not covered and place_ids:
        warnings.append(_error("PLACE_NO_CREATIVE",
                               "Не для всех мест показа настроены креативы", "places"))
    return {"errors": errors, "warnings": warnings}


@tool
def get_audit(campaign_id: int) -> list[dict]:
    """GET /campaigns/{id}/audit — история изменений."""
    return _AUDIT.get(campaign_id, [])


@tool
def to_moderation(campaign_id: int) -> dict:
    """POST /campaigns/{id}/to-moderation."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    if c["state"] not in ("DRAFT", "NEEDS_WORK", "ACTIVE_EDITING"):
        return {"errors": [_error("TO_MODERATION_NOT_ALLOWED",
                                  f"Нельзя из state={c['state']}", "state")]}
    w = get_warnings.invoke({"campaign_id": campaign_id})
    if w["errors"]:
        return {"errors": w["errors"]}
    c["state"] = "ON_MODERATION"
    _audit(campaign_id, "CAMPAIGN", campaign_id, "TO_MODERATION")
    return {"id": campaign_id, "state": "ON_MODERATION"}


@tool
def approve(campaign_id: int) -> dict:
    """POST /campaigns/{id}/approve (роль campaignModerator)."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    if c["state"] != "ON_MODERATION":
        return {"errors": [_error("APPROVE_NOT_ALLOWED",
                                  f"Нельзя из state={c['state']}", "state")]}
    c["state"] = "APPROVED"
    _audit(campaign_id, "CAMPAIGN", campaign_id, "APPROVE")
    return {"id": campaign_id, "state": "APPROVED"}


@tool
def decline(campaign_id: int, comment: str) -> dict:
    """POST /campaigns/{id}/decline (роль campaignModerator)."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    if c["state"] != "ON_MODERATION":
        return {"errors": [_error("DECLINE_NOT_ALLOWED",
                                  f"Нельзя из state={c['state']}", "state")]}
    if not comment:
        return {"errors": [_error("DECLINE_COMMENT_REQUIRED",
                                  "comment обязателен", "comment")]}
    c["state"] = "NEEDS_WORK"
    _audit(campaign_id, "CAMPAIGN", campaign_id, "DECLINE", comment=comment)
    return {"id": campaign_id, "state": "NEEDS_WORK"}


@tool
def activate(campaign_id: int) -> dict:
    """POST /campaigns/{id}/activate."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    if c["state"] != "APPROVED":
        return {"errors": [_error("ACTIVATE_NOT_ALLOWED",
                                  f"Нельзя из state={c['state']}", "state")]}
    c["state"] = "ACTIVE"
    c["published"] = True
    _audit(campaign_id, "CAMPAIGN", campaign_id, "ACTIVATE")
    return {"id": campaign_id, "state": "ACTIVE", "published": True}


@tool
def stop(campaign_id: int) -> dict:
    """POST /campaigns/{id}/stop."""
    c = _CAMPAIGNS.get(campaign_id)
    if not c:
        return {"errors": [_error("ENTITY_NOT_FOUND", "Кампания не найдена", "id")]}
    if not c["published"]:
        return {"errors": [_error("STOP_NOT_ALLOWED",
                                  "Остановить можно только published=true", "published")]}
    c["state"] = "STOPPED"
    c["published"] = False
    _audit(campaign_id, "CAMPAIGN", campaign_id, "STOP")
    return {"id": campaign_id, "state": "STOPPED", "published": False}


@tool
def preview_campaign(draft_json: str) -> str:
    """Рендерит превью черновика кампании (баннер + PROMO) в текст."""
    try:
        d = json.loads(draft_json)
    except json.JSONDecodeError as e:
        return f"Ошибка разбора JSON: {e}"
    lines = ["=== ПРЕВЬЮ КАМПАНИИ ==="]
    lines.append(f"Название: {d.get('name', '—')}")
    lines.append(f"Тематика: {d.get('topic', '—')}")
    lines.append(f"Аудитория: {d.get('audienceType', '—')}")
    lines.append(f"Места показа: {d.get('places', [])}")
    for i, b in enumerate(d.get("banners", []), 1):
        c = b.get("content", {})
        lines.append(f"\n[Баннер {i}] {b.get('name', '—')}")
        lines.append(f"  title: {c.get('title', '—')}")
        lines.append(f"  text:  {c.get('text', '—')}")
        lines.append(f"  actionType: {c.get('actionType', '—')}")
    for i, ct in enumerate(d.get("contents", []), 1):
        comps = (ct.get("content", {}).get("component", {}) or {}).get("components", [])
        lines.append(f"\n[PROMO {i}] {ct.get('name', '—')}: {len(comps)} компонент(ов)")
        for j, comp in enumerate(comps, 1):
            role = comp.get("role")
            if role == "text":
                lines.append(f"  {j}. text: {comp.get('text', '')[:60]}")
            elif role == "image":
                lines.append(f"  {j}. image: {comp.get('url', '')}")
            elif role == "button":
                lines.append(f"  {j}. button: {comp.get('text', '')}")
    return "\n".join(lines)


ALL_TOOLS = [
    get_topics, get_tags, get_channels, get_banner_types, get_segments, get_places,
    get_campaign_list,
    validate_json,
    create_campaign, update_campaign, put_segments,
    create_banner, create_content, create_creative,
    get_campaign, get_warnings, get_audit,
    to_moderation, approve, decline, activate, stop,
    preview_campaign,
]