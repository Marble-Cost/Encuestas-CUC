import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ═════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PÁGINA
#  Debe ser el PRIMER comando Streamlit del archivo.
# ═════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Diagnóstico Operativo · CUC",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ═════════════════════════════════════════════════════════════════
#  CONSTANTES
# ═════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = "Admin123"
LOGO_PATH      = "logo_cuc.png"

# Columnas exactas que se escriben en Google Sheets.
# La hoja debe tener estos encabezados en la fila 1.
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
        "Escriba su respuesta aquí. Ej: Sí, en un proyecto de cocina la utilidad fue 30 % menor porque el material subió de precio…",
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

# ═════════════════════════════════════════════════════════════════
#  CSS – DARK MODE PROFESIONAL
#  Fondo negro para que el logo JPG con fondo negro quede perfecto.
#  Rojo institucional CUC: #E3000F
# ═════════════════════════════════════════════════════════════════
CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

/* ── Variables Dark Mode ── */
:root {
    --cuc-red:          #E3000F;
    --cuc-red-dark:     #B3000B;
    --cuc-red-light:    #FF3341;
    --cuc-red-glow:     rgba(227, 0, 15, 0.18);
    --bg-app:           #0D0D0D;
    --bg-surface:       #161616;
    --bg-elevated:      #1F1F1F;
    --bg-input:         #252525;
    --border-dim:       #2A2A2A;
    --border-accent:    #3A1010;
    --text-primary:     #F0F0F0;
    --text-secondary:   #9A9A9A;
    --text-muted:       #4E4E4E;
    --success:          #22C55E;
    --success-bg:       rgba(34, 197, 94, 0.08);
    --warning:          #F97316;
    --warning-bg:       rgba(249, 115, 22, 0.08);
    --info-bg:          rgba(227, 0, 15, 0.06);
}

/* ── Fuente global ── */
html, body, [class*="css"], * {
    font-family: 'Montserrat', sans-serif !important;
}

/* ── Fondo total ── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
.main .block-container {
    background-color: var(--bg-app) !important;
    color: var(--text-primary) !important;
}

/* Ocultar sidebar y su botón colapsable */
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Centrar y limitar ancho (feel móvil) */
[data-testid="stMainBlockContainer"] {
    max-width: 700px !important;
    padding: 0 18px 48px 18px !important;
}

/* Scrollbar oscura */
::-webkit-scrollbar            { width: 5px; }
::-webkit-scrollbar-track      { background: var(--bg-app); }
::-webkit-scrollbar-thumb      { background: var(--border-dim); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover{ background: var(--cuc-red-dark); }

/* ══ BANNER INTRO ══ */
.banner-intro {
    background: var(--info-bg);
    border: 1px solid var(--border-accent);
    border-left: 4px solid var(--cuc-red);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 22px;
}
.banner-intro .b-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #FF3341;
    margin: 0 0 5px 0;
}
.banner-intro .b-body {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.6;
}

/* ══ AVISO PRIVACIDAD ══ */
.privacy-notice {
    background: rgba(227, 0, 15, 0.05);
    border-left: 3px solid var(--cuc-red-dark);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 4px 0 20px 0;
}
.privacy-notice p {
    font-size: 0.70rem;
    font-style: italic;
    color: var(--text-muted);
    margin: 0;
    line-height: 1.6;
}

/* ══ SECTION LABEL ══ */
.section-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-dim);
    margin-bottom: 16px;
}

/* ══ LABELS E INPUTS ══ */
.stTextInput label,
.stTextArea label,
.stPasswordInput label {
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    font-size: 1.05rem !important;
    line-height: 1.55 !important;
    margin-bottom: 5px !important;
}

