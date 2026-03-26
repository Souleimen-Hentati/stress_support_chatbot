import streamlit as st
from components.history_download import render_history_download
from components.chatUI import render_chat_ui

st.set_page_config(
    page_title="MediBot - Stress Support Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "MediBot: Your AI-powered stress support chatbot"
    }
)

st.markdown("""
<style>
    .main-title {
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #666;
        text-align: center;
        margin-bottom: 1.5rem;
        font-size: 1rem;
    }
    
    [data-testid="chatAvatarIcon-user"] {
        background-color: #1f77b4;
    }
    
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #2ca02c;
    }
    
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .stChatInput {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<div class='main-title'>🤖 MediBot</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>AI-Powered Stress Support Assistant</div>", unsafe_allow_html=True)

st.info("⚠️ MediBot provides emotional support for stress management and is not a replacement for professional care or emergency services.")
st.markdown("---")

render_chat_ui()
render_history_download()
