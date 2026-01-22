import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image
import json
import os

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v4.1", page_icon="🚴‍♂️", layout="wide")

# --- MEMORIA DATI ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "", "med": "", "goal": "", "giorni": ["Sab", "Dom"]
    }
if "debug_log" not in st.session_state: st.session_state.debug_log = ""

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state.strava_token = token_response['access_token']
    except Exception as e:
        st.error(f"Errore Strava: {e}")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    input_key = st.text_input("Gemini API Key", type="password")
    if input_key:
        st.session_state.gemini_key = input_key.strip()
    
    st.divider()
    if "strava_token" not in st.session_state or not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat & Log"):
        st.session_state.messages = []
        st.session_state.debug_log = ""
        st.rerun()

# --- INTERFACCIA ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
t1, t2, t3 = st.tabs(["👤 Profilo", "🏆 Obiettivi", "🚀 Dashboard & Chat"])

# TAB 1: PROFILO
with t1:
    st.header("Il Tuo Profilo")
    c1, c2 = st.columns(2)
    with c1:
        u_disc = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        u_eta = st.number_input("Età", 14, 90, st.session_state.user_data["eta"])
        u_peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data["peso"])
        u_alt = st.number_input("Altezza (cm)", 100, 220, st.session_state.user_data["altezza"])
    with c2:
        u_no_food = st.text_area("Cibi proibiti (es: Lattosio, peperoni...)", st.session_state.user_data["no_food"])
        u_med = st.text_area("Note Mediche / Patologie", st.session_state.user_data["med"])
        uploaded_docs = st.file_uploader("Carica Analisi (Foto/PDF)", type=["jpg", "png", "pdf"], accept_multiple_files=True)
    
    if st.button("💾 Salva Profilo"):
        st.session_state.user_data.update({"disc": u_disc, "eta": u_eta, "peso": u_peso, "altezza": u_alt, "no_food": u_no_food, "med": u_med})
        st.success("Profilo salvato in sessione!")

# TAB 2: OBIETTIVI
with t2:
    st.header("Obiettivi & Prestazioni")
    u_goal = st.text_area("Specifica il tuo obiettivo", st.session_state.user_data["goal"], placeholder="Es: Scalata dello Stelvio o Granfondo")
    u_giorni = st.multiselect("Giorni disponibili", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], default=st.session_state.user_data["giorni"])
    if st.button("💾 Salva Obiettivi"):
        st.session_state.user_data.update({"goal": u_goal, "giorni": u_giorni})
        st.success("Obiettivi aggiornati!")

# TAB 3: DASHBOARD
with t3:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            if not st.session_state.get("gemini_key"):
                st.error("Inserisci la chiave API nella sidebar!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                try:
                    genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    u = st.session_state.user_data
                    ctx = f"Atleta {u['disc']}, {u['eta']} anni. Goal: {u['goal']}. No food: {u['no_food']}. Med: {u['med']}."
                    
                    # LOGGING
                    st.session_state.debug_log += f"\n--- CHAT PROMPT ---\nContesto: {ctx}\nMessaggio: {prompt}\n"
                    
                    with st.chat_message("assistant"):
                        res = model.generate_content([ctx, prompt])
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e: st.error(f"Errore AI: {e}")

    with col_strava:
        st.subheader("📊 Analisi Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Ultima uscita: {act.name}")
                    d_km = float(act.distance) / 1000
                    st.metric("Distanza", f"{d_km:.2f} km")
                    
                    if st.button("✨ Analizza Giro"):
                        if not st.session_state.get("gemini_key"):
                            st.error("Manca la chiave API!")
                        else:
                            try:
                                genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                u = st.session_state.user_data
                                p_strava = f"Analizza giro di {d_km:.2f}km per atleta {u['peso']}kg. A) Capacità allenata. B) Recupero (no {u['no_food']})."
                                
                                content_list = [p_strava]
                                if uploaded_docs:
                                    for doc in uploaded_docs:
                                        if doc.type.startswith("image"):
                                            content_list.append(Image.open(doc))
                                
                                st.session_state.debug_log += f"\n--- STRAVA ANALYSIS ---\nPrompt: {p_strava}\nFiles caricati: {len(uploaded_docs) if uploaded_docs else 0}\n"
                                
                                with st.spinner("Analisi in corso..."):
                                    r = model.generate_content(content_list)
                                    st.write(r.text)
                            except Exception as e: st.error(f"Errore IA: {e}")
            except Exception as e: st.error(f"Errore Strava: {e}")
        else: st.warning("Connetti Strava")

    # --- SEZIONE LOG TECNICO (Nascosta) ---
    st.divider()
    with st.expander("🛠️ Log Tecnico (Debug)"):
        st.text_area("Cronologia chiamate all'IA", st.session_state.debug_log, height=200)
