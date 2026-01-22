import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'
GEMINI_MODEL = "gemini-1.5-flash-latest"

st.set_page_config(page_title="BioCycle AI v4.2", page_icon="🚴‍♂️", layout="wide")

# --- INIZIALIZZAZIONE SESSION STATE ---
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "strava_token" not in st.session_state: 
    st.session_state.strava_token = None
if "gemini_key" not in st.session_state: 
    st.session_state.gemini_key = ""
if "debug_log" not in st.session_state: 
    st.session_state.debug_log = ""
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "", "med": "", "goal": "scalata del mount ventoux", 
        "giorni": ["Sab", "Dom"]
    }

# --- LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            code=code
        )
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.session_state.debug_log += f"Errore Strava Auth: {e}\n"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    input_key = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_key)
    if input_key:
        st.session_state.gemini_key = input_key.strip()
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(
            client_id=CLIENT_ID, 
            redirect_uri=REDIRECT_URI, 
            scope=['read_all', 'activity:read_all']
        )
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat & Log"):
        st.session_state.messages = []
        st.session_state.debug_log = ""
        st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")

# ← QUI CREIAMO I TAB (PRIMA DI USARLI)
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
        uploaded_docs = st.file_uploader(
            "Carica Analisi (Foto/PDF)", 
            type=["jpg", "png", "pdf"], 
            accept_multiple_files=True,
            key="uploaded_files"
        )
    
    if st.button("💾 Salva Profilo"):
        st.session_state.user_data.update({
            "disc": u_disc, "eta": u_eta, "peso": u_peso, "altezza": u_alt, "med": u_med
        })
        st.success("Profilo salvato!")

# TAB 2: OBIETTIVI
with t2:
    st.header("Obiettivi e Dieta")
    c3, c4 = st.columns(2)
    with c3:
        u_goal = st.text_input("Specifica obiettivo", st.session_state.user_data["goal"])
        opzioni_giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        default_validi = [g for g in st.session_state.user_data["giorni"] if g in opzioni_giorni]
        u_giorni = st.multiselect("Giorni disponibili", opzioni_giorni, default=default_validi)
    with c4:
        u_no_food = st.text_area("Alimenti proibiti", st.session_state.user_data["no_food"])
    
    if st.button("💾 Salva Obiettivi"):
        st.session_state.user_data.update({"goal": u_goal, "giorni": u_giorni, "no_food": u_no_food})
        st.success("Obiettivi aggiornati!")

# TAB 3: DASHBOARD
with t3:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): 
                st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            if not st.session_state.gemini_key:
                st.error("Inserisci la Gemini API Key nella sidebar!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): 
                    st.markdown(prompt)
                try:
                    genai.configure(api_key=st.session_state.gemini_key)
                    model = genai.GenerativeModel(GEMINI_MODEL)
                    u = st.session_state.user_data
                    context = f"Atleta {u['disc']}, Goal: {u['goal']}. No food: {u['no_food']}. Med: {u['med']}."
                    
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
                                genai.configure(api_key=st.session_state.gemini_key)
                                model = genai.GenerativeModel(GEMINI_MODEL)
                                u = st.session_state.user_data
                                prompt_s = f"Giro di {d_km:.2f}km. Peso {u['peso']}kg. Analizza Recupero (No {u['no_food']})."
                                
                                content_list = [prompt_s]
                                if st.session_state.get("uploaded_files"):
                                    for doc in st.session_state.uploaded_files:
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
            st.warning("Connetti Strava per vedere i dati")

    st.divider()
    with st.expander("🛠️ Log Tecnico"):
        st.text_area("Debug", st.session_state.debug_log, height=150)
