import streamlit as st
import google.generativeai as genai
from stravalib.client import Client
from PIL import Image

# --- CONFIGURAZIONE ---
CLIENT_ID = '196357'
CLIENT_SECRET = '25a52cfbe7ddd6de7964e341aae473c643ff26c3'
REDIRECT_URI = 'https://biocycle-app-fm8xahzxwrfjstshjcgw6v.streamlit.app/'
GEMINI_MODEL = "gemini-1.5-flash-latest"  # ← AGGIUNTO

st.set_page_config(page_title="BioCycle AI v4.2", page_icon="🚴‍♂️", layout="wide")

# ... resto dell'inizializzazione uguale ...

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
                    model = genai.GenerativeModel(GEMINI_MODEL)  # ← CORRETTO
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
                                model = genai.GenerativeModel(GEMINI_MODEL)  # ← CORRETTO
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
            st.warning("Connetti Strava")
