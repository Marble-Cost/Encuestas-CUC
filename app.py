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
        "Rentabilidad Financiera",
        "¿En los últimos 3 meses ha tenido algún proyecto donde la utilidad final fue menor a la esperada? ¿Qué ocurrió y cuánto fue la diferencia aproximada?",
        "Ej: Sí, en un proyecto de cocina la utilidad fue 30% menor porque el material subió de precio y hubo desperdicio no calculado.",
    ),
    (
        "p2_tiempo_operativo",
        "Tiempo Operativo",
        "¿Cuánto tiempo le toma en promedio elaborar una cotización completa desde que recibe la solicitud hasta que la envía al cliente?",
        "Ej: Me toma entre 1 y 2 días, principalmente porque debo consultar precios actualizados con proveedores.",
    ),
    (
        "p3_normatividad_aiu",
        "Normatividad AIU",
        "¿Ha tenido observaciones, ajustes o pérdida de contratos por errores en el manejo tributario (AIU, IVA u otros)? ¿Cuántas veces en el último año?",
        "Ej: Sí, dos veces en el último año me pidieron corregir el AIU en contratos con constructoras.",
    ),
    (
        "p4_percepcion_valor",
        "Percepción de Valor",
        "¿Cómo entrega actualmente sus cotizaciones (WhatsApp, Excel, PDF formal, sistema)? ¿Ha notado diferencias en la respuesta del cliente según el formato?",
        "Ej: Las envío por WhatsApp en texto; los clientes empresariales me piden PDF formal y a veces dudan del precio.",
    ),
    (
        "p5_inteligencia_negocio",
        "Inteligencia de Negocio",
        "¿Cuenta actualmente con algún sistema o registro que le permita identificar qué tipo de material (granito, sinterizado, cuarzo, etc.) le deja mayor margen? Si no, ¿cómo toma esa decisión?",
        "Ej: No tengo un sistema exacto, lo decido por experiencia empírica de lo que me quedó en proyectos pasados.",
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
    "tema_oscuro": True,  # Inicia en oscuro por defecto
    "r_p1": "", "r_p2": "", "r_p3": "", "r_p4": "", "r_p5": "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

SS_KEYS = {
    "p1_rentabilidad": "r_p1",
    "p2_tiempo_operativo": "r_p2",
    "p3_normatividad_aiu": "r_p3",
    "p4_percepcion_valor": "r_p4",
    "p5_inteligencia_negocio": "r_p5",
}
TOTAL_PREGUNTAS = len(PREGUNTAS)

# ══════════════════════════════════════════════════════════════════
#  LÓGICA DINÁMICA DE COLORES (MODO CLARO / OSCURO)
# ══════════════════════════════════════════════════════════════════
if st.session_state.tema_oscuro:
    # Variables Modo Oscuro
    bg_main = "#0B0E14"
    bg_card = "#151A23"
    text_main = "#F2F5F8"
    text_muted = "#8B949E"
    border_subtle = "#30363D"
    btn_text = "#0B0E14"
    btn_bg = "#F2F5F8"
    logo_blend = "normal"
else:
    # Variables Modo Claro
    bg_main = "#F8F9FA"
    bg_card = "#FFFFFF"
    text_main = "#0F172A"
    text_muted = "#64748B"
    border_subtle = "#E2E8F0"
    btn_text = "#FFFFFF"
    btn_bg = "#0F172A"
    logo_blend = "multiply"  # Desaparece el fondo negro del JPG

# ══════════════════════════════════════════════════════════════════
#  CSS — DISEÑO PREMIUM Y RESPONSIVO
# ══════════════════════════════════════════════════════════════════
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {{
    --bg-main: {bg_main};
    --bg-card: {bg_card};
    --text-main: {text_main};
    --text-muted: {text_muted};
    --border-subtle: {border_subtle};
    --btn-text: {btn_text};
    --btn-bg: {btn_bg};
    --cuc-red: #E3000F;
    --cuc-red-hover: #B3000B;
}}

html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stTextArea {{
    font-family: 'Inter', sans-serif !important;
}}

#MainMenu {{visibility: hidden !important;}}
header {{visibility: hidden !important;}}
footer {{visibility: hidden !important;}}

.stApp {{ background-color: var(--bg-main) !important; }}

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
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-main);
    margin: 0;
    letter-spacing: 0.02em;
    text-align: center;
}}

