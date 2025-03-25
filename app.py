import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --------------------------------------
# 1) Fichiers CSV & Fonctions I/O
# --------------------------------------
OF_CSV = "data/of_list.csv"
EVENTS_CSV = "data/events.csv"

def load_of_data():
    return pd.read_csv(OF_CSV)

def load_events_data():
    try:
        return pd.read_csv(EVENTS_CSV)
    except FileNotFoundError:
        return pd.DataFrame(columns=["timestamp", "OF", "evenement", "type_arret", "commentaire"])

def save_of_data(df):
    df.to_csv(OF_CSV, index=False)

def save_events_data(df):
    df.to_csv(EVENTS_CSV, index=False)

# --------------------------------------
# 2) Reconstitution des intervalles (prod / arrêt)
# --------------------------------------
def build_intervals(df_events, df_of):
    """
    Construit un DataFrame pour un Gantt :
      - 'OF'
      - 'start' : début de la plage
      - 'end'   : fin de la plage (ou maintenant si en cours)
      - 'mode'  : "Production" ou "Arrêt"
      - 'commentaire'
      - On utilise 'type_arret' si c'est un arrêt (pour le hover).
    """

    # 1) Convertir en datetime
    df_events["timestamp_dt"] = pd.to_datetime(df_events["timestamp"], errors="coerce")

    intervals = []
    # On traite chaque OF séparément
    for of_id in df_of["OF"].unique():
        statut = df_of.loc[df_of["OF"] == of_id, "Statut"].values[0]
        ev_of = df_events[df_events["OF"] == of_id].sort_values("timestamp_dt")

        current_mode = None  # "Production" ou "Arrêt"
        current_start = None
        current_comment = ""

        for idx, e in ev_of.iterrows():
            evt_type = e["evenement"]     # "Début Prod", "Début Arrêt", "Fin Arrêt", "Fin OF"
            evt_time = e["timestamp_dt"]
            evt_arret = e["type_arret"]   # cause (Qualité, etc.)
            evt_com = e["commentaire"]

            if evt_type == "Début Prod":
                # On ferme l'intervalle en cours (si existant)
                if current_mode and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": current_mode,
                        "commentaire": current_comment
                    })
                # On ouvre un intervalle de Production
                current_mode = "Production"
                current_start = evt_time
                current_comment = ""

            elif evt_type == "Début Arrêt":
                # Fermer la production
                if current_mode == "Production" and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": "Production",
                        "commentaire": ""
                    })
                # Ouvrir un intervalle d'arrêt
                current_mode = "Arrêt"
                current_start = evt_time
                current_comment = ""

            elif evt_type == "Fin Arrêt":
                # On ferme l'arrêt
                if current_mode == "Arrêt" and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": "Arrêt",
                        "commentaire": f"{evt_arret} - {evt_com}"  # cause + commentaire
                    })
                # Reprise en prod
                current_mode = "Production"
                current_start = evt_time
                current_comment = ""

            elif evt_type == "Fin OF":
                # On ferme le segment en cours
                if current_mode and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": current_mode,
                        "commentaire": ""
                    })
                # plus de segment ouvert
                current_mode = None
                current_start = None
                current_comment = ""

        # Si l'OF est en cours ou en arrêt, on veut un segment qui s'étend jusqu'à "maintenant"
        # pour visualiser la timeline qui avance en continu.
        if current_mode in ["Production", "Arrêt"] and current_start:
            intervals.append({
                "OF": of_id,
                "start": current_start,
                "end": datetime.now(),
                "mode": current_mode,
                "commentaire": current_comment
            })

    df_intervals = pd.DataFrame(intervals)
    return df_intervals

