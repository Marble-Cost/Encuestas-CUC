import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
import os

# ══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Diagnóstico CostoMármol · CUC",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
#  CONSTANTES
# ══════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = "Admin123"
LOGO_PATH      = "logo_cuc.png"

COLUMNAS = [
    "timestamp",
    "nombre_taller",
    "correo",
    "p1_rentabilidad",
    "p2_tiempo_operativo",
    "p3_normatividad_aiu",
    "p4_percepcion_valor",
    "p5_inteligencia_negocio",
]

# Respuestas rápidas por módulo
QUICK_OPTIONS = {
    "p1_rentabilidad": [
        "✅ No, todo bien",
        "⚠️ Sí, una vez",
        "🔴 Sí, varias veces",
    ],
    "p2_tiempo_operativo": [
        "⚡ Menos de 1 hora",
        "⏱️ Pocas horas",
        "📅 1 a 2 días",
        "⏳ Más de 3 días",
    ],
    "p3_normatividad_aiu": [
        "✅ Nunca",
        "⚠️ 1 a 2 veces",
        "🔴 3 o más veces",
    ],
    "p4_percepcion_valor": [
        "💬 WhatsApp / texto",
        "📊 Excel",
        "📄 PDF formal",
        "💻 Sistema propio",
    ],
    "p5_inteligencia_negocio": [
        "✅ Sí, tengo registro",
        "📝 Solo apuntes",
        "🧠 Solo experiencia",
        "❌ No tengo nada",
    ],
}

# Cada entrada: (clave_db, titulo_modulo, pregunta, placeholder, razon, emoji_modulo)
PREGUNTAS = [
    (
        "p1_rentabilidad",
        "Rentabilidad Financiera",
        "¿En los últimos 3 meses ha tenido algún proyecto donde la utilidad final fue menor a la esperada? ¿Qué ocurrió y cuánto fue la diferencia aproximada?",
        "Ej: Sí, en un proyecto de cocina la utilidad fue 30% menor porque el material subió de precio y hubo desperdicio no calculado.",
        "Identifica pérdidas sistemáticas por consumibles no controlados.",
        "💰",
    ),
    (
        "p2_tiempo_operativo",
        "Tiempo Operativo",
        "¿Cuánto tiempo le toma en promedio elaborar una cotización completa desde que recibe la solicitud hasta que la envía al cliente?",
        "Ej: Me toma entre 1 y 2 días, principalmente porque debo consultar precios actualizados con proveedores.",
        "Mide si la cotización es un cuello de botella operativo.",
        "⏱️",
    ),
    (
        "p3_normatividad_aiu",
        "Normatividad AIU",
        "¿Ha tenido observaciones, ajustes o pérdida de contratos por errores en el manejo tributario (AIU, IVA u otros)? ¿Cuántas veces en el último año?",
        "Ej: Sí, dos veces en el último año me pidieron corregir el AIU en contratos con constructoras.",
        "Cuantifica el impacto económico de la informalidad normativa.",
        "📋",
    ),
    (
        "p4_percepcion_valor",
        "Percepción de Valor",
        "¿Cómo entrega actualmente sus cotizaciones (WhatsApp, Excel, PDF formal, sistema)? ¿Ha notado diferencias en la respuesta del cliente según el formato?",
        "Ej: Las envío por WhatsApp en texto; los clientes empresariales me piden PDF formal y a veces dudan del precio.",
        "Analiza si el formato afecta la tasa de cierre de negocios.",
        "📤",
    ),
    (
        "p5_inteligencia_negocio",
        "Inteligencia de Negocio",
        "¿Cuenta actualmente con algún sistema o registro que le permita identificar qué tipo de material o proyecto le deja mayor margen? Si no, ¿cómo toma esa decisión?",
        "Ej: No tengo un sistema exacto, lo decido por experiencia empírica de lo que me quedó en proyectos pasados.",
        "Evalúa el nivel de madurez analítica del sector.",
        "📊",
    ),
]

