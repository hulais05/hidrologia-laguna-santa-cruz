import pathlib
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Hidrología Satelital y Volúmenes (m³) · Laguna Santa Cruz (1985–2026)",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove default Streamlit padding so the D3 dashboard fills the viewport cleanly
st.markdown(
    """
    <style>
        .block-container { padding: 0rem !important; max-width: 100% !important; }
        header[data-testid="stHeader"] { display: none; }
        footer { display: none; }
        iframe { border: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

html_path = pathlib.Path(__file__).parent / "laguna_santa_cruz_standalone.html"
html_content = html_path.read_text(encoding="utf-8")
components.html(html_content, height=3550, scrolling=True)
