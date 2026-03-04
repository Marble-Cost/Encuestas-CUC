import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
import os

# ══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PÁGINA  ← debe ser el primer comando Streamlit
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Diagnóstico Operativo · CUC",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
#  CONSTANTES
# ══════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = "Admin123"
LOGO_PATH      = "logo_cuc.png"

# Encabezados exactos que debe tener la fila 1 de la hoja de Google Sheets
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

PREGUNTAS = [
    (
        "p1_rentabilidad",
        "1. Rentabilidad: ¿En los últimos 3 meses ha tenido algún proyecto donde la utilidad final fue menor a la esperada? ¿Qué ocurrió y cuánto fue la diferencia aproximada?",
        "Escriba su respuesta aquí. Ej: Sí, en un proyecto de cocina la utilidad fue 30% menor porque el material subió de precio…",
    ),
    (
        "p2_tiempo_operativo",
        "2. Tiempo operativo: ¿Cuánto tiempo le toma en promedio elaborar una cotización completa desde que recibe la solicitud hasta que la envía al cliente?",
        "Escriba su respuesta aquí. Ej: Me toma entre 1 y 2 días, principalmente porque debo consultar precios con proveedores…",
    ),
    (
        "p3_normatividad_aiu",
        "3. Normatividad AIU: ¿Ha tenido observaciones, ajustes o pérdida de contratos por errores en el manejo tributario (AIU, IVA u otros)? ¿Cuántas veces en el último año?",
        "Escriba su respuesta aquí. Ej: Sí, dos veces en el último año me pidieron corregir el AIU en contratos con empresas…",
    ),
    (
        "p4_percepcion_valor",
        "4. Percepción de valor: ¿Cómo entrega actualmente sus cotizaciones (WhatsApp, Excel, PDF formal, sistema)? ¿Ha notado diferencias en la respuesta del cliente según el formato?",
        "Escriba su respuesta aquí. Ej: Las envío por WhatsApp en una foto escrita a mano; los clientes empresariales me piden PDF…",
    ),
    (
        "p5_inteligencia_negocio",
        "5. Inteligencia de negocio: ¿Cuenta actualmente con algún sistema o registro que le permita identificar qué tipo de material (granito, sinterizado, etc.) o proyecto le deja mayor margen? Si no, ¿cómo toma esa decisión?",
        "Escriba su respuesta aquí. Ej: No tengo un sistema, lo decido por experiencia o según cómo me fue en proyectos anteriores…",
    ),
]

# ══════════════════════════════════════════════════════════════════
#  CSS — COMPLETAMENTE ADAPTATIVO AL TEMA (CLARO / OSCURO)
#
#  Principios aplicados:
#  1. CERO colores de fondo hardcodeados en tarjetas o body.
#     Todos los fondos usan var(--background-color) y
#     var(--secondary-background-color), las variables nativas
#     que Streamlit actualiza al cambiar de tema.
#  2. Los colores de texto usan var(--text-color) para adaptarse.
#  3. El logo JPG con fondo negro usa mix-blend-mode: multiply en
#     modo claro → el fondo negro desaparece; en modo oscuro se
#     desactiva para que el logo se vea con normalidad.
#  4. El selector de fuente está acotado al contenido de la app,
#     no a los menús nativos de Streamlit, para evitar overflow.
# ══════════════════════════════════════════════════════════════════
CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,600;0,700;0,800;1,300;1,400&display=swap');

/* ── Variables CUC: SOLO colores de marca, nunca fondos fijos ── */
:root {
    --cuc-red:      #E3000F;
    --cuc-red-dark: #B3000B;
    --cuc-red-a08:  rgba(227, 0, 15, 0.08);
    --cuc-red-a18:  rgba(227, 0, 15, 0.18);
    --cuc-red-a35:  rgba(227, 0, 15, 0.35);
    --success:      #16A34A;
    --success-a10:  rgba(22, 163, 74, 0.10);
    --warning:      #D97706;
    --warning-a10:  rgba(217, 119, 6, 0.10);
    --border-muted: rgba(127, 127, 127, 0.20);
}

