from dotenv import load_dotenv
import os
load_dotenv()

import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

from supabase import create_client
supabase_client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

import streamlit as st

from PIL import Image, ImageEnhance
import io

def comprimi_immagine(file, max_size_mb=4):
    img = Image.open(file)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    quality = 85
    while True:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        size_mb = buffer.tell() / (1024 * 1024)
        if size_mb <= max_size_mb or quality < 20:
            buffer.seek(0)
            return buffer
        quality -= 10

def mostra_risposta(testo):
    import re
    testo = re.sub(r'\\\[', '\n$$', testo)
    testo = re.sub(r'\\\]', '$$\n', testo)
    testo = re.sub(r'\\\(', '$', testo)
    testo = re.sub(r'\\\)', '$', testo)
    blocchi = re.split(r'(\$\$[\s\S]*?\$\$)', testo)
    for blocco in blocchi:
        blocco = blocco.strip()
        if not blocco:
            continue
        if blocco.startswith('$$') and blocco.endswith('$$'):
            formula = blocco[2:-2].strip()
            try:
                st.latex(formula)
            except:
                st.code(formula)
        else:
            st.markdown(blocco)

ARGOMENTI = {
    "Matematica": {
        "1°": [
            "Numeri naturali", "Numeri interi", "Numeri razionali e reali",
            "Insiemi e logica", "Relazioni e funzioni", "Monomi e polinomi",
            "Scomposizione in fattori", "Frazioni algebriche", "Equazioni lineari",
            "Disequazioni lineari", "Statistica introduttiva", "Geometria del piano",
            "Triangoli", "Perpendicolari e parallele", "Parallelogrammi e trapezi"
        ],
        "2°": [
            "Sistemi lineari", "Radicali e operazioni", "Piano cartesiano e retta",
            "Equazioni di secondo grado e parabola", "Sistemi di secondo grado",
            "Disequazioni di secondo grado", "Equazioni e disequazioni di grado superiore",
            "Probabilità introduttiva", "Circonferenza e poligoni inscritti/circoscritti",
            "Equivalenza delle superfici piane", "Grandezze proporzionali",
            "Trasformazioni geometriche", "Similitudine"
        ],
        "3°": [
            "Equazioni e disequazioni", "Funzioni", "Successioni e progressioni",
            "Piano cartesiano e retta", "Parabola", "Circonferenza", "Ellisse",
            "Iperbole", "Coniche", "Funzioni goniometriche", "Formule goniometriche",
            "Equazioni goniometriche", "Trigonometria", "Statistica"
        ],
        "4°": [
            "Esponenziali", "Logaritmi", "Numeri complessi", "Vettori, matrici e determinanti",
            "Trasformazioni geometriche", "Geometria euclidea nello spazio",
            "Geometria analitica nello spazio", "Calcolo combinatorio", "Probabilità",
            "Funzioni e successioni", "Limiti", "Calcolo dei limiti e continuità"
        ],
        "5°": [
            "Derivate", "Teoremi sulle derivate", "Massimi, minimi e flessi",
            "Studio di funzioni", "Integrali indefiniti", "Integrali definiti",
            "Equazioni differenziali", "Distribuzioni di probabilità"
        ]
    },
    "Fisica": {
        "1°": [
            "Misura di una grandezza fisica", "Vettori", "Forze e dinamica di Newton",
            "Equilibrio", "Fluidi"
        ],
        "2°": [
            "Moto rettilineo", "Moto in due dimensioni", "Moto rotatorio", "Gravitazione",
            "Lavoro e energia", "Potenza", "Quantità di moto e urti",
            "Temperatura e calore", "Cambiamenti di stato e termodinamica",
            "Luce e onde elettromagnetiche", "Ottica"
        ],
        "3°": [
            "Moto in più dimensioni", "Dinamica e leggi di Newton", "Forze e moto",
            "Lavoro ed energia", "Impulso e quantità di moto", "Moto rotatorio",
            "Equilibrio e momento angolare", "Gravitazione", "Fluidi", "Temperatura e calore"
        ],
        "4°": [
            "Oscillazioni e onde", "Onde sonore", "Ottica geometrica", "Ottica ondulatoria",
            "Campo elettrico", "Potenziale elettrico", "Circuiti elettrici", "Magnetismo"
        ],
        "5°": [
            "Induzione elettromagnetica", "Circuiti in corrente alternata",
            "Onde elettromagnetiche", "Relatività ristretta",
            "Fisica moderna e dualismo onda-corpuscolo", "Modelli atomici",
            "Fisica nucleare e radioattività"
        ]
    }
}

# Password beta
if "accesso" not in st.session_state:
    st.session_state.accesso = False

