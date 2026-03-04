import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Diagnóstico Operativo · CUC",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────
CSV_PATH = "base_diagnostico.csv"
ADMIN_PASSWORD = "Admin123"

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

# ─────────────────────────────────────────────
#  PALETA CUC  (extraída del logo adjunto)
#  Rojo institucional: #E3000F  →  rojo vivo CUC
#  Rojo oscuro:        #B3000B
#  Rojo claro:         #FF3341
#  Rojo pálido:        #FDEDED
#  Gris oscuro texto:  #1E1E1E
#  Blanco fondo:       #FFFFFF
# ─────────────────────────────────────────────
CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,600;0,700;0,800;1,300;1,400&display=swap');

/* ── Variables ── */
:root {
    --cuc-red:        #E3000F;
    --cuc-red-dark:   #B3000B;
    --cuc-red-light:  #FF3341;
    --cuc-red-pale:   #FDEDED;
    --text-dark:      #1E1E1E;
    --text-mid:       #555555;
    --bg-white:       #FFFFFF;
    --bg-light:       #F8F4F4;
    --border-light:   #F0D0D0;
    --success:        #1A7A4A;
    --success-bg:     #E8F5EE;
    --warning-bg:     #FFF3E0;
    --warning:        #E65100;
}

/* ── Reset global ── */
html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
    color: var(--text-dark);
}

/* ── Fondo general ── */
.stApp {
    background: linear-gradient(160deg, #FDF6F6 0%, #F8F4F4 60%, #F0E8E8 100%);
    min-height: 100vh;
}

/* ── Header institucional ── */
.header-institucional {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 24px 0 8px 0;
    border-bottom: 3px solid var(--cuc-red);
    margin-bottom: 32px;
}
.header-institucional img {
    height: 52px;
    object-fit: contain;
}
.header-text h1 {
    font-family: 'Montserrat', sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    color: var(--cuc-red-dark);
    margin: 0;
    line-height: 1.2;
}
.header-text p {
    font-size: 0.78rem;
    color: var(--text-mid);
    margin: 2px 0 0 0;
    font-weight: 300;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Tarjeta contenedor ── */
.card {
    background: var(--bg-white);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 32px 36px;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(227, 0, 15, 0.07);
}

/* ── Aviso de privacidad ── */
.privacy-notice {
    background: var(--cuc-red-pale);
    border-left: 4px solid var(--cuc-red);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 4px 0 20px 0;
}
.privacy-notice p {
    font-size: 0.78rem;
    font-style: italic;
    color: var(--cuc-red-dark);
    margin: 0;
    line-height: 1.5;
}

/* ── Alerta duplicado ── */
.alert-duplicate {
    background: var(--warning-bg);
    border: 1.5px solid var(--warning);
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
}
.alert-duplicate p {
    color: var(--warning);
    font-weight: 600;
    font-size: 1rem;
    margin: 0;
}

/* ── Alerta éxito ── */
.alert-success {
    background: var(--success-bg);
    border: 1.5px solid var(--success);
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
    margin-top: 16px;
}
.alert-success p {
    color: var(--success);
    font-weight: 600;
    font-size: 1rem;
    margin: 0;
}

/* ── Divider decorativo ── */
.divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0 20px;
}
.divider span {
    font-family: 'Montserrat', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--cuc-red);
}
.divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-light);
}

/* ── Labels de campos ── */
.stTextInput label, .stTextArea label {
    font-weight: 600 !important;
    color: var(--text-dark) !important;
    font-size: 1.15rem !important;
    font-family: 'Montserrat', sans-serif !important;
    line-height: 1.5 !important;
    margin-bottom: 8px !important;
}

/* ── Espaciado entre preguntas ── */
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stTextArea"]) {
    margin-bottom: 32px !important;
}
.stTextArea {
    margin-bottom: 28px !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    border: 1.5px solid var(--border-light) !important;
    border-radius: 8px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 1rem !important;
    transition: border-color 0.2s;
    padding: 10px 14px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--cuc-red) !important;
    box-shadow: 0 0 0 3px rgba(227, 0, 15, 0.12) !important;
}

/* ── Botón principal ── */
.stButton > button {
    background: var(--cuc-red) !important;
    color: white !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.15rem !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 1rem 3rem !important;
    min-width: 280px !important;
    width: 100% !important;
    transition: background 0.2s, transform 0.1s, box-shadow 0.2s !important;
    box-shadow: 0 6px 22px rgba(227, 0, 15, 0.40) !important;
    margin-top: 12px !important;
}
.stButton > button:hover {
    background: var(--cuc-red-dark) !important;
    box-shadow: 0 8px 28px rgba(227, 0, 15, 0.50) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Botón de descarga ── */
.stDownloadButton > button {
    background: var(--cuc-red) !important;
    color: white !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem 2rem !important;
    box-shadow: 0 4px 14px rgba(227, 0, 15, 0.30) !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    background: var(--cuc-red-dark) !important;
    box-shadow: 0 6px 20px rgba(227, 0, 15, 0.40) !important;
    transform: translateY(-1px) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2C1010 0%, var(--cuc-red-dark) 100%);
}
[data-testid="stSidebar"] * {
    color: #F5E8E8 !important;
}
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color: white !important;
}
[data-testid="stSidebar"] label {
    color: #F5E8E8 !important;
    font-weight: 500 !important;
}