/* ── Fuente aplicada SOLO al contenido de la app.
   Excluye menús nativos de Streamlit (toolbar, dropdowns)
   para evitar que el texto de esos elementos se desborde. ── */
.stApp,
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
.stTextInput, .stTextArea, .stButton,
.stDownloadButton, .stMarkdown,
.stMetric, .stDataFrame, .stCaption {
    font-family: 'Montserrat', sans-serif;
}

/* ── Fondo de la app: variable nativa de Streamlit ── */
.stApp {
    background-color: var(--background-color) !important;
}

/* ════════════════════════════════════════════
   HEADER — grid responsivo + logo blend
════════════════════════════════════════════ */
.cuc-header {
    display: grid;
    grid-template-columns: 175px 1fr;
    align-items: center;
    gap: 20px;
    padding-bottom: 18px;
    border-bottom: 3px solid var(--cuc-red);
    margin-bottom: 28px;
}

/* En móvil: apilar centrado sin desproporción */
@media (max-width: 520px) {
    .cuc-header {
        grid-template-columns: 1fr;
        gap: 12px;
        text-align: center;
    }
    .logo-wrap { justify-content: center; }
    .logo-wrap img { max-width: 120px; }
}

.logo-wrap {
    display: flex;
    align-items: center;
}

.logo-wrap img {
    width: 100%;
    max-width: 175px;
    height: auto;
    object-fit: contain;
    display: block;
    border-radius: 4px;
    /* MODO CLARO: el negro del JPG desaparece fundiéndose con el fondo blanco */
    mix-blend-mode: multiply;
    transition: mix-blend-mode 0.2s;
}

/* MODO OSCURO: desactivar blend para que el logo se vea normal */
@media (prefers-color-scheme: dark) {
    .logo-wrap img { mix-blend-mode: normal; }
}
/* Streamlit inyecta data-theme en el body según el tema activo */
[data-theme="dark"]  .logo-wrap img { mix-blend-mode: normal   !important; }
[data-theme="light"] .logo-wrap img { mix-blend-mode: multiply !important; }

.header-text h2 {
    font-family: 'Montserrat', sans-serif;
    font-size: clamp(1.05rem, 3vw, 1.45rem);
    font-weight: 800;
    color: var(--cuc-red);
    margin: 0 0 4px 0;
    line-height: 1.2;
}
.header-text .header-sub {
    font-size: 0.70rem;
    color: var(--text-color);
    opacity: 0.50;
    margin: 0;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ════════════════════════════════════════════
   BANNER INTRODUCTORIO — fondo adaptativo
════════════════════════════════════════════ */
.banner-intro {
    background: var(--cuc-red-a08);
    border: 1px solid var(--cuc-red-a18);
    border-left: 4px solid var(--cuc-red);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 22px;
}
.banner-intro .b-title {
    font-family: 'Montserrat', sans-serif;
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--cuc-red);
    margin: 0 0 6px 0;
}
.banner-intro .b-body {
    font-family: 'Montserrat', sans-serif;
    font-size: 0.84rem;
    color: var(--text-color);
    opacity: 0.80;
    margin: 0;
    line-height: 1.65;
}

/* ════════════════════════════════════════════
   SECTION LABEL (cabecera de sección)
════════════════════════════════════════════ */
.section-label {
    font-family: 'Montserrat', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--cuc-red-a18);
    margin-bottom: 16px;
    margin-top: 8px;
}

/* ════════════════════════════════════════════
   AVISO PRIVACIDAD — fondo adaptativo
════════════════════════════════════════════ */
.privacy-notice {
    background: var(--cuc-red-a08);
    border-left: 3px solid var(--cuc-red-dark);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 4px 0 20px 0;
}
.privacy-notice p {
    font-family: 'Montserrat', sans-serif;
    font-size: 0.72rem;
    font-style: italic;
    color: var(--text-color);
    opacity: 0.65;
    margin: 0;
    line-height: 1.6;
}

