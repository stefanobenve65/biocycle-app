import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI Coach", page_icon="🚴‍♂️", layout="wide")

# --- MEMORIA DI SESSIONE (Il database temporaneo) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    code = st.query_params["code"]
    try:
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state['strava_token'] = token_response['access_token']
        st.query_params.clear()
    except Exception:
        pass

# --- TITOLO E NAVIGAZIONE ---
st.title("🚴‍♂️ BioCycle: Il tuo Coach Intelligente")

tab1, tab2, tab3 = st.tabs(["👤 Profilo & Obiettivi", "🩺 Dati Medici & Strava", "💬 Chat BioCycle"])

# --- TAB 1: PROFILO UTENTE ---
with tab1:
    st.header("Il tuo Profilo Biologico")
    col1, col2 = st.columns(2)
    with col1:
        sesso = st.radio("Sesso", ["Uomo", "Donna"], horizontal=True)
        eta = st.number_input("Età", 14, 90, 40)
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 75.0)
    with col2:
        ore_sett = st.slider("Quante ore a settimana puoi allenarti?", 1, 25, 6)
        patologie = st.text_area("Note mediche o patologie", placeholder="Es. Diabete tipo 1, Intolleranza glutine...")
    
    st.divider()
    st.header("I tuoi Obiettivi")
    obiettivo = st.selectbox("Cosa vogliamo raggiungere?", [
        "Dimagrimento localizzato", 
        "Recupero post-infortunio", 
        "Maratona delle Dolomiti", 
        "Miglioramento soglia anaerobica",
        "Gran Fondo Nove Colli",
        "Salute generale e longevità"
    ])
    
    # Salvataggio nel profilo di sessione
    st.session_state.user_profile = {
        "sesso": sesso, "eta": eta, "peso": peso, 
        "ore": ore_sett, "note": patologie, "goal": obiettivo
    }

# --- TAB 2: DATI TECNICI ---
with tab2:
    st.header("Caricamento Dati")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🩺 Analisi Mediche")
        uploaded_file = st.file_uploader("Carica foto analisi del sangue", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, width=300)
    
    with col4:
        st.subheader("🔗 Stato Strava")
        if 'strava_token' not in st.session_state:
            url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
            st.link_button("Connetti Strava", url)
        else:
            st.success("🟢 Strava Sincronizzato")
            client.access_token = st.session_state['strava_token']
            activities = client.get_activities(limit=1)
            for act in activities:
                st.session_state['last_workout'] = f"{act.name}: {act.distance/1000:.1f}km, {act.total_elevation_gain}m d+"
                st.info(f"Ultimo dato letto: {st.session_state['last_workout']}")

# --- TAB 3: CHAT INTERATTIVA ---
with tab3:
    st.header("Chiedi al tuo Coach")
    
    # Visualizzazione cronologia
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Chiedimi consigli su cibo o allenamento..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Risposta IA con CONTESTO TOTALE
        if not st.sidebar.text_input("Gemini API Key", type="password", key="sidebar_key"):
            st.error("Inserisci la chiave API nella barra laterale!")
        else:
            try:
                genai.configure(api_key=st.session_state.sidebar_key, transport='rest')
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                # Costruiamo il contesto per l'IA
                workout = st.session_state.get('last_workout', 'Nessun allenamento recente')
                p = st.session_state.user_profile
                
                context = f"""
                PROFILO ATLETA: {p['sesso']}, {p['eta']} anni, {p['peso']}kg. 
                DISPONIBILITÀ: {p['ore']} ore/settimana. 
                NOTE MEDICHE: {p['note']}.
                OBIETTIVO: {p['goal']}.
                ULTIMO ALLENAMENTO: {workout}.
                
                RISPONDI COME COACH BIOCYCLE: Sii proattivo. Se l'utente chiede della colazione, 
                adattala al suo peso e al prossimo obiettivo. Se l'allenamento è stato duro, 
                suggerisci subito il recupero.
                """
                
                # Se c'è un'analisi medica, la inviamo
                content = [context, prompt]
                if uploaded_file:
                    content.append(Image.open(uploaded_file))
                
                with st.spinner("BioCycle sta elaborando..."):
                    response = model.generate_content(content)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    with st.chat_message("assistant"):
                        st.markdown(response.text)
            except Exception as e:
                st.error(f"Errore AI: {e}")