# ══════════════════════════════════════════════════════════════════
#  SESSION STATE INICIAL
# ══════════════════════════════════════════════════════════════════
_defaults = {
    "step": 0,
    "enviado": False,
    "w_nombre": "",
    "w_correo": "",
    "tema_oscuro": True,
    "r_p1": "", "r_p2": "", "r_p3": "", "r_p4": "", "r_p5": "",
    "q_p1": None, "q_p2": None, "q_p3": None, "q_p4": None, "q_p5": None,
    "_gs_error": False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

SS_KEYS = {
    "p1_rentabilidad":         "r_p1",
    "p2_tiempo_operativo":     "r_p2",
    "p3_normatividad_aiu":     "r_p3",
    "p4_percepcion_valor":     "r_p4",
    "p5_inteligencia_negocio": "r_p5",
}
QQ_KEYS = {
    "p1_rentabilidad":         "q_p1",
    "p2_tiempo_operativo":     "q_p2",
    "p3_normatividad_aiu":     "q_p3",
    "p4_percepcion_valor":     "q_p4",
    "p5_inteligencia_negocio": "q_p5",
}
TOTAL_PREGUNTAS = len(PREGUNTAS)

# ══════════════════════════════════════════════════════════════════
#  LÓGICA DINÁMICA DE COLORES (MODO CLARO / OSCURO)
# ══════════════════════════════════════════════════════════════════
if st.session_state.tema_oscuro:
    bg_main          = "#0B0E14"
    bg_card          = "#151A23"
    bg_context       = "#1A2030"
    bg_welcome_card  = "#12151E"
    text_main        = "#F2F5F8"
    text_muted       = "#8B949E"
    border_subtle    = "#30363D"
    btn_text         = "#0B0E14"
    btn_bg           = "#F2F5F8"
    logo_blend       = "normal"
    stepper_idle     = "#2A3040"
    stepper_txt_idle = "#4A5568"
    pill_bg          = "rgba(255,255,255,0.06)"
    pill_border      = "rgba(255,255,255,0.12)"
    pill_color       = "#8B949E"
    info_card_bg     = "#1A2030"
else:
    bg_main          = "#F4F6FA"
    bg_card          = "#FFFFFF"
    bg_context       = "#FFF5F5"
    bg_welcome_card  = "#FFFFFF"
    text_main        = "#0F172A"
    text_muted       = "#64748B"
    border_subtle    = "#E2E8F0"
    btn_text         = "#FFFFFF"
    btn_bg           = "#0F172A"
    logo_blend       = "multiply"
    stepper_idle     = "#E2E8F0"
    stepper_txt_idle = "#94A3B8"
    pill_bg          = "rgba(0,0,0,0.04)"
    pill_border      = "rgba(0,0,0,0.10)"
    pill_color       = "#64748B"
    info_card_bg     = "#F0F4FF"

# ══════════════════════════════════════════════════════════════════
#  CSS — DISEÑO PREMIUM MOBILE-FIRST
# ══════════════════════════════════════════════════════════════════
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {{
    --bg-main:       {bg_main};
    --bg-card:       {bg_card};
    --bg-context:    {bg_context};
    --text-main:     {text_main};
    --text-muted:    {text_muted};
    --border-subtle: {border_subtle};
    --btn-text:      {btn_text};
    --btn-bg:        {btn_bg};
    --cuc-red:       #E3000F;
    --cuc-red-hover: #B3000B;
    --cuc-red-soft:  rgba(227,0,15,0.10);
    --stepper-idle:  {stepper_idle};
    --stepper-txt:   {stepper_txt_idle};
    --pill-bg:       {pill_bg};
    --pill-border:   {pill_border};
    --pill-color:    {pill_color};
    --info-card-bg:  {info_card_bg};
    --welcome-bg:    {bg_welcome_card};
}}

html, body, [class*="css"], .stApp, .stMarkdown,
.stTextInput, .stTextArea {{
    font-family: 'Inter', sans-serif !important;
}}

#MainMenu {{ visibility: hidden !important; }}
header    {{ visibility: hidden !important; }}
footer    {{ visibility: hidden !important; }}

.stApp {{ background-color: var(--bg-main) !important; }}

/* ══ HEADER ════════════════════════════════════════════ */
.premium-header {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 18px 0 8px 0;
}}
.premium-header img {{
    height: 42px;
    object-fit: contain;
    margin-bottom: 12px;
    mix-blend-mode: {logo_blend};
}}
.premium-header h1 {{
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-main);
    margin: 0;
    letter-spacing: 0.02em;
    text-align: center;
    line-height: 1.5;
    max-width: 560px;
}}