/* ── Métricas admin ── */
[data-testid="metric-container"] {
    background: var(--bg-white);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 2px 10px rgba(227, 0, 15, 0.08);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--cuc-red) !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid var(--border-light) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Footer ── */
.footer-cuc {
    text-align: center;
    padding: 32px 0 16px;
    color: var(--text-mid);
    font-size: 0.75rem;
    border-top: 1px solid var(--border-light);
    margin-top: 40px;
}
.footer-cuc strong { color: var(--cuc-red); }

/* ── Número de pregunta ── */
.q-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--cuc-red);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 2px;
}

/* ── Badge admin ── */
.admin-badge {
    display: inline-block;
    background: var(--cuc-red);
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 12px;
}
</style>
"""

# ─────────────────────────────────────────────
#  HELPERS CSV
# ─────────────────────────────────────────────
def cargar_datos() -> pd.DataFrame:
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return pd.DataFrame(columns=COLUMNAS)


def correo_existe(df: pd.DataFrame, correo: str) -> bool:
    if df.empty:
        return False
    return correo.strip().lower() in df["correo"].str.strip().str.lower().values


def guardar_registro(registro: dict):
    df = cargar_datos()
    nuevo = pd.DataFrame([registro])
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


# ─────────────────────────────────────────────
#  INYECCIÓN DE ESTILOS
# ─────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SIDEBAR – ACCESO ADMIN
# ─────────────────────────────────────────────
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
        "<small style='opacity:0.6'>Panel de administración CUC · Investigación académica</small>",
        unsafe_allow_html=True,
    )

es_admin = pwd_input == ADMIN_PASSWORD

# ─────────────────────────────────────────────
#  LOGO  (desde archivo local)
# ─────────────────────────────────────────────
LOGO_PATH = "logo_cuc.png"

def header_html(logo_src: str) -> str:
    return f"""
    <div class="header-institucional">
        <img src="{logo_src}" alt="Logo CUC" style="max-width:140px;height:auto;object-fit:contain;">
        <div class="header-text">
            <h1>Diagnóstico Operativo</h1>
            <p>Transformadores de Superficies · Investigación CUC 2026</p>
        </div>
    </div>
    """

# Mostrar logo con st.image (Streamlit lo maneja de forma nativa)
col_logo, col_title = st.columns([1, 3])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=180)
with col_title:
    st.markdown("""
    <div style='padding-top:10px'>
        <h2 style='font-family:"Montserrat",sans-serif; color:#E3000F; margin:0; font-size:1.5rem; font-weight:800;'>
            Diagnóstico Operativo
        </h2>
        <p style='color:#666; font-size:0.8rem; letter-spacing:0.06em; text-transform:uppercase; margin:4px 0 0; font-family:"Montserrat",sans-serif;'>
            Transformadores de Superficies · Investigación CUC 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border:none; border-top:3px solid #E3000F; margin:8px 0 28px;'>", unsafe_allow_html=True)


