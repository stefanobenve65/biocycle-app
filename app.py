import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE CORE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v6.5", page_icon="🚴‍♂️", layout="wide")

# --- INIZIALIZZAZIONE SESSIONE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None

# --- LOGICA STRAVA (Esatta della 3.1) ---
client = Client()
# Recuperiamo il codice dalla URL se presente
if "code" in st.query_params:
    try:
        # Lo usiamo una volta sola
        code = st.query_params["code"]
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            code=code
        )
        st.session_state.strava_token = token_response['access_token']
        # Puliamo subito la URL per evitare che l'errore si ripeta al ricaricamento
        st.query_params.clear()
    except:
        # Se il codice è già stato usato, puliamo e basta
        st.query_params.clear()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    gemini_key = st.text_input("Inserisci Gemini API Key", type="password")
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACCIA A TAB ---
t1, t2, t3 = st.tabs(["👤 Profilo & Obiettivi", "🩺 Info Mediche", "🚀 Dashboard & Chat"])

with t1:
    st.header("Profilo & Obiettivi")
    c1, c2 = st.columns(2)
    with c1:
        disciplina = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 75.0)
    with c2:
        goal = st.text_input("Obiettivo", placeholder="Es: Maratona delle Dolomiti")
        no_food = st.text_area("Cibi da evitare")

with t2:
    st.header("Documentazione Medica")
    med_info = st.text_area("Patologie o note mediche")
    uploaded_file = st.file_uploader("Carica foto analisi", type=["jpg", "png", "jpeg"])

with t3:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Chat Coach")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            if gemini_key:
                try:
                    genai.configure(api_key=gemini_key.strip(), transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    # Contesto immediato
                    context = f"Atleta {disciplina}, peso {peso}kg, obiettivo {goal}. Evita {no_food}."
                    res = model.generate_content([context, prompt])
                    with st.chat_message("assistant"):
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e:
                    st.error(f"Errore IA: {e}")

    with col_strava:
        st.subheader("📊 Ultima Attività")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Giro: {act.name}")
                    d_km = act.distance / 1000
                    st.metric("Distanza", f"{d_km:.2f} km")
                    
                    if st.button("✨ Analizza Giro"):
                        if gemini_key:
                            genai.configure(api_key=gemini_key.strip(), transport='rest')
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            p = f"Analizza giro di {d_km:.2f}km per atleta di {peso}kg. Cosa mangiare per recupero (no {no_food})?"
                            with st.spinner("Analisi..."):
                                # Se c'è una foto medica, la passiamo
                                input_ia = [p]
                                if uploaded_file:
                                    input_ia.append(Image.open(uploaded_file))
                                r = model.generate_content(input_ia)
                                st.write(r.text)
                        else:
                            st.error("Manca la chiave API!")
            except:
                st.error("Errore nel caricamento dell'attività. Riprova a connettere Strava.")
        else:
            st.warning("Connetti Strava dalla barra laterale.")