if not st.session_state.accesso:
    st.title("📚 Tutor AI")
    st.subheader("Versione Beta")
    password = st.text_input("Inserisci il codice di accesso", type="password")
    if st.button("Accedi", type="primary"):
        if password == "liceo2025":
            st.session_state.accesso = True
            st.rerun()
        else:
            st.error("❌ Codice non corretto")
    st.stop()

st.set_page_config(
    page_title="Tutor AI — Liceo Scientifico",
    page_icon="📚",
    layout="centered"
)

# Inizializza session state
if "conversazione" not in st.session_state:
    st.session_state.conversazione = []
if "sessione_attiva" not in st.session_state:
    st.session_state.sessione_attiva = False
if "istruzioni" not in st.session_state:
    st.session_state.istruzioni = ""
if "classe_saved" not in st.session_state:
    st.session_state.classe_saved = "1°"
if "materia_saved" not in st.session_state:
    st.session_state.materia_saved = "Matematica"

st.title("📚 Tutor AI — Liceo Scientifico")
st.subheader("Il tuo assistente personale per matematica e fisica")

with st.expander("ℹ️ Come funziona", expanded=False):
    st.markdown("""
    **Benvenuto nel Tutor AI!** Ecco come usarlo:
    
    1. **Scegli la tua classe e materia**
    2. **Controlla gli argomenti trattati** — sono tutti selezionati, deseleziona quelli che non hai ancora studiato
    3. **Scegli la modalità:**
       - 🎓 **Tutor** — ti guida con domande per arrivare alla soluzione da solo
       - 📖 **Soluzione** — ti mostra la soluzione completa passo per passo
    4. **Inserisci l'esercizio** — scrivi il testo oppure carica una foto
    5. **Clicca Inizia** e chatta con il tutor!
    
    💡 *Il tutor usa solo gli argomenti che hai già studiato — niente formule che non conosci ancora!*
    """)

