import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image
import json
import os

# --- CONFIGURAZIONE CORE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v3.8", page_icon="🚴‍♂️", layout="wide")

# --- SISTEMA DI SALVATAGGIO (Persistenza) ---
DB_FILE = "biocycle_data.json"
def salva_dati(dati):
    with open(DB_FILE, "w") as f: json.dump(dati, f)
def carica_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

# Inizializzazione Sessione
if "messages" not in st.session_state: st.session_state.messages = []
if "user_data" not in st.session_state: st.session_state.user_data = carica_dati()

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
    
    st.divider()
    if "strava_token" not in st.session_state or not st.session_state.strava_token:
        # Usiamo gli scopes corretti per vedere i km
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else: st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACCIA A 3 TAB (Riorganizzata come volevi) ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
tab_profilo, tab_obiettivi, tab_dashboard = st.tabs(["👤 Profilo Utente", "🏆 Obiettivi & Prestazioni", "🚀 Dashboard & Chat"])

# --- TAB 1: PROFILO & SALUTE ---
with tab_profilo:
    st.header("Il Tuo Profilo Personale")
    col_bio, col_med = st.columns(2)
    with col_bio:
        st.subheader("Dati Biometrici")
        eta = st.number_input("Età", 14, 90, st.session_state.user_data.get("eta", 40))
        peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data.get("peso", 75.0))
        altezza = st.number_input("Altezza (cm)", 100, 220, st.session_state.user_data.get("altezza", 175))
        disc = st.radio("Specialità", ["Strada", "MTB"], horizontal=True, 
                        index=0 if st.session_state.user_data.get("disc") == "Strada" else 1)
    with col_med:
        st.subheader("Info Mediche e Nutrizione")
        patologie = st.text_area("Note mediche / Patologie", st.session_state.user_data.get("med", ""))
        alimenti_no = st.text_area("Cibi proibiti o non amati", st.session_state.user_data.get("no_food", ""), placeholder="Es: Lattosio, carne rossa...")
        uploaded_docs = st.file_uploader("Carica Analisi (Foto/PDF)", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

    if st.button("💾 Fissa Profilo"):
        st.session_state.user_data.update({"eta": eta, "peso": peso, "altezza": altezza, "disc": disc, "med": patologie, "no_food": alimenti_no})
        salva_dati(st.session_state.user_data)
        st.success("Profilo fissato correttamente!")

# --- TAB 2: OBIETTIVI ---
with tab_obiettivi:
    st.header("Obiettivi e Prestazioni")
    obj_testo = st.text_area("Cosa vuoi raggiungere?", st.session_state.user_data.get("goal", ""), 
                             placeholder="Es: Scalare lo Stelvio, Maratona delle Dolomiti...")
    giorni = st.multiselect("Giorni disponibili", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sat", "Dom"],
                            default=st.session_state.user_data.get("giorni", ["Sab", "Dom"]))
    
    if st.button("💾 Fissa Obiettivi"):
        st.session_state.user_data.update({"goal": obj_testo, "giorni": giorni})
        salva_dati(st.session_state.user_data)
        st.success("Obiettivi salvati!")

# --- TAB 3: DASHBOARD & CHAT ---
with tab_dashboard:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            if not st.session_state.api_key_input:
                st.error("Inserisci la chiave API nella barra laterale!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                try:
                    # Configurazione ESATTA della versione 3.1
                    genai.configure(api_key=st.session_state.api_key_input.strip(), transport='rest')
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    u = st.session_state.user_data
                    ctx = f"Coach BioCycle. Atleta {u.get('disc')}, {u.get('eta')} anni. Goal: {u.get('goal')}. No food: {u.get('no_food')}. Usa farro, integrale, pasta lenticchie."
                    
                    with st.chat_message("assistant"):
                        res = model.generate_content([ctx, prompt])
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e: st.error(f"Errore Chat: {e}")

    with col_strava:
        st.subheader("📊 Analisi Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Rilevato: {act.name}")
                    dist_km = float(act.distance) / 1000
                    st.metric("Distanza", f"{dist_km:.2f} km")
                    
                    if st.button("✨ Analizza Giro"):
                        genai.configure(api_key=st.session_state.api_key_input.strip(), transport='rest')
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        u = st.session_state.user_data
                        prompt_s = f"Analizza giro di {dist_km:.2f}km. Atleta {u.get('peso')}kg. A) Capacità allenata B) Recupero (no {u.get('no_food')}). Includi farro, integrale o pasta lenticchie."
                        with st.spinner("Analisi..."):
                            input_ai = [prompt_s]
                            if uploaded_docs:
                                for doc in uploaded_docs:
                                    if doc.type.startswith("image"): input_ai.append(Image.open(doc))
                            res = model.generate_content(input_ai)
                            st.write(res.text)
            except Exception as e: st.error(f"Errore Strava: {e}")
        else: st.warning("Connetti Strava")