# --------------------------------------
# 3) Page Déclaration temps réel
# --------------------------------------
def page_declaration():
    st.header("Déclaration temps réel (Production / Arrêt)")

    df_of = load_of_data()
    df_events = load_events_data()

    # Sélection OF
    of_list = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionner un OF", of_list)

    statut = df_of.loc[df_of["OF"] == selected_of, "Statut"].values[0]
    st.write(f"Statut actuel : **{statut}**")

    # Affichage de l'action possible
    if statut == "En attente":
        # Bouton "Démarrer"
        if st.button("Démarrer la Production"):
            # On crée un événement "Début Prod"
            new_ev = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Début Prod",
                "type_arret": "",
                "commentaire": ""
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"
            save_of_data(df_of)
            save_events_data(df_events)
            st.success(f"OF {selected_of} est passé en Production.")

    elif statut == "En cours":
        colA, colB = st.columns(2)
        # Bouton "Passer en Arrêt" (rouge)
        if colA.button("Passer en Arrêt"):
            # Créer "Début Arrêt"
            new_ev = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Début Arrêt",
                "type_arret": "",
                "commentaire": ""
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En arrêt"
            save_of_data(df_of)
            save_events_data(df_events)
            st.warning(f"OF {selected_of} est maintenant en Arrêt.")

        # Bouton "Terminer l'OF"
        if colB.button("Terminer l'OF"):
            new_ev = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Fin OF",
                "type_arret": "",
                "commentaire": ""
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"
            save_of_data(df_of)
            save_events_data(df_events)
            st.success(f"OF {selected_of} est terminé.")

    elif statut == "En arrêt":
        st.error("OF en Arrêt.")
        # On propose de REPRENDRE la production
        st.write("Pour reprendre la production, précisez la cause d'arrêt et un commentaire.")
        cause = st.selectbox("Cause de l'arrêt", ["Qualité", "Manque de charge", "Manque personnel", "Réunion", "Formation"])
        commentaire = st.text_input("Commentaire (obligatoire)")

        if st.button("Reprendre la Production"):
            if not commentaire.strip():
                st.error("Veuillez entrer un commentaire avant de reprendre.")
            else:
                # Créer "Fin Arrêt"
                new_ev = {
                    "timestamp": datetime.now().isoformat(timespec='seconds'),
                    "OF": selected_of,
                    "evenement": "Fin Arrêt",
                    "type_arret": cause,
                    "commentaire": commentaire
                }
                df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
                df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"
                save_of_data(df_of)
                save_events_data(df_events)
                st.success(f"Fin de l'arrêt. L'OF {selected_of} est repassé en Production.")

    elif statut == "Terminé":
        st.info("Cet OF est déjà Terminé. Aucune action disponible.")

    # ------------------------------------------------
    # Timeline en temps réel pour l'OF sélectionné
    # ------------------------------------------------
    st.subheader("Timeline de l'OF (vert = Production, rouge = Arrêt)")
    df_intervals = build_intervals(df_events, df_of[df_of["OF"] == selected_of])

    if df_intervals.empty:
        st.info("Pas encore d'activité enregistrée pour cet OF.")
    else:
        # Filtrer juste l'OF sélectionné
        df_current = df_intervals[df_intervals["OF"] == selected_of].copy()
        if df_current.empty:
            st.info("Pas d'intervalles pour cet OF.")
        else:
            color_map = {
                "Production": "green",
                "Arrêt": "red"
            }
            fig = px.timeline(
                df_current,
                x_start="start",
                x_end="end",
                y="OF",
                color="mode",
                color_discrete_map=color_map,
                hover_data=["commentaire"]
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                showlegend=True,
                xaxis_title="Temps",
                yaxis_title="OF",
                legend_title="Mode"
            )
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# 4) Page : Dashboard
# ---------------------------------------
def page_dashboard():
    st.header("Tableau de bord global")

    df_of = load_of_data()
    df_events = load_events_data()

    # 4.1 Quelques KPI
    nb_en_cours = (df_of["Statut"] == "En cours").sum()
    nb_arret = (df_of["Statut"] == "En arrêt").sum()
    nb_termine = (df_of["Statut"] == "Terminé").sum()
    nb_attente = (df_of["Statut"] == "En attente").sum()

    df_arrets = df_events[df_events["evenement"].isin(["Début Arrêt", "Fin Arrêt"])]
    total_arrets = len(df_arrets[df_arrets["evenement"] == "Début Arrêt"])  # Nombre d'arrêts déclarés

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("En attente", nb_attente)
    c2.metric("En cours", nb_en_cours)
    c3.metric("En arrêt", nb_arret)
    c4.metric("Terminé", nb_termine)
    c5.metric("Arrêts déclarés", total_arrets)

    st.markdown("---")

    # 4.2 Kanban global
    st.subheader("Kanban global des OF")
    statuts = ["En attente", "En cours", "En arrêt", "Terminé"]
    for s in statuts:
        subset = df_of[df_of["Statut"] == s]
        st.write(f"### {s} ({len(subset)})")
        if len(subset) > 0:
            st.table(subset[["OF", "Description"]])

    st.markdown("---")

    # 4.3 Pareto des causes d'arrêts
    st.subheader("Pareto des causes d'arrêts")
    # On prend tous les événements "Fin Arrêt" (c'est là qu'on logue la cause)
    df_fin_arrets = df_events[df_events["evenement"] == "Fin Arrêt"]
    if df_fin_arrets.empty:
        st.info("Aucun arrêt terminé, donc pas de données sur les causes.")
    else:
        pareto = df_fin_arrets.groupby("type_arret")["timestamp"].count().reset_index(name="count").sort_values("count", ascending=False)
        st.write(pareto)
        # Petit graph
        import matplotlib.pyplot as plt
        fig_pareto, ax = plt.subplots()
        ax.bar(pareto["type_arret"], pareto["count"])
        ax.set_title("Pareto des causes d'arrêts")
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Occurrences")
        st.pyplot(fig_pareto)

    st.markdown("---")

    # 4.4 Timeline global (tous les OF)
    st.subheader("Timeline global (tous les OF)")
    df_intervals = build_intervals(df_events, df_of)
    if df_intervals.empty:
        st.info("Aucun intervalle n'a été enregistré.")
    else:
        color_map = {
            "Production": "green",
            "Arrêt": "red"
        }
        fig_global = px.timeline(
            df_intervals,
            x_start="start",
            x_end="end",
            y="OF",
            color="mode",
            color_discrete_map=color_map,
            hover_data=["commentaire"]
        )
        fig_global.update_yaxes(autorange="reversed")
        fig_global.update_layout(
            title="Timeline global",
            xaxis_title="Temps",
            yaxis_title="OF",
            legend_title="Mode"
        )
        st.plotly_chart(fig_global, use_container_width=True)

# ---------------------------------------
# 5) main : navigation
# ---------------------------------------
def main():
    st.set_page_config(layout="wide")
    st.title("Mini-MES : Production & Arrêts en continu")

    menu = st.sidebar.radio("Navigation", ["Déclaration temps réel", "Dashboard global"])
    if menu == "Déclaration temps réel":
        page_declaration()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()