if not st.session_state.sessione_attiva:

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.classe_saved = st.selectbox(
            "Classe",
            ["1°", "2°", "3°", "4°", "5°"],
            index=["1°", "2°", "3°", "4°", "5°"].index(st.session_state.classe_saved)
        )
        classe = st.session_state.classe_saved
    with col2:
        st.session_state.materia_saved = st.selectbox(
            "Materia",
            ["Matematica", "Fisica"],
            index=["Matematica", "Fisica"].index(st.session_state.materia_saved)
        )
        materia = st.session_state.materia_saved

    st.divider()

    classi_ordine = ["1°", "2°", "3°", "4°", "5°"]
    indice_classe = classi_ordine.index(classe)
    classi_disponibili = classi_ordine[:indice_classe + 1]

    st.subheader("📋 Argomenti trattati")
    st.caption("Tutti gli argomenti sono selezionati. Deseleziona quelli che non hai ancora studiato.")

    argomenti_selezionati = []
    for c in classi_disponibili:
        with st.expander(f"📖 Anno {c}", expanded=(c == classe)):
            for argomento in ARGOMENTI[materia][c]:
                key = f"chk_{c}_{argomento}"
                saved_key = f"saved_{key}"
                if key not in st.session_state:
                    st.session_state[key] = st.session_state.get(saved_key, True)
                if st.checkbox(argomento, key=key):
                    argomenti_selezionati.append(argomento)

    st.divider()
    st.success(f"✅ {len(argomenti_selezionati)} argomenti selezionati")

    st.divider()
    st.subheader("🎯 Come vuoi essere aiutato?")
    modalita = st.radio(
        "Scegli la modalità",
        options=["🎓 Tutor", "📖 Soluzione"],
        captions=[
            "Ti guido con domande fino alla soluzione",
            "Soluzione completa spiegata passo per passo",
        ]
    )

    st.divider()
    st.subheader("📝 Inserisci l'esercizio")

    testo_esercizio = st.text_area(
        "Scrivi o incolla l'esercizio",
        placeholder="Es. Risolvi l'equazione x² + 5x + 6 = 0",
        height=120
    )
    tab1, tab2 = st.tabs(["📁 Carica file", "📷 Scatta foto"])
    with tab1:
        foto_esercizio = st.file_uploader("Carica una foto dell'esercizio", type=["jpg", "jpeg", "png"], key="upload_esercizio")
        st.caption("📸 Consiglio: fotografa con buona luce, foglio piatto e inquadra bene il testo")
    with tab2:
        camera_esercizio = st.camera_input("Scatta una foto dell'esercizio", key="camera_esercizio")

    if st.button("🚀 Inizia", type="primary", use_container_width=True):

        immagine = None
        if foto_esercizio:
            immagine = foto_esercizio
        elif camera_esercizio:
            immagine = camera_esercizio

        if not testo_esercizio and not immagine:
            st.warning("⚠️ Scrivi un esercizio o carica una foto prima di continuare!")
        else:
            argomenti_testo = ", ".join(argomenti_selezionati)

            regole_latex = (
                "- Scrivi SEMPRE le formule inline tra $ e $\n"
                "- Scrivi SEMPRE le formule su riga separata tra $$ e $$\n"
                "- Inizia SEMPRE con $$ su una riga nuova e chiudi con $$ su una riga nuova\n"
                "- Per funzioni a tratti usa sempre $$ all'inizio e $$ alla fine\n"
                "- Non scrivere mai formule senza delimitatori\n"
                "- Quando ricevi un'immagine, valuta la complessità della notazione:\n"
                "  se semplice e chiara procedi direttamente\n"
                "  se complessa o ambigua trascrivi prima e chiedi conferma\n"
                "- Le funzioni definite a tratti sono SEMPRE ambigue — chiedi SEMPRE conferma\n"
            )

            if modalita == "🎓 Tutor":
                istruzioni = f"""Sei un tutor di matematica e fisica per il liceo scientifico italiano.
Lo studente è al {classe} anno e sta studiando {materia}.
Gli argomenti che ha già trattato sono: {argomenti_testo}.
REGOLE FONDAMENTALI:
- Non dare mai la soluzione completa
- Guida lo studente con domande socratiche
- Usa SOLO concetti e strumenti che lo studente conosce
- Se l'esercizio richiede strumenti non ancora studiati, dillo chiaramente
- Parla in italiano, con linguaggio adatto a uno studente di liceo
- Sii incoraggiante e paziente
{regole_latex}"""
            else:
                istruzioni = f"""Sei un tutor di matematica e fisica per il liceo scientifico italiano.
Lo studente è al {classe} anno e sta studiando {materia}.
Gli argomenti che ha già trattato sono: {argomenti_testo}.
REGOLE FONDAMENTALI:
- Fornisci la soluzione completa passo per passo
- Usa SOLO concetti e strumenti che lo studente conosce
- Se l'esercizio richiede strumenti non ancora studiati, dillo chiaramente
- Spiega ogni passaggio in modo chiaro
- Parla in italiano, con linguaggio adatto a uno studente di liceo
{regole_latex}"""

            st.session_state.istruzioni = istruzioni

            if immagine:
                import base64
                immagine_compressa = comprimi_immagine(immagine)
                image_data = base64.standard_b64encode(immagine_compressa.getvalue()).decode("utf-8")
                contenuto = []
                if testo_esercizio:
                    contenuto.append({"type": "text", "text": testo_esercizio})
                contenuto.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data
                    }
                })
            else:
                contenuto = testo_esercizio

            # Salva stato checkbox prima del rerun
            for c in classi_disponibili:
                for argomento in ARGOMENTI[materia][c]:
                    key = f"chk_{c}_{argomento}"
                    if key in st.session_state:
                        st.session_state[f"saved_{key}"] = st.session_state[key]

            # Salva sessione su Supabase
            try:
                supabase_client.table("sessioni").insert({
                    "classe": classe,
                    "materia": materia,
                    "modalita": modalita,
                    "tipo_input": "foto" if immagine else "testo"
                }).execute()
            except:
                pass

            st.session_state.conversazione = [{"role": "user", "content": contenuto}]
            st.session_state.sessione_attiva = True
            st.rerun()
else:
    if len(st.session_state.conversazione) == 1:
        with st.spinner("Il tutor sta analizzando l'esercizio..."):
            risposta = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=st.session_state.istruzioni,
                messages=st.session_state.conversazione
            )
            st.session_state.conversazione.append({
                "role": "assistant",
                "content": risposta.content[0].text
            })

    for msg in st.session_state.conversazione:
        if msg["role"] == "user":
            with st.chat_message("user"):
                if isinstance(msg["content"], str):
                    mostra_risposta(msg["content"])
                else:
                    st.markdown("*Esercizio caricato come immagine*")
        else:
            with st.chat_message("assistant", avatar="📚"):
                mostra_risposta(msg["content"])

    risposta_studente = st.chat_input("Scrivi la tua risposta...")
    if risposta_studente:
        st.session_state.conversazione.append({"role": "user", "content": risposta_studente})
        with st.spinner("Il tutor sta rispondendo..."):
            risposta = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=st.session_state.istruzioni,
                messages=st.session_state.conversazione
            )
            st.session_state.conversazione.append({
                "role": "assistant",
                "content": risposta.content[0].text
            })
        st.rerun()

    if st.button("🔄 Nuovo esercizio", type="secondary"):
        st.session_state.conversazione = []
        st.session_state.sessione_attiva = False
        st.session_state.istruzioni = ""
        st.rerun()
