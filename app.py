import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# -------------------------
# 1) Fichiers CSV
# -------------------------
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

# -----------------------------------------------------
# 2) Générer les intervalles (Production / Arrêt)
# -----------------------------------------------------
def build_intervals_for_OF(of_id, df_events):
    """
    À partir de tous les events de l'OF (triés), on construit
    des segments de "Production" ou d'"Arrêt".
    On renvoie un DataFrame avec colonnes :
      - 'OF'
      - 'type_intervalle' (Production ou Arrêt)
      - 'start'
      - 'end'
      - 'commentaire' (surtout pour les arrêts)
    """
    # Filtrons les événements de cet OF, triés par timestamp
    events = df_events[df_events["OF"] == of_id].copy()
    events["timestamp_dt"] = pd.to_datetime(events["timestamp"], errors="coerce")
    events = events.sort_values("timestamp_dt")

    intervals = []
    current_mode = None  # soit "Production", soit "Arrêt"
    current_start = None
    current_comment = ""

    for idx, ev in events.iterrows():
        evt_type = ev["evenement"]      # e.g. "Début Prod", "Début Arrêt", "Fin Arrêt", "Fin OF"
        evt_time = ev["timestamp_dt"]
        evt_com  = ev["commentaire"]

        if evt_type == "Début Prod":
            # On clôture l'intervalle précédent (s'il y en a un)
            if current_mode is not None and current_start is not None:
                intervals.append({
                    "OF": of_id,
                    "type_intervalle": current_mode,
                    "start": current_start,
                    "end": evt_time,
                    "commentaire": current_comment
                })
            # On ouvre un nouvel intervalle en mode "Production"
            current_mode = "Production"
            current_start = evt_time
            current_comment = ""

        elif evt_type == "Début Arrêt":
            # Clôturer la production en cours
            if current_mode == "Production" and current_start is not None:
                intervals.append({
                    "OF": of_id,
                    "type_intervalle": "Production",
                    "start": current_start,
                    "end": evt_time,
                    "commentaire": ""
                })
            # Ouvrir un intervalle "Arrêt"
            current_mode = "Arrêt"
            current_start = evt_time
            current_comment = ""  # on le renseignera peut-être à la fin

        elif evt_type == "Fin Arrêt":
            # Clôturer l'Arrêt
            if current_mode == "Arrêt" and current_start is not None:
                intervals.append({
                    "OF": of_id,
                    "type_intervalle": "Arrêt",
                    "start": current_start,
                    "end": evt_time,
                    "commentaire": evt_com  # le commentaire saisi à la fin
                })
            # Repasser en production
            current_mode = "Production"
            current_start = evt_time
            current_comment = ""

        elif evt_type == "Fin OF":
            # Clôturer l'intervalle en cours (que ce soit Prod ou Arrêt)
            if current_mode is not None and current_start is not None:
                intervals.append({
                    "OF": of_id,
                    "type_intervalle": current_mode,
                    "start": current_start,
                    "end": evt_time,
                    "commentaire": ""
                })
            # Plus rien en cours
            current_mode = None
            current_start = None
            current_comment = ""

    # S'il reste un intervalle ouvert à la fin (OF non terminé), on le ferme maintenant
    # (optionnel, selon votre logique)
    # if current_mode is not None and current_start is not None:
    #     intervals.append({
    #         "OF": of_id,
    #         "type_intervalle": current_mode,
    #         "start": current_start,
    #         "end": datetime.now(),
    #         "commentaire": current_comment
    #     })

    df_intervals = pd.DataFrame(intervals)
    return df_intervals

