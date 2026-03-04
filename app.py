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
    page_title="Estudio de Rentabilidad y Eficiencia Operativa · CUC",
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

# Cada entrada: (clave_db, titulo_modulo, pregunta, placeholder_ejemplo, razon_investigacion)
PREGUNTAS = [
    (
        "p1_rentabilidad",
        "Rentabilidad Financiera",
        "¿En los últimos 3 meses ha tenido algún proyecto donde la utilidad final fue menor a la esperada? ¿Qué ocurrió y cuál fue la diferencia aproximada?",
        "Ej: Sí, en un proyecto de cocina la utilidad fue 30% menor porque el material subió de precio y hubo desperdicio no calculado.",
        "Esta variable nos permite identificar si existen pérdidas sistemáticas por consumibles no controlados, un indicador clave del diagnóstico.",
    ),
    (
        "p2_tiempo_operativo",
        "Tiempo Operativo",
        "¿Cuánto tiempo le toma en promedio elaborar una cotización completa desde que recibe la solicitud hasta que la envía al cliente?",
        "Ej: Me toma entre 1 y 2 días, principalmente porque debo consultar precios actualizados con proveedores.",
        "Medimos la eficiencia del proceso de cotización para determinar si representa un cuello de botella operativo en el sector.",
    ),
    (
        "p3_normatividad_aiu",
        "Normatividad AIU",
        "¿Ha tenido observaciones, ajustes o pérdida de contratos por errores en el manejo tributario (AIU, IVA u otros)? ¿Cuántas veces en el último año?",
        "Ej: Sí, dos veces en el último año me pidieron corregir el AIU en contratos con constructoras.",
        "Cuantificar la frecuencia de errores tributarios nos permite estimar el impacto económico real de la informalidad normativa en el sector.",
    ),
    (
        "p4_percepcion_valor",
        "Percepción de Valor",
        "¿Cómo entrega actualmente sus cotizaciones (WhatsApp, Excel, PDF formal, sistema)? ¿Ha notado diferencias en la respuesta del cliente según el formato utilizado?",
        "Ej: Las envío por WhatsApp en texto; los clientes empresariales me piden PDF formal y a veces dudan del precio.",
        "Analizamos si el formato de entrega afecta la percepción de profesionalismo y la tasa de cierre de negocios.",
    ),
    (
        "p5_inteligencia_negocio",
        "Inteligencia de Negocio",
        "¿Cuenta con algún sistema o registro que le permita identificar qué tipo de material (granito, sinterizado, cuarzo, etc.) le genera mayor margen? Si no, ¿cómo toma esa decisión actualmente?",
        "Ej: No tengo un sistema exacto, lo decido por experiencia empírica de lo que me quedó en proyectos pasados.",
        "Esta variable evalúa el nivel de madurez en inteligencia de negocio del sector, base fundamental del módulo analítico de CostoMármol.",
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
TOTAL_PREGUNTAS = len(PREGUNTAS)

# ══════════════════════════════════════════════════════════════════
#  LÓGICA DINÁMICA DE COLORES (MODO CLARO / OSCURO)
# ══════════════════════════════════════════════════════════════════
if st.session_state.tema_oscuro:
    bg_main          = "#0B0E14"
    bg_card          = "#151A23"
    bg_context       = "#1A2030"
    text_main        = "#F2F5F8"
    text_muted       = "#8B949E"
    border_subtle    = "#30363D"
    btn_text         = "#0B0E14"
    btn_bg           = "#F2F5F8"
    logo_blend       = "normal"
    stepper_idle     = "#2A3040"
    stepper_txt_idle = "#4A5568"
else:
    bg_main          = "#F8F9FA"
    bg_card          = "#FFFFFF"
    bg_context       = "#FFF5F5"
    text_main        = "#0F172A"
    text_muted       = "#64748B"
    border_subtle    = "#E2E8F0"
    btn_text         = "#FFFFFF"
    btn_bg           = "#0F172A"
    logo_blend       = "multiply"
    stepper_idle     = "#E2E8F0"
    stepper_txt_idle = "#94A3B8"

# ══════════════════════════════════════════════════════════════════
#  CSS — DISEÑO PREMIUM, RESPONSIVO Y CORPORATIVO
# ══════════════════════════════════════════════════════════════════
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

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
    --stepper-idle:  {stepper_idle};
    --stepper-txt:   {stepper_txt_idle};
}}

