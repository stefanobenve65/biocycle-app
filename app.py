import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image
import json
import os

# --- CONFIGURAZIONE CORE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v3.2", page_icon="🚴‍♂️", layout="wide")

# --- FUNZIONI DI SALVATAGGIO (Persistenza) ---
def salva_profilo(dati):
    with open("profilo_utente.json", "w") as f:
        json.dump(dati, f)

def carica_profilo():
    if os.path.exists("profilo_utente.json"):
        with open("profilo_utente.json", "r") as f:
            return json.load(f)
    return None

# --- INIZIALIZZAZIONE SESSIONE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None

# Carichiamo i dati salvati se esistono
profilo_salvato = carica_profilo()
if "user_profile" not in st.session_state:
    st.session_state.user_profile = profilo_salvato if profilo_salvato else {}

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
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else: st.success("🟢 Strava Connesso")
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACCIA ---
st.title("🚴‍♂️ BioCycle AI: Il tuo Digital Coach")
t1, t2, t3 = st.tabs(["👤 Profilo Utente", "🏁 Obiettivi & Prestazioni", "🚀 Dashboard & Chat"])

# --- TAB 1: PROFILO (Dati che rimangono fissati) ---
with t1:
    st.header("Il Tuo Profilo Biologico")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Dati Biometrici")
        disc = st.radio("Specialità", ["Strada", "MTB"], 
                        index=0 if st.session_state.user_profile.get("disciplina") == "Strada" else 1)
        eta = st.number_input("Età", 14, 90, st.session_state.user_profile.get("eta", 40))
        peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_profile.get("peso", 75.0))
        altezza = st.number_input("Altezza (cm)", 100, 220, st.session_state.user_profile.get("altezza", 175))
    with c2:
        st.subheader("Nutrizione & Salute")
        alimenti_no = st.text_area("Cibi proibiti o non amati", st.session_state.user_profile.get("no_food", ""), placeholder="Es: Lattosio, peperoni...")
        patologie = st.text_area("Note mediche / Patologie", st.session_state.user_profile.get("med", ""))
        uploaded_docs = st.file_uploader("Carica Analisi (Foto/PDF)", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

    if st.button("💾 Salva Profilo"):
        dati = {
            "disciplina": disc, "eta": eta, "peso": peso, "altezza": altezza,
            "no_food": alimenti_no, "med": patologie
        }
        st.session_state.user_profile.update(dati)
        salva_profilo(st.session_state.user_profile)
        st.success("Profilo salvato correttamente!")

# --- TAB 2: OBIETTIVI ---
with t2:
    st.header("Obiettivi e Prestazioni")
    c3, c4 = st.columns(2)
    with c3:
        tipo_obj = st.selectbox("Ambito obiettivo", ["Salute", "Gara/Evento", "Scalata Montagna", "Custom"],
                                index=0)
        obj_dett = st.text_input("Dettaglio Obiettivo", st.session_state.user_profile.get("goal_detail", ""), 
                                 placeholder="Es: Raggiungere il rifugio X o Finire la Granfondo Y")
    with c4:
        giorni = st.multiselect("Giorni di allenamento", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"],
                                default=st.session_state.user_profile.get("giorni", ["Sab", "Dom"]))
    
    if st.button("💾 Salva Obiettivi"):
        st.session_state.user_profile.update({"goal_type": tipo_obj, "goal_detail": obj_dett, "giorni": giorni})
        salva_profilo(st.session_state.user_profile)
        st.success("Obiettivi aggiornati!")

# --- TAB 3: DASHBOARD (CHAT + STRAVA) ---
with t3:
    col_chat, col_data = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if chat_input := st.chat_input("Chiedi un consiglio..."):
            st.session_state.messages.append({"role": "user", "content": chat_input})
            with st.chat_message("user"): st.markdown(chat_input)
            
            if st.session_state.api_key_input:
                genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                model = genai.GenerativeModel("gemini-2.5-flash")
                p = st.session_state.user_profile
                context = f"Atleta {p.get('disciplina')}, {p.get('eta')} anni. Peso {p.get('peso')}kg. Goal: {p.get('goal_detail')}. No food: {p.get('no_food')}. Note Mediche: {p.get('med')}"
                
                with st.chat_message("assistant"):
                    res = model.generate_content([context, chat_input])
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})

    with col_data:
        st.subheader("📊 Analisi Rapida Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Ultimo giro: {act.name}")
                    if st.button("✨ Analizza Recupero & Proprietà"):
                        genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        p = st.session_state.user_profile
                        prompt = f"Giro: {act.name}, {act.distance/1000:.1f}km. Profilo: {p}. Analizza: A) Proprietà allenate B) Cosa mangiare (evitando {p.get('no_food')})."
                        with st.spinner("Calcolo..."):
                            resp = model.generate_content(prompt)
                            st.write(resp.text)
            except: st.error("Errore Strava")
        else: st.warning("Connetti Strava")
