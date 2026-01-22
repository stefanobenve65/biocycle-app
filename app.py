import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image
import json
import os

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v3.3", page_icon="🚴‍♂️", layout="wide")

# --- SISTEMA DI SALVATAGGIO (Dati Fissati) ---
DB_FILE = "biocycle_data.json"

def salva_dati(dati):
    with open(DB_FILE, "w") as f:
        json.dump(dati, f)

def carica_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

# Inizializzazione Sessione
if "messages" not in st.session_state: st.session_state.messages = []
if "user_data" not in st.session_state:
    st.session_state.user_data = carica_dati()

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=st.query_params["code"])
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
    except: pass

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    gemini_key = st.text_input("Gemini API Key", type="password", key="api_key_input")
    if "strava_token" not in st.session_state:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else: st.success("🟢 Strava Connesso")
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACCIA A 3 TAB ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
tab_profilo, tab_obiettivi, tab_dashboard = st.tabs(["👤 Profilo Utente", "🏆 Obiettivi e Prestazioni", "🚀 Dashboard & Chat"])

# --- TAB 1: PROFILO UTENTE (Dati Biometrici e Medici) ---
with tab_profilo:
    st.header("Il Tuo Profilo Personale")
    col_bio, col_med = st.columns(2)
    
    with col_bio:
        st.subheader("Dati Biometrici")
        eta = st.number_input("Età", 14, 90, st.session_state.user_data.get("eta", 40))
        peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data.get("peso", 75.0))
        altezza = st.number_input("Altezza (cm)", 100, 220, st.session_state.user_data.get("altezza", 175))
        disciplina = st.radio("Specialità", ["Strada", "MTB"], horizontal=True, 
                              index=0 if st.session_state.user_data.get("disc") == "Strada" else 1)
    
    with col_med:
        st.subheader("Informazioni Mediche")
        patologie = st.text_area("Patologie o informazioni mediche", st.session_state.user_data.get("med", ""))
        uploaded_files = st.file_uploader("Carica PDF o Immagini (Analisi, Referti)", type=["jpg", "png", "pdf"], accept_multiple_files=True)
        st.subheader("Consigli Nutrizionali")
        alimenti_no = st.text_area("Alimenti proibiti o non amati", st.session_state.user_data.get("no_food", ""), placeholder="Es: Lattosio, carne rossa...")

    if st.button("💾 Fissa Informazioni Profilo"):
        st.session_state.user_data.update({"eta": eta, "peso": peso, "altezza": altezza, "disc": disciplina, "med": patologie, "no_food": alimenti_no})
        salva_dati(st.session_state.user_data)
        st.success("Profilo aggiornato e fissato!")

# --- TAB 2: OBIETTIVI E PRESTAZIONI ---
with tab_obiettivi:
    st.header("Obiettivi e Prestazioni")
    st.write("Definisci i tuoi traguardi prestazionali e la tua disponibilità.")
    
    col_obj, col_disp = st.columns(2)
    with col_obj:
        st.subheader("Traguardi")
        obj_testo = st.text_area("Cosa vuoi raggiungere?", st.session_state.user_data.get("goal", ""), 
                                 placeholder="Es: Scalare lo Stelvio entro luglio, partecipare alla Maratona delle Dolomiti...")
    
    with col_disp:
        st.subheader("Disponibilità Allenamento")
        giorni = st.multiselect("Giorni disponibili", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"],
                                default=st.session_state.user_data.get("giorni", ["Sab", "Dom"]))
        ore = st.slider("Ore settimanali totali", 1, 30, st.session_state.user_data.get("ore", 6))

    if st.button("💾 Fissa Obiettivi"):
        st.session_state.user_data.update({"goal": obj_testo, "giorni": giorni, "ore": ore})
        salva_dati(st.session_state.user_data)
        st.success("Obiettivi salvati!")

# --- TAB 3: DASHBOARD & CHAT ---
with tab_dashboard:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat Interattiva")
        # Visualizzazione cronologia
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Chiedi dubbi, sensazioni o consigli..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            if st.session_state.api_key_input:
                try:
                    genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    # Contesto basato sui dati fissati
                    u = st.session_state.user_data
                    context = f"Atleta: {u.get('disc')}, {u.get('eta')} anni. Peso {u.get('peso')}kg. Goal: {u.get('goal')}. No food: {u.get('no_food')}. Med: {u.get('med')}."
                    
                    with st.chat_message("assistant"):
                        response = model.generate_content([context, prompt])
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e: st.error(f"Errore AI: {e}")

    with col_strava:
        st.subheader("📊 Analisi Rapida Strava")
        if "strava_token" in st.session_state:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Ultimo giro: {act.name}")
                    if st.button("✨ Analizza Recupero & Proprietà"):
                        genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        u = st.session_state.user_data
                        
                        prompt_strava = f"""
                        PROFILO: {u}. 
                        ULTIMO GIRO: {act.name}, {act.distance/1000:.1f}km.
                        
                        1. REPORT PROPRIETÀ ALLENATE: Cosa abbiamo allenato oggi?
                        2. CONSIGLIO RECUPERO: Cosa mangiare ora e nelle prossime ore (evitando {u.get('no_food')}).
                        """
                        with st.spinner("Analisi in corso..."):
                            res = model.generate_content(prompt_strava)
                            st.write(res.text)
            except: st.error("Errore nel caricamento attività Strava.")
        else: st.warning("Connetti Strava per l'analisi automatica.")
