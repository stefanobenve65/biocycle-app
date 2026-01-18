import streamlit as st
import google.generativeai as genai

# 1. Configurazione Pagina
st.set_page_config(page_title="BioCycle AI Prototype", layout="centered")
st.title("🚴‍♂️ BioCycle AI - VERSIONE 2.3 (Debug)")

# 2. Sidebar con Debug
with st.sidebar:
    st.header("Configurazione")
    gemini_key = st.text_input("Inserisci la tua Gemini API Key", type="password")
    
    st.divider()
    st.subheader("🛠 Strumenti di Diagnosi")
    if st.button("Verifica Modelli Disponibili"):
        if not gemini_key:
            st.error("Inserisci prima la chiave!")
        else:
            try:
                genai.configure(api_key=gemini_key.strip())
                st.write("Modelli trovati per la tua Key:")
                models = genai.list_models()
                for m in models:
                    if 'generateContent' in m.supported_generation_methods:
                        st.code(m.name) # Mostra il nome esatto da usare
            except Exception as e:
                st.error(f"Errore durante il test: {e}")

# 3. Input Dati Utente
st.divider()
st.header("1. Dati Biologici")
blood_test_text = st.text_area("Incolla qui le analisi del sangue.")

st.header("2. Dati Strava")
workout_data = st.text_input("Esempio: 50km, 1200 kcal")

# 4. Logica di Elaborazione
if st.button("Genera Report Bio-Sportivo"):
    if not gemini_key:
        st.error("Manca la chiave API.")
    else:
        try:
            genai.configure(api_key=gemini_key.strip(), transport='rest')
            # Qui useremo il nome esatto che uscirà dal test sopra
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"Analizza questi dati: {blood_test_text} {workout_data}"
            
            with st.spinner("Analisi in corso..."):
                response = model.generate_content(prompt)
                st.success("✅ Analisi Completata")
                st.markdown(response.text)
        except Exception as e:
            st.error(f"Errore tecnico: {e}")
