import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v3.1", page_icon="🚴‍♂️", layout="wide")

# --- MEMORIA DI SESSIONE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_profile" not in st.session_state: st.session_state.user_profile = {}
if "strava_token" not in st.session_state: st.session_state.strava_token = None

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            code=st.query_params["code"]
        )
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
    except:
        pass

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    gemini_key = st.text_input("Inserisci Gemini API Key", type="password", key="api_key_input")
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Sincronizzato")

# --- INTERFACCIA PRINCIPALE ---
st.title("🚴‍♂️ BioCycle AI: Road & MTB Specialist")

t1, t2, t3 = st.tabs(["👤 Profilo & Obiettivi", "🩺 Info Mediche", "🏁 Dashboard & Chat"])

# --- TAB 1: PROFILO ---
with t1:
    st.header("Profilo Biomeccanico")
    c1, c2, c3 = st.columns(3)
    with c1:
        disciplina = st.radio("Specialità prevalente", ["Strada", "MTB"], horizontal=True)
        eta = st.number_input("Età", 14, 90, 40)
    with c2:
        peso = st.number_input("Peso attuale (kg)", 40.0, 150.0, 75.0)
        altezza = st.number_input("Altezza (cm)", 100, 220, 175)
    with c3:
        giorni_all = st.multiselect("Giorni per allenamento", 
                                    ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], 
                                    ["Sab", "Dom"])
    
    st.divider()
    st.header("Obiettivi e Dieta")
    c4, c5 = st.columns(2)
    with c4:
        tipo_obj = st.selectbox("Tipo Obiettivo", ["Salute & Forma", "Evento Sportivo", "Custom"])
        obj_dettaglio = st.text_input("Specifica obiettivo", placeholder="Es: Maratona delle Dolomiti")
    with c5:
        alimenti_no = st.text_area("Alimenti proibiti o non amati", placeholder="Es: Lattosio, Carne rossa...")

    st.session_state.user_profile = {
        "disciplina": disciplina, "eta": eta, "peso": peso, "altezza": altezza,
        "giorni": giorni_all, "goal_type": tipo_obj, "goal_detail": obj_dettaglio, "no_food": alimenti_no
    }

# --- TAB 2: INFO MEDICHE ---
with t2:
    st.header("Documentazione Medica")
    patologie_testo = st.text_area("Descrivi patologie o info mediche")
    uploaded_docs = st.file_uploader("Carica foto o PDF analisi", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

# --- TAB 3: DASHBOARD & CHAT ---
with t3:
    st.header("Analisi Post-Giro & Assistente")
    
    if st.session_state.strava_token:
        client.access_token = st.session_state.strava_token
        try:
            activities = client.get_activities(limit=1)
            for act in activities:
                st.subheader(f"🏁 Ultima uscita: {act.name}")
                dist = act.distance / 1000
                elev = act.total_elevation_gain
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Distanza", f"{dist:.1f} km")
                m2.metric("Dislivello", f"{elev} m")
                m3.metric("Tempo", str(act.moving_time))
                
                if st.button("✨ Genera Report Punti A e B"):
                    if not st.session_state.api_key_input:
                        st.error("Inserisci la chiave API!")
                    else:
                        genai.configure(api_key=st.session_state.api_key_input, transport='rest')
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        p = st.session_state.user_profile
                        prompt_auto = f"""
                        Analisi per ciclista {p['disciplina']}. 
                        Peso: {p['peso']}kg, Altezza: {p['altezza']}cm.
                        Giro: {dist:.1f}km, {elev}m d+.
                        OBIETTIVO: {p['goal_detail']}.
                        NO FOOD: {p['no_food']}.
                        
                        PUNTO A: Capacità allenata.
                        PUNTO B: Recupero nutrizionale (dosi e tempi).
                        """
                        with st.spinner("Analisi in corso..."):
                            input_ai = [prompt_auto]
                            if uploaded_docs:
                                for doc in uploaded_docs:
                                    if doc.type.startswith("image"): input_ai.append(Image.open(doc))
                            res = model.generate_content(input_ai)
                            st.markdown("---")
                            st.markdown(res.text)
        except:
            st.warning("Connetti Strava per l'analisi.")

    st.divider()
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if chat_input := st.chat_input("Chiedimi consigli..."):
        st.session_state.messages.append({"role": "user", "content": chat_input})
        with st.chat_message("user"): st.markdown(chat_input)
        
        if st.session_state.api_key_input:
            genai.configure(api_key=st.session_state.api_key_input, transport='rest')
            model = genai.GenerativeModel("gemini-2.5-flash")
            with st.chat_message("assistant"):
                response = model.generate_content([str(st.session_state.user_profile), chat_input])
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
