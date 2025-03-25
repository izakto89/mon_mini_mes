import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 1) Les chemins vers nos fichiers CSV
OF_CSV = "data/of_list.csv"
EVENTS_CSV = "data/events.csv"

# 2) Fonctions pour charger et sauvegarder les données
def load_of_data():
    """Charge la liste des OF."""
    return pd.read_csv(OF_CSV)

def load_events_data():
    """Charge l'historique des événements."""
    try:
        return pd.read_csv(EVENTS_CSV)
    except FileNotFoundError:
        # Si le fichier n'existe pas encore, renvoie un DataFrame vide avec les colonnes voulues
        return pd.DataFrame(columns=["timestamp", "OF", "evenement", "commentaire"])

def save_of_data(df):
    """Sauvegarde la liste des OF."""
    df.to_csv(OF_CSV, index=False)

def save_events_data(df):
    """Sauvegarde l'historique des événements."""
    df.to_csv(EVENTS_CSV, index=False)

# 3) Page "Déclaration" : démarrer, terminer, déclarer un arrêt, etc.
def page_declaration():
    st.header("Déclaration en temps réel")

    df_of = load_of_data()
    df_events = load_events_data()

    # Liste déroulante pour sélectionner un OF
    of_list = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionner un OF", of_list)

    # Récupérer le statut actuel de l'OF
    statut_actuel = df_of.loc[df_of["OF"] == selected_of, "Statut"].values[0]
    st.write(f"Statut actuel : **{statut_actuel}**")

    # Bouton "Démarrer l'OF"
    if st.button("Démarrer l'OF"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": "Début OF",
            "commentaire": ""
        }
        # Remplacer append par concat
        df_new_event = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new_event], ignore_index=True)

        # Mettre à jour le statut de l'OF
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"

        # Sauvegarder
        save_events_data(df_events)
        save_of_data(df_of)
        st.success(f"OF {selected_of} démarré.")

    # Bouton "Terminer l'OF"
    if st.button("Terminer l'OF"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": "Fin OF",
            "commentaire": ""
        }
        df_new_event = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new_event], ignore_index=True)

        # Changer le statut en "Terminé"
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"

        save_events_data(df_events)
        save_of_data(df_of)
        st.success(f"OF {selected_of} terminé.")

    # Section "Déclarer un arrêt de production"
    st.subheader("Déclarer un arrêt de production")
    arret_choice = st.selectbox("Type d'arrêt", ["Qualité", "Manque de charge", "Manque personnel", "Réunion", "Formation"])
    commentaire_arret = st.text_input("Commentaire (raison, détail)")

    if st.button("Enregistrer cet arrêt"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": arret_choice,
            "commentaire": commentaire_arret
        }
        df_new_event = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new_event], ignore_index=True)

        # Mettre le statut à "En pause" (ou autre statut de votre choix)
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En pause"

        save_events_data(df_events)
        save_of_data(df_of)
        st.success(f"Arrêt '{arret_choice}' enregistré pour l'OF {selected_of}.")

# 4) Page "Kanban & Performance"
def page_kanban_et_pareto():
    st.header("Vue Kanban & Performance")

    df_of = load_of_data()
    df_events = load_events_data()

    # Petit Kanban : on affiche les OF par statut
    st.subheader("Kanban des OF")
    statuts = df_of["Statut"].unique()
    for s in statuts:
        st.write(f"### {s}")
        subset = df_of[df_of["Statut"] == s]
        st.write(subset[["OF", "Description"]])

    # Pareto des arrêts
    st.subheader("Pareto des arrêts")
    # On filtre tout ce qui n'est pas "Début OF" ou "Fin OF"
    df_arrets = df_events[~df_events["evenement"].isin(["Début OF", "Fin OF"])]

    # On compte le nombre d'occurrences par type d'arrêt
    pareto = df_arrets.groupby("evenement")["timestamp"].count().reset_index(name="count").sort_values("count", ascending=False)

    if pareto.empty:
        st.info("Aucun arrêt déclaré pour le moment.")
    else:
        st.write(pareto)

        # On fait un petit graphique en barres
        fig, ax = plt.subplots()
        ax.bar(pareto["evenement"], pareto["count"])
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Nombre d'occurrences")
        ax.set_title("Pareto des causes d'arrêts")
        st.pyplot(fig)

# 5) Point d'entrée principal : menu de navigation
def main():
    st.title("Mini-MES : Suivi de Production")
    page = st.sidebar.selectbox("Navigation", ["Déclaration temps réel", "Kanban & Performance"])

    if page == "Déclaration temps réel":
        page_declaration()
    else:
        page_kanban_et_pareto()

if __name__ == "__main__":
    main()
