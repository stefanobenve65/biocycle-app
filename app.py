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

st.set_page_config(page_title="BioCycle AI v4.2", page_icon="🚴‍♂️", layout="wide")

# --- 1. INIZIALIZZAZIONE SESSION STATE (Fix AttributeError) ---
# Inizializziamo tutto all'inizio per evitare l'errore visto in image_80c44f.png
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "gemini_key" not in st.session_state: st.session_state.gemini_key = ""
if "debug_log" not in st.session_state: st.session_state.debug_log = ""
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "", "med": "", "goal": "scalata del mount ventoux", 
        "giorni": ["Sab", "Dom"] # Nomi che devono coincidere con le opzioni
    }

# --- 2. LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state.strava_token = token_response['access_token']
        # Non puliamo i params qui per evitare loop di ricaricamento
    except Exception as e:
        st.session_state.debug_log += f"Errore Strava Auth: {e}\n"

# --- 3. SIDEBAR (Configurazione) ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    # Salvataggio corretto della chiave (Fix errore segnalato)
    input_key = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_key)
    if input_key:
        st.session_state.gemini_key = input_key.strip()
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat & Log"):
        st.session_state.messages = []
        st.session_state.debug_log = ""
        st.rerun()

# --- 4. INTERFACCIA A TAB ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
t1, t2, t3 = st.tabs(["👤 Profilo", "🏆 Obiettivi & Dieta", "🚀 Dashboard & Chat"])

# TAB 1: PROFILO
with t1:
    st.header("Profilo Biologico")
    c1, c2 = st.columns(2)
    with c1:
        u_disc = st.radio("Specialità", ["Strada", "MTB"], horizontal=True, 
                          index=0 if st.session_state.user_data["disc"] == "Strada" else 1)
        u_eta = st.number_input("Età", 14, 90, st.session_state.user_data["eta"])
        u_peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data["peso"])
        u_alt = st.number_input("Altezza (cm)", 100, 220, st.session_state.user_data["altezza"])
    with c2:
        u_med = st.text_area("Note Mediche / Patologie", st.session_state.user_data["med"])
        uploaded_docs = st.file_uploader("Carica Analisi (Foto/PDF)", type=["jpg", "png", "pdf"], accept_multiple_files=True)
    
    if st.button("💾 Salva Profilo"):
        st.session_state.user_data.update({"disc": u_disc, "eta": u_eta, "peso": u_peso, "altezza": u_alt, "med": u_med})
        st.success("Profilo salvato!")

# TAB 2: OBIETTIVI E DIETA (Riorganizzata come image_617c9f.png)
with t2:
    st.header("Obiettivi e Dieta")
    c3, c4 = st.columns(2)
    with c3:
        u_goal = st.text_input("Specifica obiettivo", st.session_state.user_data["goal"])
        # Fix errore image_814c0a.png: i nomi devono coincidere esattamente
        opzioni_giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        u_giorni = st.multiselect("Giorni disponibili", opzioni_giorni, default=st.session_state.user_data["giorni"])
    with c4:
        u_no_food = st.text_area("Alimenti proibiti o non amati", st.session_state.user_data["no_food"], placeholder="Es: Lattosio, Carne rossa...")
    
    if st.button("💾 Salva Obiettivi"):
        st.session_state.user_data.update({"goal": u_goal, "giorni": u_giorni, "no_food": u_no_food})
        st.success("Obiettivi aggiornati!")

# TAB 3: DASHBOARD (CHAT + STRAVA)
with t3:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            if not st.session_state.gemini_key:
                st.error("Inserisci la Gemini API Key nella sidebar!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                try:
                    # Fix image_81c7ca.png usando transport='rest'
                    genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    u = st.session_state.user_data
                    context = f"Atleta {u['disc']}, Goal: {u['goal']}. No food: {u['no_food']}. Med: {u['med']}."
                    
                    st.session_state.debug_log += f"Chat Prompt: {prompt}\n"
                    
                    with st.chat_message("assistant"):
                        res = model.generate_content([context, prompt])
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e:
                    st.error(f"Errore AI: {e}")

    with col_strava:
        st.subheader("📊 Analisi Rapida Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Ultima uscita: {act.name}")
                    d_km = float(act.distance) / 1000
                    st.metric("Distanza", f"{d_km:.2f} km")
                    
                    if st.button("✨ Analizza Recupero"):
                        if not st.session_state.gemini_key:
                            st.error("Manca la chiave API!")
                        else:
                            try:
                                genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                u = st.session_state.user_data
                                prompt_s = f"Giro di {d_km:.2f}km. Peso {u['peso']}kg. Analizza Proprietà e Recupero (No {u['no_food']})."
                                
                                # Integrazione file caricati (Punto 3 della tua analisi)
                                content_list = [prompt_s]
                                if uploaded_docs:
                                    for doc in uploaded_docs:
                                        if doc.type.startswith("image"):
                                            content_list.append(Image.open(doc))
                                
                                with st.spinner("Analisi in corso..."):
                                    r = model.generate_content(content_list)
                                    st.write(r.text)
                            except Exception as e:
                                st.error(f"Errore Analisi: {e}")
            except Exception as e:
                st.error(f"Errore Strava: {e}")
        else:
            st.warning("Connetti Strava")

    # LOG TECNICO (Per monitorare i flussi dati)
    st.divider()
    with st.expander("🛠️ Log Tecnico (Debug)"):
        st.text_area("Flusso dati", st.session_state.debug_log, height=150)
