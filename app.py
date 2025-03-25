import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 1) Les chemins vers nos fichiers CSV
OF_CSV = "data/of_list.csv"
EVENTS_CSV = "data/events.csv"

# 2) Fonctions pour charger et sauvegarder les données
def load_of_data():
    return pd.read_csv(OF_CSV)

def load_events_data():
    try:
        return pd.read_csv(EVENTS_CSV)
    except FileNotFoundError:
        return pd.DataFrame(columns=["timestamp", "OF", "evenement", "commentaire"])

def save_of_data(df):
    df.to_csv(OF_CSV, index=False)

def save_events_data(df):
    df.to_csv(EVENTS_CSV, index=False)

# 3) Page de déclaration (l'opérateur clique pour démarrer, arrêter, etc.)
def page_declaration():
    st.header("Déclaration en temps réel")

    df_of = load_of_data()
    df_events = load_events_data()

    # Sélection d'un OF
    of_list = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionne un OF", of_list)

    # Statut actuel
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
        df_events = df_events.append(new_event, ignore_index=True)
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"

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
        df_events = df_events.append(new_event, ignore_index=True)
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"

        save_events_data(df_events)
        save_of_data(df_of)
        st.success(f"OF {selected_of} terminé.")

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
        df_events = df_events.append(new_event, ignore_index=True)
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En pause"

        save_events_data(df_events)
        save_of_data(df_of)
        st.success(f"Arrêt '{arret_choice}' enregistré pour l'OF {selected_of}.")

# 4) Page Kanban & Performance
def page_kanban_et_pareto():
    st.header("Vue Kanban & Performance")

    df_of = load_of_data()
    df_events = load_events_data()

    st.subheader("Kanban des OF")
    statuts = df_of["Statut"].unique()
    for s in statuts:
        st.write(f"### {s}")
        subset = df_of[df_of["Statut"] == s]
        st.write(subset[["OF", "Description"]])

    st.subheader("Pareto des arrêts")
    df_arrets = df_events[~df_events["evenement"].isin(["Début OF", "Fin OF"])]
    pareto = df_arrets.groupby("evenement")["timestamp"].count().reset_index(name="count").sort_values("count", ascending=False)

    if pareto.empty:
        st.info("Aucun arrêt déclaré pour le moment.")
    else:
        st.write(pareto)
        fig, ax = plt.subplots()
        ax.bar(pareto["evenement"], pareto["count"])
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Nombre d'occurrences")
        ax.set_title("Pareto des causes d'arrêts")
        st.pyplot(fig)

# 5) Fonction principale
def main():
    st.title("Mini-MES : Suivi de Production")
    page = st.sidebar.selectbox("Navigation", ["Déclaration temps réel", "Kanban & Performance"])

    if page == "Déclaration temps réel":
        page_declaration()
    else:
        page_kanban_et_pareto()

if __name__ == "__main__":
    main()
