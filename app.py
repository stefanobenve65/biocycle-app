import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE (Identica alla 3.1) ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v3.9", page_icon="🚴‍♂️", layout="wide")

# --- MEMORIA DI SESSIONE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_profile" not in st.session_state: st.session_state.user_profile = {}
if "strava_token" not in st.session_state: st.session_state.strava_token = None

# --- LOGICA STRAVA (Identica alla 3.1) ---
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
    else: st.success("🟢 Strava Sincronizzato")

# --- INTERFACCIA A 3 TAB (Nuova Organizzazione) ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
t1, t2, t3 = st.tabs(["👤 Profilo Utente", "🏁 Obiettivi & Prestazioni", "🚀 Dashboard & Chat"])

# --- TAB 1: PROFILO & SALUTE ---
with t1:
    st.header("Il Tuo Profilo")
    col1, col2 = st.columns(2)
    with col1:
        disciplina = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        eta = st.number_input("Età", 14, 90, 40)
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 75.0)
        altezza = st.number_input("Altezza (cm)", 100, 220, 175)
    with col2:
        alimenti_no = st.text_area("Cibi proibiti o non amati", placeholder="Es: Lattosio, peperoni...")
        patologie = st.text_area("Note Mediche")
        uploaded_docs = st.file_uploader("Carica Analisi (Foto/PDF)", type=["jpg", "png", "pdf"], accept_multiple_files=True)

    # Aggiorniamo il profilo in memoria
    st.session_state.user_profile = {
        "disciplina": disciplina, "eta": eta, "peso": peso, "altezza": altezza,
        "no_food": alimenti_no, "med": patologie
    }

# --- TAB 2: OBIETTIVI ---
with t2:
    st.header("Obiettivi & Prestazioni")
    obj_dettaglio = st.text_area("Cosa vuoi raggiungere?", placeholder="Es: Scalata del Mount Ventoux")
    giorni_all = st.multiselect("Giorni per allenamento", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], ["Sab", "Dom"])
    st.session_state.user_profile.update({"goal_detail": obj_dettaglio, "giorni": giorni_all})

# --- TAB 3: DASHBOARD (CHAT + STRAVA AFFIANCATI) ---
with t3:
    c_chat, c_data = st.columns([1.5, 1])
    
    with c_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if chat_input := st.chat_input("Chiedi al coach..."):
            st.session_state.messages.append({"role": "user", "content": chat_input})
            with st.chat_message("user"): st.markdown(chat_input)
            if st.session_state.api_key_input:
                genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                model = genai.GenerativeModel("gemini-1.5-flash")
                u = st.session_state.user_profile
                context = f"Atleta {u['disciplina']}, {u['eta']} anni. Obiettivo: {u['goal_detail']}. No food: {u['no_food']}."
                with st.chat_message("assistant"):
                    res = model.generate_content([context, chat_input])
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})

    with c_data:
        st.subheader("📊 Analisi Strava")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Ultima uscita: {act.name}")
                    dist = act.distance / 1000
                    st.metric("Distanza", f"{dist:.2f} km")
                    
                    if st.button("✨ Analizza Giro"):
                        genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        u = st.session_state.user_profile
                        prompt = f"Giro di {dist:.1f}km. Atleta {u['peso']}kg. A) Capacità allenata B) Recupero (no {u['no_food']})."
                        with st.spinner("Analisi..."):
                            res = model.generate_content(prompt)
                            st.write(res.text)
            except: st.warning("Connetti Strava.")