html, body, [class*="css"], .stApp, .stMarkdown,
.stTextInput, .stTextArea {{
    font-family: 'Inter', sans-serif !important;
}}

#MainMenu {{ visibility: hidden !important; }}
header    {{ visibility: hidden !important; }}
footer    {{ visibility: hidden !important; }}

.stApp {{ background-color: var(--bg-main) !important; }}

/* ── Header ─────────────────────────────────────── */
.premium-header {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px 0 10px 0;
}}
.premium-header img {{
    height: 45px;
    object-fit: contain;
    margin-bottom: 15px;
    mix-blend-mode: {logo_blend};
}}
.premium-header h1 {{
    font-size: 1.0rem;
    font-weight: 600;
    color: var(--text-main);
    margin: 0;
    letter-spacing: 0.02em;
    text-align: center;
    line-height: 1.5;
    max-width: 560px;
}}

/* ── Cards ───────────────────────────────────────── */
.saas-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    margin-bottom: 20px;
    transition: all 0.3s ease;
}}

/* ── Bienvenida ──────────────────────────────────── */
.welcome-eyebrow {{
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 12px;
    display: block;
}}
.welcome-title {{
    font-size: 1.65rem;
    font-weight: 700;
    color: var(--text-main);
    margin-bottom: 16px;
    line-height: 1.3;
}}
.welcome-title span {{
    color: var(--cuc-red);
}}
.welcome-text {{
    font-size: 0.94rem;
    color: var(--text-muted);
    line-height: 1.75;
    margin-bottom: 22px;
    border-left: 2px solid var(--border-subtle);
    padding-left: 16px;
}}
.welcome-pills {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 28px;
}}
.pill {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(227,0,15,0.07);
    border: 1px solid rgba(227,0,15,0.18);
    color: var(--cuc-red);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.02em;
}}

/* ── Stepper visual ──────────────────────────────── */
.stepper-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 22px 0 18px 0;
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
    box-shadow: 0 0 0 4px rgba(227,0,15,0.14);
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

/* ── Indicador de módulo ─────────────────────────── */
.wizard-step {{
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
    display: block;
}}
.wizard-title {{
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-main);
    line-height: 1.45;
    margin: 0 0 22px 0;
}}

/* ── Contexto de investigación ───────────────────── */
.context-box {{
    background-color: var(--bg-context);
    border-left: 3px solid var(--cuc-red);
    border-radius: 0 8px 8px 0;
    padding: 11px 16px;
    margin-bottom: 22px;
    font-size: 0.83rem;
    color: var(--text-muted);
    line-height: 1.6;
}}
.context-box strong {{
    color: var(--cuc-red);
    font-weight: 600;
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    display: block;
    margin-bottom: 3px;
}}

