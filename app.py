import streamlit as st
import google.generativeai as genai

# 1. Configurazione della Pagina
st.set_page_config(
    page_title="BioCycle AI - Sport Nutrition",
    page_icon="🚴‍♂️",
    layout="centered"
)

st.title("🚴‍♂️ BioCycle AI - VERSIONE 2.5")
st.subheader("Analisi Nutrizionale Avanzata per Ciclisti")

# 2. Sidebar per Configurazione API
with st.sidebar:
    st.header("Impostazioni")
    gemini_key = st.text_input("Inserisci la tua Gemini API Key", type="password")
    st.info("La chiave viene usata solo per questa sessione e non viene salvata.")
    
    st.divider()
    st.caption("Prototipo BioCycle 2026 - US Market")

# 3. Sezione Input Dati
st.header("1. Analisi del Sangue e Dati Utente")
blood_test_text = st.text_area(
    "Incolla qui i risultati delle analisi (es. Ferritina, Emoglobina) e i tuoi dati (Età, Peso, Sesso).",
    height=150,
    placeholder="Esempio: Uomo, 45 anni, 76kg. Ferritina 35 ng/ml, Magnesio 1.8..."
)

st.header("2. Dati Strava / Allenamento")
workout_data = st.text_input(
    "Dati dell'ultima attività:",
    placeholder="Esempio: 62 km, 850m dislivello, 2h 30m, 140 bpm medi."
)

# 4. Elaborazione del Report
if st.button("Genera Report Bio-Sportivo"):
    if not gemini_key:
        st.error("⚠️ Errore: Inserisci la API Key nella barra laterale per procedere.")
    elif not blood_test_text or not workout_data:
        st.warning("⚠️ Attenzione: Assicurati di aver inserito sia i dati biologici che quelli di allenamento.")
    else:
        try:
            # Configurazione API con trasporto REST (stabile per v1)
            genai.configure(
                api_key=gemini_key.strip(),
                transport='rest'
            )
            
            # Utilizzo del modello confermato dal test diagnostico
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # Prompt ottimizzato per il mercato Americano e precisione tecnica
            prompt = f"""
            Agisci come un esperto nutrizionista sportivo e coach di ciclismo d'élite.
            Analizza i seguenti dati per fornire un piano d'azione immediato.
            
            DATI BIOLOGICI:
            {blood_test_text}
            
            DATI ALLENAMENTO:
            {workout_data}
            
            Fornisci un report strutturato in questo modo:
            1. ANALISI TECNICA: Relazione tra lo sforzo fisico e i parametri ematici forniti.
            2. REINTEGRO 24H: Cosa mangiare e quali micronutrienti prioritizzare nelle prossime 24 ore.
            3. CONSIGLIO COACH: Nota motivazionale e tecnica per il prossimo obiettivo.
            
            Usa un tono professionale, empatico e basato sui dati.
            """
            
            with st.spinner("L'AI sta elaborando i tuoi dati con Gemini 2.5 Flash..."):
                response = model.generate_content(prompt)
                
                # Visualizzazione Risultato
                st.success("✅ Report Generato con Successo")
                st.markdown("---")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"❌ Si è verificato un errore tecnico: {e}")
            st.info("Suggerimento: Verifica che la tua API Key sia attiva e di avere una connessione stabile.")

# 5. Footer
st.divider()
st.caption("© 2026 BioCycle AI Prototype | Sviluppato per atleti di resistenza.")
