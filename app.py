import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- 1. CONFIGURAZIONE CORE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v5.1", page_icon="🚴‍♂️", layout="wide")

# --- 2. INIZIALIZZAZIONE TOTALE (Fix KeyError & AttributeError) ---
# Questo blocco assicura che l'app sappia chi è fin dal primo millisecondo
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "gemini_key" not in st.session_state: st.session_state.gemini_key = ""
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "Nessuno", "med": "Nessuna", "goal": "Obiettivo generico", 
        "giorni": ["Sab", "Dom"]
    }

# --- 3. MOTORE OAUTH STRAVA ---
client = Client()
if "code" in st.query_params and st.session_state.strava_token is None:
    try:
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=st.query_params["code"]
        )
        st.session_state.strava_
