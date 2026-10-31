import streamlit as st
import json
from datetime import datetime

# ============================================================
# §1. DESIGN TOKENS (Sber fintech style)
# ============================================================
st.set_page_config(page_title="Sber AI-Campaign | DevGirls", layout="wide", page_icon="💚")

TOKENS = {
    "sber_green": "#21A038",
    "sber_green_bright": "#00D046",
    "sber_green_dark": "#0B6B24",
    "bg_deep": "#0A1410",
    "bg_surface": "#122019",
    "bg_glass": "rgba(255,255,255,0.06)",
    "text_primary": "#FFFFFF",
    "text_secondary": "#A8B8AE",
    "text_muted": "#6B7C72",
    "warning": "#F5A623",
    "danger": "#E5484D",
    "info": "#3B82F6",
    "violet": "#8B7CF6",
    "border_glass": "1px solid rgba(255,255,255,0.12)",
    "glass_blur": "backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);",
    "radius_card": "22px",
    "radius_btn": "12px",
    "glow": "0 0 40px rgba(0,208,70,0.25)",
}

SBER_GRADIENT = "linear-gradient(135deg, #0B6B24 0%, #21A038 50%, #00D046 100%)"

STATE_META = {
    "DRAFT":           {"label": "Draft",          "dot": "#6B7C72", "bg": "rgba(107,124,114,0.15)", "fg": "#A8B8AE"},
    "ON_MODERATION":   {"label": "On moderation",  "dot": "#F5A623", "bg": "rgba(245,166,35,0.15)",  "fg": "#F5A623"},
    "NEEDS_WORK":      {"label": "Needs work",     "dot": "#E5484D", "bg": "rgba(229,72,77,0.15)",   "fg": "#E5484D"},
    "APPROVED":        {"label": "Approved",       "dot": "#3B82F6", "bg": "rgba(59,130,246,0.15)",  "fg": "#3B82F6"},
    "ACTIVE":          {"label": "Active",         "dot": "#00D046", "bg": "rgba(0,208,70,0.15)",    "fg": "#00D046"},
    "ACTIVE_EDITING":  {"label": "Active editing", "dot": "#F5A623", "bg": "rgba(0,208,70,0.12)",    "fg": "#00D046"},
    "STOPPED":         {"label": "Stopped",        "dot": "#4B5A50", "bg": "rgba(75,90,80,0.2)",     "fg": "#6B7C72"},
}

def state_chip(state: str, published: bool = False) -> str:
    meta = STATE_META.get(state, STATE_META["DRAFT"])
    pulse = "animation: pulse 1.6s infinite;" if state == "ACTIVE" else ""
    eye = " 👁" if published else ""
    return (
        f'<span style="display:inline-flex; align-items:center; gap:6px; '
        f'padding:4px 12px; border-radius:999px; font-size:12px; font-weight:600; '
        f'background:{meta["bg"]}; color:{meta["fg"]}; border:1px solid {meta["fg"]}33;">'
        f'<span style="width:8px; height:8px; border-radius:50%; background:{meta["dot"]}; {pulse}"></span>'
        f'{meta["label"]}{eye}</span>'
    )

# ============================================================
# SIDEBAR: theme + auth (X-User / X-Role)
# ============================================================
with st.sidebar:
    st.markdown("### 🎨 Управление стилем")
    theme_label = "☀️ Светлая экосистема" if st.session_state.get("theme_mode", False) else "🌙 Тёмная экосистема"
    theme_mode = st.toggle(theme_label, value=False, key="theme_mode")

    st.markdown("---")
    st.markdown("### 👤 Авторизация (X-User / X-Role)")
    user_login = st.text_input("Логин (X-User):", value="ivanova.a")
    user_role = st.selectbox(
        "Роль (X-Role):",
        ["campaignManager", "campaignModerator"],
        help="Менеджер собирает и правит. Модератор делает Approve / Decline."
    )

# -------- Theme tokens (light override per §1.1) --------
if theme_mode:
    bg_deep = "#F4F6F8"
    bg_surface = "#FFFFFF"
    bg_glass = "rgba(255,255,255,0.85)"
    text_primary = "#111827"
    text_secondary = "#4B5563"
    text_muted = "#6B7280"
    border_glass = "1px solid #E5E7EB"
else:
    bg_deep = TOKENS["bg_deep"]
    bg_surface = TOKENS["bg_surface"]
    bg_glass = TOKENS["bg_glass"]
    text_primary = TOKENS["text_primary"]
    text_secondary = TOKENS["text_secondary"]
    text_muted = TOKENS["text_muted"]
    border_glass = TOKENS["border_glass"]

