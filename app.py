import json
import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="DevGirls | Sber AI-Campaign", layout="wide", page_icon="💚")

# ---------- палитра (как у вас) ----------
with st.sidebar:
    st.markdown("### 🎨 Управление стилем")
    toggle_label = "☀️ Включить светлую экосистему" if st.session_state.get('theme_mode', False) else "🌙 Включить тёмную экосистему"
    theme_mode = st.toggle(toggle_label, value=False, key="theme_mode")
    st.markdown("---")
    st.markdown("### 👤 Авторизация (ИТ-контур)")
    user_login = st.text_input("Логин сотрудника:", value="ivanova.a")
    user_role = st.selectbox(
        "Роль в системе (X-Role):",
        ["campaignManager", "campaignModerator"],
        help="Менеджер собирает и правит. Модератор делает Approve/Decline.",
    )

if theme_mode:
    bg_color = "#0B0F19"; text_color = "#F3F4F6"; card_bg = "rgba(26, 32, 44, 0.65)"
    border_style = "1px solid rgba(255, 255, 255, 0.08)"
    glass_effect = "backdrop-filter: blur(16px); webkit-backdrop-filter: blur(16px);"
    chat_user_bg = "rgba(45, 55, 72, 0.7)"; chat_ai_bg = "rgba(4, 120, 87, 0.25)"
    ai_glow = "box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);"
    phone_border = "#1E293B"; phone_bg = "#1A1A1E"; text_in_bubble = "#F3F4F6"
    sidebar_bg = "#111827"; input_bg = "rgba(255,255,255,0.05)"
else:
    bg_color = "#F4F6F8"; text_color = "#111827"; card_bg = "#FFFFFF"
    border_style = "1px solid #E5E7EB"; glass_effect = ""
    chat_user_bg = "#E9ECEF"; chat_ai_bg = "#E6F4EA"
    ai_glow = "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);"
    phone_border = "#E5E7EB"; phone_bg = "#F3F4F6"; text_in_bubble = "#111827"
    sidebar_bg = "#FFFFFF"; input_bg = "#FFFFFF"

sber_gradient = "linear-gradient(135deg, #00875A 0%, #22C55E 50%, #0057B7 100%)"

st.markdown(f"""
<style>
.stApp {{ background-color: {bg_color}; }}
h1,h2,h3,h4,h5,h6,p,span,label {{ font-family:'SB Sans Text','PT Sans','Arial',sans-serif; }}
.stMarkdown,.stMarkdown p,.stMarkdown span,.stText,.stCaption,h1,h2,h3,h4,h5,h6,p,label,
div[data-testid="stMarkdownContainer"] {{ color:{text_color} !important; }}
button[data-baseweb="tab"] {{ color:{text_color} !important; opacity:.7; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color:#22C55E !important; opacity:1; font-weight:bold; }}
.stSelectbox div[data-baseweb="select"], .stTextInput input {{
    color:{text_color} !important; background-color:{input_bg} !important; border:{border_style} !important;
}}
.stSelectbox label, .stTextInput label {{ color:{text_color} !important; font-weight:600; }}
section[data-testid="stSidebar"] {{ background-color:{sidebar_bg} !important; border-right:{border_style}; }}
.chat-container-box div,.chat-container-box span,.chat-container-box p {{ color:{text_in_bubble} !important; }}
.sber-title {{ background:{sber_gradient}; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    font-weight:800; font-size:2.2rem; margin-bottom:1.5rem; }}
.chat-container-box {{ background-color:{card_bg}; border:{border_style}; border-radius:24px;
    padding:20px; {glass_effect} margin-bottom:15px; display:block; }}
.tg-bubble {{ padding:12px 18px; border-radius:20px; margin-bottom:12px; max-width:80%;
    font-size:14px; box-shadow:0 2px 5px rgba(0,0,0,0.02); white-space:pre-wrap; }}
.tg-user {{ background-color:{chat_user_bg}; margin-left:auto; border-bottom-right-radius:4px; border:{border_style}; }}
.tg-ai {{ background-color:{chat_ai_bg}; margin-right:auto; border-bottom-left-radius:4px;
    border-left:4px solid #22C55E; {ai_glow} }}
.sber-phone {{ background-color:{card_bg}; border:10px solid {phone_border}; border-radius:44px;
    padding:20px; width:100%; max-width:350px; margin:0 auto; {glass_effect};
    box-shadow:0 15px 35px rgba(0,0,0,0.15); color:{text_color} !important; }}
.phone-top {{ background:{sber_gradient}; color:white !important; padding:10px;
    border-radius:14px; font-weight:bold; text-align:center; font-size:13px; letter-spacing:.5px; }}
.phone-wallet {{ background-color:rgba(128,128,128,0.1); border:{border_style}; padding:14px;
    border-radius:18px; margin:15px 0; color:{text_color} !important; }}
.promo-banner {{ background-color:{card_bg}; border:2px solid #22C55E; border-radius:20px;
    padding:14px; box-shadow:0 8px 20px rgba(34,197,94,0.15); color:{text_color} !important; }}
.stButton>button {{ background:{sber_gradient}; color:white !important; border-radius:12px;
    border:none; font-weight:600; padding:10px 20px; transition:transform .2s; }}
.stButton>button:hover {{ transform:scale(1.02); color:white !important; }}
div[data-testid="stExpander"] summary, div[data-testid="stExpander"] p, div[data-testid="stAlert"] p {{
    color:{text_color} !important; }}
.floating-cat {{ position:fixed; bottom:90px; right:30px; width:180px; height:180px; z-index:9999;
    pointer-events:none; transition:all .4s ease-in-out; filter:drop-shadow(0 10px 15px rgba(0,0,0,.2)); }}
.floating-cat img {{ width:100%; height:100%; object-fit:contain; }}
</style>
""", unsafe_allow_html=True)