/* ── Inputs ──────────────────────────────────────── */
.stTextInput input, .stTextArea textarea {{
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid var(--border-subtle) !important;
    border-radius: 0 !important;
    color: var(--text-main) !important;
    font-size: 1.05rem !important;
    padding: 12px 0 !important;
    box-shadow: none !important;
    transition: border-color 0.2s ease !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-bottom: 2px solid var(--cuc-red) !important;
}}
.stTextInput label, .stTextArea label {{
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── Botones ─────────────────────────────────────── */
.stButton > button {{
    background-color: var(--btn-bg) !important;
    color: var(--btn-text) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 12px 24px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}}
.stButton > button:hover {{ transform: translateY(-2px); opacity: 0.9; }}

.btn-rojo .stButton > button {{
    background-color: var(--cuc-red) !important;
    color: #FFFFFF !important;
}}
.btn-rojo .stButton > button:hover {{
    background-color: var(--cuc-red-hover) !important;
}}
.btn-outline .stButton > button {{
    background-color: transparent !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border-subtle) !important;
}}
.btn-outline .stButton > button:hover {{
    color: var(--text-main) !important;
    border-color: var(--text-muted) !important;
}}

/* ── Alerta ──────────────────────────────────────── */
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

/* ── Barra de progreso ───────────────────────────── */
.stProgress > div > div > div > div {{
    background-color: var(--cuc-red) !important;
}}

/* ── Pantalla de confirmación ────────────────────── */
.confirm-icon {{
    font-size: 3rem;
    display: block;
    text-align: center;
    margin-bottom: 16px;
}}
.confirm-title {{
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-main);
    text-align: center;
    margin-bottom: 10px;
}}
.confirm-text {{
    font-size: 0.93rem;
    color: var(--text-muted);
    text-align: center;
    line-height: 1.7;
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

/* ── Admin métricas ──────────────────────────────── */
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

/* ── Footer ──────────────────────────────────────── */
.minimal-footer {{
    text-align: center;
    margin-top: 50px;
    padding-bottom: 20px;
    font-size: 0.75rem;
    color: var(--text-muted);
    line-height: 1.8;
}}

/* ── Toggle ──────────────────────────────────────── */
div[data-testid="stToggle"] label p {{
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
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
    """
    Lee el Google Sheet y retorna un DataFrame normalizado.
    Activa _gs_error=True si la conexión falla para bloquear
    registros duplicados en correo_existe().
    """
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
    """
    Valida la llave primaria (correo) contra la base de datos.
    Si hubo un error de conexión (_gs_error=True), retorna True
    como bloqueo preventivo para evitar duplicados silenciosos.
    """
    if st.session_state.get("_gs_error", False):
        return True
    if df.empty or "correo" not in df.columns:
        return False
    return (
        correo.strip().lower()
        in df["correo"].dropna().str.strip().str.lower().values
    )


def guardar_registro(registro: dict) -> bool:
    """
    Agrega un nuevo registro al Google Sheet.
    No escribe archivos locales (compatible con Streamlit Community Cloud).
    """
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
#  COMPONENTE: STEPPER VISUAL DE MÓDULOS
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
#  ▸ Título rediseñado: "Estudio de Rentabilidad y Eficiencia
#    Operativa — Sector Superficies Arquitectónicas"
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

    # ── Pantalla de confirmación (post-envío) ─────────────────────
    if st.session_state.enviado:
        nombre_taller = st.session_state.w_nombre or "su empresa"
        st.markdown(
            f"""
            <div class="saas-card" style="text-align:center; padding:48px 40px;">
                <span class="confirm-icon">✅</span>
                <h2 class="confirm-title">Diagnóstico registrado con éxito.</h2>
                <p class="confirm-text">
                    Las respuestas de <strong>{nombre_taller}</strong> han sido almacenadas
                    de forma segura en la base de datos de la investigación.<br>
                    Su experiencia es fundamental para el desarrollo de <strong>CostoMármol</strong>.
                    Gracias por su tiempo y confianza.
                </p>
                <div class="confirm-badge">
                    🏛️ &nbsp;Universidad de la Costa (CUC) · Barranquilla &nbsp;|&nbsp; Uso Académico Exclusivo
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── Paso 0: Pantalla de bienvenida / registro ─────────────────
    if st.session_state.step == 0:
        # ── COPY REDISEÑADO: tono BI / consultoría de alto nivel ──
        st.markdown(
            """
            <div class="saas-card">
                <span class="welcome-eyebrow">
                    Investigación Aplicada · Universidad de la Costa (CUC)
                </span>
                <h2 class="welcome-title">
                    Estudio de Rentabilidad y Eficiencia Operativa —
                    <span>Sector Superficies Arquitectónicas</span>
                </h2>
                <p class="welcome-text">
                    Esta iniciativa académica, liderada por el grupo de investigación de la
                    <strong>Universidad de la Costa (CUC)</strong>, aplica metodologías de
                    <strong>Business Intelligence</strong> para diagnosticar las brechas operativas
                    y financieras en talleres de transformación de superficies (mármol, granito,
                    cuarzo y sinterizado) en la región Caribe colombiana.<br><br>
                    Los hallazgos alimentarán el modelo de validación comercial de
                    <strong>CostoMármol</strong>, un sistema de gestión y cotización diseñado
                    específicamente para el sector. Su participación es confidencial, voluntaria
                    y protegida por la Ley 1581 de 2012.
                </p>
                <div class="welcome-pills">
                    <span class="pill">⏱ Menos de 4 minutos</span>
                    <span class="pill">🔒 Confidencial · Ley 1581</span>
                    <span class="pill">📋 5 módulos</span>
                    <span class="pill">🏛 Respaldo CUC</span>
                    <span class="pill">📊 Impacto sectorial</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        nombre_input = st.text_input(
            "Empresa o Taller",
            value=st.session_state.w_nombre,
            placeholder="Nombre de su negocio o razón social",
        )
        correo_input = st.text_input(
            "Correo electrónico",
            value=st.session_state.w_correo,
            placeholder="correo@empresa.com",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Iniciar Diagnóstico →"):
            nombre_ok = bool(nombre_input.strip())
            correo_ok = "@" in correo_input and "." in correo_input.split("@")[-1]

            if not nombre_ok or not correo_ok:
                st.markdown(
                    '<div class="custom-alert">'
                    "⚠️ Por favor complete ambos campos correctamente para continuar."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                with st.spinner("Verificando registro..."):
                    df_check = cargar_datos()

                    if st.session_state.get("_gs_error", False):
                        st.markdown(
                            '<div class="custom-alert">'
                            "⚠️ No fue posible conectar con la base de datos en este momento. "
                            "Por favor intente de nuevo en unos instantes."
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    elif correo_existe(df_check, correo_input):
                        st.markdown(
                            '<div class="custom-alert">'
                            "Este correo ya completó el diagnóstico previamente. "
                            "Cada empresa participa una sola vez. Gracias."
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.session_state.w_nombre = nombre_input.strip()
                        st.session_state.w_correo = correo_input.strip().lower()
                        st.session_state.step = 1
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Pasos 1 – TOTAL_PREGUNTAS: Wizard de preguntas ────────────
    elif 1 <= st.session_state.step <= TOTAL_PREGUNTAS:
        idx = st.session_state.step - 1
        clave, titulo_corto, pregunta, placeholder, razon = PREGUNTAS[idx]
        ss_key    = SS_KEYS[clave]
        es_ultima = (st.session_state.step == TOTAL_PREGUNTAS)

        render_stepper(st.session_state.step)
        st.progress((st.session_state.step - 1) / TOTAL_PREGUNTAS)

        st.markdown(
            f"""
            <div class="saas-card" style="margin-top:18px;">
                <span class="wizard-step">
                    Módulo {st.session_state.step} de {TOTAL_PREGUNTAS} — {titulo_corto}
                </span>
                <h3 class="wizard-title">{pregunta}</h3>
                <div class="context-box">
                    <strong>Objetivo del módulo</strong>
                    {razon}
                </div>
            """,
            unsafe_allow_html=True,
        )

        respuesta_actual = st.text_area(
            label="Su respuesta:",
            value=st.session_state[ss_key],
            placeholder=placeholder,
            height=140,
            label_visibility="collapsed",
            key=f"resp_{st.session_state.step}",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_back, col_next = st.columns([1, 2])

        with col_back:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("← Atrás", key=f"back_{st.session_state.step}"):
                st.session_state[ss_key] = respuesta_actual
                st.session_state.step -= 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_next:
            if es_ultima:
                st.markdown('<div class="btn-rojo">', unsafe_allow_html=True)

            label_next = "Finalizar y Enviar" if es_ultima else "Continuar →"
            if st.button(label_next, key=f"next_{st.session_state.step}"):
                if not respuesta_actual.strip():
                    st.markdown(
                        '<div class="custom-alert">'
                        "⚠️ Por favor ingrese una respuesta antes de continuar."
                        "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.session_state[ss_key] = respuesta_actual

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
                                    "⚠️ Ocurrió un error al guardar. Por favor intente de nuevo. "
                                    "Si el problema persiste, contacte al equipo de investigación."
                                    "</div>",
                                    unsafe_allow_html=True,
                                )
                    else:
                        st.session_state.step += 1
                        st.rerun()

            if es_ultima:
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────
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
