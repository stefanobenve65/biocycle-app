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

st.set_page_config(page_title="BioCycle AI", layout="wide")

# --- 1. BLINDAGGIO DELLA MEMORIA (Session State) ---
# Inizializziamo tutto subito per evitare errori di "variabile non trovata"
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "peso": 75, "altezza": 175, "eta": 40, "sesso": "Uomo",
        "disciplina": "Strada", "cibi_no": "", "med_notes": ""
    }

# --- 2. MOTORE AI (Chiamata Diretta REST) ---
def call_coach_ai(prompt, api_key):
    # Endpoint stabile v1beta (il più affidabile per Gemini 1.5 Flash attualmente)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload).encode('utf-8'), timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Nota tecnica: Il servizio AI sta aggiornando i dati. (Codice: {response.status_code})"
    except:
        return "Connessione al coach momentaneamente interrotta."

# --- 3. LOGICA STRAVA (OAuth Pulito) ---
query_params = st.query_params
if "code" in query_params and st.session_state.strava_token is None:
    try:
        client = Client()
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=query_params["code"])
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
        st.rerun()
    except:
        st.query_params.clear()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    gemini_key = st.text_input("Inserisci la tua Gemini API Key", type="password")
    
    if not st.session_state.strava_token:
        client = Client()
        auth_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", auth_url)
    else:
        st.success("🟢 Strava Sincronizzato")
    
    if st.button("🗑️ Reset Applicazione"):
        st.session_state.clear()
        st.rerun()

# --- 5. INTERFACCIA A TAB ---
tab_profilo, tab_dashboard = st.tabs(["👤 Profilo Biologico", "🚀 Coach & Report"])

with tab_profilo:
    st.header("Inserisci le tue caratteristiche")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.user_data["disciplina"] = st.radio("Tipo di attività principale", ["Strada", "MTB"], horizontal=True)
        st.session_state.user_data["sesso"] = st.selectbox("Sesso", ["Uomo", "Donna", "Altro"])
        st.session_state.user_data["peso"] = st.number_input("Peso attuale (kg)", 30, 200, st.session_state.user_data["peso"])
    with c2:
        st.session_state.user_data["altezza"] = st.number_input("Altezza (cm)", 100, 250, st.session_state.user_data["altezza"])
        st.session_state.user_data["eta"] = st.number_input("Età", 14, 100, st.session_state.user_data["eta"])
    
    st.divider()
    st.subheader("Informazioni Mediche & Dieta")
    st.session_state.user_data["cibi_no"] = st.text_area("Cibi non graditi o allergie", placeholder="Es: peperoni, lattosio...")
    st.session_state.user_data["med_notes"] = st.text_area("Note mediche (Analisi del sangue, referti)", placeholder="Scrivi qui o carica un file sotto...")
    file_med = st.file_uploader("Carica Analisi o Referti (Foto)", type=["jpg", "jpeg", "png"])

with tab_dashboard:
    if not st.session_state.strava_token:
        st.warning("Per favore, connetti il tuo account Strava nella barra laterale per vedere i report.")
    else:
        try:
            client = Client(access_token=st.session_state.strava_token)
            activities = client.get_activities(limit=1)
            
            for act in activities:
                st.subheader(f"📊 Report Ultima Attività: {act.name}")
                dist_km = act.distance / 1000
                st.metric("Distanza percorsa", f"{dist_km:.2f} km")
                
                # Generazione automatica del report
                if gemini_key:
                    u = st.session_state.user_data
                    prompt_report = f"""
                    Sei un coach esperto. Analizza questo giro di {dist_km:.2f}km per un atleta ({u['sesso']}, {u['peso']}kg, {u['disciplina']}).
                    Note mediche: {u['med_notes']}. Cibi da evitare: {u['cibi_no']}.
                    Fornisci un report breve:
                    1. Cosa ha realmente allenato.
                    2. Recupero immediato (snack/sali).
                    3. Pasto principale (bilanciamento carboidrati/proteine/fibre).
                    Tono costruttivo e asciutto.
                    """
                    with st.spinner("Il Coach sta analizzando i dati..."):
                        report = call_coach_ai(prompt_report, gemini_key)
                        st.markdown(report)
                else:
                    st.info("Inserisci la API Key per ricevere l'analisi del Coach.")

                st.divider()
                # Sezione Chat di approfondimento
                st.subheader("💬 Approfondimento col Coach")
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
                if chat_in := st.chat_input("Vuoi approfondire l'analisi?"):
                    st.session_state.chat_history.append({"role": "user", "content": chat_in})
                    with st.chat_message("user"): st.markdown(chat_in)
                    if gemini_key:
                        risposta = call_coach_ai(chat_in, gemini_key)
                        st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                        with st.chat_message("assistant"): st.markdown(risposta)
        except:
            st.error("Si è verificato un problema nel caricamento dei dati Strava. Prova a ricollegare l'account.")
