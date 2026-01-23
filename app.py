import streamlit as st
import google.generativeai as genai
from stravalib.client import Client

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle v7.0", layout="wide")

# --- GESTIONE STATO ---
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- LOGICA STRAVA (Copia esatta 3.1 con fix per i ricaricamenti) ---
client = Client()
if "code" in st.query_params and st.session_state.strava_token is None:
    try:
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=st.query_params["code"]
        )
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
    except:
        st.query_params.clear()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    api_key = st.text_input("Gemini API Key", type="password")
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    if st.button("🗑️ Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

# --- INTERFACCIA A TAB ---
t1, t2 = st.tabs(["👤 Profilo e Obiettivi", "🚀 Dashboard & Coach"])

with t1:
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso Atleta (kg)", 40, 150, 75)
        disc = st.selectbox("Specialità", ["Strada", "MTB"])
    with col2:
        goal = st.text_input("Obiettivo", "Scalata del Ventoux")
        cibi_no = st.text_area("Allergie o cibi da evitare")

with t2:
    chat_col, data_col = st.columns([1.5, 1])
    
    with chat_col:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi qualcosa..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            if api_key:
                try:
                    genai.configure(api_key=api_key.strip(), transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    # Contesto semplificato per evitare errori di caratteri
                    ctx = f"Atleta {disc}, peso {peso}kg, goal {goal}. Evita {cibi_no}."
                    res = model.generate_content([ctx, prompt])
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                    with st.chat_message("assistant"): st.markdown(res.text)
                except Exception as e:
                    st.error(f"Errore IA: {e}")

    with data_col:
        st.subheader("📊 Dati Strava")
        if st.session_state.strava_token:
            try:
                client.access_token = st.session_state.strava_token
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Uscita: {act.name}")
                    km = act.distance / 1000
                    st.metric("Distanza", f"{km:.2f} km")
                    
                    if st.button("✨ Analizza Giro"):
                        if api_key:
                            genai.configure(api_key=api_key.strip(), transport='rest')
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            with st.spinner("Analizzando..."):
                                res = model.generate_content(f"Analizza giro di {km:.2f}km per atleta di {peso}kg.")
                                st.write(res.text)
            except:
                st.error("Errore nel recupero dati. Riprova la connessione.")
