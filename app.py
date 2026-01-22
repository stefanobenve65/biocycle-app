import streamlit as st
import requests
import json
from stravalib.client import Client
from PIL import Image
import io

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v6.1", page_icon="🚴‍♂️", layout="wide")

# --- 1. FUNZIONE CHIAMATA DIRETTA (Niente librerie instabili) ---
def call_gemini_direct(prompt, api_key):
    # Usiamo l'endpoint v1 stabile per evitare l'errore 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}
    }
    try:
        # Forza l'encoding in UTF-8 per uccidere l'errore Latin-1
        response = requests.post(url, headers=headers, data=json.dumps(payload).encode('utf-8'), timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Errore Google: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Errore di Connessione: {str(e)}"

# --- 2. GESTIONE MEMORIA E OAUTH ---
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "messages" not in st.session_state: st.session_state.messages = []

# Pulizia automatica del codice Strava per evitare l'errore 400
query_params = st.query_params
if "code" in query_params and st.session_state.strava_token is None:
    try:
        client = Client()
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=query_params["code"])
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear() # Svuota la URL
        st.rerun()
    except:
        st.query_params.clear()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("Gemini API Key", type="password")
    
    if not st.session_state.strava_token:
        client = Client()
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Sincronizzato")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. INTERFACCIA A TAB ---
t_profilo, t_obiettivi, t_dashboard = st.tabs(["👤 Profilo", "🏁 Obiettivi", "🚀 Dashboard"])

with t_profilo:
    st.header("Profilo")
    col1, col2 = st.columns(2)
    with col1:
        disciplina = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        peso = st.number_input("Peso (kg)", 40, 150, 75)
    with col2:
        no_food = st.text_area("Cibi no", placeholder="Es: Lattosio, carne rossa...")

with t_obiettivi:
    st.header("Obiettivi")
    goal = st.text_input("Il tuo traguardo", placeholder="Es: Maratona delle Dolomiti")

with t_dashboard:
    chat_col, strava_col = st.columns([1.5, 1])
    
    with chat_col:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            if api_key:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                
                # Creiamo il messaggio per l'IA
                full_prompt = f"Sei un coach esperto. Atleta: {disciplina}, Peso: {peso}kg, Goal: {goal}, Dieta: evita {no_food}. Domanda: {prompt}"
                
                with st.chat_message("assistant"):
                    risposta = call_gemini_direct(full_prompt, api_key)
                    st.markdown(risposta)
                    st.session_state.messages.append({"role": "assistant", "content": risposta})
            else:
                st.error("Inserisci la chiave API nella sidebar!")

    with strava_col:
        st.subheader("📊 Dati Strava")
        if st.session_state.strava_token:
            try:
                client = Client(access_token=st.session_state.strava_token)
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Uscita: {act.name}")
                    d_km = act.distance / 1000
                    st.metric("Distanza", f"{d_km:.2f} km")
                    
                    if st.button("✨ Analizza"):
                        if api_key:
                            prompt_s = f"Analizza giro di {d_km:.2f}km per atleta {peso}kg. Cosa allenato? Cosa mangiare per recupero? (No {no_food})."
                            with st.spinner("Analisi..."):
                                res = call_gemini_direct(prompt_s, api_key)
                                st.write(res)
            except:
                st.error("Ricollega Strava (Sessione scaduta)")
        else:
            st.warning("Connetti Strava")