.stTextInput input,
.stTextArea textarea,
.stPasswordInput input {
    background: var(--bg-input) !important;
    border: 1.5px solid var(--border-dim) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    padding: 11px 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    caret-color: var(--cuc-red) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
.stPasswordInput input::placeholder {
    color: var(--text-muted) !important;
    font-style: italic;
    font-size: 0.88rem !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stPasswordInput input:focus {
    border-color: var(--cuc-red) !important;
    box-shadow: 0 0 0 3px var(--cuc-red-glow) !important;
    outline: none !important;
}

/* Espaciado entre preguntas */
.stTextArea { margin-bottom: 22px !important; }

/* ══ BOTÓN PRIMARIO (enviar / login) ══ */
.stButton > button {
    background: var(--cuc-red) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 2rem !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(227, 0, 15, 0.32) !important;
    transition: background 0.2s, transform 0.12s, box-shadow 0.2s !important;
    margin-top: 6px !important;
}
.stButton > button:hover {
    background: var(--cuc-red-dark) !important;
    box-shadow: 0 6px 28px rgba(227, 0, 15, 0.48) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ══ BOTÓN ADMIN FOOTER (override discreto) ══ */
.admin-footer-btn .stButton > button {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.65rem !important;
    font-weight: 500 !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 20px !important;
    padding: 4px 14px !important;
    width: auto !important;
    min-width: unset !important;
    box-shadow: none !important;
    margin-top: 0 !important;
    letter-spacing: 0.06em !important;
}
.admin-footer-btn .stButton > button:hover {
    color: var(--text-secondary) !important;
    border-color: var(--text-muted) !important;
    transform: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

/* ══ BOTÓN VOLVER ══ */
.btn-back .stButton > button {
    background: var(--bg-elevated) !important;
    color: var(--text-secondary) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    margin-top: 4px !important;
}
.btn-back .stButton > button:hover {
    background: #252525 !important;
    border-color: var(--text-muted) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ══ BOTÓN CERRAR SESIÓN ══ */
.btn-logout .stButton > button {
    background: transparent !important;
    color: var(--cuc-red) !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    border: 1.5px solid var(--cuc-red) !important;
    border-radius: 8px !important;
    padding: 6px 16px !important;
    width: auto !important;
    min-width: unset !important;
    box-shadow: none !important;
    margin-top: 0 !important;
    letter-spacing: 0.04em !important;
}
.btn-logout .stButton > button:hover {
    background: var(--cuc-red) !important;
    color: white !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ══ BOTÓN DESCARGA ══ */
.stDownloadButton > button {
    background: var(--cuc-red) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    width: 100% !important;
    box-shadow: 0 4px 16px rgba(227, 0, 15, 0.28) !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    background: var(--cuc-red-dark) !important;
    box-shadow: 0 6px 22px rgba(227, 0, 15, 0.44) !important;
    transform: translateY(-1px) !important;
}

/* ══ ALERTAS ══ */
.alert-success {
    background: var(--success-bg);
    border: 1.5px solid rgba(34,197,94,0.30);
    border-radius: 12px;
    padding: 20px 22px;
    text-align: center;
    margin-top: 14px;
}
.alert-success .as-title {
    color: #4ADE80;
    font-weight: 700;
    font-size: 1rem;
    margin: 0 0 6px 0;
}
.alert-success .as-body {
    color: #86EFAC;
    font-weight: 400;
    font-size: 0.85rem;
    margin: 0;
}
.alert-duplicate {
    background: var(--warning-bg);
    border: 1.5px solid rgba(249,115,22,0.30);
    border-radius: 12px;
    padding: 20px 22px;
    text-align: center;
}
.alert-duplicate p {
    color: var(--warning);
    font-weight: 600;
    font-size: 0.95rem;
    margin: 0;
    line-height: 1.5;
}

/* ══ MÉTRICAS ADMIN ══ */
[data-testid="metric-container"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
}
[data-testid="stMetricLabel"] p {
    color: var(--text-secondary) !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}
[data-testid="stMetricValue"] {
    color: var(--cuc-red) !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
}

/* ══ DATAFRAME ══ */
.stDataFrame {
    border: 1px solid var(--border-dim) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ══ LOGIN CARD ══ */
.login-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-dim);
    border-top: 3px solid var(--cuc-red);
    border-radius: 16px;
    padding: 36px 30px 30px;
    max-width: 420px;
    margin: 50px auto 0 auto;
    box-shadow: 0 8px 40px rgba(0,0,0,0.55);
}

/* ══ BADGE ADMIN ══ */
.admin-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(227,0,15,0.10);
    border: 1px solid rgba(227,0,15,0.25);
    color: #FF3341;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 10px;
}

/* ══ FOOTER ══ */
.footer-cuc {
    text-align: center;
    padding: 22px 0 10px;
    color: var(--text-muted);
    font-size: 0.65rem;
    border-top: 1px solid var(--border-dim);
    margin-top: 32px;
    letter-spacing: 0.05em;
}
.footer-cuc strong { color: #5C5C5C; }

/* ══ HR ══ */
hr { border-color: var(--border-dim) !important; margin: 14px 0 !important; }

/* ══ Texto Markdown general ══ */
p, li, span, div { color: var(--text-primary); }
h1, h2, h3, h4, h5 { color: var(--text-primary) !important; }

/* ══ Streamlit info/error/warning nativos ══ */
[data-testid="stAlert"] {
    background: var(--bg-elevated) !important;
    border-radius: 10px !important;
    border-color: var(--border-dim) !important;
}
.stCaption, .stCaption p {
    color: var(--text-muted) !important;
    font-size: 0.70rem !important;
}

/* Bloques internos transparentes */
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
div.block-container {
    background: transparent !important;
}
</style>
"""

# ═════════════════════════════════════════════════════════════════
#  INYECTAR CSS
# ═════════════════════════════════════════════════════════════════
st.markdown(CSS, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
#  CONEXIÓN GOOGLE SHEETS
#  Requiere .streamlit/secrets.toml — ver README para instrucciones.
# ═════════════════════════════════════════════════════════════════
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def cargar_datos() -> pd.DataFrame:
    """Lee todos los registros desde Google Sheets (caché 30 s)."""
    try:
        conn = get_connection()
        df = conn.read(usecols=list(range(len(COLUMNAS))), ttl=30)
        df = df.dropna(how="all")
        if df.empty:
            return pd.DataFrame(columns=COLUMNAS)
        df.columns = COLUMNAS[: len(df.columns)]
        return df
    except Exception as e:
        st.error(f"Error al leer Google Sheets: {e}")
        return pd.DataFrame(columns=COLUMNAS)


def correo_existe(df: pd.DataFrame, correo: str) -> bool:
    if df.empty or "correo" not in df.columns:
        return False
    return correo.strip().lower() in df["correo"].dropna().str.strip().str.lower().values


def guardar_registro(registro: dict) -> bool:
    """Añade una nueva fila a Google Sheets."""
    try:
        conn = get_connection()
        df_actual = cargar_datos()
        nueva_fila = pd.DataFrame([registro])
        df_nuevo = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_nuevo)
        st.cache_resource.clear()  # forzar refresh en próxima lectura
        return True
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")
        return False


# ═════════════════════════════════════════════════════════════════
#  INICIALIZAR SESSION STATE
# ═════════════════════════════════════════════════════════════════
defaults = {
    "screen":       "cliente",   # "cliente" | "login" | "admin"
    "form_enviado": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def ir_a(screen: str):
    st.session_state.screen = screen
    st.rerun()


# ═════════════════════════════════════════════════════════════════
#  COMPONENTE: HEADER CON LOGO
# ═════════════════════════════════════════════════════════════════
def render_header():
    import os, base64 as b64lib
    col_logo, col_titulo = st.columns([2, 5])
    with col_logo:
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, "rb") as f:
                b64 = b64lib.b64encode(f.read()).decode()
            ext = LOGO_PATH.rsplit(".", 1)[-1].lower()
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
            # Fondo #0D0D0D para que el logo con fondo negro sea invisible al borde
            st.markdown(
                f"""<div style="background:#0D0D0D;padding:6px 4px;border-radius:8px;
                                display:flex;align-items:center;">
                        <img src="data:{mime};base64,{b64}"
                             style="width:160px;height:auto;object-fit:contain;display:block;">
                    </div>""",
                unsafe_allow_html=True,
            )
    with col_titulo:
        st.markdown(
            """<div style="padding-top:10px;">
                   <div style="font-size:1.3rem;font-weight:800;color:#F0F0F0;
                               line-height:1.2;margin-bottom:5px;letter-spacing:-0.01em;">
                       Diagnóstico Operativo
                   </div>
                   <div style="font-size:0.62rem;color:#4E4E4E;text-transform:uppercase;
                               letter-spacing:0.10em;font-weight:600;">
                       Transformadores de Superficies · CUC 2026
                   </div>
               </div>""",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<hr style='border:none;border-top:2px solid #E3000F;margin:14px 0 24px;'>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  VISTA 1 – CLIENTE (encuesta)
# ═══════════════════════════════════════════════════════════════════
def vista_cliente():
    render_header()

    # Banner introductorio
    st.markdown("""
    <div class="banner-intro">
        <p class="b-title">🔬 Investigación Académica · Universidad de la Costa</p>
        <p class="b-body">
            Este diagnóstico hace parte de un estudio sobre procesos operativos y comerciales
            en talleres de transformación de superficies. Sus respuestas son fundamentales
            para el avance de la investigación.
            <strong style="color:#F0F0F0;">El proceso toma menos de 5 minutos.</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sección: Identificación
    st.markdown('<div class="section-label">📝 Datos de Identificación</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        nombre_taller = st.text_input(
            "Nombre del Taller / Negocio *",
            placeholder="Ej: Mármoles del Norte",
            key="input_nombre",
        )
    with col_b:
        correo = st.text_input(
            "Correo Electrónico *",
            placeholder="ejemplo@correo.com",
            key="input_correo",
        )

    # Aviso Habeas Data
    st.markdown("""
    <div class="privacy-notice">
        <p>🔒 <em>Sus datos están protegidos por la Ley 1581 de 2012 (Habeas Data).
        Esta información es recopilada con fines netamente académicos y de validación investigativa
        para la Universidad de la Costa (CUC). No será compartida con terceros ni utilizada
        para fines comerciales.</em></p>
    </div>
    """, unsafe_allow_html=True)

    # Verificar correo duplicado en tiempo real
    if correo and "@" in correo:
        df_check = cargar_datos()
        if correo_existe(df_check, correo):
            st.markdown("""
            <div class="alert-duplicate">
                <p>⚠️ Este correo ya ha completado el diagnóstico.<br>
                <span style="font-weight:400;font-size:0.85rem;">
                ¡Gracias por su valioso aporte a nuestra investigación!</span></p>
            </div>
            """, unsafe_allow_html=True)
            _footer_cliente()
            return

    # Pantalla de éxito post-envío
    if st.session_state.form_enviado:
        st.markdown("""
        <div class="alert-success">
            <p class="as-title">✅ ¡Diagnóstico enviado con éxito!</p>
            <p class="as-body">Gracias por contribuir a la investigación de la
            Universidad de la Costa. Su información ha sido registrada en la nube
            de forma segura.</p>
        </div>
        """, unsafe_allow_html=True)
        _footer_cliente()
        return

    # Preguntas (solo si hay nombre y correo válidos)
    if nombre_taller and correo:
        st.markdown(
            '<div class="section-label" style="margin-top:26px;">🗒 Diagnóstico Operativo</div>',
            unsafe_allow_html=True,
        )

        respuestas = {}
        for clave, pregunta, placeholder in PREGUNTAS:
            respuestas[clave] = st.text_area(
                label=pregunta,
                placeholder=placeholder,
                height=115,
                key=f"resp_{clave}",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("✅  Enviar Diagnóstico", key="btn_enviar"):
            campos_vacios = [k for k, v in respuestas.items() if not v.strip()]
            if not nombre_taller.strip():
                st.error("Por favor ingrese el nombre del taller.")
            elif not correo.strip() or "@" not in correo:
                st.error("Por favor ingrese un correo electrónico válido.")
            elif campos_vacios:
                st.warning(
                    f"Por favor complete todas las preguntas. "
                    f"Faltan {len(campos_vacios)} respuesta(s)."
                )
            else:
                registro = {
                    "timestamp":               datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nombre_taller":           nombre_taller.strip(),
                    "correo":                  correo.strip().lower(),
                    "p1_rentabilidad":         respuestas["p1_rentabilidad"].strip(),
                    "p2_tiempo_operativo":     respuestas["p2_tiempo_operativo"].strip(),
                    "p3_normatividad_aiu":     respuestas["p3_normatividad_aiu"].strip(),
                    "p4_percepcion_valor":     respuestas["p4_percepcion_valor"].strip(),
                    "p5_inteligencia_negocio": respuestas["p5_inteligencia_negocio"].strip(),
                }
                if guardar_registro(registro):
                    st.session_state.form_enviado = True
                    st.balloons()
                    st.rerun()

    else:
        st.markdown(
            "<p style='color:#4E4E4E;font-style:italic;font-size:0.83rem;margin-top:4px;'>"
            "👆 Complete los campos de identificación para acceder al formulario.</p>",
            unsafe_allow_html=True,
        )

    _footer_cliente()


def _footer_cliente():
    """Footer con copyright y botón admin discreto."""
    st.markdown(
        '<div class="footer-cuc">© 2026 · <strong>Universidad de la Costa (CUC)</strong> · '
        'Barranquilla, Colombia · Investigación Académica</div>',
        unsafe_allow_html=True,
    )
    # Botón admin: centrado y muy pequeño
    cola, colb, colc = st.columns([3, 2, 3])
    with colb:
        st.markdown('<div class="admin-footer-btn">', unsafe_allow_html=True)
        if st.button("🔒 Ingreso Admin", key="btn_ir_login"):
            ir_a("login")
        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  VISTA 2 – LOGIN ADMIN
# ═══════════════════════════════════════════════════════════════════
def vista_login():
    st.markdown("""
    <div class="login-card">
        <div style="text-align:center;margin-bottom:6px;">
            <span style="font-size:2rem;">🛡</span>
        </div>
        <div style="text-align:center;font-size:1.2rem;font-weight:800;
                    color:#F0F0F0;margin-bottom:4px;">
            Acceso Administrador
        </div>
        <div style="text-align:center;font-size:0.68rem;color:#4E4E4E;
                    text-transform:uppercase;letter-spacing:0.08em;margin-bottom:26px;">
            Panel de Control · CUC 2026
        </div>
    """, unsafe_allow_html=True)

    pwd = st.text_input(
        "Contraseña de acceso",
        type="password",
        placeholder="Ingrese su contraseña…",
        key="login_pwd",
    )

    if st.button("Ingresar al Panel →", key="btn_login"):
        if pwd == ADMIN_PASSWORD:
            ir_a("admin")
        else:
            st.error("Contraseña incorrecta. Intente de nuevo.")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="btn-back">', unsafe_allow_html=True)
    if st.button("← Volver a la Encuesta", key="btn_volver"):
        ir_a("cliente")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # cierre login-card


# ═══════════════════════════════════════════════════════════════════
#  VISTA 3 – DASHBOARD ADMIN
# ═══════════════════════════════════════════════════════════════════
def vista_admin():
    # Encabezado con badge y botón cerrar sesión
    col_info, col_exit = st.columns([5, 2])
    with col_info:
        st.markdown(
            '<div class="admin-badge">🛡 Panel de Administración</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h2 style='font-size:1.35rem;font-weight:800;color:#F0F0F0;"
            "margin:4px 0 2px;'>📊 Datos Recolectados</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='font-size:0.65rem;color:#4E4E4E;text-transform:uppercase;"
            "letter-spacing:0.08em;margin:0;'>Universidad de la Costa · 2026</p>",
            unsafe_allow_html=True,
        )
    with col_exit:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="btn-logout">', unsafe_allow_html=True)
        if st.button("Cerrar Sesión", key="btn_logout"):
            st.session_state.screen = "cliente"
            st.session_state.form_enviado = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Cargar datos frescos
    with st.spinner("Cargando datos desde Google Sheets…"):
        df = cargar_datos()

    total          = len(df)
    correos_unicos = df["correo"].nunique() if not df.empty else 0
    ultimo         = "—"
    if not df.empty and "timestamp" in df.columns:
        val = df["timestamp"].dropna()
        ultimo = str(val.iloc[-1])[:10] if not val.empty else "—"

    # Métricas
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total registros", total)
    with c2:
        st.metric("Correos únicos", correos_unicos)
    with c3:
        st.metric("Último registro", ultimo)

    st.markdown("<hr>", unsafe_allow_html=True)

    if df.empty:
        st.info("Aún no hay registros en Google Sheets.")
    else:
        st.markdown(
            "<p style='font-size:0.68rem;font-weight:700;color:#9A9A9A;"
            "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>"
            "📋 Tabla de Respuestas</p>",
            unsafe_allow_html=True,
        )
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

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:0.68rem;font-weight:700;color:#9A9A9A;"
            "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>"
            "⬇️ Exportar para Business Intelligence</p>",
            unsafe_allow_html=True,
        )
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥  Descargar CSV para Power BI / Excel",
            data=csv_bytes,
            file_name=f"diagnostico_cuc_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown(
            "<p style='font-size:0.65rem;color:#4E4E4E;margin-top:6px;'>"
            "Exportado con UTF-8 BOM · Compatible con Power BI, Excel y Tableau.</p>",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="footer-cuc">Panel de Administración · '
        '<strong>Universidad de la Costa (CUC)</strong> · Uso interno exclusivo</div>',
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════
#  ENRUTADOR PRINCIPAL
# ═════════════════════════════════════════════════════════════════
_screen = st.session_state.screen

if _screen == "cliente":
    vista_cliente()
elif _screen == "login":
    vista_login()
elif _screen == "admin":
    vista_admin()
else:
    st.session_state.screen = "cliente"
    st.rerun()
