import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI", page_icon="🚴‍♂️", layout="wide")

# Inizializzazione della memoria della chat se non esiste
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    code = st.query_params["code"]
    try:
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state['strava_token'] = token_response['access_token']
        st.query_params.clear()
    except Exception as e:
        st.error(f"Errore Strava: {e}")

# --- INTERFACCIA PRINCIPALE ---
st.title("🚴‍♂️ BioCycle AI: Il tuo Coach Digitale")

# Dividiamo l'app in TAB per la massima pulizia
tab1, tab2, tab3 = st.tabs(["👤 Profilo & Obiettivi", "📊 Dati & Analisi", "💬 Chat Assistente"])

with tab1:
    st.header("Il tuo Profilo Atleta")
    col_a, col_b = st.columns(2)
    with col_a:
        sesso = st.selectbox("Sesso", ["Uomo", "Donna", "Altro"])
        eta = st.number_input("Età", min_value=14, max_value=90, value=40)
        peso = st.number_input("Peso attuale (kg)", min_value=40.0, max_value=150.0, value=75.0)
    with col_b:
        patologie = st.text_area("Patologie o intolleranze (opzionale)", placeholder="Es: Gastrite, intolleranza al lattosio...")
        disponibilita = st.slider("Ore settimanali dedicate all'allenamento", 1, 20, 5)

    st.divider()
    st.header("I tuoi Obiettivi")
    obiettivo = st.selectbox("Cosa vuoi raggiungere?", 
                              ["Perdita Peso", "Miglioramento Prestazioni", "Recupero e Salute", "Maratona delle Dolomiti", "Passo dello Stelvio", "Granfondo custom"])

with tab2:
    col_c, col_d = st.columns(2)
    with col_c:
        st.header("🩺 Analisi Mediche")
        uploaded_file = st.file_uploader("Carica analisi (Foto o PDF)", type=["jpg", "jpeg", "png", "pdf"])
    
    with col_d:
        st.header("🔗 Connessione Strava")
        if 'strava_token' not in st.session_state:
            url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
            st.link_button("Collega il tuo Strava", url)
        else:
            st.success("🟢 Strava collegato")
            client.access_token = st.session_state['strava_token']
            activities = client.get_activities(limit=1)
            for act in activities:
                st.info(f"Ultimo allenamento: {act.name} ({act.distance/1000:.1f}km)")

with tab3:
    st.header("💬 Conversazione con BioCycle")
    # Visualizza i messaggi precedenti
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Chiedimi un consiglio sulla colazione o sul recupero..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Risposta AI (Logica semplificata per il test)
        with st.chat_message("assistant"):
            st.write("Sto analizzando il tuo profilo per risponderti...")

# --- BARRA LATERALE (SOLO PER CHIAVE API) ---
with st.sidebar:
    gemini_key = st.text_input("Gemini API Key", type="password")
    st.caption("BioCycle v2.7 - Mercato Italiano")
