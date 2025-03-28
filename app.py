import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(page_title="Pilotage Atelier", layout="wide")

# Menu latéral de navigation
st.sidebar.title("Navigation")
option = st.sidebar.radio("Aller à", ("Dashboard", "Chat IA", "Import/Export", "Paramètres"))

# Fonction pour charger des données simulées
@st.cache_data
def load_data():
    data = pd.DataFrame({
        "OF": [f"OF-{i:03d}" for i in range(1, 21)],
        "Production": np.random.randint(80, 120, 20),
        "Temps_Reel": np.random.uniform(1.0, 2.0, 20),
        "Temps_Standard": np.random.uniform(1.0, 1.5, 20)
    })
    return data

data = load_data()

# Vue Dashboard Principal
if option == "Dashboard":
    st.title("Dashboard Principal")
    st.subheader("Indicateurs Clés")
    # Calcul de la productivité : Production / Temps_Reel
    data["Productivité"] = data["Production"] / data["Temps_Reel"]
    avg_productivity = data["Productivité"].mean()
    st.metric(label="Productivité Moyenne", value=f"{avg_productivity:.2f}")
    st.write("Données des Ordres de Fabrication (OF)")
    st.dataframe(data)

    st.subheader("Graphique de Production")
    st.line_chart(data.set_index("OF")["Production"])

# Vue Chat IA
elif option == "Chat IA":
    st.title("Chat IA - Assistant Production")
    st.info("Posez une question pour obtenir une réponse simulée (module IA à intégrer ultérieurement).")
    user_input = st.text_input("Votre question :")
    if st.button("Envoyer"):
        # Réponse simulée (à remplacer par l'intégration de l'API OpenAI si souhaité)
        response = f"Réponse simulée pour: '{user_input}'"
        st.write(response)

# Vue Import/Export de Données
elif option == "Import/Export":
    st.title("Import/Export de Données")
    uploaded_file = st.file_uploader("Choisissez un fichier CSV à importer", type=["csv"])
    if uploaded_file is not None:
        uploaded_data = pd.read_csv(uploaded_file)
        st.write("Aperçu des données importées:")
        st.dataframe(uploaded_data)
        st.success("Import effectué avec succès.")
    st.markdown("**Export :** Cette fonctionnalité pourra être implémentée ultérieurement.")

# Vue Paramètres & Configuration
elif option == "Paramètres":
    st.title("Paramètres & Configuration")
    threshold = st.number_input("Seuil de Retard OF (en %)", min_value=100, max_value=200, value=125)
    st.write(f"Seuil défini : {threshold}%")
    operator_name = st.text_input("Nom de l'opérateur (optionnel)", value="")
    if st.button("Sauvegarder les paramètres"):
        st.success("Paramètres sauvegardés !")