/* ══ TARJETAS INFO (BIENVENIDA) ════════════════════════ */
.info-cards-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 0 0 24px 0;
}}
.info-card {{
    background: var(--info-card-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 22px 14px 18px 14px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.info-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.10);
}}
.info-card .ic-icon {{
    font-size: 2rem;
    display: block;
    margin-bottom: 10px;
    line-height: 1;
}}
.info-card .ic-title {{
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text-main);
    margin-bottom: 4px;
    display: block;
}}
.info-card .ic-desc {{
    font-size: 0.76rem;
    color: var(--text-muted);
    line-height: 1.45;
    display: block;
}}
.info-card.red {{
    border-color: rgba(227,0,15,0.25);
    background: var(--cuc-red-soft);
}}
.info-card.red .ic-title {{ color: var(--cuc-red); }}

/* ══ BIENVENIDA CARD ═══════════════════════════════════ */
.welcome-card {{
    background: var(--welcome-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 32px 28px 24px 28px;
    margin-bottom: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}}
.welcome-eyebrow {{
    font-size: 0.70rem;
    font-weight: 700;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 10px;
    display: block;
}}
.welcome-title {{
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text-main);
    margin: 0 0 20px 0;
    line-height: 1.3;
}}
.welcome-title span {{ color: var(--cuc-red); }}

/* ══ SAAS CARD (PREGUNTAS) ═════════════════════════════ */
.saas-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 28px 24px 24px 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}}

/* ══ STEPPER ═══════════════════════════════════════════ */
.stepper-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 20px 0 16px 0;
}}
.step-node {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.78rem;
    font-weight: 700;
    flex-shrink: 0;
    transition: all 0.25s ease;
}}
.step-node.done {{
    background: var(--cuc-red);
    color: #fff;
    border: 2px solid var(--cuc-red);
}}
.step-node.active {{
    background: transparent;
    color: var(--cuc-red);
    border: 2px solid var(--cuc-red);
    box-shadow: 0 0 0 5px rgba(227,0,15,0.14);
}}
.step-node.idle {{
    background: var(--stepper-idle);
    color: var(--stepper-txt);
    border: 2px solid var(--stepper-idle);
}}
.step-connector {{
    height: 2px;
    width: 26px;
    flex-shrink: 0;
    transition: background 0.25s ease;
}}
.step-connector.done {{ background: var(--cuc-red); }}
.step-connector.idle {{ background: var(--stepper-idle); }}

/* ══ WIZARD MODULE LABEL ═══════════════════════════════ */
.wizard-step {{
    font-size: 0.73rem;
    font-weight: 600;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
    display: block;
}}
.wizard-module-icon {{
    font-size: 2.2rem;
    display: block;
    margin-bottom: 8px;
}}
.wizard-title {{
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-main);
    line-height: 1.5;
    margin: 0 0 18px 0;
}}

/* ══ CONTEXT BOX ═══════════════════════════════════════ */
.context-box {{
    background-color: var(--bg-context);
    border-left: 3px solid var(--cuc-red);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin-bottom: 18px;
    font-size: 0.80rem;
    color: var(--text-muted);
    line-height: 1.6;
    display: flex;
    align-items: flex-start;
    gap: 8px;
}}

/* ══ VOZ HINT ══════════════════════════════════════════ */
.voz-hint {{
    font-style: italic;
    font-size: 0.80rem;
    color: var(--text-muted);
    margin-bottom: 8px;
    display: block;
    opacity: 0.75;
}}

/* ══ INPUTS ════════════════════════════════════════════ */
.stTextInput input, .stTextArea textarea {{
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid var(--border-subtle) !important;
    border-radius: 0 !important;
    color: var(--text-main) !important;
    font-size: 1.0rem !important;
    padding: 10px 0 !important;
    box-shadow: none !important;
    transition: border-color 0.2s ease !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-bottom: 2px solid var(--cuc-red) !important;
    outline: none !important;
}}
.stTextInput label, .stTextArea label {{
    font-size: 0.80rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ══ BOTONES PRINCIPALES ═══════════════════════════════ */
.stButton > button {{
    background-color: var(--btn-bg) !important;
    color: var(--btn-text) !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 16px 24px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em;
}}
.stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.18);
    opacity: 0.93;
}}
.stButton > button:active {{
    transform: translateY(0);
}}

