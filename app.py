import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- 1. CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v4.7", page_icon="🚴‍♂️", layout="wide")

# --- 2. INIZIALIZZAZIONE TOTALE (Il segreto per non avere KeyError) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "gemini_key" not in st.session_state: st.session_state.gemini_key = ""
if "user_data" not in st.session_state:
    # Inizializziamo ogni singola chiave che useremo
    st.session_state.user_data = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "Nessuno", "med": "Nessuna", "goal": "Obiettivo generico", 
        "giorni": ["Sab", "Dom"]
    }

# --- 3. LOGICA STRAVA (Semplificata) ---
client = Client()
code = st.query_params.get("code")
if code and not st.session_state.strava_token:
    try:
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
    except: pass

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    k = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_key)
    if k: st.session_state.gemini_key = k.strip()
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else: st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFACCIA A TAB ---
t1, t2, t3 = st.tabs(["👤 Profilo", "🏁 Obiettivi", "🚀 Dashboard & Chat"])

with t1:
    st.header("Profilo Biologico")
    c1, c2 = st.columns(2)
    with c1:
        # Aggiornano direttamente lo state senza bisogno di tasti "Salva" complicati
        st.session_state.user_data["disc"] = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        st.session_state.user_data["eta"] = st.number_input("Età", 14, 90, st.session_state.user_data["eta"])
        st.session_state.user_data["peso"] = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data["peso"])
    with c2:
        st.session_state.user_data["med"] = st.text_area("Note Mediche", st.session_state.user_data["med"])
        up_file = st.file_uploader("Carica Analisi (Immagine)", type=["jpg", "png", "jpeg"])

with t2:
    st.header("Obiettivi e Dieta")
    st.session_state.user_data["goal"] = st.text_input("Obiettivo", st.session_state.user_data["goal"])
    st.session_state.user_data["no_food"] = st.text_area("Cibi no", st.session_state.user_data["no_food"])
    st.session_state.user_data["giorni"] = st.multiselect("Giorni", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], default=st.session_state.user_data["giorni"])

with t3:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi..."):
            if not st.session_state.gemini_key: st.error("Manca chiave API!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                try:
                    genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    u = st.session_state.user_data
                    ctx = f"Atleta {u['disc']}, Peso {u['peso']}kg, Goal: {u['goal']}, No food: {u['no_food']}. Sii un coach esperto."
                    with st.chat_message("assistant"):
                        res = model.generate_content([ctx, prompt])
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e: st.error(f"Errore IA: {e}")

    with col_strava:
        st.subheader("📊 Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Giro: {act.name}")
                    d_km = float(act.distance) / 1000
                    st.metric("Distanza", f"{d_km:.2f} km")
                    if st.button("✨ Analizza"):
                        if not st.session_state.gemini_key: st.error("Manca chiave API!")
                        else:
                            genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            u = st.session_state.user_data
                            p = f"Analizza giro di {d_km:.2f}km per atleta {u['peso']}kg. Recupero (no {u['no_food']})."
                            with st.spinner("Analisi..."):
                                c = [p]
                                if up_file: c.append(Image.open(up_file))
                                r = model.generate_content(c)
                                st.write(r.text)
            except: st.error("Errore caricamento attività.")
        else: st.warning("Connetti Strava")
