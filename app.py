import streamlit as st
import google.generativeai as genai

# 1. Configurazione Pagina
st.set_page_config(page_title="BioCycle AI Prototype", layout="centered")
st.title("🚴‍♂️ BioCycle AI - VERSIONE 2.1")
st.subheader("Nutrizione e Allenamento basati sui tuoi dati")

# 2. Sezione Chiavi API nella barra laterale
with st.sidebar:
    st.header("Configurazione")
    gemini_key = st.text_input("Inserisci la tua Gemini API Key", type="password")
    st.info("Le chiavi non vengono salvate, servono solo per questa sessione.")

# 3. Input Dati Utente
st.divider()
st.header("1. Dati Biologici")
blood_test_text = st.text_area("Incolla qui le analisi del sangue e i tuoi dati (età, peso, sesso).")

st.header("2. Dati Strava")
st.info("In questa fase di test, incolla i dati principali dell'ultima corsa.")
workout_data = st.text_input("Esempio: 50km, 800m dislivello, 145 bpm medi, 1200 kcal")

# 4. Logica di Elaborazione
if st.button("Genera Report Bio-Sportivo"):
    if not gemini_key:
        st.error("Per favore, inserisci la Gemini API Key nella barra laterale.")
    elif not blood_test_text or not workout_data:
        st.warning("Assicurati di aver inserito sia i dati del sangue che dell'allenamento.")
    else:
        try:
            # Configurazione API con pulizia spazi
            genai.configure(api_key=gemini_key.strip())
            
            # Utilizziamo il modello Flash 1.5 (più moderno e performante)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            Agisci come un esperto nutrizionista sportivo e coach di ciclismo.
            Analizza questi dati:
            ANALISI DEL SANGUE E DATI UTENTE: {blood_test_text}
            ULTIMO ALLENAMENTO: {workout_data}
            
            Fornisci un report diviso in:
            1. Commento tecnico sulla relazione sforzo/parametri ematici.
            2. Consiglio pratico nutrizionale per le prossime 24 ore.
            3. Nota motivazionale per il ciclista.
            """
            
            with st.spinner("Analisi in corso (Protocollo v1 Stabile)..."):
                # FORZIAMO la versione v1 dell'API per bypassare l'errore 404 v1beta
                response = model.generate_content(
                    prompt,
                    request_options={"api_version": "v1"}
                )
                st.success("✅ Analisi Completata")
                st.markdown(response.text)
                
        except Exception as e:
            # Se l'errore persiste, mostriamo esattamente cosa dice il server
            st.error(f"Si è verificato un errore tecnico: {e}")

st.divider()
st.caption("Prototipo BioCycle 2026 - Versione Stabile")