.btn-rojo .stButton > button {{
    background: linear-gradient(135deg, #E3000F 0%, #B3000B 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 18px rgba(227,0,15,0.30) !important;
    font-size: 1.1rem !important;
    padding: 18px 24px !important;
}}
.btn-rojo .stButton > button:hover {{
    box-shadow: 0 8px 28px rgba(227,0,15,0.42) !important;
    transform: translateY(-3px);
}}

.btn-start .stButton > button {{
    background: linear-gradient(135deg, #E3000F 0%, #B3000B 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 24px rgba(227,0,15,0.36) !important;
    font-size: 1.2rem !important;
    padding: 20px 24px !important;
    border-radius: 16px !important;
    letter-spacing: 0.02em;
}}
.btn-start .stButton > button:hover {{
    box-shadow: 0 10px 32px rgba(227,0,15,0.46) !important;
    transform: translateY(-3px);
}}

.btn-outline .stButton > button {{
    background-color: transparent !important;
    color: var(--text-muted) !important;
    border: 1.5px solid var(--border-subtle) !important;
    font-size: 0.95rem !important;
    padding: 14px 24px !important;
}}
.btn-outline .stButton > button:hover {{
    color: var(--text-main) !important;
    border-color: var(--text-muted) !important;
    background: transparent !important;
}}

/* ══ ALERTA ════════════════════════════════════════════ */
.custom-alert {{
    background-color: rgba(227, 0, 15, 0.08);
    border-left: 3px solid var(--cuc-red);
    padding: 13px 15px;
    border-radius: 4px;
    color: var(--text-main);
    font-size: 0.88rem;
    margin-bottom: 16px;
    margin-top: 12px;
}}

/* ══ BARRA DE PROGRESO ═════════════════════════════════ */
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, #E3000F, #FF4D57) !important;
    border-radius: 4px !important;
}}
.stProgress > div > div {{
    background: var(--stepper-idle) !important;
    border-radius: 4px !important;
    height: 6px !important;
}}

/* ══ CONFIRMACIÓN ══════════════════════════════════════ */
.confirm-icon {{
    font-size: 3.5rem;
    display: block;
    text-align: center;
    margin-bottom: 14px;
}}
.confirm-title {{
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text-main);
    text-align: center;
    margin-bottom: 12px;
}}
.confirm-text {{
    font-size: 0.93rem;
    color: var(--text-muted);
    text-align: center;
    line-height: 1.75;
    margin-bottom: 20px;
}}
.confirm-badge {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 0.76rem;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}

