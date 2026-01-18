import streamlit as st
import google.generativeai as genai
from stravalib.client import Client

# --- I TUOI DATI STRAVA (GIÀ INSERITI) ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
# Questo è l'indirizzo che abbiamo configurato come callback
REDIRECT_URI = 'https://biocycle-app-jeyzkzryczapo3vcb5caqm.streamlit.app/'

st.set_page_config(page_title="BioCycle AI", layout="centered")
st.title("🚴‍♂️ BioCycle AI - Dashboard")

# --- LOGICA DI CONNESSIONE STRAVA ---
client = Client()

# Controlliamo se stiamo tornando da Strava con un codice di autorizzazione
if "code" in st.query_params:
    code = st.query_params["code"]
    try:
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            code=code
        )
        st.session_state['strava_token'] = token_response['access_token']
        st.success("✅ Strava collegato correttamente!")
    except Exception as e:
        st.error(f"Errore durante il collegamento: {e}")

# --- INTERFACCIA ---
with st.sidebar:
    st.header("Configurazione")
    gemini_key = st.text_input("Inserisci Gemini API Key", type="password")
    
    # Bottone per collegarsi a Strava
    if 'strava_token' not in st.session_state:
        authorize_url = client.authorization_url(
            client_id=CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            scope=['activity:read_all']
        )
        st.link_button("🔗 Connetti Strava", authorize_url)
    else:
        st.write("🟢 Strava è connesso")

# --- VISUALIZZAZIONE DATI ---
if 'strava_token' in st.session_state:
    client.access_token = st.session_state['strava_token']
    try:
        activities = client.get_activities(limit=1)
        st.header("Ultima Attività Rilevata")
        for activity in activities:
            st.info(f"Titolo: {activity.name}")
            st.write(f"Distanza: {activity.distance / 1000:.2f} km")
            st.write(f"Dislivello: {activity.total_elevation_gain} m")
    except Exception as e:
        st.error("Non è stato possibile caricare le attività.")
else:
    st.warning("Usa il tasto nella barra laterale per connettere i tuoi dati Strava.")

st.divider()
st.caption("Prototipo BioCycle AI 2026")