# ---------- сессия ----------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = False
if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []
if "campaign_state" not in st.session_state:
    st.session_state.campaign_state = "draft_not_created"
if "campaign_draft" not in st.session_state:
    st.session_state.campaign_draft = {
        "id": "—", "name": "—", "state": "—", "published": "—",
        "topic": {"value": "—", "label": "—"},
        "audienceType": {"value": "—", "label": "—"},
        "places": [], "segments": {"included": [], "excluded": []},
        "warnings": [],
    }

# ---------- API-клиент ----------
def api_chat(message: str) -> dict:
    payload = {"message": message}
    if st.session_state.thread_id:
        payload["thread_id"] = st.session_state.thread_id
    r = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def api_confirm(answer: str) -> dict:
    r = requests.post(
        f"{BACKEND_URL}/confirm",
        json={"thread_id": st.session_state.thread_id, "answer": answer},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()


def apply_response(data: dict) -> None:
    st.session_state.thread_id = data["thread_id"]
    st.session_state.pending_confirmation = data["pending_confirmation"]
    st.session_state.tool_calls = data.get("tool_calls", [])
    st.session_state.campaign_state = data.get("state", "unknown")
    st.session_state.chat_history.append(
        {"role": "assistant", "content": data.get("reply") or "…"}
    )
    # Обновляем паспорт кампании из бэкенда
    try:
        cid = st.session_state.campaign_draft.get("id")
        if st.session_state.thread_id:
            state = requests.get(
                f"{BACKEND_URL}/state/{st.session_state.thread_id}", timeout=30
            ).json()
            draft = state.get("values", {}).get("draft") or {}
            cid_from_state = draft.get("campaign_id")
            if cid_from_state:
                detail = requests.get(f"{BACKEND_URL}/campaigns/{cid_from_state}", timeout=30).json()
                if "errors" not in detail:
                    st.session_state.campaign_draft = {
                        "id": detail.get("id", "—"),
                        "name": detail.get("name", "—"),
                        "state": detail.get("state", "—"),
                        "published": str(detail.get("published", "—")),
                        "topic": {"value": detail.get("topic", "—"),
                                  "label": detail.get("topic", "—")},
                        "audienceType": {"value": detail.get("audienceType", "—"),
                                         "label": detail.get("audienceType", "—")},
                        "places": detail.get("places", []),
                        "segments": detail.get("segments", {"included": [], "excluded": []}),
                        "warnings": [],
                    }
                    warn = requests.get(
                        f"{BACKEND_URL}/campaigns/{cid_from_state}/warnings", timeout=30
                    ).json()
                    st.session_state.campaign_draft["warnings"] = [
                        w["message"] for w in warn.get("warnings", [])
                    ]
    except Exception:
        pass


# ---------- кот по состоянию ----------
state = st.session_state.campaign_state
if state == "ON_MODERATION":
    cat_img = "https://i.ibb.co/68QZ6K5/cat-think.png"
elif state == "NEEDS_WORK":
    cat_img = "https://i.ibb.co/3sXbY9v/cat-sad.png"
else:
    cat_img = "https://i.ibb.co/1QZ6K5/cat-happy.png"

st.markdown(f'<div class="floating-cat"><img src="{cat_img}" alt="СберКот"></div>', unsafe_allow_html=True)
st.markdown('<div class="sber-title">💚 Сбер AI-Campaign Оркестратор | Команда DevGirls</div>', unsafe_allow_html=True)

# ---------- чат ----------
col1, col2 = st.columns([1.1, 1])

with col1:
    st.markdown("### 💬 Агент-Оркестратор")
    if not st.session_state.chat_history:
        st.markdown(
            '<div class="chat-container-box">'
            '<div class="tg-bubble tg-ai">🤖 **AI-Агент:** Привет! Я готов собрать и валидировать рекламную кампанию по вашему текстовому брифу. Напишите параметры.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="chat-container-box">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            bubble = "tg-user" if msg["role"] == "user" else "tg-ai"
            st.markdown(
                f'<div class="tg-bubble {bubble}">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Блок подтверждения
    if st.session_state.pending_confirmation and st.session_state.tool_calls:
        st.warning("⚠️ Агент запрашивает подтверждение пишущих действий:")
        for tc in st.session_state.tool_calls:
            with st.expander(f"• {tc['name']}", expanded=True):
                st.code(json.dumps(tc.get("args", {}), indent=2, ensure_ascii=False), language="json")
        c1, c2 = st.columns(2)
        if c1.button("✅ Подтвердить (да)", use_container_width=True):
            with st.spinner("Агент выполняет действия..."):
                try:
                    data = api_confirm("да")
                    apply_response(data)
                    st.rerun()
                except requests.HTTPError as e:
                    st.error(f"Ошибка: {e.response.text}")
        if c2.button("❌ Отклонить (нет)", use_container_width=True):
            with st.spinner("Агент отменяет..."):
                try:
                    data = api_confirm("нет")
                    apply_response(data)
                    st.rerun()
                except requests.HTTPError as e:
                    st.error(f"Ошибка: {e.response.text}")

    user_input = st.chat_input("Введите бриф...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("Агент думает..."):
            try:
                data = api_chat(user_input)
                apply_response(data)
            except requests.HTTPError as e:
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": f"⚠️ Ошибка API: {e.response.text}"}
                )
        st.rerun()

# ---------- правая колонка ----------
with col2:
    st.markdown("### 📋 Инспекция и Предпросмотр")
    draft = st.session_state.campaign_draft
    tab1, tab2 = st.tabs(["📱 Превью СберОнлайн", "⚙️ ИТ-Паспорт (Доменная модель)"])

    with tab1:
        st.write(" ")
        st.markdown(f"""
            <div class="sber-phone">
                <div class="phone-top">СберБанк Онлайн</div>
                <div class="phone-wallet">
                    <div style="font-size:11px; opacity:.7; color:{text_color};">Карты и счета</div>
                    <div style="font-size:20px; font-weight:bold; margin-top:2px; color:{text_color};">129 500 ₽</div>
                </div>
                <div style="font-weight:600; font-size:13px; margin-bottom:10px; color:{text_color};">Рекомендовано вам:</div>
        """, unsafe_allow_html=True)

        banners = draft.get("banners") or []
        if banners:
            for b in banners:
                c = b.get("content", {})
                st.markdown(f"""
                    <div class="promo-banner">
                        <div style="color:#00875A; font-weight:bold; font-size:14px;">🔥 {c.get('title', '—')}</div>
                        <div style="font-size:11px; margin-top:4px; opacity:.85; line-height:1.3; color:{text_color};">{c.get('text', '')}</div>
                        <div style="background:{sber_gradient}; color:white; text-align:center; padding:7px; border-radius:10px; font-size:11px; font-weight:bold; margin-top:10px; cursor:pointer;">
                            {c.get('buttonName') or 'Открыть'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="border:2px dashed rgba(128,128,128,.3); border-radius:20px; padding:30px; text-align:center; font-size:12px; opacity:.6; color:{text_color};">
                    Ожидание автоматической генерации ИИ-креатива...
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("🛠 Показать системный JSON баннера для Бэкенда (§2.6)"):
            if banners:
                st.code(json.dumps(banners[0], indent=2, ensure_ascii=False), language="json")
            else:
                st.info("JSON-контент будет сгенерирован автоматически после заполнения паспорта.")

    with tab2:
        st.write(" ")
        st.write(f"ID кампании в БД: {draft.get('id', '—')} | name: {draft.get('name', '—')}")
        st.write(f"Тематика (topic): {draft.get('topic', {})}")
        st.write(f"Аудитория (audienceType): {draft.get('audienceType', {})}")
        st.write(f"Коды сегментов включения: {draft.get('segments', {}).get('included', [])}")
        st.write(f"Плейсменты (PLACES): {draft.get('places', [])}")
        st.write(f"Состояние ЖЦ (state): {draft.get('state', '—')} | published: {draft.get('published', '—')}")
        if draft.get("warnings"):
            st.warning("⚠️ Предупреждения (не блокируют модерацию):")
            for w in draft["warnings"]:
                st.markdown(f"- {w}")
        st.write(" ")
        st.markdown("### 🛠 Управление Жизненным Циклом (через агента)")
        st.caption("Пишущие действия выполняются через агента: они попадут в чат как запрос подтверждения.")
        b1, b2, b3, b4 = st.columns(4)

        def send(message: str):
            st.session_state.chat_history.append({"role": "user", "content": message})
            with st.spinner("Агент думает..."):
                try:
                    data = api_chat(message)
                    apply_response(data)
                except requests.HTTPError as e:
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": f"⚠️ Ошибка API: {e.response.text}"}
                    )
            st.rerun()

        if b1.button("🚀 На модерацию", use_container_width=True):
            send("Отправь кампанию на модерацию")
        if b2.button("✅ Одобрить", use_container_width=True):
            send("Одобри кампанию")
        if b3.button("⚡ Активировать", use_container_width=True):
            send("Активируй кампанию")
        if b4.button("❌ На доработку", use_container_width=True):
            send("Отклони кампанию с комментарием: требует правок")