/* ════════════════════════════════════════════
   LABELS DE CAMPOS — color adaptativo
════════════════════════════════════════════ */
.stTextInput label,
.stTextArea label,
.stPasswordInput label {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    line-height: 1.5 !important;
    margin-bottom: 6px !important;
    color: var(--text-color) !important;
}

/* ════════════════════════════════════════════
   INPUTS — fondo y borde adaptativos
════════════════════════════════════════════ */
.stTextInput input,
.stTextArea textarea,
.stPasswordInput input {
    background: var(--secondary-background-color) !important;
    border: 1.5px solid var(--border-muted) !important;
    border-radius: 9px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 0.95rem !important;
    color: var(--text-color) !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stPasswordInput input:focus {
    border-color: var(--cuc-red) !important;
    box-shadow: 0 0 0 3px var(--cuc-red-a18) !important;
    outline: none !important;
}

/* Espaciado entre preguntas */
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stTextArea"]) {
    margin-bottom: 28px !important;
}
.stTextArea { margin-bottom: 24px !important; }

/* ════════════════════════════════════════════
   BOTÓN PRINCIPAL — rojo CUC
════════════════════════════════════════════ */
.stButton > button {
    background: var(--cuc-red) !important;
    color: #FFFFFF !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.03em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.85rem 2.5rem !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow: 0 5px 20px var(--cuc-red-a35) !important;
    transition: background 0.2s, transform 0.12s, box-shadow 0.2s !important;
    margin-top: 8px !important;
}
.stButton > button:hover {
    background: var(--cuc-red-dark) !important;
    box-shadow: 0 7px 26px rgba(227, 0, 15, 0.50) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ════════════════════════════════════════════
   BOTÓN ATRÁS (wizard) — override del rojo
   Se aplica al wrapper .wizard-back-col
════════════════════════════════════════════ */
.wizard-back-col .stButton > button {
    background: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    border: 1.5px solid var(--border-muted) !important;
    box-shadow: none !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    opacity: 0.75;
}
.wizard-back-col .stButton > button:hover {
    border-color: var(--cuc-red) !important;
    color: var(--cuc-red) !important;
    background: var(--secondary-background-color) !important;
    box-shadow: none !important;
    transform: none !important;
    opacity: 1;
}

/* ════════════════════════════════════════════
   BOTÓN DESCARGA
════════════════════════════════════════════ */
.stDownloadButton > button {
    background: var(--cuc-red) !important;
    color: #FFFFFF !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    box-shadow: 0 4px 14px var(--cuc-red-a35) !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    background: var(--cuc-red-dark) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(227, 0, 15, 0.45) !important;
}

/* ════════════════════════════════════════════
   ALERTAS — fondos semitransparentes adaptativos
   (sin ningún color de fondo fijo como #FFF3E0)
════════════════════════════════════════════ */
.alert-success {
    background: var(--success-a10);
    border: 1.5px solid rgba(22, 163, 74, 0.30);
    border-radius: 12px;
    padding: 22px 24px;
    text-align: center;
    margin-top: 14px;
}
.alert-success .as-icon {
    font-size: 2rem;
    display: block;
    margin-bottom: 8px;
}
.alert-success .as-title {
    font-family: 'Montserrat', sans-serif;
    color: var(--success);
    font-weight: 700;
    font-size: 1.05rem;
    margin: 0 0 6px;
}
.alert-success .as-body {
    font-family: 'Montserrat', sans-serif;
    color: var(--text-color);
    opacity: 0.70;
    font-weight: 400;
    font-size: 0.84rem;
    margin: 0;
    line-height: 1.55;
}

.alert-duplicate {
    background: var(--warning-a10);
    border: 1.5px solid rgba(217, 119, 6, 0.30);
    border-radius: 12px;
    padding: 20px 22px;
    text-align: center;
}
.alert-duplicate p {
    font-family: 'Montserrat', sans-serif;
    color: var(--warning);
    font-weight: 600;
    font-size: 0.95rem;
    margin: 0;
    line-height: 1.55;
}

/* ════════════════════════════════════════════
   SIDEBAR — panel admin con fondo institucional fijo.
   Se mantiene oscuro intencionalmente: es un panel
   de acceso seguro, no debe seguir el tema público.
════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #1A0505 0%, #3D0B0B 100%) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] small {
    color: #F0DADA !important;
    font-family: 'Montserrat', sans-serif !important;
}
[data-testid="stSidebar"] .stTextInput label {
    color: #F0DADA !important;
    font-size: 0.88rem !important;
    font-family: 'Montserrat', sans-serif !important;
}
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
}

/* ════════════════════════════════════════════
   MÉTRICAS ADMIN — fondo adaptativo
════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: var(--secondary-background-color) !important;
    border: 1px solid var(--cuc-red-a18) !important;
    border-radius: 10px !important;
    padding: 16px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Montserrat', sans-serif !important;
    color: var(--cuc-red) !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
}
[data-testid="stMetricLabel"] p {
    color: var(--text-color) !important;
    opacity: 0.55 !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ════════════════════════════════════════════
   DATAFRAME — borde adaptativo
════════════════════════════════════════════ */
.stDataFrame {
    border: 1px solid var(--border-muted) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ════════════════════════════════════════════
   BADGE ADMIN
════════════════════════════════════════════ */
.admin-badge {
    display: inline-block;
    background: var(--cuc-red);
    color: #FFFFFF;
    font-family: 'Montserrat', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 12px;
}

/* ════════════════════════════════════════════
   FOOTER — color y borde adaptativos
════════════════════════════════════════════ */
.footer-cuc {
    font-family: 'Montserrat', sans-serif;
    text-align: center;
    padding: 28px 0 14px;
    font-size: 0.70rem;
    border-top: 1px solid var(--border-muted);
    margin-top: 36px;
    color: var(--text-color);
    opacity: 0.42;
}
.footer-cuc strong {
    color: var(--cuc-red);
    opacity: 1;
}

/* ════════════════════════════════════════════
   MENÚ NATIVO STREAMLIT — prevenir desbordamiento
════════════════════════════════════════════ */
[role="menu"], [role="menuitem"], [role="option"],
div[class*="dropdown"], ul[class*="menu"], li[class*="menu"],
[data-testid="stToolbarActionButtonTooltip"] {
    font-family: inherit !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

/* ════════════════════════════════════════════
   WIZARD — Estilos exclusivos del flujo paso a paso
════════════════════════════════════════════ */

/* Indicador "Pregunta N de 5" */
.wizard-step-indicator {
    font-family: 'Montserrat', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.10em;
    text-align: center;
    margin-bottom: 10px;
}

/* Tarjeta contenedora de cada pregunta */
.wizard-question-card {
    background: var(--secondary-background-color);
    border: 1px solid var(--border-muted);
    border-top: 3px solid var(--cuc-red);
    border-radius: 14px;
    padding: 30px 28px 10px;
    margin-bottom: 18px;
}

/* Texto de la pregunta grande y legible */
.wizard-question-text {
    font-family: 'Montserrat', sans-serif;
    font-size: 1.18rem;
    font-weight: 700;
    color: var(--text-color);
    line-height: 1.55;
    margin: 0 0 22px 0;
}

/* HR */
hr { border-color: var(--border-muted) !important; }
</style>
"""

# ══════════════════════════════════════════════════════════════════
#  INYECTAR CSS
# ══════════════════════════════════════════════════════════════════
st.markdown(CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  CONEXIÓN A GOOGLE SHEETS
#
#  Requiere .streamlit/secrets.toml con la sección [connections.gsheets].
#  Ver README.md para instrucciones de configuración completas.
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_conn() -> GSheetsConnection:
    """Retorna la conexión cacheada a Google Sheets."""
    return st.connection("gsheets", type=GSheetsConnection)


def cargar_datos() -> pd.DataFrame:
    """
    Lee todos los registros desde Google Sheets.
    ttl=60 → refresca el caché cada 60 segundos sin bloquear la app.
    """
    try:
        conn = get_conn()
        df = conn.read(usecols=list(range(len(COLUMNAS))), ttl=60)
        df = df.dropna(how="all")
        if df.empty:
            return pd.DataFrame(columns=COLUMNAS)
        df.columns = COLUMNAS[: len(df.columns)]
        return df
    except Exception as e:
        st.error(f"⚠️ Error al leer Google Sheets: {e}")
        return pd.DataFrame(columns=COLUMNAS)


def correo_existe(df: pd.DataFrame, correo: str) -> bool:
    """Verifica duplicados consultando los datos de Google Sheets."""
    if df.empty or "correo" not in df.columns:
        return False
    return correo.strip().lower() in (
        df["correo"].dropna().str.strip().str.lower().values
    )


def guardar_registro(registro: dict) -> bool:
    """
    Añade una nueva fila a Google Sheets usando conn.update().
    No escribe ningún archivo local.
    """
    try:
        conn = get_conn()
        df_actual = cargar_datos()
        nueva_fila = pd.DataFrame([registro])
        df_nuevo = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_nuevo)          # ← escribe directo en la nube
        st.cache_resource.clear()           # fuerza lectura fresca en el próximo cargar_datos()
        return True
    except Exception as e:
        st.error(f"⚠️ Error al guardar en Google Sheets: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
#  SESSION STATE
#  step = 0          → Pantalla de bienvenida (nombre + correo)
#  step = 1 … 5      → Una pregunta por pantalla (wizard)
#  enviado = True     → Pantalla de confirmación final
#  w_nombre / w_correo → Identificación persistida entre pasos
#  r_p1 … r_p5        → Respuestas temporales (persisten al retroceder)
# ══════════════════════════════════════════════════════════════════
_defaults = {
    "step":     0,
    "enviado":  False,
    "w_nombre": "",
    "w_correo": "",
    "r_p1":     "",
    "r_p2":     "",
    "r_p3":     "",
    "r_p4":     "",
    "r_p5":     "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════════
#  SIDEBAR — ACCESO ADMIN (siempre visible al abrir el panel lateral)
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 Acceso Administrador")
    st.markdown("---")
    pwd_input = st.text_input(
        "Contraseña",
        type="password",
        placeholder="Ingrese la contraseña…",
        key="admin_pwd",
    )
    if pwd_input and pwd_input != ADMIN_PASSWORD:
        st.error("Contraseña incorrecta.")
    st.markdown("---")
    st.markdown(
        "<small style='opacity:0.45;'>Panel de administración CUC · Investigación académica</small>",
        unsafe_allow_html=True,
    )

es_admin = (pwd_input == ADMIN_PASSWORD)

# ══════════════════════════════════════════════════════════════════
#  HEADER — logo con mix-blend + grid responsivo
# ══════════════════════════════════════════════════════════════════
def render_header() -> None:
    """Renderiza el header institucional con logo y título."""
    logo_tag = ""
    if os.path.exists(LOGO_PATH):
        ext  = LOGO_PATH.rsplit(".", 1)[-1].lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_tag = f'<img src="data:{mime};base64,{b64}" alt="Logo Universidad de la Costa CUC">'

    st.markdown(f"""
    <div class="cuc-header">
        <div class="logo-wrap">{logo_tag}</div>
        <div class="header-text">
            <h2>Diagnóstico Operativo</h2>
            <p class="header-sub">Transformadores de Superficies · Investigación CUC 2026</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  VISTA 2 — PANEL DE ADMINISTRACIÓN
# ══════════════════════════════════════════════════════════════════
if es_admin:
    render_header()
    st.markdown('<div class="admin-badge">🛡 Panel de Administración</div>', unsafe_allow_html=True)
    st.markdown("## 📊 Datos Recolectados")

    with st.spinner("Cargando datos desde Google Sheets…"):
        df = cargar_datos()

    total          = len(df)
    correos_unicos = df["correo"].nunique() if not df.empty else 0
    ultimo         = "—"
    if not df.empty and "timestamp" in df.columns:
        valores = df["timestamp"].dropna()
        ultimo  = str(valores.iloc[-1])[:10] if not valores.empty else "—"

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total de registros", total)
    with col2: st.metric("Correos únicos", correos_unicos)
    with col3: st.metric("Último registro", ultimo)

    st.markdown("---")

    if df.empty:
        st.info("Aún no hay registros en Google Sheets.")
    else:
        st.markdown("### 📋 Tabla de Respuestas")
        df_display = df.rename(columns={
            "timestamp":               "Fecha/Hora",
            "nombre_taller":           "Nombre del Taller",
            "correo":                  "Correo",
            "p1_rentabilidad":         "P1 – Rentabilidad",
            "p2_tiempo_operativo":     "P2 – Tiempo Operativo",
            "p3_normatividad_aiu":     "P3 – Normatividad AIU",
            "p4_percepcion_valor":     "P4 – Percepción de Valor",
            "p5_inteligencia_negocio": "P5 – Inteligencia de Negocio",
        })
        st.dataframe(df_display, use_container_width=True, height=420)

        st.markdown("---")
        st.markdown("### ⬇️ Exportar para Business Intelligence")
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥  Descargar CSV para Power BI / Excel",
            data=csv_bytes,
            file_name=f"diagnostico_cuc_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption(
            "Exportado con **UTF-8 con BOM** — compatible con Power BI, "
            "Excel y Tableau sin errores de caracteres especiales."
        )

    st.markdown(
        '<div class="footer-cuc">Panel de Administración · '
        '<strong>Universidad de la Costa (CUC)</strong> · Uso interno exclusivo</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
#  VISTA 1 — INTERFAZ DEL CLIENTE  (Wizard paso a paso)
# ══════════════════════════════════════════════════════════════════
else:
    render_header()

    # ── Llave de session_state para cada pregunta ─────────────────
    SS_KEYS = {
        "p1_rentabilidad":         "r_p1",
        "p2_tiempo_operativo":     "r_p2",
        "p3_normatividad_aiu":     "r_p3",
        "p4_percepcion_valor":     "r_p4",
        "p5_inteligencia_negocio": "r_p5",
    }
    TOTAL_PREGUNTAS = len(PREGUNTAS)

    # ─────────────────────────────────────────────────────────────
    #  PANTALLA FINAL — confirmación tras envío exitoso
    # ─────────────────────────────────────────────────────────────
    if st.session_state.enviado:
        st.markdown("""
        <div class="alert-success">
            <span class="as-icon">✅</span>
            <p class="as-title">¡Diagnóstico enviado con éxito!</p>
            <p class="as-body">Gracias por contribuir a la investigación de la
            Universidad de la Costa. Su información ha sido registrada de forma
            segura en la nube.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(
            '<div class="footer-cuc">© 2026 · <strong>Universidad de la Costa (CUC)</strong> · '
            'Barranquilla, Colombia · Investigación Académica</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    # ─────────────────────────────────────────────────────────────
    #  PASO 0 — Bienvenida + identificación
    # ─────────────────────────────────────────────────────────────
    if st.session_state.step == 0:

        # Banner introductorio
        st.markdown("""
        <div class="banner-intro">
            <p class="b-title">🔬 Investigación Académica · Universidad de la Costa</p>
            <p class="b-body">
                Este diagnóstico hace parte de un estudio sobre procesos operativos y comerciales
                en talleres de transformación de superficies. Sus respuestas son fundamentales
                para el avance de la investigación.
                <strong>El proceso toma menos de 5 minutos.</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">📝 Datos de Identificación</div>', unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            nombre_input = st.text_input(
                "Nombre del Taller / Negocio *",
                value=st.session_state.w_nombre,
                placeholder="Ej: Mármoles del Norte",
                key="input_nombre_p0",
            )
        with col_b:
            correo_input = st.text_input(
                "Correo Electrónico *",
                value=st.session_state.w_correo,
                placeholder="ejemplo@correo.com",
                key="input_correo_p0",
            )

        st.markdown("""
        <div class="privacy-notice">
            <p>🔒 <em>Sus datos están protegidos por la Ley 1581 de 2012 (Habeas Data).
            Esta información es recopilada con fines netamente académicos y de validación
            investigativa para la Universidad de la Costa (CUC). No será compartida con
            terceros ni utilizada para fines comerciales.</em></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Comenzar Diagnóstico →", key="btn_comenzar"):
            if not nombre_input.strip():
                st.error("Por favor ingrese el nombre del taller.")
            elif not correo_input.strip() or "@" not in correo_input:
                st.error("Por favor ingrese un correo electrónico válido.")
            else:
                with st.spinner("Verificando…"):
                    df_check = cargar_datos()
                    es_dup = correo_existe(df_check, correo_input)

                if es_dup:
                    st.markdown("""
                    <div class="alert-duplicate">
                        <p>⚠️ Este correo ya ha completado el diagnóstico.<br>
                        <span style="font-weight:400;font-size:0.88rem;">
                        ¡Gracias por su valioso aporte a nuestra investigación!</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state.w_nombre = nombre_input.strip()
                    st.session_state.w_correo = correo_input.strip().lower()
                    st.session_state.step = 1
                    st.rerun()

    # ─────────────────────────────────────────────────────────────
    #  PASOS 1–5 — Una pregunta por pantalla
    # ─────────────────────────────────────────────────────────────
    elif 1 <= st.session_state.step <= TOTAL_PREGUNTAS:

        idx              = st.session_state.step - 1   # índice 0-based en PREGUNTAS
        clave, pregunta, placeholder = PREGUNTAS[idx]
        ss_key           = SS_KEYS[clave]
        es_ultima        = (st.session_state.step == TOTAL_PREGUNTAS)

        # Barra de progreso nativa
        st.progress(st.session_state.step / TOTAL_PREGUNTAS)

        # Indicador de paso
        st.markdown(
            f'<div class="wizard-step-indicator">'
            f'Pregunta {st.session_state.step} de {TOTAL_PREGUNTAS}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Tarjeta con la pregunta grande
        st.markdown(
            f'<div class="wizard-question-card">'
            f'<p class="wizard-question-text">{pregunta}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Área de respuesta — el valor se recupera del session_state
        respuesta_actual = st.text_area(
            label="Su respuesta:",
            value=st.session_state[ss_key],
            placeholder=placeholder,
            height=165,
            key=f"ta_{clave}_{st.session_state.step}",
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Botones de navegación en dos columnas
        col_back, col_next = st.columns([1, 2])

        with col_back:
            # Wrapper CSS para override del botón rojo → estilo secundario
            st.markdown('<div class="wizard-back-col">', unsafe_allow_html=True)
            if st.button("← Atrás", key=f"btn_atras_{st.session_state.step}"):
                st.session_state[ss_key] = respuesta_actual  # guardar antes de retroceder
                st.session_state.step -= 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_next:
            label_next = "✅ Enviar Diagnóstico" if es_ultima else "Siguiente →"
            if st.button(label_next, key=f"btn_siguiente_{st.session_state.step}"):
                if not respuesta_actual.strip():
                    st.warning("Por favor escriba su respuesta antes de continuar.")
                else:
                    st.session_state[ss_key] = respuesta_actual  # persistir respuesta

                    if es_ultima:
                        # Construir registro y enviar a Google Sheets
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
                        with st.spinner("Guardando en Google Sheets…"):
                            exito = guardar_registro(registro)

                        if exito:
                            st.toast("¡Diagnóstico enviado con éxito! 🎉", icon="✅")
                            st.balloons()
                            st.session_state.enviado = True
                            st.rerun()
                    else:
                        st.session_state.step += 1
                        st.rerun()

    # Footer visible en todos los pasos del wizard
    st.markdown(
        '<div class="footer-cuc">© 2026 · <strong>Universidad de la Costa (CUC)</strong> · '
        'Barranquilla, Colombia · Investigación Académica</div>',
        unsafe_allow_html=True,
    )
