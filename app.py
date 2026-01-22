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

st.set_page_config(page_title="BioCycle AI v3.4", page_icon="🚴‍♂️", layout="wide")

# --- SISTEMA DI SALVATAGGIO ---
DB_FILE = "biocycle_data.json"
def salva_dati(dati):
    with open(DB_FILE, "w") as f: json.dump(dati, f)
def carica_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

if "messages" not in st.session_state: st.session_state.messages = []
if "user_data" not in st.session_state: st.session_state.user_data = carica_dati()

# --- LOGICA STRAVA POTENZIATA ---
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
        # AGGIORNATO: Chiediamo esplicitamente 'activity:read_all'
        url = client.authorization_url(
            client_id=CLIENT_ID, 
            redirect_uri=REDIRECT_URI, 
            scope=['read_all', 'activity:read_all']
        )
        st.link_button("🔗 Connetti Strava", url)
    else: st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACCIA ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
tab_profilo, tab_obiettivi, tab_dashboard = st.tabs(["👤 Profilo Utente", "🏆 Obiettivi", "🚀 Dashboard & Chat"])

with tab_profilo:
    st.header("Il Tuo Profilo")
    col1, col2 = st.columns(2)
    with col1:
        eta = st.number_input("Età", 14, 90, st.session_state.user_data.get("eta", 40))
        peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data.get("peso", 75.0))
        altezza = st.number_input("Altezza (cm)", 100, 220, st.session_state.user_data.get("altezza", 175))
        disc = st.radio("Specialità", ["Strada", "MTB"], horizontal=True, index=0 if st.session_state.user_data.get("disc") == "Strada" else 1)
    with col2:
        patologie = st.text_area("Patologie/Info Mediche", st.session_state.user_data.get("med", ""))
        alimenti_no = st.text_area("Cibi proibiti", st.session_state.user_data.get("no_food", ""))
    
    if st.button("💾 Fissa Profilo"):
        st.session_state.user_data.update({"eta": eta, "peso": peso, "altezza": altezza, "disc": disc, "med": patologie, "no_food": alimenti_no})
        salva_dati(st.session_state.user_data)
        st.success("Dati fissati!")

with tab_obiettivi:
    st.header("I Tuoi Obiettivi")
    obj_testo = st.text_area("Cosa vuoi raggiungere?", st.session_state.user_data.get("goal", ""))
    if st.button("💾 Fissa Obiettivi"):
        st.session_state.user_data.update({"goal": obj_testo})
        salva_dati(st.session_state.user_data)
        st.success("Obiettivi salvati!")

with tab_dashboard:
    c_chat, c_strava = st.columns([1.5, 1])
    with c_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Chiedi al coach..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if st.session_state.api_key_input:
                genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                model = genai.GenerativeModel("gemini-2.5-flash")
                u = st.session_state.user_data
                context = f"Atleta {u.get('disc')}, {u.get('eta')} anni. Goal: {u.get('goal')}. No food: {u.get('no_food')}."
                with st.chat_message("assistant"):
                    resp = model.generate_content([context, prompt])
                    st.markdown(resp.text)
                    st.session_state.messages.append({"role": "assistant", "content": resp.text})

    with c_strava:
        st.subheader("📊 Analisi Strava")
        if "strava_token" in st.session_state:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Rilevato: {act.name}")
                    # Mostriamo subito i dati se disponibili
                    dist_km = float(act.distance) / 1000
                    st.write(f"Distanza: {dist_km:.2f} km")
                    
                    if st.button("✨ Analizza Giro"):
                        genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        prompt_s = f"Analizza questo giro di {dist_km:.2f}km per un atleta di {st.session_state.user_data.get('peso')}kg. A) Proprietà allenate B) Recupero post-giro (no {st.session_state.user_data.get('no_food')})."
                        with st.spinner("Analisi..."):
                            res = model.generate_content(prompt_s)
                            st.write(res.text)
            except Exception as e:
                st.error(f"Errore tecnico: {e}. Prova a ricollegare Strava spuntando tutte le caselle.")
        else: st.warning("Connetti Strava")
