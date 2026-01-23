
import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE (Identica alla tua 3.1) ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v3.1+", page_icon="🚴‍♂️", layout="wide")

# --- INIZIALIZZAZIONE SESSIONE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_profile" not in st.session_state: st.session_state.user_profile = {}
if "strava_token" not in st.session_state: st.session_state.strava_token = None

# --- LOGICA STRAVA (Identica alla tua 3.1) ---
client = Client()
if "code" in st.query_params:
    try:
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=st.query_params["code"]
        )
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
    except: pass

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    gemini_key = st.text_input("Inserisci Gemini API Key", type="password")
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Sincronizzato")

# --- INTERFACCIA A 3 TAB (Solo estetica, cuore 3.1) ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
t1, t2, t3 = st.tabs(["👤 Profilo", "🏁 Obiettivi", "🚀 Dashboard & Chat"])

with t1:
    st.header("Profilo Biomeccanico")
    c1, c2 = st.columns(2)
    with c1:
        disciplina = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        eta = st.number_input("Età", 14, 90, 40)
    with c2:
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 75.0)
        altezza = st.number_input("Altezza (cm)", 100, 220, 175)

with t2:
    st.header("Obiettivi e Dieta")
    obj_dettaglio = st.text_input("Specifica obiettivo", placeholder="Es: Maratona delle Dolomiti")
    alimenti_no = st.text_area("Cibi da evitare")
    # Salviamo nello state
    st.session_state.user_profile = {
        "disciplina": disciplina, "eta": eta, "peso": peso, "altezza": altezza,
        "goal": obj_dettaglio, "no_food": alimenti_no
    }

with t3:
    col_chat, col_data = st.columns([1.5, 1])
    with col_chat:
        st.subheader("💬 Chat Coach")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Chiedi..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if gemini_key:
                genai.configure(api_key=gemini_key.strip(), transport='rest')
                model = genai.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content([str(st.session_state.user_profile), prompt])
                with st.chat_message("assistant"):
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})

    with col_data:
        st.subheader("📊 Dati Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Giro: {act.name}")
                    d_km = act.distance / 1000
                    st.metric("Distanza", f"{d_km:.2f} km")
                    if st.button("✨ Analizza"):
                        if gemini_key:
                            genai.configure(api_key=gemini_key.strip(), transport='rest')
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            r = model.generate_content(f"Analizza giro {d_km}km per atleta {peso}kg.")
                            st.write(r.text)
            except: st.error("Errore Strava")
