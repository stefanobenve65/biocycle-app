import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI", page_icon="🚴‍♂️", layout="wide")
st.title("🚴‍♂️ BioCycle AI - Dashboard")

client = Client()

# Gestione ritorno da Strava
if "code" in st.query_params:
    code = st.query_params["code"]
    try:
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state['strava_token'] = token_response['access_token']
        st.success("✅ Strava collegato!")
        st.query_params.clear()
    except Exception as e:
        st.error(f"Errore Strava: {e}")

# --- BARRA LATERALE ---
with st.sidebar:
    st.header("1. Configurazione")
    gemini_key = st.text_input("Inserisci Gemini API Key", type="password")
    
    if 'strava_token' not in st.session_state:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.write("🟢 Strava Connesso")
    
    st.divider()
    st.header("2. Obiettivo")
    goal = st.selectbox("Cosa vuoi fare?", ["Dimagrire", "Migliorare Performance", "Recupero Attivo"])

# --- COLONNE PRINCIPALI ---
col1, col2 = st.columns(2)

with col1:
    st.header("🩺 Analisi del Sangue")
    # Caricamento immagine
    uploaded_file = st.file_uploader("Carica la foto delle tue analisi", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Analisi caricate", use_container_width=True)

with col2:
    st.header("📊 Ultimo Allenamento")
    workout_summary = "Nessun dato Strava"
    if 'strava_token' in st.session_state:
        client.access_token = st.session_state['strava_token']
        activities = client.get_activities(limit=1)
        for activity in activities:
            workout_summary = f"{activity.name}: {activity.distance / 1000:.2f}km, {activity.total_elevation_gain}m d+"
            st.info(workout_summary)
            st.write(f"Tempo: {activity.moving_time}")
    else:
        st.warning("Connetti Strava per leggere l'attività")

# --- GENERAZIONE REPORT AI ---
st.divider()
if st.button("🚀 Genera Report BioCycle"):
    if not gemini_key or not uploaded_file or 'strava_token' not in st.session_state:
        st.error("Mancano dati: controlla Chiave API, Foto Analisi e Strava.")
    else:
        try:
            genai.configure(api_key=gemini_key.strip(), transport='rest')
            # Usiamo il modello 2.5 Flash che legge anche le immagini
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # Prepariamo l'immagine per l'AI
            img = Image.open(uploaded_file)
            
            prompt = f"""
            Agisci come un esperto medico sportivo e nutrizionista per ciclisti amatori italiani.
            
            1. Leggi i valori delle analisi del sangue dall'immagine allegata.
            2. Considera l'ultimo allenamento Strava: {workout_summary}.
            3. L'obiettivo dell'atleta è: {goal}.
            
            Fornisci un report in italiano con:
            - COMMENTO VALORI: Indica se ci sono carenze (es. Ferro, Magnesio) rilevanti per il ciclismo.
            - PIANO NUTRIZIONALE: Cosa mangiare oggi per recuperare o dimagrire.
            - CONSIGLIO TECNICO: Come affrontare la prossima uscita in base a come stai.
            """
            
            with st.spinner("L'AI sta leggendo le tue analisi e i dati Strava..."):
                response = model.generate_content([prompt, img])
                st.success("✅ Analisi Completata")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Errore durante l'analisi: {e}")
