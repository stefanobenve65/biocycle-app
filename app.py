import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE CORE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v5.1", page_icon="🚴‍♂️", layout="wide")

# --- FUNZIONE DI PULIZIA TESTO (Fix Latin-1 Error) ---
def clean_text(text):
    """Converte il testo in UTF-8 puro per evitare errori di encoding"""
    if not text:
        return ""
    return str(text).encode("utf-8", errors="ignore").decode("utf-8")

# --- INIZIALIZZAZIONE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "gemini_key" not in st.session_state: st.session_state.gemini_key = ""
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "Nessuno", "med": "Nessuna", "goal": "Obiettivo generico", 
        "giorni": ["Sab", "Dom"]
    }

# --- LOGICA STRAVA ---
client = Client()
query_params = st.query_params
if "code" in query_params and st.session_state.strava_token is None:
    try:
        code = query_params["code"]
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state.strava_token = token_response['access_token']
        st.query_params.clear()
        st.rerun()
    except:
        st.query_params.clear()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Setup")
    api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_key)
    if api_key_input:
        st.session_state.gemini_key = api_key_input.strip()
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Collega Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Totale App"):
        st.session_state.clear()
        st.rerun()

# --- INTERFACCIA A TAB ---
t_profilo, t_obiettivi, t_dashboard = st.tabs(["👤 Profilo", "🏁 Obiettivi", "🚀 Coach & Analisi"])

with t_profilo:
    st.header("Dati Biometrici")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.user_profile["disc"] = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        st.session_state.user_profile["eta"] = st.number_input("Età", 14, 90, st.session_state.user_profile["eta"])
        st.session_state.user_profile["peso"] = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_profile["peso"])
    with col2:
        st.session_state.user_profile["med"] = st.text_area("Note Mediche", st.session_state.user_profile["med"])
        file_analisi = st.file_uploader("Analisi (JPG/PNG)", type=["jpg", "png", "jpeg"])

with t_obiettivi:
    st.header("Traguardi")
    st.session_state.user_profile["goal"] = st.text_input("Obiettivo", st.session_state.user_profile["goal"])
    st.session_state.user_profile["no_food"] = st.text_area("Cibi da evitare", st.session_state.user_profile["no_food"])
    st.session_state.user_profile["giorni"] = st.multiselect("Giorni", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], default=st.session_state.user_profile["giorni"])

with t_dashboard:
    c_chat, c_strava = st.columns([1.5, 1])
    
    with c_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi un consiglio..."):
            if not st.session_state.gemini_key:
                st.error("Inserisci la chiave API.")
            else:
                cleaned_prompt = clean_text(prompt)
                st.session_state.messages.append({"role": "user", "content": cleaned_prompt})
                with st.chat_message("user"): st.markdown(cleaned_prompt)
                try:
                    genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    u = st.session_state.user_profile
                    # Pulizia del contesto
                    context = clean_text(f"Atleta {u['disc']}, Goal: {u['goal']}, No food: {u['no_food']}. Sii un coach sincero.")
                    with st.chat_message("assistant"):
                        response = model.generate_content([context, cleaned_prompt])
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Errore AI: {e}")

    with c_strava:
        st.subheader("📊 Ultima Attività")
        if st.session_state.strava_token:
            client.access_token = st.session_state.strava_token
            try:
                activities = client.get_activities(limit=1)
                for act in activities:
                    st.info(f"Giro: {act.name}")
                    dist_km = float(act.distance) / 1000
                    st.metric("Distanza", f"{dist_km:.2f} km")
                    
                    if st.button("✨ Analizza"):
                        if not st.session_state.gemini_key:
                            st.error("Manca chiave API!")
                        else:
                            try:
                                genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                u = st.session_state.user_profile
                                # Pulizia prompt Strava
                                raw_p = f"Analisi giro {dist_km:.2f}km. Peso {u['peso']}kg. Recupero (no {u['no_food']})."
                                p_strava = clean_text(raw_p)
                                
                                input_ia = [p_strava]
                                if file_analisi:
                                    input_ia.append(Image.open(file_analisi))
                                
                                with st.spinner("Analisi..."):
                                    res = model.generate_content(input_ia)
                                    st.write(res.text)
                            except Exception as ai_err:
                                st.error(f"Errore Analisi: {ai_err}")
            except Exception as st_err:
                st.error(f"Errore caricamento: {st_err}")
        else:
            st.warning("Collega Strava nella sidebar.")
