import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import matplotlib.dates as mdates  # pour d'éventuels besoins si on veut du matplotlib sur les dates

# -----------------------------------------------------
# 1) Paramètres de chemins vers les CSV
# -----------------------------------------------------
OF_CSV = "data/of_list.csv"
EVENTS_CSV = "data/events.csv"

# -----------------------------------------------------
# 2) Chargement / Sauvegarde
# -----------------------------------------------------
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

# -----------------------------------------------------
# 3) Calcul des temps et pourcentage d'avancement
# -----------------------------------------------------
def compute_times_and_progress(df_of, df_events):
    """
    Ajoute dans df_of :
      - start_dt : Date/heure du dernier 'Début OF'
      - end_dt   : Date/heure du dernier 'Fin OF' (ou maintenant si En cours)
      - progress : Pourcentage d'avancement, calculé avec la Duree_prevue
    Hypothèse : Duree_prevue est en minutes, on compare le temps réel accumulé
    seulement entre le dernier 'Début OF' et la fin ou l'instant présent.
    """
    df_of["start_dt"] = pd.NaT
    df_of["end_dt"] = pd.NaT
    df_of["progress"] = 0.0

    # Convertir la durée prévue en numérique (en cas de virgule) :
    df_of["Duree_prevue"] = pd.to_numeric(df_of["Duree_prevue"], errors="coerce").fillna(0)

    # Convertir le timestamp des events en datetime
    df_events["timestamp_dt"] = pd.to_datetime(df_events["timestamp"], errors="coerce")

    for i, row in df_of.iterrows():
        of_id = row["OF"]
        statut = row["Statut"]
        duree_prevue = row["Duree_prevue"]

        # Filtrer les events de cet OF, triés
        subset = df_events[df_events["OF"] == of_id].sort_values("timestamp_dt")

        # Dernier "Début OF"
        debuts = subset[subset["evenement"] == "Début OF"]
        last_start_dt = None
        if not debuts.empty:
            last_start_dt = debuts.iloc[-1]["timestamp_dt"]

        # Dernier "Fin OF"
        fins = subset[subset["evenement"] == "Fin OF"]
        last_end_dt = None
        if not fins.empty:
            last_end_dt = fins.iloc[-1]["timestamp_dt"]

        if last_start_dt is not None:
            # on stocke le start
            df_of.at[i, "start_dt"] = last_start_dt

            # Déterminer end_dt
            if statut == "Terminé" and last_end_dt is not None:
                # L'OF est terminé => end_dt = date du dernier Fin OF
                df_of.at[i, "end_dt"] = last_end_dt
            elif statut == "En cours":
                # Actuellement en cours => end_dt = maintenant
                df_of.at[i, "end_dt"] = datetime.now()
            # Si "En attente" ou qu'on n'a pas encore démarré => end_dt reste NaT

            # Calculer la progression
            start_val = df_of.at[i, "start_dt"]
            end_val = df_of.at[i, "end_dt"]
            if pd.notna(start_val) and pd.notna(end_val) and duree_prevue > 0:
                delta = end_val - start_val
                delta_minutes = delta.total_seconds() / 60.0
                progress_pct = (delta_minutes / duree_prevue) * 100
                # Borne à 100% max
                if progress_pct > 100:
                    progress_pct = 100
                df_of.at[i, "progress"] = progress_pct

    return df_of

# -----------------------------------------------------
# 4) Page Déclaration : Boutons Démarrer / Fin / Arrêt
# -----------------------------------------------------
def page_declaration():
    st.header("Déclaration en temps réel")

    df_of = load_of_data()
    df_events = load_events_data()

    # Sélection d'un OF
    of_list = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionner un OF", of_list)

    # Statut
    statut_actuel = df_of.loc[df_of["OF"] == selected_of, "Statut"].values[0]
    st.write(f"Statut actuel : **{statut_actuel}**")

    if st.button("Démarrer l'OF"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": "Début OF",
            "commentaire": ""
        }
        df_new = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new], ignore_index=True)

        # Statut = En cours
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"
        save_of_data(df_of)
        save_events_data(df_events)

        st.success(f"L'OF {selected_of} est lancé (En cours).")

    if st.button("Terminer l'OF"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": "Fin OF",
            "commentaire": ""
        }
        df_new = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new], ignore_index=True)

        # Statut = Terminé
        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"
        save_of_data(df_of)
        save_events_data(df_events)

        st.success(f"L'OF {selected_of} est terminé.")

    # Déclarer un arrêt
    st.subheader("Déclarer un arrêt ou défaut")
    arret_choice = st.selectbox("Type d'arrêt", ["Qualité", "Manque de charge", "Manque personnel", "Réunion", "Formation"])
    commentaire_arret = st.text_input("Commentaire (facultatif)")

    if st.button("Enregistrer l'arrêt"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": arret_choice,
            "commentaire": commentaire_arret
        }
        df_new = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new], ignore_index=True)

        # On ne change pas le statut (reste "En cours" si l'OF tournait)
        save_of_data(df_of)
        save_events_data(df_events)

        st.success(f"Arrêt '{arret_choice}' enregistré pour l'OF {selected_of}.")

