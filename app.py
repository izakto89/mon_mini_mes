import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -------------------------------------------------------------
# 1) Config & fichiers CSV
# -------------------------------------------------------------
OF_CSV = "data/of_list.csv"
EVENTS_CSV = "data/events.csv"

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

# -------------------------------------------------------------
# 2) Calculer debut, fin, progression, etc.
# -------------------------------------------------------------
def compute_times_and_progress(df_of, df_events):
    """
    Ajoute :
      - 'start_dt' : date/heure du dernier "Début OF"
      - 'end_dt'   : date/heure du dernier "Fin OF" ou 'now' si En cours
      - 'progress' : % d'avancement par rapport à Duree_prevue
    Duree_prevue = minutes ou heures (à clarifier). Pour l'exemple, on suppose minutes.
    """
    df_of["start_dt"] = pd.NaT
    df_of["end_dt"] = pd.NaT
    df_of["progress"] = 0.0

    df_of["Duree_prevue"] = pd.to_numeric(df_of["Duree_prevue"], errors="coerce").fillna(0)

    # Convertir les timestamps en datetime
    df_events["timestamp_dt"] = pd.to_datetime(df_events["timestamp"], errors="coerce")

    for i, row in df_of.iterrows():
        of_id = row["OF"]
        statut = row["Statut"]
        duree_prevue = row["Duree_prevue"]

        # Récupérer tous les events de cet OF
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
            df_of.at[i, "start_dt"] = last_start_dt

            if statut == "Terminé" and last_end_dt is not None:
                df_of.at[i, "end_dt"] = last_end_dt
            elif statut == "En cours":
                df_of.at[i, "end_dt"] = datetime.now()

            # Calculer la progression
            start_val = df_of.at[i, "start_dt"]
            end_val = df_of.at[i, "end_dt"]
            if pd.notna(start_val) and pd.notna(end_val) and duree_prevue > 0:
                delta = end_val - start_val
                delta_minutes = delta.total_seconds() / 60.0  # on suppose minutes
                progress_pct = (delta_minutes / duree_prevue) * 100
                if progress_pct > 100:
                    progress_pct = 100
                df_of.at[i, "progress"] = progress_pct

    return df_of

# -------------------------------------------------------------
# 3) Page : Déclaration temps réel
# -------------------------------------------------------------
def page_declaration():
    st.header("Déclaration en temps réel")

    df_of = load_of_data()
    df_events = load_events_data()

    # Sélection d'un OF
    of_list = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionner un OF", of_list)

    # Statut actuel
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

        df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"

        save_of_data(df_of)
        save_events_data(df_events)

        st.success(f"L'OF {selected_of} est terminé.")

    st.subheader("Déclarer un arrêt (défaut, etc.)")
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

        save_of_data(df_of)
        save_events_data(df_events)

        st.success(f"Arrêt '{arret_choice}' enregistré pour l'OF {selected_of}.")

# -------------------------------------------------------------
# 4) Page : Tableau de bord (Kanban, KPIs, Gantt, Pareto)
# -------------------------------------------------------------
def page_dashboard():
    st.header("Tableau de bord de production")

    df_of = load_of_data()
    df_events = load_events_data()

    # Calcul des colonnes start_dt, end_dt, progress
    df_of = compute_times_and_progress(df_of, df_events)

    # --------------------------
    # 4.1 - Quelques KPIs (en haut)
    # --------------------------
    # Nombre d'OF "En cours"
    nb_en_cours = (df_of["Statut"] == "En cours").sum()
    # Nombre d'OF "Terminé"
    nb_termine = (df_of["Statut"] == "Terminé").sum()
    # Progression moyenne (sur tous les OF qui sont "En cours" ou "Terminé")
    df_with_progress = df_of[df_of["Statut"].isin(["En cours", "Terminé"])]
    if len(df_with_progress) > 0:
        avg_progress = df_with_progress["progress"].mean()
    else:
        avg_progress = 0

    # Nombre d'arrêts total
    df_arrets = df_events[~df_events["evenement"].isin(["Début OF", "Fin OF"])]
    nb_arrets = len(df_arrets)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("OF en cours", nb_en_cours)
    col2.metric("OF terminés", nb_termine)
    col3.metric("Progression moy.", f"{avg_progress:3.0f}%")
    col4.metric("Nb arrêts", nb_arrets)

    st.markdown("---")

    # --------------------------
    # 4.2 - Diagramme de Gantt interactif (Plotly)
    # --------------------------
    st.subheader("Timeline Gantt")

    df_gantt = df_of.dropna(subset=["start_dt", "end_dt"]).copy()
    if df_gantt.empty:
        st.info("Aucun OF avec start_dt et end_dt pour tracer le Gantt.")
    else:
        # Convertir en datetime
        df_gantt["start_dt"] = pd.to_datetime(df_gantt["start_dt"])
        df_gantt["end_dt"] = pd.to_datetime(df_gantt["end_dt"])

        fig_gantt = px.timeline(
            df_gantt,
            x_start="start_dt",
            x_end="end_dt",
            y="OF",
            color="Statut",
            hover_data=["Description", "progress"],
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(
            title="Gantt des OF",
            xaxis_title="Temps",
            yaxis_title="OF",
            legend_title="Statut",
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

    st.markdown("---")

    # --------------------------
    # 4.3 - Pareto des arrêts
    # --------------------------
    st.subheader("Pareto des arrêts")

    pareto = (df_arrets
              .groupby("evenement")["timestamp"]
              .count()
              .reset_index(name="count")
              .sort_values("count", ascending=False))
    if pareto.empty:
        st.info("Aucun arrêt pour l'instant.")
    else:
        # Affichage en tableau
        st.write(pareto)

        fig_pareto, ax = plt.subplots()
        ax.bar(pareto["evenement"], pareto["count"])
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Occurrences")
        ax.set_title("Pareto des causes d'arrêts")
        st.pyplot(fig_pareto)

    st.markdown("---")

    # --------------------------
    # 4.4 - Affichage d'un gauge (indicatif) pour la progression moyenne
    # --------------------------
    st.subheader("Gauge de la progression moyenne")

    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=avg_progress,
            title={"text": "Progression moyenne (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "green"},
            },
            domain={"x": [0, 1], "y": [0, 1]}
        )
    )
    st.plotly_chart(fig_gauge, use_container_width=False)

    st.markdown("---")

    # --------------------------
    # 4.5 - Kanban détaillé (table)
    # --------------------------
    st.subheader("Kanban détaillé")
    statuts = df_of["Statut"].unique()
    for s in statuts:
        st.write(f"### {s}")
        subset = df_of[df_of["Statut"] == s].copy()
        subset["progress"] = subset["progress"].round(1).astype(str) + " %"
        st.table(subset[["OF", "Description", "Duree_prevue", "progress"]])

# -------------------------------------------------------------
# 5) main : navigation
# -------------------------------------------------------------
def main():
    st.set_page_config(layout="wide")
    st.title("Mini-MES : Suivi de Production (visuel avancé)")

    menu = st.sidebar.selectbox("Menu", [
        "Déclaration temps réel",
        "Tableau de bord"
    ])

    if menu == "Déclaration temps réel":
        page_declaration()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()
