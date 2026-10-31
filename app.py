import streamlit as st
import json

# Настройка страницы (Широкий экран, заголовок и иконка)
st.set_page_config(page_title="DevGirls | Sber AI-Campaign", layout="wide", page_icon="💚")

# --- ТУМБЛЕР СМЕНЫ ТЕМЫ И ПАЛИТРЫ (Светлая / Hi-Tech Тёмная) ---
with st.sidebar:
    st.markdown("### 🎨 Управление стилем")
    
    # Динамический текст для тумблера
    toggle_label = "☀️ Включить светлую экосистему" if st.session_state.get('theme_mode', False) else "🌙 Включить тёмную экосистему"
    theme_mode = st.toggle(toggle_label, value=False, key="theme_mode")

    st.markdown("---")
    st.markdown("### 👤 Авторизация (ИТ-контур)")
    user_login = st.text_input("Логин сотрудника:", value="ivanova.a")
    user_role = st.selectbox(
        "Роль в системе (X-Role):",
        ["campaignManager", "campaignModerator"],
        help="Менеджер собирает и правит. Модератор делает Approve/Decline."
    )

# Определение цветов палитры Сбера на основе тумблера и референсов
if theme_mode:
    bg_color = "#0B0F19"
    text_color = "#F3F4F6"
    card_bg = "rgba(26, 32, 44, 0.65)"
    border_style = "1px solid rgba(255, 255, 255, 0.08)"
    glass_effect = "backdrop-filter: blur(16px); webkit-backdrop-filter: blur(16px);"
    chat_user_bg = "rgba(45, 55, 72, 0.7)"
    chat_ai_bg = "rgba(4, 120, 87, 0.25)"
    ai_glow = "box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);"
    phone_border = "#1E293B"
    phone_bg = "#1A1A1E"
    text_in_bubble = "#F3F4F6"
    sidebar_bg = "#111827"
    input_bg = "rgba(255,255,255,0.05)"
else:
    bg_color = "#F4F6F8"
    text_color = "#111827"  # Темно-серый/почти черный
    card_bg = "#FFFFFF"
    border_style = "1px solid #E5E7EB"
    glass_effect = ""
    chat_user_bg = "#E9ECEF"
    chat_ai_bg = "#E6F4EA"
    ai_glow = "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);"
    phone_border = "#E5E7EB"
    phone_bg = "#F3F4F6"
    text_in_bubble = "#111827"
    sidebar_bg = "#FFFFFF"
    input_bg = "#FFFFFF"

# Фирменные Градиенты Сбера (Изумрудный -> Салатовый -> Синий)
sber_gradient = "linear-gradient(135deg, #00875A 0%, #22C55E 50%, #0057B7 100%)"

