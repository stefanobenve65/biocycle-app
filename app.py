import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- 1. CONFIGURAZIONE CORE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'

st.set_page_config(page_title="BioCycle AI v4.4", page_icon="🚴‍♂️", layout="wide")

# --- 2. INIZIALIZZAZIONE SESSIONE (Fix AttributeError & KeyError) ---
# Inizializziamo subito per evitare l'errore visto in image_80c44f.png
if "messages" not in st.session_state: st.session_state.messages = []
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "gemini_key" not in st.session_state: st.session_state.gemini_key = ""
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "disc": "Strada", "eta": 40, "peso": 75.0, "altezza": 175,
        "no_food": "", "med": "", "goal": "", 
        "giorni": ["Sab", "Dom"] # Fix image_814c0a.png: nomi allineati
    }

# --- 3. LOGICA STRAVA ---
client = Client()
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        st.session_state.strava_token = token_response['access_token']
    except Exception as e:
        st.sidebar.error(f"Errore Strava: {e}")

# --- 4. SIDEBAR (Configurazione sicura) ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    # Salviamo la chiave direttamente in session_state come da tua analisi
    temp_key = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_key)
    if temp_key:
        st.session_state.gemini_key = temp_key.strip()
    
    st.divider()
    if not st.session_state.strava_token:
        url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['read_all', 'activity:read_all'])
        st.link_button("🔗 Connetti Strava", url)
    else:
        st.success("🟢 Strava Connesso")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFACCIA A TAB ---
st.title("🚴‍♂️ BioCycle AI: Digital Coach")
t1, t2, t3 = st.tabs(["👤 Profilo", "🏁 Obiettivi & Dieta", "🚀 Dashboard & Chat"])

# TAB 1: PROFILO
with t1:
    st.header("Il Tuo Profilo Personale")
    c1, c2 = st.columns(2)
    with c1:
        u_disc = st.radio("Specialità", ["Strada", "MTB"], horizontal=True, 
                          index=0 if st.session_state.user_data["disc"] == "Strada" else 1)
        u_eta = st.number_input("Età", 14, 90, st.session_state.user_data["eta"])
        u_peso = st.number_input("Peso (kg)", 40.0, 150.0, st.session_state.user_data["peso"])
    with c2:
        u_med = st.text_area("Note Mediche / Patologie", st.session_state.user_data["med"])
        uploaded_docs = st.file_uploader("Carica Analisi (Immagini)", type=["jpg", "png", "jpeg"])
    
    if st.button("💾 Salva Profilo"):
        st.session_state.user_data.update({"disc": u_disc, "eta": u_eta, "peso": u_peso, "med": u_med})
        st.success("Profilo salvato in memoria!")

# TAB 2: OBIETTIVI E DIETA (Fix image_617c9f.png)
with t2:
    st.header("Obiettivi e Dieta")
    c3, c4 = st.columns(2)
    with c3:
        u_goal = st.text_input("Specifica obiettivo", st.session_state.user_data["goal"], placeholder="Es: scalata del mount ventoux")
        # Fix image_814c0a.png: i nomi devono coincidere esattamente tra opzioni e default
        opzioni_g = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        u_giorni = st.multiselect("Giorni disponibili", opzioni_g, default=st.session_state.user_data["giorni"])
    with c4:
        u_no_food = st.text_area("Alimenti proibiti", st.session_state.user_data["no_food"], placeholder="Es: Lattosio...")
    
    if st.button("💾 Salva Obiettivi"):
        st.session_state.user_data.update({"goal": u_goal, "giorni": u_giorni, "no_food": u_no_food})
        st.success("Obiettivi fissati!")

# TAB 3: DASHBOARD (Fix Layout e AI)
with t3:
    col_chat, col_strava = st.columns([1.5, 1])
    
    with col_chat:
        st.subheader("💬 Coach Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Chiedi al coach..."):
            if not st.session_state.gemini_key:
                st.error("Inserisci la chiave API nella barra laterale!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                try:
                    # Fix image_81c7ca.png usando transport='rest'
                    genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    u = st.session_state.user_data
                    context = f"Atleta {u['disc']}, Goal: {u['goal']}. No food: {u['no_food']}."
                    with st.chat_message("assistant"):
                        res = model.generate_content([context, prompt])
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e:
                    st.error(f"Errore AI: {e}")

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
                    
                    if st.button("✨ Analizza Recupero"):
                        if not st.session_state.gemini_key:
                            st.error("Manca la chiave API!")
                        else:
                            try:
                                genai.configure(api_key=st.session_state.gemini_key, transport='rest')
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                u = st.session_state.user_data
                                p_strava = f"Giro di {d_km:.2f}km. Peso {u['peso']}kg. Analizza Proprietà e Recupero (No {u['no_food']})."
                                
                                # Processo immagini caricate (Tua correzione)
                                content_list = [p_strava]
                                if uploaded_docs:
                                    content_list.append(Image.open(uploaded_docs))
                                
                                with st.spinner("Analisi in corso..."):
                                    r = model.generate_content(content_list)
                                    st.write(r.text)
                            except Exception as e:
                                st.error(f"Errore IA: {e}")
            except Exception as e:
                st.error(f"Errore caricamento Strava: {e}")
        else:
            st.warning("Connetti Strava nella barra laterale")