# -----------------------------------------------------
# 5) Page Kanban / Pareto / Gantt
# -----------------------------------------------------
def page_kanban_pareto_gantt():
    st.header("Vue Kanban, Pareto, et Timeline Gantt")

    df_of = load_of_data()
    df_events = load_events_data()

    # Calculer start_dt, end_dt, progress
    df_of = compute_times_and_progress(df_of, df_events)

    # -- Kanban
    st.subheader("Kanban des OF")
    statuts = df_of["Statut"].unique()
    for s in statuts:
        st.write(f"### {s}")
        subset = df_of[df_of["Statut"] == s].copy()
        # On affiche la progression arrondie à 1 décimale
        subset["progress"] = subset["progress"].round(1).astype(str) + " %"
        st.write(subset[["OF", "Description", "Duree_prevue", "progress"]])

    # -- Pareto
    st.subheader("Pareto des arrêts")
    df_arrets = df_events[~df_events["evenement"].isin(["Début OF", "Fin OF"])]
    pareto = (df_arrets.groupby("evenement")["timestamp"]
              .count()
              .reset_index(name="count")
              .sort_values("count", ascending=False))

    if pareto.empty:
        st.info("Aucun arrêt déclaré pour le moment.")
    else:
        st.write(pareto)
        fig_pareto, ax = plt.subplots()
        ax.bar(pareto["evenement"], pareto["count"])
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Nombre d'occurrences")
        ax.set_title("Pareto des causes d'arrêts")
        st.pyplot(fig_pareto)

    # -- Gantt Plotly
    st.subheader("Timeline Gantt (Début-Fin)")

    # Ne garder que les OF qui ont un start_dt et un end_dt
    df_gantt = df_of.dropna(subset=["start_dt", "end_dt"]).copy()
    if df_gantt.empty:
        st.info("Aucun OF en cours ou terminé à visualiser pour le Gantt.")
    else:
        # Convertir en string standard pour Plotly
        df_gantt["start_dt"] = pd.to_datetime(df_gantt["start_dt"])
        df_gantt["end_dt"] = pd.to_datetime(df_gantt["end_dt"])

        # On va colorer par "Statut" pour avoir un rendu plus "MES"
        fig = px.timeline(
            df_gantt,
            x_start="start_dt",
            x_end="end_dt",
            y="OF",
            color="Statut",
            hover_data=["Description", "progress"]
        )
        # Inverser l'axe Y pour avoir le premier OF en haut
        fig.update_yaxes(autorange="reversed")
        # Format date sur l'axe X
        fig.update_xaxes(
            tickformat="%d/%m %H:%M",  # ex: 25/03 14:30
        )
        fig.update_layout(
            title="Diagramme de Gantt interactif",
            xaxis_title="Temps",
            yaxis_title="Ordre de Fabrication",
            legend_title="Statut",
        )

        st.plotly_chart(fig)

# -----------------------------------------------------
# 6) Appli principale avec menu
# -----------------------------------------------------
def main():
    st.set_page_config(layout="wide")  # Optionnel, pour un affichage large
    st.title("Mini-MES : Suivi de Production (version avancée)")

    page = st.sidebar.selectbox("Menu", [
        "Déclaration temps réel",
        "Kanban / Pareto / Gantt"
    ])

    if page == "Déclaration temps réel":
        page_declaration()
    else:
        page_kanban_pareto_gantt()

if __name__ == "__main__":
    main()