# Применение глобальных стилей через CSS Injection
st.markdown(f"""
    <style>
    /* Глобальные настройки фона приложения */
    .stApp {{ background-color: {bg_color}; }}
    
    /* Базовые шрифты */
    h1, h2, h3, h4, h5, h6, p, span, label {{
        font-family: 'SB Sans Text', 'PT Sans', 'Arial', sans-serif;
    }}

    /* --- ПРИНУДИТЕЛЬНЫЙ ЦВЕТ ТЕКСТА ДЛЯ ВСЕЙ ТЕМЫ (ГЛОБАЛЬНО) --- */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stText, .stCaption,
    h1, h2, h3, h4, h5, h6, p, label, div[data-testid="stMarkdownContainer"] {{
        color: {text_color} !important;
    }}

    /* --- ФИКС ЦВЕТА ТЕКСТА ДЛЯ НАТИВНЫХ КОМПОНЕНТОВ STREAMLIT --- */
    /* Текст вкладок */
    button[data-baseweb="tab"] {{
        color: {text_color} !important;
        opacity: 0.7;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: #22C55E !important;
        opacity: 1;
        font-weight: bold;
    }}
    
    /* Текст в инпутах и селектбоксах */
    .stSelectbox div[data-baseweb="select"], 
    .stTextInput input {{
        color: {text_color} !important;
        background-color: {input_bg} !important;
        border: {border_style} !important;
    }}
    
    /* Лейблы инпутов */
    .stSelectbox label, .stTextInput label {{
        color: {text_color} !important;
        font-weight: 600;
    }}

    /* Сайдбар */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: {border_style};
    }}
    
    /* Текст внутри кастомных баблов чата */
    .chat-container-box div, .chat-container-box span, .chat-container-box p {{
        color: {text_in_bubble} !important;
    }}

    /* Сбер Градиент для главного заголовка */
    .sber-title {{
        background: {sber_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 1.5rem;
    }}

    /* СТИЛИЗАЦИЯ ЧАТА ПОД ТЕЛЕГРАМ С КАНОНАМИ СБЕРА */
    .chat-container-box {{
        background-color: {card_bg};
        border: {border_style};
        border-radius: 24px;
        padding: 20px;
        {glass_effect}
        margin-bottom: 15px;
        /* Убираем пустое пространство, если контента нет */
        display: block;
    }}
    .tg-bubble {{
        padding: 12px 18px;
        border-radius: 20px;
        margin-bottom: 12px;
        max-width: 80%;
        font-size: 14px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }}
    .tg-user {{
        background-color: {chat_user_bg};
        margin-left: auto;
        border-bottom-right-radius: 4px;
        border: {border_style};
    }}
    .tg-ai {{
        background-color: {chat_ai_bg};
        margin-right: auto;
        border-bottom-left-radius: 4px;
        border-left: 4px solid #22C55E;
        {ai_glow}
    }}

    /* ИМИТАЦИЯ СМАРТФОНА СБЕРОНЛАЙН (ПО РЕФЕРЕНСАМ) */
    .sber-phone {{
        background-color: {card_bg};
        border: 10px solid {phone_border};
        border-radius: 44px;
        padding: 20px;
        width: 100%;
        max-width: 350px;
        margin: 0 auto;
        {glass_effect}
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        color: {text_color} !important;
    }}
    .phone-top {{
        background: {sber_gradient};
        color: white !important;
        padding: 10px;
        border-radius: 14px;
        font-weight: bold;
        text-align: center;
        font-size: 13px;
        letter-spacing: 0.5px;
    }}
    .phone-wallet {{
        background-color: rgba(128, 128, 128, 0.1);
        border: {border_style};
        padding: 14px;
        border-radius: 18px;
        margin: 15px 0;
        color: {text_color} !important;
    }}
    .promo-banner {{
        background-color: {card_bg};
        border: 2px solid #22C55E;
        border-radius: 20px;
        padding: 14px;
        box-shadow: 0 8px 20px rgba(34,197,94,0.15);
        color: {text_color} !important;
    }}

    /* Кнопки */
    .stButton>button {{
        background: {sber_gradient};
        color: white !important;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        padding: 10px 20px;
        transition: transform 0.2s;
    }}
    .stButton>button:hover {{
        transform: scale(1.02);
        color: white !important;
    }}
    
    /* Экспандеры и алерты */
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] p,
    div[data-testid="stAlert"] p {{
        color: {text_color} !important;
    }}
    
    /* --- ПЛАВАЮЩИЙ КОТ СБЕРА (Внизу справа) --- */
    .floating-cat {{
        position: fixed;
        bottom: 90px;
        right: 30px;
        width: 180px;
        height: 180px;
        z-index: 9999;
        pointer-events: none;
        transition: all 0.4s ease-in-out;
        filter: drop-shadow(0px 10px 15px rgba(0,0,0,0.2));
    }}
    .floating-cat img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
    }}
    </style>
""", unsafe_allow_html=True)

# --- ЛОГИКА СОСТОЯНИЙ И ВЫБОРА КАРТИНКИ КОТА ---
state = st.session_state.get('campaign_draft', {}).get('state', 'DRAFT')

if state == "ON_MODERATION":
    cat_img = "https://i.ibb.co/68QZ6K5/cat-think.png" # Задумчивый
elif state == "NEEDS_WORK":
    cat_img = "https://i.ibb.co/3sXbY9v/cat-sad.png"   # Грустный (доработка)
elif state == "ACTIVE":
    cat_img = "https://i.ibb.co/1QZ6K5/cat-happy.png"  # Радостный (в проде)
else:
    cat_img = "https://i.ibb.co/1QZ6K5/cat-happy.png"  # Веселый (по умолчанию)