# -----------------------------------------------------
# 3) Page "Déclaration temps réel"
# -----------------------------------------------------
def page_declaration():
    st.header("Déclaration temps réel : Production / Arrêts")

    df_of = load_of_data()
    df_events = load_events_data()

    # 3.1 - Sélection d'un OF
    all_of = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionner un OF", all_of)

    # Récupérer statut
    statut = df_of.loc[df_of["OF"] == selected_of, "Statut"].values[0]
    st.write(f"Statut actuel : **{statut}**")

    # 3.2 - Boutons selon le statut
    if statut == "En attente":
        # Bouton => Début Prod
        if st.button("Démarrer l'OF"):
            new_event = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Début Prod",
                "commentaire": ""
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_event])], ignore_index=True)
            # Statut => En cours
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"

            save_of_data(df_of)
            save_events_data(df_events)
            st.success(f"OF {selected_of} est maintenant en cours.")

    elif statut == "En cours":
        colA, colB = st.columns(2)
        if colA.button("Déclarer un Arrêt"):
            new_event = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Début Arrêt",
                "commentaire": ""
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_event])], ignore_index=True)
            # Statut => En arrêt
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En arrêt"

            save_of_data(df_of)
            save_events_data(df_events)
            st.warning(f"OF {selected_of} est maintenant en arrêt.")

        if colB.button("Terminer l'OF"):
            new_event = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Fin OF",
                "commentaire": ""
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_event])], ignore_index=True)
            # Statut => Terminé
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"

            save_of_data(df_of)
            save_events_data(df_events)
            st.success(f"OF {selected_of} est terminé.")

    elif statut == "En arrêt":
        # Bouton => Fin Arrêt (oblige à saisir un commentaire)
        comment = st.text_input("Commentaire de fin d'arrêt (raison, solution, etc.)")
        if st.button("Fin d'Arrêt"):
            if not comment.strip():
                st.error("Veuillez saisir un commentaire avant de reprendre la production.")
            else:
                new_event = {
                    "timestamp": datetime.now().isoformat(timespec='seconds'),
                    "OF": selected_of,
                    "evenement": "Fin Arrêt",
                    "commentaire": comment
                }
                df_events = pd.concat([df_events, pd.DataFrame([new_event])], ignore_index=True)
                # Statut => En cours
                df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"

                save_of_data(df_of)
                save_events_data(df_events)
                st.success(f"L'arrêt est terminé. L'OF {selected_of} reprend en production.")

    elif statut == "Terminé":
        st.info("Cet OF est terminé. Aucune action disponible.")

    # -----------------------------------------------------
    # 3.3 - Affichage de la timeline (prod/arrêt) pour l'OF sélectionné
    # -----------------------------------------------------
    st.subheader("Timeline de l'OF (Production vs Arrêt)")
    df_intervals = build_intervals_for_OF(selected_of, df_events)

    if df_intervals.empty:
        st.info("Aucun segment de production ou d'arrêt à afficher (OF pas encore démarré).")
    else:
        # On utilise Plotly Express pour un Gantt coloré
        # 'type_intervalle' = "Production" ou "Arrêt"
        # On veut "Arrêt" en rouge et "Production" en vert
        color_map = {
            "Production": "green",
            "Arrêt": "red"
        }

        fig = px.timeline(
            df_intervals,
            x_start="start",
            x_end="end",
            y="OF",
            color="type_intervalle",
            color_discrete_map=color_map,
            hover_data=["commentaire"]
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            title=f"Timeline pour l'OF {selected_of}",
            xaxis_title="Temps",
            yaxis_title="OF",
            legend_title="Mode"
        )
        st.plotly_chart(fig, use_container_width=True)

        # -------------------------------------------------
        # 3.4 - Occurrences des arrêts : liste + durées
        # -------------------------------------------------
        st.subheader("Occurrences des arrêts pour cet OF")
        df_arrets = df_intervals[df_intervals["type_intervalle"] == "Arrêt"].copy()
        if df_arrets.empty:
            st.info("Aucun arrêt enregistré pour cet OF.")
        else:
            # Calcul de la durée de chaque arrêt (minutes)
            df_arrets["start_dt"] = pd.to_datetime(df_arrets["start"])
            df_arrets["end_dt"]   = pd.to_datetime(df_arrets["end"])
            df_arrets["duree_min"] = (df_arrets["end_dt"] - df_arrets["start_dt"]).dt.total_seconds() / 60.0

            st.write("Tableau des arrêts :")
            st.table(
                df_arrets[["start", "end", "duree_min", "commentaire"]]
                .rename(columns={
                    "start": "Début",
                    "end": "Fin",
                    "duree_min": "Durée (min)",
                    "commentaire": "Commentaire"
                })
            )

# -----------------------------------------------------
# 4) Page "Dashboard" (facultatif)
# -----------------------------------------------------
def page_dashboard():
    st.header("Dashboard global (facultatif)")
    st.info("Ici, vous pouvez afficher un Kanban global, un Pareto, etc. Ce n'est pas le focus actuel.")

# -----------------------------------------------------
# 5) main : appli Streamlit
# -----------------------------------------------------
def main():
    st.set_page_config(layout="wide")
    st.title("Mini-MES : Production & Arrêts alternés")

    choice = st.sidebar.selectbox("Menu", ["Déclaration temps réel", "Dashboard (optionnel)"])
    if choice == "Déclaration temps réel":
        page_declaration()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()
