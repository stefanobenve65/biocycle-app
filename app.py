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

st.set_page_config(page_title="BioCycle AI v3.6", page_icon="🚴‍♂️", layout="wide")

# --- MEMORIA DATI ---
DB_FILE = "biocycle_data.json"
def salva_dati(dati):
    with open(DB_FILE, "w") as f: json.dump(dati, f)
def carica_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

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
    if "strava_token" not in st.session_state:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else: st.success("🟢 Strava Connesso")
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACCIA ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
tab1, tab2, tab3 = st.tabs(["👤 Profilo", "🏆 Obiettivi", "🚀 Dashboard & Chat"])

with tab1:
    st.header("Il Tuo Profilo")
    col1, col2 = st.columns(2)
    with col1:
        eta = st.number_input("Età", 14, 90, st.session_state.user_data.get("eta", 40))
        peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data.get("peso", 75.0))
        altezza = st.number_input("Altezza (cm)", 100, 220, st.session_state.user_data.get("altezza", 175))
        disc = st.radio("Specialità", ["Strada", "MTB"], horizontal=True, index=0 if st.session_state.user_data.get("disc") == "Strada" else 1)
    with col2:
        patologie = st.text_area("Note Mediche", st.session_state.user_data.get("med", ""))
        alimenti_no = st.text_area("Cibi proibiti", st.session_state.user_data.get("no_food", ""))
    if st.button("💾 Fissa Profilo"):
        st.session_state.user_data.update({"eta": eta, "peso": peso, "altezza": altezza, "disc": disc, "med": patologie, "no_food": alimenti_no})
        salva_dati(st.session_state.user_data)
        st.success("Dati salvati!")

with tab2:
    st.header("I Tuoi Obiettivi")
    obj = st.text_area("Cosa vuoi raggiungere?", st.session_state.user_data.get("goal", ""))
    if st.button("💾 Fissa Obiettivi"):
        st.session_state.user_data.update({"goal": obj})
        salva_dati(st.session_state.user_data)
        st.success("Obiettivi salvati!")

with tab3:
    c_chat, c_strava = st.columns([1.5, 1])
    with c_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Chiedi al coach..."):
            if not st.session_state.api_key_input: st.error("Manca chiave API!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                try:
                    # FIX: Usiamo 'gemini-pro' per massima compatibilità v1
                    genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                    model = genai.GenerativeModel("gemini-pro")
                    u = st.session_state.user_data
                    ctx = f"Atleta {u.get('disc')}, {u.get('eta')} anni. Goal: {u.get('goal')}. No food: {u.get('no_food')}."
                    with st.chat_message("assistant"):
                        res = model.generate_content([ctx, prompt])
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e: st.error(f"Errore AI: {e}")

    with c_strava:
        st.subheader("📊 Analisi Strava")
        if "strava_token" in st.session_state:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Giro: {act.name}")
                    dist_km = float(act.distance) / 1000
                    st.metric("Distanza", f"{dist_km:.2f} km")
                    if st.button("✨ Analizza Giro"):
                        if not st.session_state.api_key_input: st.error("Manca chiave API!")
                        else:
                            try:
                                genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                                model = genai.GenerativeModel("gemini-pro")
                                prompt_s = f"Giro di {dist_km:.2f}km. Atleta {st.session_state.user_data.get('peso')}kg. A) Capacità allenata B) Recupero (no {st.session_state.user_data.get('no_food')})."
                                with st.spinner("Analisi..."):
                                    r = model.generate_content(prompt_s)
                                    st.write(r.text)
                            except Exception as e: st.error(f"Errore: {e}")
            except Exception as e: st.error(f"Errore Strava: {e}")
        else: st.warning("Connetti Strava")
