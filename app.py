import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------------------
# 1) Paramètres de fichiers CSV
# ---------------------------
OF_CSV = "data/of_list.csv"       # Liste des OF
EVENTS_CSV = "data/events.csv"    # Historique des événements (début, fin, arrêts, etc.)

# ---------------------------
# 2) Fonctions pour lire et sauvegarder
# ---------------------------
def load_of_data():
    """Charge la liste d'OF depuis le CSV."""
    return pd.read_csv(OF_CSV)

def load_events_data():
    """Charge l'historique des événements."""
    try:
        return pd.read_csv(EVENTS_CSV)
    except FileNotFoundError:
        # Si le fichier events.csv n'existe pas encore,
        # on renvoie un DataFrame vide avec les colonnes voulues
        return pd.DataFrame(columns=["timestamp", "OF", "evenement", "commentaire"])

def save_of_data(df):
    """Sauvegarde la liste d'OF dans le CSV."""
    df.to_csv(OF_CSV, index=False)

def save_events_data(df):
    """Sauvegarde l'historique dans le CSV."""
    df.to_csv(EVENTS_CSV, index=False)

# ---------------------------
# 3) Calculer le temps écoulé pour les OF "En cours"
# ---------------------------
from datetime import datetime

def compute_in_progress_time(df_of, df_events):
    """
    Pour chaque OF en statut "En cours", on calcule le temps (en minutes)
    écoulé depuis le dernier "Début OF" jusqu'à maintenant.
    On stocke ce temps dans une colonne 'Temps_en_cours'.
    Les OF qui ne sont pas "En cours" auront un champ vide.
    """
    df_of["Temps_en_cours"] = ""  # On crée la colonne (vide par défaut)

    for i, row in df_of.iterrows():
        if row["Statut"] == "En cours":
            # Récupérer tous les événements de cet OF, triés par date
            events_of = df_events[df_events["OF"] == row["OF"]].sort_values("timestamp")
            # Trouver le dernier "Début OF"
            starts = events_of[events_of["evenement"] == "Début OF"]
            if not starts.empty:
                # On prend le plus récent "Début OF"
                last_start_ts = starts.iloc[-1]["timestamp"]
                dt_start = pd.to_datetime(last_start_ts)
                dt_now = datetime.now()

                # Durée en minutes
                delta = dt_now - dt_start
                minutes_in_progress = delta.total_seconds() / 60

                # On arrondit à 1 décimale par exemple
                df_of.at[i, "Temps_en_cours"] = f"{minutes_in_progress:.1f} min"
        # Sinon, OF n'est pas "En cours", on laisse Temps_en_cours vide
    return df_of

# ---------------------------
# 4) Page "Déclaration" : Démarrer, Terminer, Arrêts
# ---------------------------
def page_declaration():
    st.header("Déclaration en temps réel")

    df_of = load_of_data()
    df_events = load_events_data()

    # Sélection d'un OF
    of_list = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionner un OF", of_list)

    # Récupérer statut actuel
    statut_actuel = df_of.loc[df_of["OF"] == selected_of, "Statut"].values[0]
    st.write(f"Statut actuel de l'OF {selected_of} : **{statut_actuel}**")

    # Bouton "Démarrer l'OF"
    if st.button("Démarrer l'OF"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": "Début OF",
            "commentaire": ""
        }
        # Au lieu de append (déprécié), on fait un concat
        df_new_event = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new_event], ignore_index=True)

        # Mettre à jour l'OF en "En cours"
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"

        # Sauvegarder
        save_of_data(df_of)
        save_events_data(df_events)
        st.success(f"L'OF {selected_of} est maintenant en cours.")

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

        # Mettre l'OF en "Terminé"
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"

        save_of_data(df_of)
        save_events_data(df_events)
        st.success(f"L'OF {selected_of} est terminé.")

    # Section : Déclarer un arrêt (défaut)
    st.subheader("Déclarer un arrêt ou défaut")
    arret_choice = st.selectbox("Type d'arrêt", ["Qualité", "Manque de charge", "Manque personnel", "Réunion", "Formation"])
    commentaire_arret = st.text_input("Commentaire (facultatif)")

    if st.button("Enregistrer l'arrêt"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": arret_choice,   # ex: "Qualité"
            "commentaire": commentaire_arret
        }
        df_new_event = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new_event], ignore_index=True)

        # NOTE : On ne change PLUS le statut de l'OF (on le laisse "En cours")
        # df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En pause"  <-- supprimé

        save_of_data(df_of)
        save_events_data(df_events)
        st.success(f"Arrêt '{arret_choice}' enregistré pour l'OF {selected_of} (statut inchangé).")

# ---------------------------
# 5) Page "Kanban & Performance"
# ---------------------------
def page_kanban_et_pareto():
    st.header("Vue Kanban & Performance")

    df_of = load_of_data()
    df_events = load_events_data()

    # Calculer la durée "en cours" (pour chaque OF qui est en statut "En cours")
    df_of = compute_in_progress_time(df_of, df_events)

    # Afficher un Kanban basique
    st.subheader("Kanban des OF (statut + durée en cours)")

    statuts = df_of["Statut"].unique()
    for s in statuts:
        st.write(f"### Statut : {s}")
        subset = df_of[df_of["Statut"] == s]

        # On affiche les colonnes OF, Description, Temps_en_cours
        # (Comme ça, si c'est "En cours", on voit la durée)
        st.write(subset[["OF", "Description", "Temps_en_cours"]])

    # Afficher un Pareto des arrêts
    st.subheader("Pareto des arrêts")
    # Filtrons tout ce qui n'est pas 'Début OF' ou 'Fin OF'
    df_arrets = df_events[~df_events["evenement"].isin(["Début OF", "Fin OF"])]

    pareto = (df_arrets
              .groupby("evenement")["timestamp"]
              .count()
              .reset_index(name="count")
              .sort_values("count", ascending=False))

    if pareto.empty:
        st.info("Aucun arrêt déclaré pour le moment.")
    else:
        st.write(pareto)

        # Petit histogramme
        fig, ax = plt.subplots()
        ax.bar(pareto["evenement"], pareto["count"])
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Nombre d'occurrences")
        ax.set_title("Pareto des causes d'arrêts")
        st.pyplot(fig)

# ---------------------------
# 6) Navigation principale
# ---------------------------
def main():
    st.title("Mini-MES : Suivi de Production")
    page = st.sidebar.selectbox("Navigation", ["Déclaration temps réel", "Kanban & Performance"])

    if page == "Déclaration temps réel":
        page_declaration()
    else:
        page_kanban_et_pareto()

if __name__ == "__main__":
    main()