.saas-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    margin-bottom: 20px;
    transition: all 0.3s ease;
}}

.welcome-title {{
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-main);
    margin-bottom: 10px;
    line-height: 1.3;
}}
.welcome-text {{
    font-size: 0.95rem;
    color: var(--text-muted);
    line-height: 1.6;
    margin-bottom: 25px;
}}

.stTextInput input, .stTextArea textarea {{
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid var(--border-subtle) !important;
    border-radius: 0 !important;
    color: var(--text-main) !important;
    font-size: 1.1rem !important;
    padding: 12px 0 !important;
    box-shadow: none !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-bottom: 2px solid var(--cuc-red) !important;
}}
.stTextInput label, .stTextArea label {{
    font-size: 0.85rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

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
.btn-rojo .stButton > button:hover {{ background-color: var(--cuc-red-hover) !important; }}

.btn-outline .stButton > button {{
    background-color: transparent !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border-subtle) !important;
}}
.btn-outline .stButton > button:hover {{
    color: var(--text-main) !important;
    border-color: var(--text-muted) !important;
}}

.wizard-step {{
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 10px;
    display: block;
}}
.wizard-title {{
    font-size: 1.6rem;
    font-weight: 600;
    color: var(--text-main);
    line-height: 1.4;
    margin: 0 0 30px 0;
}}

.custom-alert {{
    background-color: rgba(227, 0, 15, 0.1);
    border-left: 3px solid var(--cuc-red);
    padding: 15px;
    border-radius: 4px;
    color: var(--text-main);
    font-size: 0.9rem;
    margin-bottom: 20px;
}}

.stProgress > div > div > div > div {{ background-color: var(--cuc-red) !important; }}

.minimal-footer {{
    text-align: center;
    margin-top: 50px;
    padding-bottom: 20px;
    font-size: 0.75rem;
    color: var(--text-muted);
}}

/* Ajuste del Toggle Switch */
div[data-testid="stToggle"] label p {{
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
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
    try:
        conn = get_conn()
        df = conn.read(usecols=list(range(len(COLUMNAS))), ttl=60)
        df = df.dropna(how="all")
        if df.empty:
            return pd.DataFrame(columns=COLUMNAS)
        df.columns = COLUMNAS[: len(df.columns)]
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNAS)

def correo_existe(df: pd.DataFrame, correo: str) -> bool:
    if df.empty or "correo" not in df.columns:
        return False
    return correo.strip().lower() in (df["correo"].dropna().str.strip().str.lower().values)

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
#  SIDEBAR — ACCESO ADMIN OCULTO
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 Acceso Admin")
    pwd_input = st.text_input("Contraseña", type="password", key="admin_pwd")
es_admin = (pwd_input == ADMIN_PASSWORD)

# ══════════════════════════════════════════════════════════════════
#  HEADER Y TOGGLE DE TEMA
# ══════════════════════════════════════════════════════════════════
def render_header() -> None:
    # Selector de Tema alineado a la derecha
    col_vacia, col_toggle = st.columns([4, 1])
    with col_toggle:
        st.toggle("Tema Oscuro", key="tema_oscuro")
        
    logo_tag = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_tag = f'<img src="data:image/jpeg;base64,{b64}" alt="CUC">'
    
    st.markdown(f"""
    <div class="premium-header">
        {logo_tag}
        <h1>Investigación de Operaciones</h1>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  VISTA 2 — PANEL DE ADMINISTRACIÓN
# ══════════════════════════════════════════════════════════════════
if es_admin:
    render_header()
    st.markdown("## 📊 Base de Datos Activa")
    df = cargar_datos()
    
    if df.empty:
        st.info("Sin registros.")
    else:
        st.dataframe(df, use_container_width=True, height=400)
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥 Descargar CSV", data=csv_bytes, file_name="datos.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════
#  VISTA 1 — INTERFAZ DEL CLIENTE
# ══════════════════════════════════════════════════════════════════
else:
    render_header()

    if st.session_state.enviado:
        st.markdown(f"""
        <div class="saas-card" style="text-align:center;">
            <h2 style="color:{text_main}; margin-bottom:10px;">Diagnóstico completado.</h2>
            <p style="color:{text_muted}; line-height:1.6;">Sus respuestas han sido encriptadas y guardadas de forma segura.<br>Gracias por su tiempo y experiencia.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    if st.session_state.step == 0:
        st.markdown(f"""
        <div class="saas-card">
            <h2 class="welcome-title">Bienvenido al Diagnóstico Sectorial.</h2>
            <p class="welcome-text">Esta herramienta académica evalúa la eficiencia operativa en la transformación de superficies arquitectónicas. Toma menos de 4 minutos y consta de 5 preguntas breves.</p>
        """, unsafe_allow_html=True)

        nombre_input = st.text_input("Compañía / Taller", value=st.session_state.w_nombre, placeholder="Nombre de su negocio")
        correo_input = st.text_input("Correo corporativo o personal", value=st.session_state.w_correo, placeholder="ejemplo@correo.com")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Comenzar Evaluación"):
            if not nombre_input.strip() or "@" not in correo_input:
                st.markdown('<div class="custom-alert">⚠️ Por favor complete ambos campos correctamente para iniciar.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Conectando..."):
                    if correo_existe(cargar_datos(), correo_input):
                        st.markdown('<div class="custom-alert">El correo ingresado ya completó la evaluación previamente.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state.w_nombre = nombre_input.strip()
                        st.session_state.w_correo = correo_input.strip().lower()
                        st.session_state.step = 1
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif 1 <= st.session_state.step <= TOTAL_PREGUNTAS:
        idx = st.session_state.step - 1
        clave, titulo_corto, pregunta, placeholder = PREGUNTAS[idx]
        ss_key = SS_KEYS[clave]
        es_ultima = (st.session_state.step == TOTAL_PREGUNTAS)

        st.progress(st.session_state.step / TOTAL_PREGUNTAS)
        
        st.markdown(f"""
        <div class="saas-card" style="margin-top:20px;">
            <span class="wizard-step">Módulo {st.session_state.step} de {TOTAL_PREGUNTAS} — {titulo_corto}</span>
            <h3 class="wizard-title">{pregunta}</h3>
        """, unsafe_allow_html=True)

        respuesta_actual = st.text_area(
            label="Su análisis:",
            value=st.session_state[ss_key],
            placeholder=placeholder,
            height=130,
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_back, col_next = st.columns([1, 2])

        with col_back:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("Atrás"):
                st.session_state[ss_key] = respuesta_actual
                st.session_state.step -= 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col_next:
            if es_ultima:
                st.markdown('<div class="btn-rojo">', unsafe_allow_html=True)
            
            label_next = "Finalizar y Enviar" if es_ultima else "Continuar"
            if st.button(label_next):
                if not respuesta_actual.strip():
                    st.markdown('<div class="custom-alert" style="margin-top:15px;">⚠️ Por favor, ingrese una respuesta para avanzar.</div>', unsafe_allow_html=True)
                else:
                    st.session_state[ss_key] = respuesta_actual
                    if es_ultima:
                        registro = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "nombre_taller": st.session_state.w_nombre,
                            "correo": st.session_state.w_correo,
                            "p1_rentabilidad": st.session_state.r_p1,
                            "p2_tiempo_operativo": st.session_state.r_p2,
                            "p3_normatividad_aiu": st.session_state.r_p3,
                            "p4_percepcion_valor": st.session_state.r_p4,
                            "p5_inteligencia_negocio": st.session_state.r_p5,
                        }
                        with st.spinner("Asegurando datos..."):
                            if guardar_registro(registro):
                                st.session_state.enviado = True
                                st.rerun()
                    else:
                        st.session_state.step += 1
                        st.rerun()
            
            if es_ultima:
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="minimal-footer">Protegido por Ley 1581 (Habeas Data) · Uso Académico<br>Universidad de la Costa (CUC) · Barranquilla</div>', unsafe_allow_html=True)