/* ══ ADMIN ═════════════════════════════════════════════ */
.admin-metric {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 18px 22px;
    text-align: center;
}}
.admin-metric .value {{
    font-size: 2rem;
    font-weight: 700;
    color: var(--cuc-red);
    line-height: 1;
    margin-bottom: 4px;
}}
.admin-metric .label {{
    font-size: 0.76rem;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* ══ FOOTER ════════════════════════════════════════════ */
.minimal-footer {{
    text-align: center;
    margin-top: 44px;
    padding-bottom: 20px;
    font-size: 0.73rem;
    color: var(--text-muted);
    line-height: 1.8;
}}

/* ══ TOGGLE ════════════════════════════════════════════ */
div[data-testid="stToggle"] label p {{
    color: var(--text-muted) !important;
    font-size: 0.80rem !important;
    font-weight: 600 !important;
}}

/* ══ PILLS (st.pills / radio) ══════════════════════════ */
div[data-testid="stPills"] button, div[data-baseweb="radio"] label {{
    background: var(--pill-bg) !important;
    border: 1.5px solid var(--pill-border) !important;
    color: var(--pill-color) !important;
    border-radius: 24px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: all 0.18s ease !important;
    cursor: pointer;
}}
div[data-testid="stPills"] button[aria-selected="true"] {{
    background: var(--cuc-red-soft) !important;
    border-color: var(--cuc-red) !important;
    color: var(--cuc-red) !important;
    font-weight: 700 !important;
}}

/* ══ RESPONSIVE MOBILE ═════════════════════════════════ */
@media (max-width: 480px) {{
    .info-cards-row {{ grid-template-columns: 1fr; gap: 10px; }}
    .welcome-title {{ font-size: 1.25rem; }}
    .wizard-title {{ font-size: 1.05rem; }}
    .saas-card {{ padding: 20px 16px; }}
    .welcome-card {{ padding: 24px 18px 20px 18px; }}
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  FUNCIONES DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_conn() -> GSheetsConnection:
    return st.connection("gsheets", type=GSheetsConnection)


def cargar_datos() -> pd.DataFrame:
    try:
        conn = get_conn()
        df = conn.read(usecols=list(range(len(COLUMNAS))), ttl=60)
        df = df.dropna(how="all")
        st.session_state["_gs_error"] = False
        if df.empty:
            return pd.DataFrame(columns=COLUMNAS)
        df.columns = COLUMNAS[: len(df.columns)]
        return df
    except Exception:
        st.session_state["_gs_error"] = True
        return pd.DataFrame(columns=COLUMNAS)


def correo_existe(df: pd.DataFrame, correo: str) -> bool:
    if st.session_state.get("_gs_error", False):
        return True
    if df.empty or "correo" not in df.columns:
        return False
    return (
        correo.strip().lower()
        in df["correo"].dropna().str.strip().str.lower().values
    )


def guardar_registro(registro: dict) -> bool:
    try:
        conn = get_conn()
        df_actual = cargar_datos()
        nueva_fila = pd.DataFrame([registro])
        df_nuevo = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_nuevo)
        st.cache_resource.clear()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════
#  COMPONENTE: STEPPER VISUAL
# ══════════════════════════════════════════════════════════════════
_STEPPER_LABELS = ["01", "02", "03", "04", "05"]


def render_stepper(step_actual: int) -> None:
    partes = []
    for i, lbl in enumerate(_STEPPER_LABELS):
        num = i + 1
        if num < step_actual:
            cls, contenido = "done", "✓"
        elif num == step_actual:
            cls, contenido = "active", lbl
        else:
            cls, contenido = "idle", lbl

        titulo = PREGUNTAS[i][1]
        partes.append(
            f'<div class="step-node {cls}" title="{titulo}">{contenido}</div>'
        )
        if i < len(_STEPPER_LABELS) - 1:
            conn_cls = "done" if num < step_actual else "idle"
            partes.append(f'<div class="step-connector {conn_cls}"></div>')

    st.markdown(
        f'<div class="stepper-wrap">{"".join(partes)}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR — ACCESO ADMIN OCULTO
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 Acceso Admin")
    pwd_input = st.text_input("Contraseña", type="password", key="admin_pwd")
es_admin = (pwd_input == ADMIN_PASSWORD)


# ══════════════════════════════════════════════════════════════════
#  HEADER COMPARTIDO
# ══════════════════════════════════════════════════════════════════
def render_header() -> None:
    col_vacia, col_toggle = st.columns([4, 1])
    with col_toggle:
        st.toggle("Tema Oscuro", key="tema_oscuro")

    logo_tag = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_tag = f'<img src="data:image/jpeg;base64,{b64}" alt="Universidad de la Costa">'

    st.markdown(
        f"""
        <div class="premium-header">
            {logo_tag}
            <h1>Estudio de Rentabilidad y Eficiencia Operativa<br>
                Sector Superficies Arquitectónicas</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
#  VISTA A — PANEL DE ADMINISTRACIÓN
# ══════════════════════════════════════════════════════════════════
if es_admin:
    render_header()
    st.markdown("## 📊 Panel de Control — CostoMármol")

    df = cargar_datos()

    if st.session_state.get("_gs_error", False):
        st.error(
            "⚠️ No se pudo conectar con Google Sheets. "
            "Verifique las credenciales en secrets.toml."
        )
    elif df.empty:
        st.info("La base de datos aún no tiene registros.")
    else:
        total = len(df)
        ultima_fecha = (
            pd.to_datetime(df["timestamp"], errors="coerce").dropna().max()
        )
        ultima_str = (
            ultima_fecha.strftime("%d/%m/%Y %H:%M")
            if not pd.isnull(ultima_fecha)
            else "—"
        )
        cols_p = [c for c in COLUMNAS if c.startswith("p")]
        completos = df.dropna(subset=cols_p).shape[0]
        tasa = f"{round(completos / total * 100)}%" if total > 0 else "—"

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="admin-metric"><div class="value">{total}</div>'
                f'<div class="label">Registros totales</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="admin-metric"><div class="value">{tasa}</div>'
                f'<div class="label">Tasa de completitud</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="admin-metric">'
                f'<div class="value" style="font-size:1.05rem;line-height:1.2">{ultima_str}</div>'
                f'<div class="label">Última respuesta</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Respuestas registradas")
        st.dataframe(df, use_container_width=True, height=400)

        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥 Exportar CSV para Power BI",
            data=csv_bytes,
            file_name=f"costomarmol_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════
#  VISTA B — INTERFAZ DEL ENCUESTADO
# ══════════════════════════════════════════════════════════════════
else:
    render_header()

    # ── Pantalla de confirmación ───────────────────────────────────
    if st.session_state.enviado:
        nombre_taller = st.session_state.w_nombre or "su empresa"
        st.markdown(
            f"""
            <div class="saas-card" style="text-align:center; padding:48px 28px;">
                <span class="confirm-icon">🎉</span>
                <h2 class="confirm-title">¡Diagnóstico enviado!</h2>
                <p class="confirm-text">
                    Las respuestas de <strong>{nombre_taller}</strong> quedaron registradas
                    de forma segura.<br><br>
                    Su experiencia es clave para el desarrollo de <strong>CostoMármol</strong>.<br>
                    ¡Gracias por su tiempo!
                </p>
                <div class="confirm-badge">
                    🏛️ &nbsp;Universidad de la Costa (CUC) · Barranquilla &nbsp;|&nbsp; Uso Académico Exclusivo
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── PASO 0: Bienvenida visual ─────────────────────────────────
    if st.session_state.step == 0:

        st.markdown(
            """
            <div class="welcome-card">
                <span class="welcome-eyebrow">
                    Investigación Aplicada · Universidad de la Costa (CUC)
                </span>
                <h2 class="welcome-title">
                    Diagnóstico Rápido para<br>
                    <span>Talleres de Superficies</span>
                </h2>

                <div class="info-cards-row">
                    <div class="info-card red">
                        <span class="ic-icon">🔬</span>
                        <span class="ic-title">¿Qué es esto?</span>
                        <span class="ic-desc">Validación comercial de CostoMármol · CUC</span>
                    </div>
                    <div class="info-card">
                        <span class="ic-icon">⚡</span>
                        <span class="ic-title">Menos de 3 min</span>
                        <span class="ic-desc">Solo 5 preguntas cortas sobre su taller</span>
                    </div>
                    <div class="info-card">
                        <span class="ic-icon">🔒</span>
                        <span class="ic-title">100% Privado</span>
                        <span class="ic-desc">Protegido por Ley 1581 de 2012</span>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        nombre_input = st.text_input(
            "Empresa o Taller",
            value=st.session_state.w_nombre,
            placeholder="Nombre de su negocio",
        )
        correo_input = st.text_input(
            "Correo electrónico",
            value=st.session_state.w_correo,
            placeholder="correo@empresa.com",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="btn-start">', unsafe_allow_html=True)
        iniciar = st.button("🚀  Iniciar Diagnóstico", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if iniciar:
            nombre_ok = bool(nombre_input.strip())
            correo_ok = "@" in correo_input and "." in correo_input.split("@")[-1]

            if not nombre_ok or not correo_ok:
                st.markdown(
                    '<div class="custom-alert">'
                    "⚠️ Complete ambos campos correctamente para continuar."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                with st.spinner("Verificando registro..."):
                    df_check = cargar_datos()

                    if st.session_state.get("_gs_error", False):
                        st.markdown(
                            '<div class="custom-alert">'
                            "⚠️ No fue posible conectar con la base de datos. "
                            "Intente de nuevo en unos instantes."
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    elif correo_existe(df_check, correo_input):
                        st.markdown(
                            '<div class="custom-alert">'
                            "Este correo ya completó el diagnóstico. "
                            "Cada empresa participa una sola vez. ¡Gracias!"
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.session_state.w_nombre = nombre_input.strip()
                        st.session_state.w_correo = correo_input.strip().lower()
                        st.session_state.step = 1
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # cierra welcome-card

    # ── PASOS 1–5: Wizard de preguntas ────────────────────────────
    elif 1 <= st.session_state.step <= TOTAL_PREGUNTAS:
        idx = st.session_state.step - 1
        clave, titulo_corto, pregunta, placeholder, razon, emoji = PREGUNTAS[idx]
        ss_key    = SS_KEYS[clave]
        qq_key    = QQ_KEYS[clave]
        es_ultima = (st.session_state.step == TOTAL_PREGUNTAS)
        opciones  = QUICK_OPTIONS[clave]

        render_stepper(st.session_state.step)
        st.progress((st.session_state.step - 1) / TOTAL_PREGUNTAS)

        st.markdown(
            f"""
            <div class="saas-card" style="margin-top:14px;">
                <span class="wizard-step">
                    Módulo {st.session_state.step} de {TOTAL_PREGUNTAS}
                </span>
                <span class="wizard-module-icon">{emoji}</span>
                <h3 class="wizard-title">{pregunta}</h3>
                <div class="context-box">
                    🎯&nbsp; {razon}
                </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Selección rápida visual ──────────────────────────────
        st.markdown("**Selección rápida** *(opcional)*")
        seleccion_rapida = st.pills(
            label="Selección rápida",
            options=opciones,
            default=st.session_state.get(qq_key),
            key=f"pills_{st.session_state.step}",
            label_visibility="collapsed",
        )

        # ── Hint de voz ─────────────────────────────────────────
        st.markdown(
            '<span class="voz-hint">🎙️ Consejo: Usa el micrófono de tu teclado para responder más rápido.</span>',
            unsafe_allow_html=True,
        )

        # ── Text area detalle ────────────────────────────────────
        respuesta_actual = st.text_area(
            label="Cuéntenos más (opcional si ya eligió arriba):",
            value=st.session_state[ss_key],
            placeholder=placeholder,
            height=120,
            key=f"resp_{st.session_state.step}",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_back, col_next = st.columns([1, 2])

        with col_back:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("← Atrás", key=f"back_{st.session_state.step}", use_container_width=True):
                st.session_state[ss_key] = respuesta_actual
                st.session_state[qq_key] = seleccion_rapida
                st.session_state.step -= 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_next:
            label_next = "✅  Finalizar y Enviar" if es_ultima else "Siguiente  →"
            if es_ultima:
                st.markdown('<div class="btn-rojo">', unsafe_allow_html=True)

            if st.button(label_next, key=f"next_{st.session_state.step}", use_container_width=True):
                # Construir respuesta combinada (selección rápida + texto libre)
                texto_combinado = respuesta_actual.strip()
                if seleccion_rapida:
                    prefijo = f"[{seleccion_rapida}] "
                    if not texto_combinado:
                        texto_combinado = seleccion_rapida
                    elif not texto_combinado.startswith(prefijo):
                        texto_combinado = prefijo + texto_combinado

                if not texto_combinado:
                    st.markdown(
                        '<div class="custom-alert">'
                        "⚠️ Elige una opción o escribe una respuesta antes de continuar."
                        "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.session_state[ss_key] = texto_combinado
                    st.session_state[qq_key] = seleccion_rapida

                    if es_ultima:
                        registro = {
                            "timestamp":               datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "nombre_taller":           st.session_state.w_nombre,
                            "correo":                  st.session_state.w_correo,
                            "p1_rentabilidad":         st.session_state.r_p1,
                            "p2_tiempo_operativo":     st.session_state.r_p2,
                            "p3_normatividad_aiu":     st.session_state.r_p3,
                            "p4_percepcion_valor":     st.session_state.r_p4,
                            "p5_inteligencia_negocio": st.session_state.r_p5,
                        }
                        with st.spinner("Registrando sus respuestas..."):
                            if guardar_registro(registro):
                                st.session_state.enviado = True
                                st.rerun()
                            else:
                                st.markdown(
                                    '<div class="custom-alert">'
                                    "⚠️ Ocurrió un error al guardar. Intente de nuevo. "
                                    "Si el problema persiste, contacte al equipo de investigación."
                                    "</div>",
                                    unsafe_allow_html=True,
                                )
                    else:
                        st.session_state.step += 1
                        st.rerun()

            if es_ultima:
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # cierra saas-card

    # ── Footer ─────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="minimal-footer">
            Protegido por Ley 1581 de 2012 (Habeas Data) · Uso Académico Exclusivo<br>
            Universidad de la Costa (CUC) · Barranquilla, Colombia<br>
            Validación Comercial — <strong>CostoMármol</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
