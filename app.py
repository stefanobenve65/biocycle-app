import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI Coach", page_icon="🚴‍♂️", layout="wide")

# --- INIZIALIZZAZIONE MEMORIA (Fondamentale per non perdere la chiave) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "strava_token" not in st.session_state:
    st.session_state.strava_token = None

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    code = st.query_params["code"]
    try:
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
    except Exception:
        pass

# --- BARRA LATERALE (Configurazione Chiave) ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    # Usiamo 'key' per salvare il valore direttamente nello session_state
    gemini_key = st.text_input("Inserisci Gemini API Key", type="password", key="api_key_input")
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Sincronizzato")

# --- INTERFACCIA A TAB ---
st.title("🚴‍♂️ BioCycle: Il tuo Coach Intelligente")
tab1, tab2, tab3 = st.tabs(["👤 Profilo", "🩺 Dati Medici", "💬 Chat BioCycle"])

with tab1:
    st.header("Profilo Atleta")
    c1, c2 = st.columns(2)
    with c1:
        sesso = st.radio("Sesso", ["Uomo", "Donna"], horizontal=True)
        eta = st.number_input("Età", 14, 90, 40)
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 75.0)
    with c2:
        ore = st.slider("Ore settimanali", 1, 25, 6)
        obiettivo = st.selectbox("Obiettivo", ["Dimagrire", "Performance", "Maratona Dolomiti", "Salute"])
    
    st.session_state.user_profile = {"sesso": sesso, "eta": eta, "peso": peso, "ore": ore, "goal": obiettivo}

with tab2:
    st.header("Analisi Mediche")
    uploaded_file = st.file_uploader("Carica foto analisi", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, width=300)

with tab3:
    st.header("Chiedi al tuo Coach")
    
    # Visualizza i messaggi della chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input della Chat
    if prompt := st.chat_input("Chiedimi cosa mangiare o come allenarti..."):
        # CONTROLLO CHIAVE: Verifichiamo se l'utente l'ha scritta nella sidebar
        if not st.session_state.api_key_input:
            st.error("⚠️ Errore: Inserisci la chiave API nella barra laterale prima di scrivere!")
        else:
            # 1. Aggiungi messaggio utente alla memoria
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 2. Risposta AI
            try:
                genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                # Recupero dati Strava se disponibili
                workout = "Nessun dato Strava"
                if st.session_state.strava_token:
                    client.access_token = st.session_state.strava_token
                    activities = client.get_activities(limit=1)
                    for act in activities:
                        workout = f"{act.name}: {act.distance/1000:.1f}km"

                # Costruzione contesto
                p = st.session_state.user_profile
                full_prompt = f"Contesto Atleta: {p}. Ultimo Allenamento: {workout}. Domanda: {prompt}"
                
                content = [full_prompt]
                if uploaded_file:
                    content.append(Image.open(uploaded_file))

                with st.chat_message("assistant"):
                    with st.spinner("Analisi in corso..."):
                        response = model.generate_content(content)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Errore tecnico: {e}")
