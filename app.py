import streamlit as st
import google.generativeai as genai

# Configurazione Pagina
st.set_page_config(page_title="BioCycle AI Prototype", layout="centered")
st.title("🚴‍♂️ BioCycle AI Prototype")
st.subheader("Nutrizione e Allenamento basati sui tuoi dati")

# Sezione Chiavi API (Sicurezza)
with st.sidebar:
    st.header("Configurazione")
    gemini_key = st.text_input("Inserisci la tua Gemini API Key", type="password")
    st.info("Le chiavi non vengono salvate, servono solo per questa sessione.")

# 1. Caricamento Dati Biologici
st.divider()
st.header("1. Dati Biologici")
blood_test_text = st.text_area("Incolla qui i risultati delle tue analisi del sangue (es: Ferro, Colesterolo...) e i tuoi dati (età, peso, sesso).")

# 2. Dati Allenamento
st.header("2. Dati Strava")
st.info("In questa fase di test, incolla i dati principali dell'ultima corsa.")
workout_data = st.text_input("Esempio: 50km, 800m dislivello, 145 bpm medi, 1200 kcal")

# 3. Elaborazione AI
if st.button("Genera Report Bio-Sportivo"):
    if not gemini_key:
        st.error("Per favore, inserisci la Gemini API Key nella barra laterale.")
    elif not blood_test_text or not workout_data:
        st.warning("Assicurati di aver inserito sia i dati del sangue che dell'allenamento.")
    else:
        try:
            # Configura Gemini (Uso di .strip() per evitare spazi nella chiave)
            genai.configure(api_key=gemini_key.strip())
           model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
            
            prompt = f"""
            Agisci come un esperto nutrizionista sportivo e coach di ciclismo.
            Analizza questi dati:
            ANALISI DEL SANGUE E DATI UTENTE: {blood_test_text}
            ULTIMO ALLENAMENTO: {workout_data}
            
            Fornisci:
            1. Un commento sulla relazione tra lo sforzo fatto e i parametri ematici.
            2. Un consiglio pratico su cosa mangiare nelle prossime 24 ore per ottimizzare il recupero.
            3. Una nota motivazionale per il prossimo obiettivo.
            """
            
            with st.spinner("L'AI sta analizzando i tuoi dati..."):
                response = model.generate_content(prompt)
                st.success("✅ Analisi Completata")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")

st.divider()
st.caption("Prototipo BioCycle 2026 - Uso Personale")
