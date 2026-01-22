import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- 1. CONFIGURAZIONE FISSA ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v5.0", page_icon="🚴‍♂️", layout="wide")

# --- 2. INIZIALIZZAZIONE SICURA (Niente più KeyError) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "gemini_key" not in st.session_state: st.session_state.gemini_key = ""
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "Nessuno", "med": "Nessuna", "goal": "Obiettivo generico", 
        "giorni": ["Sab", "Dom"]
    }

# --- 3. MOTORE OAUTH STRAVA (Con Pulizia Automatica) ---
client = Client()
# Recuperiamo il codice solo se presente nella URL
query_params = st.query_params
if "code" in query_params and st.session_state.strava_token is None:
    try:
        code = query_params["code"]
        token_response = client.exchange_code_for_token(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code
        )
        st.session_state.strava_token = token_response['access_token']
        # Puliamo la URL per evitare che il codice venga riutilizzato
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Errore Scambio Token: {e}")

# --- 4. SIDEBAR CONFIGURAZIONE ---
with st.sidebar:
    st.header("⚙️ Setup")
    api_key_input = st.text_input("Inserisci Gemini API Key", type="password", value=st.session_state.gemini_key)
    if api_key_input:
        st.session_state.gemini_key = api_key_input.strip()
    
    st.divider()
    if not st.session_state.strava_token:
        # Chiediamo permessi totali 'read_all' e 'activity:read_all'
        url = client.authorization_url(
            client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, 
            scope=['read_all', 'activity:read_all']
        )
        st.link_button("🔗 Collega il tuo Strava", url)
    else:
        st.success("🟢 Connesso a Strava")
    
    if st.button("🗑️ Reset Totale App"):
        st.session_state.clear()
        st.rerun()

# --- 5. INTERFACCIA A 3 TAB ---
t_profilo, t_obiettivi, t_dashboard = st.tabs(["👤 Profilo", "🏁 Obiettivi", "🚀 Coach & Analisi"])

with t_profilo:
    st.header("Dati Biometrici & Medici")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.user_profile["disc"] = st.radio("Specialità", ["Strada", "MTB"], horizontal=True)
        st.session_state.user_profile["eta"] = st.number_input("Età", 14, 90, st.session_state.user_profile["eta"])
        st.session_state.user_profile["peso"] = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data.get("peso", 75.0) if hasattr(st.session_state, 'user_data') else 75.0)
    with col2:
        st.session_state.user_profile["med"] = st.text_area("Patologie o Info Mediche", st.session_state.user_profile["med"])
        file_analisi = st.file_uploader("Allega Analisi (Immagini)", type=["jpg", "png", "jpeg"])

with t_obiettivi:
    st.header("Traguardi & Nutrizione")
    st.session_state.user_profile["goal"] = st.text_input("Qual è il tuo obiettivo?", st.session_state.user_profile["goal"])
    st.session_state.user_profile["no_food"] = st.text_area("Cibi da evitare", st.session_state.user_profile["no_food"])
    st.session_state.user_profile["giorni"] = st.multiselect("Giorni disponibili", ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], default=st.session_state.user_profile["giorni"])

with t_dashboard:
    c_chat, c_strava = st.columns([1.5, 1])
    
    with c_chat:
        st.subheader("💬 Parla con il tuo Coach")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi un consiglio..."):
            if not st.session_state.gemini_key:
                st.error("Inserisci la chiave API nella barra laterale.")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                try:
                    genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    u = st.session_state.user_profile
                    # Contesto per il coach
                    context = f"Sei un coach di ciclismo. Atleta {u['disc']}, Goal: {u['goal']}, No food: {u['no_food']}. Sii professionale e sincero."
                    with st.chat_message("assistant"):
                        response = model.generate_content([context, prompt])
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
                    
                    if st.button("✨ Analizza questo Giro"):
                        if not st.session_state.gemini_key:
                            st.error("Manca la chiave API!")
                        else:
                            try:
                                genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                u = st.session_state.user_profile
                                input_ia = [f"Analizza questo giro di {dist_km:.2f}km. Peso atleta: {u['peso']}kg. A) Quali proprietà sono state allenate? B) Cosa mangiare per il recupero (evitando {u['no_food']})?"]
                                if file_analisi:
                                    input_ia.append(Image.open(file_analisi))
                                
                                with st.spinner("Analisi in corso..."):
                                    res = model.generate_content(input_ia)
                                    st.write(res.text)
                            except Exception as ai_err:
                                st.error(f"Errore durante l'analisi: {ai_err}")
            except Exception as st_err:
                st.error(f"Errore Strava: {st_err}. Prova a ricollegare l'account.")
        else:
            st.warning("Collega Strava dalla sidebar per vedere i tuoi dati.")
            