# Рендерим плавающего кота
st.markdown(f"""
    <div class="floating-cat">
        <img src="{cat_img}" alt="СберКот">
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="sber-title">💚 Сбер AI-Campaign Оркестратор | Команда DevGirls</div>', unsafe_allow_html=True)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'campaign_draft' not in st.session_state:
    st.session_state.campaign_draft = {
        "id": "—", "name": "Не задано", "state": "DRAFT", "published": "false",
        "topic": {"value": "NONE", "label": "Не задана"}, 
        "startDate": "—", "startTime": "—",
        "audienceType": {"value": "ALL_USERS", "label": "Все пользователи"}, 
        "places": [], 
        "segments": {"included": [], "excluded": []},
        "warnings": []
    }

col1, col2 = st.columns([1.1, 1])

with col1:
    st.markdown("### 💬 Агент-Оркестратор")
    
    # Рендерим контейнер только если есть сообщения или это первое сообщение
    if not st.session_state.chat_history:
        st.markdown('<div class="chat-container-box">', unsafe_allow_html=True)
        st.markdown('<div class="tg-bubble tg-ai">🤖 **AI-Агент:** Привет! Я готов собрать и валидировать рекламную кампанию по вашему текстовому брифу. Напишите параметры.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="chat-container-box">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            bubble_type = "tg-user" if msg["role"] == "user" else "tg-ai"
            st.markdown(f'<div class="tg-bubble {bubble_type}">{msg["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Введите бриф...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        is_youth = "молодеж" in user_input.lower() or "кредитк" in user_input.lower()
        is_date = "5 ноября" in user_input.lower() or "10:00" in user_input.lower()

        if is_youth:
            ai_response = (
                "🤖 **AI-Оркестратор:** Бриф принят! Подключаюсь к базам данных Сбера.\n\n"
                "• **Извлечен сегмент:** `SEG_YOUTH_18` (Молодёжь от 18 до 25 лет).\n"
                "• **Определен плейсмент:** `mainScreenStories` (Формат: STORY).\n\n"
                "⚠️ **Slot-Filling:** В запросе не хватает обязательных полей: `startDate` и `startTime`. С какого числа и времени запускаем показ рекламы?"
            )
            st.session_state.campaign_draft.update({
                "name": "Акция: Кредитные карты для студентов",
                "topic": {"value": "CREDIT_CARDS", "label": "Кредитные карты"},
                "audienceType": {"value": "SEGMENTED", "label": "По сегментам"},
                "places": ["mainScreenStories"],
                "segments": {"included": ["SEG_YOUTH_18"], "excluded": ["EXC_UNSUBSCRIBED"]},
                "warnings": ["У кампании отсутствуют теги", "Не для всех мест показа настроены креативы"]
            })
        elif is_date:
            ai_response = (
                "🤖 **AI-Оркестратор:** Расписание зафиксировано. Вызываю команду `generate_creative`.\n\n"
                "🎉 **Все обязательные слоты успешно заполнены (0 ошибок)!** Сгенерирован валидный JSON баннера. "
                "Проверьте превью экрана смартфона справа и подтвердите отправку на модерацию."
            )
            st.session_state.campaign_draft.update({
                "id": "101", "startDate": "2026-11-05", "startTime": "10:00", "state": "DRAFT"
            })
        else:
            ai_response = "🤖 **AI-Агент:** Принял информацию в контекст сессии. Корректирую параметры черновика рекламной кампании."

        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()

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
                    <div style="font-size: 11px; opacity: 0.7; color: {text_color};">Карты и счета</div>
                    <div style="font-size: 20px; font-weight: bold; margin-top: 2px; color: {text_color};">129 500 ₽</div>
                </div>
                <div style="font-weight: 600; font-size: 13px; margin-bottom: 10px; color: {text_color};">Рекомендовано вам:</div>
        """, unsafe_allow_html=True)

        if draft['id'] != "—":
            st.markdown(f"""
                <div class="promo-banner">
                    <div style="color: #00875A; font-weight: bold; font-size: 14px;">🔥 Кредитка Молодежная</div>
                    <div style="font-size: 11px; margin-top: 4px; opacity: 0.85; line-height: 1.3; color: {text_color};">Ставка 16% для студентов. Кэшбэк на всё в СберМаркете!</div>
                    <div style="background: {sber_gradient}; color: white; text-align: center; padding: 7px; border-radius: 10px; font-size: 11px; font-weight: bold; margin-top: 10px; cursor: pointer;">
                        Оформить в 1 клик
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="border: 2px dashed rgba(128,128,128,0.3); border-radius: 20px; padding: 30px; text-align: center; font-size: 12px; opacity: 0.6; color: {text_color};">
                    Ожидание автоматической генерации ИИ-креатива...
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.write(" ")

        with st.expander("🛠 Показать системный JSON баннера для Бэкенда (§2.6)"):
            if draft['id'] != "—":
                st.code(json.dumps({
                    "name": "Креатив Студенческий",
                    "bannerTypeId": 2,
                    "content": {
                        "title": "Кредитка Молодежная",
                        "text": "Ставка 16% для студентов.",
                        "actionType": "openSmartLink",
                        "link": {"iOS": "sberbank://smartlink/youth", "android": "sberbank://smartlink/youth"}
                    }
                }, indent=2, ensure_ascii=False), language="json")
            else:
                st.info("JSON-контент будет сгенерирован автоматически после заполнения паспорта.")

    with tab2:
        st.write(" ")
        st.write(f"ID кампании в БД: {draft['id']} | name: {draft['name']}")
        st.write(f"Тематика (topic): {{'value': '{draft['topic']['value']}', 'label': '{draft['topic']['label']}'}}")
        st.write(f"Аудитория (audienceType): {{'value': '{draft['audienceType']['value']}', 'label': '{draft['audienceType']['label']}'}}")
        st.write(f"Коды сегментов включения: {draft['segments']['included']}")
        st.write(f"Плейсменты (PLACES): {draft['places']}")
        st.write(f"Расписание показа: с {draft['startDate']} в {draft['startTime']}")
        st.write(f"Состояние ЖЦ (state): {draft['state']} | published (Content Broker): {draft['published']}")
        
        # --- БЛОК WARNINGS (ПРЕДУПРЕЖДЕНИЯ) ---
        if draft.get('warnings'):
            st.write(" ")
            st.warning("⚠️ **Предупреждения (не блокируют модерацию):**")
            for warn in draft['warnings']:
                st.markdown(f"- {warn}")
                
        st.write(" ")

        st.markdown("### 🛠 Управление Жизненным Циклом (API Сбера)")
        b1, b2, b3, b4 = st.columns(4)
        
        if b1.button("🚀 На модерацию", use_container_width=True):
            if draft['id'] == "—":
                st.error("Ошибка API: Обязательные слоты пусты. Сначала заполните бриф в чате.")
            else:
                st.session_state.campaign_draft["state"] = "ON_MODERATION"
                st.success("HTTP 200: Статус успешно изменен на ON_MODERATION")
                st.rerun()

        if b2.button("✅ Одобрить (Approve)", use_container_width=True):
            if user_role != "campaignModerator":
                st.error("ИБ-Ошибка [ROLE_FORBIDDEN]: Данное действие доступно только роли модератора.")
            elif draft['state'] != "ON_MODERATION":
                st.error("Ошибка бэкенда [APPROVE_NOT_ALLOWED]: Нельзя одобрить кампанию, не находящуюся на модерации.")
            else:
                st.session_state.campaign_draft["state"] = "APPROVED"
                st.success("HTTP 200: Одобрено! Статус изменен на APPROVED")
                st.rerun()

        if b3.button("⚡ Активировать (В прод)", use_container_width=True):
            if draft['state'] != "APPROVED":
                st.error("Ошибка бэкенда [ACTIVATE_NOT_ALLOWED]: Публикация в Content Broker невозможна без статуса APPROVED.")
            else:
                st.session_state.campaign_draft["state"] = "ACTIVE"
                st.session_state.campaign_draft["published"] = "true"
                st.balloons()
                st.success("🎉 Успешно выгружено в Content Broker Сбера! Показ активен.")
                st.rerun()
                
        if b4.button("❌ На доработку", use_container_width=True):
            if user_role != "campaignModerator":
                st.error("ИБ-Ошибка [ROLE_FORBIDDEN]: Данное действие доступно только роли модератора.")
            else:
                st.session_state.campaign_draft["state"] = "NEEDS_WORK"
                st.error("Кампания отправлена на доработку (NEEDS_WORK).")
                st.rerun()
