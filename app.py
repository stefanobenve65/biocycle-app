import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'
GEMINI_MODEL = "gemini-1.5-flash-latest"

st.set_page_config(page_title="BioCycle AI v4.2", page_icon="🚴‍♂️", layout="wide")

# --- INIZIALIZZAZIONE SESSION STATE ---
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "strava_token" not in st.session_state: 
    st.session_state.strava_token = None
if "gemini_key" not in st.session_state: 
    st.session_state.gemini_key = ""
if "debug_log" not in st.session_state: 
    st.session_state.debug_log = ""
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "", "med": "", "goal": "scalata del mount ventoux", 
        "giorni": ["Sab", "Dom"]
    }

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            code=code
        )
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.session_state.debug_log += f"Errore Strava Auth: {e}\n"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    input_key = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_key)
    if input_key:
        st.session_state.gemini_key = input_key.strip()
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(
            client_id=CLIENT_ID, 
            redirect_uri=REDIRECT_URI, 
            scope=['read_all', 'activity:read_all']
        )
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat & Log"):
        st.session_state.messages =