# ============================================================
# §1, §3 — GLOBAL CSS
# ============================================================
st.markdown(f"""
<style>
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.35}} }}
.stApp {{ background: {bg_deep}; }}
h1,h2,h3,h4,h5,h6,p,span,label,div[data-testid="stMarkdownContainer"] {{
    font-family:'SB Sans Text','Inter','SF Pro','PT Sans',Arial,sans-serif;
    color: {text_primary};
}}
section[data-testid="stSidebar"] {{ background:{bg_surface} !important; border-right:{border_glass}; }}
section[data-testid="stSidebar"] * {{ color:{text_primary} !important; }}
section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] div[data-baseweb="select"] {{
    background: transparent !important; border:{border_glass} !important; color:{text_primary} !important;
}}
button[data-baseweb="tab"] {{ color:{text_secondary} !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color:{TOKENS['sber_green_bright']} !important; font-weight:700; }}
div[data-testid="stExpander"] {{ background:{bg_glass}; border:{border_glass}; border-radius:{TOKENS['radius_card']}; {TOKENS['glass_blur']} }}
div[data-testid="stExpander"] summary {{ color:{text_primary} !important; }}

.surface {{
    background:{bg_glass}; border:{border_glass}; border-radius:{TOKENS['radius_card']};
    padding:18px; {TOKENS['glass_blur']} margin-bottom:12px;
}}
.topbar {{
    display:flex; align-items:center; justify-content:space-between; gap:16px;
    background:{bg_glass}; border:{border_glass}; border-radius:{TOKENS['radius_card']};
    padding:14px 20px; {TOKENS['glass_blur']} margin-bottom:14px;
}}
.logo-check {{
    width:34px; height:34px; border-radius:10px; background:{SBER_GRADIENT};
    display:flex; align-items:center; justify-content:center; color:white; font-weight:800;
    box-shadow:{TOKENS['glow']};
}}
.topbar-user {{
    font-size:12px; color:{text_secondary}; padding:6px 12px; border-radius:999px;
    border:{border_glass}; background:rgba(255,255,255,0.04);
}}
.section-title {{ font-size:13px; color:{text_secondary}; text-transform:uppercase; letter-spacing:1px; margin:0 0 10px 0; }}

.tg-bubble {{ padding:12px 16px; border-radius:20px; margin-bottom:10px; max-width:85%; font-size:14px; line-height:1.45; color:{text_primary} !important; }}
.tg-user {{ background:rgba(33,160,56,0.25); margin-left:auto; border-bottom-right-radius:6px; border:1px solid rgba(33,160,56,0.45); }}
.tg-ai   {{ background:{bg_glass}; margin-right:auto; border-bottom-left-radius:6px; border:{border_glass}; border-left:3px solid {TOKENS['sber_green_bright']}; }}
.tg-sys  {{ background:rgba(255,255,255,0.03); border:1px dashed {text_muted}; font-family:'JetBrains Mono',monospace; font-size:12px; color:{text_secondary} !important; }}

.stButton>button {{
    background:{SBER_GRADIENT}; color:white !important; border:none;
    border-radius:{TOKENS['radius_btn']}; font-weight:600; padding:8px 14px; transition:transform .15s;
}}
.stButton>button:hover:not(:disabled) {{ transform:translateY(-1px); box-shadow:{TOKENS['glow']}; }}
.stButton>button:disabled {{ background:rgba(255,255,255,0.08) !important; color:{text_muted} !important; }}

.sber-phone {{
    background:{bg_surface}; border:8px solid {bg_surface}; border-radius:40px; padding:16px;
    max-width:340px; margin:0 auto; border:{border_glass}; box-shadow:0 15px 40px rgba(0,0,0,0.35);
}}
.phone-top {{ background:{SBER_GRADIENT}; color:white !important; padding:8px; border-radius:12px;
    text-align:center; font-weight:700; font-size:12px; letter-spacing:.4px; }}
.phone-wallet {{ background:rgba(128,128,128,0.12); border:{border_glass}; padding:12px; border-radius:16px; margin:12px 0; }}
.story-frame {{ aspect-ratio:9/16; width:100%; max-width:220px; margin:8px auto; border-radius:20px; overflow:hidden;
    background:linear-gradient(160deg,#0B6B24,#21A038); color:white; display:flex; flex-direction:column; justify-content:flex-end; padding:14px; }}
.story-frame .title {{ font-size:16px; font-weight:800; color:white !important; }}
.story-frame .text {{ font-size:11px; color:rgba(255,255,255,0.9) !important; margin-top:4px; }}
.story-frame .cta {{ margin-top:10px; text-align:center; background:white; color:#0B6B24 !important; padding:6px; border-radius:8px; font-size:11px; font-weight:700; }}

.val-error {{ background:rgba(229,72,77,0.12); border-left:3px solid {TOKENS['danger']}; padding:8px 12px; border-radius:8px; margin-bottom:6px; font-size:12px; color:{text_primary} !important; }}
.val-warn  {{ background:rgba(245,166,35,0.12); border-left:3px solid {TOKENS['warning']}; padding:8px 12px; border-radius:8px; margin-bottom:6px; font-size:12px; color:{text_primary} !important; }}

.confirm-card {{ background:rgba(245,166,35,0.10); border:1px solid {TOKENS['warning']}; border-radius:18px; padding:14px; margin-bottom:12px; }}

.audit-item {{ border-left:2px solid {TOKENS['sber_green']}; padding:6px 12px; margin-bottom:8px; font-size:12px; color:{text_secondary} !important; }}
.audit-item b {{ color:{text_primary} !important; }}

.rail-item {{ padding:10px 12px; border-radius:14px; border:{border_glass}; background:{bg_glass}; margin-bottom:8px; cursor:pointer; }}
.rail-item .name {{ font-weight:600; font-size:13px; color:{text_primary} !important; margin-bottom:6px; }}

.floating-cat {{ position:fixed; bottom:90px; right:24px; width:150px; height:150px; z-index:9999; pointer-events:none;
    filter:drop-shadow(0 10px 20px rgba(0,0,0,0.35)); transition:all .4s ease; }}
.floating-cat img {{ width:100%; height:100%; object-fit:contain; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# STATE
# ============================================================
if "campaigns" not in st.session_state:
    st.session_state.campaigns = [
        {"id": "101", "name": "Кредитка Молодежная", "state": "DRAFT", "published": False},
        {"id": "102", "name": "Вклад «Копи и копи»", "state": "ON_MODERATION", "published": False},
        {"id": "103", "name": "Ипотека. Новостройки", "state": "APPROVED", "published": False},
        {"id": "104", "name": "Кэшбэк на СберМаркет", "state": "NEEDS_WORK", "published": False},
        {"id": "105", "name": "Подписка СберПрайм", "state": "ACTIVE", "published": True},
    ]

if "active_campaign_id" not in st.session_state:
    st.session_state.active_campaign_id = "101"

if "campaign_draft" not in st.session_state:
    st.session_state.campaign_draft = {
        "id": "101",
        "name": "Кредитка Молодежная",
        "state": "DRAFT",
        "published": False,
        "topic": {"value": "CREDIT_CARDS", "label": "Кредитные карты"},
        "startDate": "—",
        "startTime": "—",
        "audienceType": {"value": "ALL_USERS", "label": "Все пользователи"},
        "places": [],
        "segments": {"included": [], "excluded": []},
        "banner": None,
        "warnings": [],
        "errors": [],
        "audit": [],
    }

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

draft = st.session_state.campaign_draft

# ============================================================
# AUDIT (§3: entity, action, changes, at, actor, comment)
# ============================================================
def log_audit(entity: str, action: str, changes, actor: str, comment: str | None = None):
    draft["audit"].append({
        "at": datetime.now().strftime("%H:%M:%S"),
        "entity": entity,
        "action": action,
        "actor": actor,
        "changes": changes,
        "comment": comment,
    })

# ============================================================
# VALIDATION (§4: errors блокируют, warnings — нет)
# ============================================================
def validate(d):
    errors, warnings = [], []
    if not d["places"]:
        errors.append("Не указаны места показа (places).")
    if d["startDate"] == "—" or d["startTime"] == "—":
        errors.append("Не задано расписание показа (startDate / startTime).")
    if not d["segments"]["included"] and d["audienceType"]["value"] == "SEGMENTED":
        errors.append("SEGMENTED без включённых сегментов.")
    if d.get("banner") is None:
        warnings.append("Не для всех мест показа настроены креативы.")
    if d["places"]:
        warnings.append("У кампании отсутствуют теги.")
        warnings.append("Некоторые места показа деактивированы.")
    if len(d.get("name", "")) > 100:
        errors.append("Название превышает лимит 100 символов для STORY.")
    d["errors"] = errors
    d["warnings"] = list(dict.fromkeys(warnings))
    return d

validate(draft)

# ============================================================
# FLOATING CAT (state-driven)
# ============================================================
state = draft.get("state", "DRAFT")
if state in ("ON_MODERATION", "ACTIVE_EDITING"):
    cat_img = "https://i.ibb.co/68QZ6K5/cat-think.png"
elif state in ("NEEDS_WORK", "STOPPED"):
    cat_img = "https://i.ibb.co/3sXbY9v/cat-sad.png"
elif state == "ACTIVE":
    cat_img = "https://i.ibb.co/1QZ6K5/cat-happy.png"
else:
    cat_img = "https://i.ibb.co/1QZ6K5/cat-happy.png"

st.markdown(f'<div class="floating-cat"><img src="{cat_img}" alt="SberCat"></div>', unsafe_allow_html=True)

# ============================================================
# TOPBAR
# ============================================================
role_badge = "Moderator" if user_role == "campaignModerator" else "Manager"
st.markdown(f"""
<div class="topbar">
  <div style="display:flex; align-items:center; gap:12px;">
    <div class="logo-check">✓</div>
    <div>
      <div style="font-weight:800; font-size:16px; color:{text_primary};">Sber AI-Campaign</div>
      <div style="font-size:11px; color:{text_secondary};">{draft['name']} · {state_chip(draft['state'], draft.get('published', False))}</div>
    </div>
  </div>
  <div style="display:flex; gap:8px; align-items:center;">
    <span class="topbar-user">X-User: {user_login}</span>
    <span class="topbar-user">X-Role: <b style="color:{TOKENS['sber_green_bright']};">{role_badge}</b></span>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# LAYOUT: Chat (left) + Tabs (right)
# ============================================================
col_chat, col_insp = st.columns([2, 1.4])

# ---------- CHAT ----------
with col_chat:
    st.markdown('<div class="section-title">💬 Агент-Оркестратор</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    if not st.session_state.chat_history:
        st.markdown(
            '<div class="tg-bubble tg-ai">🤖 <b>Агент:</b> Привет! Опишите бриф — соберу черновик, '
            'подберу сегменты и места, покажу превью перед отправкой на модерацию.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="tg-bubble tg-sys">⚙ example tools: get_segments(), suggest_places(), generate_creative()</div>',
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.chat_history:
            role = msg["role"]
            cls = {"user": "tg-user", "assistant": "tg-ai", "tool": "tg-sys"}.get(role, "tg-ai")
            st.markdown(f'<div class="tg-bubble {cls}">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Опишите бриф, например: кредитка для молодёжи, старт 5 ноября 10:00")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        text = user_input.lower()

        st.session_state.chat_history.append({
            "role": "tool",
            "content": "⚙ orchestrator.parse_brief(text) → intent, slots"
        })

        if "молодеж" in text or "кредитк" in text:
            draft["name"] = "Кредитка Молодежная"
            draft["topic"] = {"value": "CREDIT_CARDS", "label": "Кредитные карты"}
            draft["audienceType"] = {"value": "SEGMENTED", "label": "По сегментам"}
            draft["segments"]["included"] = ["SEG_YOUTH_18"]
            draft["segments"]["excluded"] = ["EXC_UNSUBSCRIBED"]
            draft["places"] = ["mainScreenStories"]
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": (
                    "🤖 <b>Агент:</b> Бриф принят. Извлёк сегмент <code>SEG_YOUTH_18</code> (18–25, ~2.4M клиентов) "
                    "и плейсмент <code>mainScreenStories</code> (STORY).<br><br>"
                    "⚠️ Не хватает расписания — <b>с какого числа и времени запускаем показ?</b>"
                ),
            })
        elif "5 ноября" in text or "10:00" in text:
            draft["startDate"] = "2026-11-05"
            draft["startTime"] = "10:00"
            draft["banner"] = {
                "title": "Кредитка Молодежная",
                "text": "Ставка 16% для студентов. Кэшбэк на всё.",
                "cta": "Оформить в 1 клик",
            }
            st.session_state.chat_history.append({
                "role": "tool",
                "content": "⚙ generate_creative(topic='CREDIT_CARDS') → banner JSON (validated)"
            })
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": (
                    "🤖 <b>Агент:</b> Расписание зафиксировано. Сгенерирован валидный креатив. "
                    "Проверьте превью справа и отправьте на модерацию."
                ),
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "🤖 <b>Агент:</b> Уточните, пожалуйста, тему кампании (например, «кредитка для молодёжи»)."
            })

        validate(draft)
        st.rerun()

    # ---------- CONFIRMATION CARD (§3.3) ----------
    if st.session_state.pending_action:
        pa = st.session_state.pending_action
        st.markdown(f"""
        <div class="confirm-card">
          <div style="font-weight:700; color:{text_primary};">⚠️ Требуется подтверждение</div>
          <div style="font-size:13px; color:{text_secondary}; margin-top:6px;">
            Действие: <b>{pa.get('method', 'POST /campaigns/{id}/' + pa['kind'])}</b><br>
            Изменения: <code>{pa['payload']}</code>
          </div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        if c1.button("✓ Подтвердить", key="confirm_action", use_container_width=True):
            kind = pa["kind"]
            if kind == "create_campaign":
                new_id = str(200 + len(st.session_state.campaigns))
                st.session_state.campaigns.append({
                    "id": new_id, "name": pa["payload"]["name"], "state": "DRAFT", "published": False
                })
                log_audit("CAMPAIGN", "CREATE", None, user_login)
            elif kind == "to_moderation":
                draft["state"] = "ON_MODERATION"
                log_audit("CAMPAIGN", "TO_MODERATION", None, user_login)
            elif kind == "approve":
                draft["state"] = "APPROVED"
                log_audit("CAMPAIGN", "APPROVE", None, user_login)
            elif kind == "decline":
                draft["state"] = "NEEDS_WORK"
                log_audit("CAMPAIGN", "DECLINE", None, user_login, pa.get("comment"))
            elif kind == "activate":
                draft["state"] = "ACTIVE"
                draft["published"] = True
                log_audit("CAMPAIGN", "ACTIVATE", {"published": {"from": False, "to": True}}, user_login)
            elif kind == "stop":
                draft["state"] = "STOPPED"
                draft["published"] = False
                log_audit("CAMPAIGN", "STOP", {"published": {"from": True, "to": False}}, user_login)
            elif kind == "delete":
                log_audit("CAMPAIGN", "DELETE", None, user_login)
                st.session_state.campaigns = [c for c in st.session_state.campaigns if c["id"] != draft["id"]]
                draft["id"] = "—"
                draft["name"] = "Не задано"
                draft["state"] = "DRAFT"
                draft["published"] = False
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "🤖 <b>Агент:</b> Кампания удалена. Можете начать новую — просто опишите бриф.",
                })
            st.session_state.pending_action = None
            st.rerun()
        if c2.button("✕ Отмена", key="cancel_action", use_container_width=True):
            st.session_state.pending_action = None
            st.rerun()

# ---------- RIGHT: TABS ----------
with col_insp:
    st.markdown('<div class="section-title">📋 Инспекция и Предпросмотр</div>', unsafe_allow_html=True)

    tab_preview, tab_passport, tab_campaigns = st.tabs(
        ["📱 Превью", "⚙️ ИТ-паспорт", "🗂 Кампании"]
    )

    # --- TAB 1: PREVIEW ---
    with tab_preview:
        banner = draft.get("banner")
        st.markdown(f"""
        <div class="sber-phone">
          <div class="phone-top">СберБанк Онлайн</div>
          <div class="phone-wallet">
            <div style="font-size:11px; color:{text_secondary};">Карты и счета</div>
            <div style="font-size:20px; font-weight:800; color:{text_primary};">129 500 ₽</div>
          </div>
          <div style="font-size:12px; font-weight:600; margin-bottom:8px; color:{text_primary};">Рекомендовано вам:</div>
          <div class="story-frame">
            <div class="title">{banner['title'] if banner else '—'}</div>
            <div class="text">{banner['text'] if banner else 'Ожидание креатива...'}</div>
            <div class="cta">{banner['cta'] if banner else 'CTA'}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="margin-top:14px;">Валидация</div>', unsafe_allow_html=True)
        if draft["errors"]:
            for e in draft["errors"]:
                st.markdown(f'<div class="val-error">⛔ {e}</div>', unsafe_allow_html=True)
        if draft["warnings"]:
            for w in draft["warnings"]:
                st.markdown(f'<div class="val-warn">⚠️ {w}</div>', unsafe_allow_html=True)
        if not draft["errors"] and not draft["warnings"]:
            st.markdown(
                f'<div class="val-warn" style="background:rgba(0,208,70,0.12); border-color:{TOKENS["sber_green"]};">✓ Валидация пройдена</div>',
                unsafe_allow_html=True,
            )

    # --- TAB 2: PASSPORT ---
    with tab_passport:
        st.markdown('<div class="surface">', unsafe_allow_html=True)
        st.write(f"**ID:** {draft['id']} · **state:** {draft['state']} · **published:** {draft['published']}")
        st.write(f"**topic:** {draft['topic']}")
        st.write(f"**audienceType:** {draft['audienceType']}")
        st.write(f"**places:** {draft['places'] or '—'}")
        st.write(f"**segments.included:** {draft['segments']['included'] or '—'}")
        st.write(f"**startDate / startTime:** {draft['startDate']} {draft['startTime']}")
        st.markdown('</div>', unsafe_allow_html=True)

        if banner:
            with st.expander("🛠 JSON креатива (как отправим в Content Broker)"):
                st.code(json.dumps({
                    "name": banner["title"],
                    "bannerTypeId": 2,
                    "content": {
                        "title": banner["title"],
                        "text": banner["text"],
                        "actionType": "openSmartLink",
                        "link": {"iOS": "sberbank://smartlink/youth", "android": "sberbank://smartlink/youth"}
                    }
                }, indent=2, ensure_ascii=False), language="json")
        else:
            st.info("JSON появится после генерации креатива.")

        st.markdown('<div class="section-title" style="margin-top:12px;">Audit</div>', unsafe_allow_html=True)
        if not draft["audit"]:
            st.caption("Пока нет записей.")
        for a in reversed(draft["audit"][-8:]):
            ch = a.get("changes")
            ch_txt = json.dumps(ch, ensure_ascii=False) if ch else "—"
            cmt = f'<br><i style="color:{TOKENS["text_muted"]};">💬 {a["comment"]}</i>' if a.get("comment") else ""
            st.markdown(
                f'<div class="audit-item"><b>{a["at"]}</b> · {a["action"]} · {a["actor"]} '
                f'<br><span style="font-size:11px;">{ch_txt}</span>{cmt}</div>',
                unsafe_allow_html=True,
            )

    # --- TAB 3: CAMPAIGNS ---
    with tab_campaigns:
        st.markdown('<div class="section-title">Список кампаний</div>', unsafe_allow_html=True)

        filter_state = st.selectbox(
            "Фильтр по state",
            ["Все", "DRAFT", "ON_MODERATION", "NEEDS_WORK", "APPROVED", "ACTIVE", "ACTIVE_EDITING", "STOPPED"],
            label_visibility="collapsed",
            key="rail_filter_state",
        )

        if st.button("➕ Новая кампания", use_container_width=True, key="btn_new_campaign"):
            st.session_state.pending_action = {
                "kind": "create_campaign",
                "payload": {"name": "Новая кампания", "topic": "NEW"},
                "method": "POST /campaigns",
            }
            st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        for c in st.session_state.campaigns:
            if filter_state != "Все" and c["state"] != filter_state:
                continue
            is_active = c["id"] == st.session_state.active_campaign_id
            border = f"2px solid {TOKENS['sber_green_bright']}" if is_active else border_glass
            st.markdown(f"""
            <div class="rail-item" style="border:{border};">
              <div class="name">{c['name']}</div>
              {state_chip(c['state'], c['published'])}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Открыть #{c['id']}", key=f"open_{c['id']}", use_container_width=True):
                st.session_state.active_campaign_id = c["id"]
                draft["id"] = c["id"]
                draft["name"] = c["name"]
                draft["state"] = c["state"]
                draft["published"] = c["published"]
                st.rerun()

# ============================================================
# LIFECYCLE (§2.3, §3, §6.1) — кнопки публикации / модерации / брокера
# ============================================================
st.markdown('<div class="section-title" style="margin-top:16px;">🔄 Жизненный цикл кампании</div>', unsafe_allow_html=True)

state = draft["state"]
published = draft["published"]
is_moderator = user_role == "campaignModerator"

# §2.3 — предикаты переходов
can_to_moderation = state in ("DRAFT", "NEEDS_WORK", "ACTIVE_EDITING") and not draft["errors"]
can_approve       = is_moderator and state == "ON_MODERATION"
can_decline       = is_moderator and state == "ON_MODERATION"
can_activate      = state == "APPROVED" and not is_moderator  # activate выполняет менеджер (после approve)
can_stop          = published is True
can_delete        = state in ("DRAFT", "NEEDS_WORK") and not published

# Tool