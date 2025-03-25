import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime

# -----------------------------------------------------------
# 1) Fichiers CSV & Fonctions I/O
# -----------------------------------------------------------
OF_CSV = "data/of_list.csv"
EVENTS_CSV = "data/events.csv"

def load_of_data():
    return pd.read_csv(OF_CSV)

def load_events_data():
    try:
        return pd.read_csv(EVENTS_CSV)
    except FileNotFoundError:
        # Colonnes : timestamp, OF, evenement, type_arret, commentaire, quantite
        return pd.DataFrame(columns=["timestamp", "OF", "evenement", "type_arret", "commentaire", "quantite"])

def save_of_data(df):
    df.to_csv(OF_CSV, index=False)

def save_events_data(df):
    df.to_csv(EVENTS_CSV, index=False)

# -----------------------------------------------------------
# 2) Reconstitution des intervalles (Production/Arrêt)
#    pour le Gantt
# -----------------------------------------------------------
def build_intervals(df_events, df_of):
    """
    Identique au code précédent, on construit des segments
    (production vs. arrêt).
    """
    df_events["timestamp_dt"] = pd.to_datetime(df_events["timestamp"], errors="coerce")

    intervals = []
    for of_id in df_of["OF"].unique():
        ev_of = df_events[df_events["OF"] == of_id].sort_values("timestamp_dt")
        statut = df_of.loc[df_of["OF"] == of_id, "Statut"].values[0]

        current_mode = None
        current_start = None
        current_comment = ""

        for idx, e in ev_of.iterrows():
            evt_type = e["evenement"]
            evt_time = e["timestamp_dt"]
            evt_arret = e["type_arret"]
            evt_com = e["commentaire"]

            if evt_type == "Début Prod":
                # Clôture l'intervalle en cours
                if current_mode and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": current_mode,
                        "commentaire": current_comment
                    })
                # Ouvre la prod
                current_mode = "Production"
                current_start = evt_time
                current_comment = ""

            elif evt_type == "Début Arrêt":
                # Fermer la prod
                if current_mode == "Production" and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": "Production",
                        "commentaire": ""
                    })
                # Ouvrir l'arrêt
                current_mode = "Arrêt"
                current_start = evt_time
                current_comment = ""

            elif evt_type == "Fin Arrêt":
                # Fermer l'arrêt
                if current_mode == "Arrêt" and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": "Arrêt",
                        "commentaire": f"{evt_arret} - {evt_com}"
                    })
                # Reprendre la prod
                current_mode = "Production"
                current_start = evt_time
                current_comment = ""

            elif evt_type == "Fin OF":
                # Clôturer ce qui est en cours
                if current_mode and current_start:
                    intervals.append({
                        "OF": of_id,
                        "start": current_start,
                        "end": evt_time,
                        "mode": current_mode,
                        "commentaire": ""
                    })
                current_mode = None
                current_start = None

        # Si l'OF est "En cours" ou "En arrêt", on trace jusqu'à maintenant
        if statut in ["En cours", "En arrêt"] and current_mode and current_start:
            intervals.append({
                "OF": of_id,
                "start": current_start,
                "end": datetime.now(),
                "mode": current_mode,
                "commentaire": current_comment
            })

    return pd.DataFrame(intervals)

