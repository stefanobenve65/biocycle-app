import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- 1. CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v5.2", page_icon="🚴‍♂️", layout="wide")

# --- 2. INIZIALIZZAZIONE (Obbligatoria per evitare KeyError) ---
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "messages" not in st.session_state: st.session_state.messages = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "", "med": "", "goal": "", "giorni": ["Sabato", "Domenica"]
    }

# --- 3. LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
    except: pass

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    api_key = st.text_input("Inserisci Gemini API Key", type="password")
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Totale"):
        st.session_state.clear()
        st.rerun()

# --- 5. INTERFACCIA A TAB ---
t1, t2, t3 = st.tabs(["👤 Profilo", "🏁 Obiettivi", "🚀 Coach & Analisi"])

with t1:
    st.header("Profilo Biologico")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.user_profile["disc"] = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        st.session_state.user_profile["eta"] = st.number_input("Età", 14, 90, st.session_state.user_profile["eta"])
        st.session_state.user_profile["peso"] = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_profile["peso"])
    with c2:
        st.session_state.user_profile["med"] = st.text_area("Note Mediche", st.session_state.user_profile["med"])
        file_up = st.file_uploader("Allega Analisi (Immagini)", type=["jpg", "png", "jpeg"])

with t2:
    st.header("Obiettivi & Dieta")
    st.session_state.user_profile["goal"] = st.text_input("Cosa vuoi raggiungere?", st.session_state.user_profile["goal"])
    st.session_state.user_profile["no_food"] = st.text_area("Alimenti da evitare", st.session_state.user_profile["no_food"])
    # Fix Errore Sabato/Sat: Usiamo nomi lunghi per evitare ambiguità
    giorni_opt = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    st.session_state.user_profile["giorni"] = st.multiselect("Giorni disponibili", giorni_opt, default=st.session_state.user_profile["giorni"])

with t3:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if api_key:
                try:
                    # Fix Errore Latin-1: Forza l'encoding UTF-8
                    genai.configure(api_key=api_key.strip(), transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    u = st.session_state.user_profile
                    # Creiamo un contesto pulito senza caratteri speciali eccessivi
                    context = f"Atleta {u['disc']}, Peso {u['peso']}kg. Obiettivo: {u['goal']}. No food: {u['no_food']}."
                    with st.chat_message("assistant"):
                        response = model.generate_content([context, prompt])
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e: st.error(f"Errore AI: {e}")

    with col_strava:
        st.subheader("📊 Analisi Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Giro: {act.name}")
                    d_km = float(act.distance) / 1000
                    st.metric("Distanza", f"{d_km:.2f} km")
                    if st.button("✨ Analizza"):
                        if api_key:
                            try:
                                genai.configure(api_key=api_key.strip(), transport='rest')
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                u = st.session_state.user_profile
                                p = f"Analizza giro di {d_km:.2f}km. Recupero per atleta di {u['peso']}kg (no {u['no_food']})."
                                input_ia = [p]
                                if file_up: input_ia.append(Image.open(file_up))
                                with st.spinner("Analisi..."):
                                    res = model.generate_content(input_ia)
                                    st.write(res.text)
                            except Exception as e: st.error(f"Errore: {e}")
            except: st.error("Errore caricamento attività.")