# ═════════════════════════════════════════════
#  VISTA 2 – PANEL DE ADMINISTRACIÓN
# ═════════════════════════════════════════════
if es_admin:
    st.markdown('<div class="admin-badge">🛡 Panel de Administración</div>', unsafe_allow_html=True)
    st.markdown("## 📊 Datos Recolectados")

    df = cargar_datos()
    total = len(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de registros", total)
    with col2:
        correos_unicos = df["correo"].nunique() if not df.empty else 0
        st.metric("Correos únicos", correos_unicos)
    with col3:
        if not df.empty and "timestamp" in df.columns:
            ultimo = df["timestamp"].iloc[-1][:10] if pd.notna(df["timestamp"].iloc[-1]) else "—"
        else:
            ultimo = "—"
        st.metric("Último registro", ultimo)

    st.markdown("---")

    if df.empty:
        st.info("Aún no hay registros en la base de datos.")
    else:
        st.markdown("### 📋 Tabla de Respuestas")

        # Renombrar columnas para mayor legibilidad
        df_display = df.copy()
        df_display.columns = [
            "Fecha/Hora", "Nombre del Taller", "Correo",
            "P1 – Rentabilidad",
            "P2 – Tiempo Operativo",
            "P3 – Normatividad AIU",
            "P4 – Percepción de Valor",
            "P5 – Inteligencia de Negocio",
        ]
        st.dataframe(df_display, use_container_width=True, height=420)

        # Descarga CSV limpio con BOM para Power BI
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.markdown("---")
        st.markdown("### ⬇️ Exportar para Business Intelligence")
        st.download_button(
            label="📥  Descargar CSV para Power BI / Excel",
            data=csv_bytes,
            file_name=f"diagnostico_superficies_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=False,
        )
        st.caption(
            "El archivo se exporta con codificación **UTF-8 con BOM**, "
            "compatible con Power BI, Excel y Tableau sin problemas de caracteres especiales."
        )

    st.markdown(
        '<div class="footer-cuc">Panel de Administración · <strong>Universidad de la Costa (CUC)</strong> · Uso interno exclusivo</div>',
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════
#  VISTA 1 – INTERFAZ DEL CLIENTE
# ═════════════════════════════════════════════
else:
    # Introducción
    st.markdown("""
    <div style='background:#FDEDED; border-radius:10px; padding:18px 22px; margin-bottom:24px; border:1px solid #F0D0D0;'>
        <p style='margin:0; font-size:0.95rem; color:#B3000B; font-weight:600;'>
            🔬 Investigación Académica – Universidad de la Costa
        </p>
        <p style='margin:6px 0 0; font-size:0.88rem; color:#555; line-height:1.6;'>
            Este diagnóstico hace parte de un estudio sobre procesos operativos en talleres de transformación 
            de superficies. Sus respuestas son fundamentales para el avance de la investigación.
            <strong>El proceso toma menos de 5 minutos.</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Campos de ingreso ──
    st.markdown("""
    <div style='font-family:"Montserrat",sans-serif; font-size:1.1rem; color:#E3000F; 
         font-weight:700; margin-bottom:14px; padding-bottom:6px; border-bottom:1px solid #F0D0D0;'>
        📝 Datos de Identificación
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        nombre_taller = st.text_input(
            "Nombre del Taller / Negocio *",
            placeholder="Ej: Taller Pinturas Caribe",
            key="nombre",
        )
    with col_b:
        correo = st.text_input(
            "Correo Electrónico *",
            placeholder="ejemplo@correo.com",
            key="correo",
        )

    # Aviso de privacidad
    st.markdown("""
    <div class="privacy-notice">
        <p>
            🔒 <em>Sus datos están protegidos por la Ley 1581 de 2012 (Habeas Data). 
            Esta información es recopilada con fines netamente académicos y de validación investigativa 
            para la Universidad de la Costa (CUC). No será compartida con terceros ni utilizada 
            para fines comerciales.</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Lógica de duplicados ──
    if correo:
        df_actual = cargar_datos()
        if correo_existe(df_actual, correo):
            st.markdown("""
            <div class="alert-duplicate">
                <p>⚠️ Este correo ya ha completado el diagnóstico.<br>
                <span style='font-weight:400;font-size:0.9rem;'>
                ¡Gracias por su valioso aporte a nuestra investigación!</span></p>
            </div>
            """, unsafe_allow_html=True)
            st.stop()

    # ── Formulario de preguntas ──
    if nombre_taller and correo:
        st.markdown("""
        <div style='font-family:"Montserrat",sans-serif; font-size:1.1rem; color:#E3000F; 
             font-weight:700; margin:28px 0 18px; padding-bottom:6px; border-bottom:1px solid #F0D0D0;'>
            🗒 Diagnóstico Operativo
        </div>
        """, unsafe_allow_html=True)

        respuestas = {}
        for clave, pregunta, placeholder in PREGUNTAS:
            respuestas[clave] = st.text_area(
                label=pregunta,
                placeholder=placeholder,
                height=110,
                key=clave,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Botón de envío
        if st.button("✅  Enviar Diagnóstico", use_container_width=False, key="btn_enviar"):
            # Validaciones
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
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nombre_taller": nombre_taller.strip(),
                    "correo": correo.strip().lower(),
                    **{k: v.strip() for k, v in respuestas.items()},
                }
                guardar_registro(registro)
                st.markdown("""
                <div class="alert-success">
                    <p>✅ ¡Diagnóstico enviado con éxito!<br>
                    <span style='font-weight:400;font-size:0.9rem;'>
                    Gracias por contribuir a la investigación de la Universidad de la Costa. 
                    Su información ha sido registrada de forma segura.</span></p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

    elif not nombre_taller and not correo:
        st.markdown("""
        <p style='color:#888; font-style:italic; font-size:0.88rem; margin-top:8px;'>
        👆 Complete los campos de identificación para acceder al formulario de diagnóstico.
        </p>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown(
        '<div class="footer-cuc">© 2026 · <strong>Universidad de la Costa (CUC)</strong> · '
        'Barranquilla, Colombia · Investigación Académica</div>',
        unsafe_allow_html=True,
    )