# -----------------------------------------------------------
# 3) Page "Déclaration temps réel"
#    - Démarrer/Terminer l'OF
#    - Arrêt / Reprise
#    - Saisie de production (quantité)
# -----------------------------------------------------------
def page_declaration():
    st.header("Déclaration Production / Arrêts / Quantités")

    df_of = load_of_data()
    df_events = load_events_data()

    # Choisir un OF
    of_list = df_of["OF"].unique()
    selected_of = st.selectbox("Sélectionner un OF", of_list)

    # Statut
    row = df_of[df_of["OF"] == selected_of].iloc[0]
    statut = row["Statut"]
    machine = row["Machine"]
    qte_prevue = row.get("QtePrevue", 0)
    qte_realisee = row.get("QteRealisee", 0)

    st.write(f"**Statut** : {statut} | **Machine** : {machine}")
    st.write(f"Quantité prévue : {qte_prevue}, Quantité réalisée : {qte_realisee}")

    # Boutons selon le statut
    if statut == "En attente":
        if st.button("Démarrer la Production"):
            new_ev = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Début Prod",
                "type_arret": "",
                "commentaire": "",
                "quantite": 0
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"
            save_of_data(df_of)
            save_events_data(df_events)
            st.success(f"OF {selected_of} démarré (Production).")

    elif statut == "En cours":
        c1, c2, c3 = st.columns(3)
        # Passer en Arrêt
        if c1.button("Arrêt"):
            new_ev = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Début Arrêt",
                "type_arret": "",
                "commentaire": "",
                "quantite": 0
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En arrêt"
            save_of_data(df_of)
            save_events_data(df_events)
            st.warning("OF en Arrêt.")

        # Terminer l'OF
        if c2.button("Terminer l'OF"):
            new_ev = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "OF": selected_of,
                "evenement": "Fin OF",
                "type_arret": "",
                "commentaire": "",
                "quantite": 0
            }
            df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
            df_of.loc[df_of["OF"] == selected_of, "Statut"] = "Terminé"
            save_of_data(df_of)
            save_events_data(df_events)
            st.success("OF terminé.")

        # Déclarer de la production (quantité partielle)
        added_qty = c3.number_input("Quantité produite (partielle)", min_value=0, value=0)
        if c3.button("Ajouter la production"):
            if added_qty > 0:
                # Créer un événement "ProdQuantite"
                new_ev = {
                    "timestamp": datetime.now().isoformat(timespec='seconds'),
                    "OF": selected_of,
                    "evenement": "Production",
                    "type_arret": "",
                    "commentaire": f"+{added_qty} pièces",
                    "quantite": added_qty
                }
                df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)

                # Mettre à jour QteRealisee dans df_of
                df_of.loc[df_of["OF"] == selected_of, "QteRealisee"] += added_qty

                save_of_data(df_of)
                save_events_data(df_events)
                st.success(f"{added_qty} pièces ajoutées à l'OF {selected_of}.")

    elif statut == "En arrêt":
        st.error("OF en Arrêt.")
        # On propose la fin d'arrêt => cause + commentaire
        cause = st.selectbox("Cause de l'arrêt", ["Qualité", "Manque de charge", "Manque personnel", "Réunion", "Formation"])
        com = st.text_input("Commentaire de fin d'arrêt")

        if st.button("Reprendre la Production"):
            if not com.strip():
                st.error("Veuillez renseigner un commentaire.")
            else:
                new_ev = {
                    "timestamp": datetime.now().isoformat(timespec='seconds'),
                    "OF": selected_of,
                    "evenement": "Fin Arrêt",
                    "type_arret": cause,
                    "commentaire": com,
                    "quantite": 0
                }
                df_events = pd.concat([df_events, pd.DataFrame([new_ev])], ignore_index=True)
                df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En cours"
                save_of_data(df_of)
                save_events_data(df_events)
                st.success("Production reprise.")

    else:  # Terminé
        st.info("OF terminé. Aucune action possible.")

    # ------------------------------------------------
    # Timeline pour l'OF
    # ------------------------------------------------
    st.subheader("Timeline pour l'OF sélectionné")
    intervals = build_intervals(df_events, df_of[df_of["OF"] == selected_of])
    if intervals.empty:
        st.info("Pas encore d'activité enregistrée.")
    else:
        color_map = {"Production": "green", "Arrêt": "red"}
        fig = px.timeline(
            intervals,
            x_start="start",
            x_end="end",
            y="OF",
            color="mode",
            color_discrete_map=color_map,
            hover_data=["commentaire"]
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# 4) Calcul d'un TRS simplifié
#    TRS = (QteRealisee / QtePrevue) * 100 (optionnel)
# -----------------------------------------------------------
def compute_trs(df_of):
    """
    TRS simplifié : QteRealisee / QtePrevue * 100
    On borne à 100 % max.
    """
    df_of["QtePrevue"] = pd.to_numeric(df_of["QtePrevue"], errors="coerce").fillna(0)
    df_of["QteRealisee"] = pd.to_numeric(df_of["QteRealisee"], errors="coerce").fillna(0)
    df_of["TRS"] = 0.0
    mask = df_of["QtePrevue"] > 0
    df_of.loc[mask, "TRS"] = (df_of["QteRealisee"] / df_of["QtePrevue"]) * 100
    df_of.loc[df_of["TRS"] > 100, "TRS"] = 100
    return df_of

# -----------------------------------------------------------
# 5) Page "Dashboard global"
#    - KPI
#    - Kanban
#    - Pareto
#    - Timeline globale
#    - Filtre par machine
# -----------------------------------------------------------
def page_dashboard():
    st.header("Dashboard Global : Performance & Analyse")

    df_of = load_of_data()
    df_events = load_events_data()
    df_of = compute_trs(df_of)  # calcul du TRS simplifié

    # Choix machine (multi-lignes)
    machines = df_of["Machine"].unique()
    selected_machine = st.selectbox("Filtrer par Machine (ou Toutes)", ["(Toutes)"] + list(machines))

    if selected_machine != "(Toutes)":
        df_of = df_of[df_of["Machine"] == selected_machine]

    # KPI
    nb_en_cours = (df_of["Statut"] == "En cours").sum()
    nb_arret = (df_of["Statut"] == "En arrêt").sum()
    nb_termine = (df_of["Statut"] == "Terminé").sum()
    nb_attente = (df_of["Statut"] == "En attente").sum()

    # TRS moyen
    if len(df_of) > 0:
        trs_moyen = df_of["TRS"].mean()
    else:
        trs_moyen = 0

    df_arrets = df_events[df_events["evenement"] == "Fin Arrêt"]
    nb_arrets = len(df_arrets)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Attente", nb_attente)
    c2.metric("Prod en cours", nb_en_cours)
    c3.metric("En arrêt", nb_arret)
    c4.metric("Terminé", nb_termine)
    c5.metric("Arrêts cumulés", nb_arrets)

    st.markdown("---")

    # TRS moyen
    st.subheader(f"TRS moyen : {trs_moyen:.1f} % (machine = {selected_machine})")

    # Kanban
    st.subheader("Kanban")
    for s in ["En attente", "En cours", "En arrêt", "Terminé"]:
        subset = df_of[df_of["Statut"] == s]
        st.write(f"### {s} ({len(subset)})")
        if not subset.empty:
            # On affiche OF, Description, QtePrevue, QteRealisee, TRS
            sub_copy = subset.copy()
            sub_copy["TRS"] = sub_copy["TRS"].round(1).astype(str) + " %"
            st.table(sub_copy[["OF", "Description", "Machine", "QtePrevue", "QteRealisee", "TRS"]])

    st.markdown("---")

    # Pareto
    st.subheader("Pareto des causes d'arrêts")
    if df_arrets.empty:
        st.info("Aucun arrêt (Fin Arrêt) enregistré, Pareto impossible.")
    else:
        pareto = df_arrets.groupby("type_arret")["timestamp"].count().reset_index(name="count").sort_values("count", ascending=False)
        st.write(pareto)

        fig_pareto, ax = plt.subplots()
        ax.bar(pareto["type_arret"], pareto["count"])
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Occurrences")
        ax.set_title("Pareto des causes d'arrêts")
        st.pyplot(fig_pareto)

    st.markdown("---")

    # Timeline globale
    st.subheader("Timeline globale")
    intervals = build_intervals(df_events, df_of)
    if intervals.empty:
        st.info("Aucun intervalle à afficher.")
    else:
        color_map = {"Production": "green", "Arrêt": "red"}
        fig_global = px.timeline(
            intervals,
            x_start="start",
            x_end="end",
            y="OF",
            color="mode",
            color_discrete_map=color_map,
            hover_data=["commentaire"]
        )
        fig_global.update_yaxes(autorange="reversed")
        fig_global.update_layout(
            title=f"Timeline globale (machine={selected_machine})",
            xaxis_title="Temps",
            yaxis_title="OF"
        )
        st.plotly_chart(fig_global, use_container_width=True)

# -----------------------------------------------------------
# 6) main : navigation
# -----------------------------------------------------------
def main():
    st.set_page_config(layout="wide")
    st.title("Mini-MES Avancé : Production, Arrêts, Quantités, TRS")

    menu = st.sidebar.radio("Navigation", ["Déclaration temps réel", "Dashboard global"])
    if menu == "Déclaration temps réel":
        page_declaration()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()
