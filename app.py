import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates  # Pour gérer les dates dans le Gantt
from datetime import datetime

# ------------------------------------------
# 1) Les chemins vers nos CSV
# ------------------------------------------
OF_CSV = "data/of_list.csv"
EVENTS_CSV = "data/events.csv"


# ------------------------------------------
# 2) Fonctions de lecture / écriture CSV
# ------------------------------------------
def load_of_data():
    """Charge la liste d'OF (avec Duree_prevue)."""
    return pd.read_csv(OF_CSV)

def load_events_data():
    """Charge l'historique (début, fin, arrêts...)."""
    try:
        return pd.read_csv(EVENTS_CSV)
    except FileNotFoundError:
        return pd.DataFrame(columns=["timestamp", "OF", "evenement", "commentaire"])

def save_of_data(df):
    df.to_csv(OF_CSV, index=False)

def save_events_data(df):
    df.to_csv(EVENTS_CSV, index=False)


# ------------------------------------------
# 3) Calculer le Gantt et la progression
# ------------------------------------------
def compute_times_and_progress(df_of, df_events):
    """
    - Trouve le dernier "Début OF" et la "Fin OF" pour chaque OF
    - Calcule le temps réellement passé (si terminé) ou le temps en cours (si pas terminé)
    - En déduit un pourcentage d'avancement = (temps passé / Duree_prevue) * 100
      (on limite à 100% si ça dépasse)
    - Prépare aussi les dates "start_dt" et "end_dt" pour tracer un Gantt
       * Si un OF est "En cours" => end_dt = maintenant
       * Si un OF est "Terminé" => end_dt = timestamp du dernier "Fin OF"
       * Sinon, si "En attente", on met rien
    Retourne df_of avec les colonnes supplémentaires : start_dt, end_dt, progress
    """

    # On va ajouter ces colonnes :
    df_of["start_dt"] = pd.NaT
    df_of["end_dt"] = pd.NaT
    df_of["progress"] = 0.0  # En pourcentage

    # Convertir la colonne "Duree_prevue" en numérique (au cas où)
    # On suppose qu'elle est en minutes
    df_of["Duree_prevue"] = pd.to_numeric(df_of["Duree_prevue"], errors="coerce").fillna(0)

    # Convertir timestamp en datetime
    df_events["timestamp_dt"] = pd.to_datetime(df_events["timestamp"], errors="coerce")

    for i, row in df_of.iterrows():
        of_id = row["OF"]
        statut = row["Statut"]
        duree_prevue = row["Duree_prevue"]

        # Tous les événements de cet OF (triés par date)
        subset = df_events[df_events["OF"] == of_id].sort_values("timestamp_dt")

        # On cherche le dernier "Début OF"
        debuts = subset[subset["evenement"] == "Début OF"]
        if not debuts.empty:
            last_start_ts = debuts.iloc[-1]["timestamp_dt"]
            df_of.at[i, "start_dt"] = last_start_ts

        # On cherche le dernier "Fin OF"
        fins = subset[subset["evenement"] == "Fin OF"]
        if not fins.empty:
            last_end_ts = fins.iloc[-1]["timestamp_dt"]
        else:
            last_end_ts = pd.NaT

        # Selon le statut, on détermine end_dt
        if statut == "En cours":
            # On est en cours => end_dt = maintenant
            df_of.at[i, "end_dt"] = datetime.now()
        elif statut == "Terminé" and not pd.isna(last_end_ts):
            # Terminé => end_dt = la date du dernier "Fin OF"
            df_of.at[i, "end_dt"] = last_end_ts
        else:
            # En attente ou pas de start => pas de Gantt
            # (on laisse NaT)
            pass

        # Calcul du temps passé
        start_val = df_of.at[i, "start_dt"]
        end_val = df_of.at[i, "end_dt"]
        if pd.notna(start_val) and pd.notna(end_val) and duree_prevue > 0:
            delta = end_val - start_val
            delta_minutes = delta.total_seconds() / 60.0
            # Pourcentage d'avancement
            progress_pct = (delta_minutes / duree_prevue) * 100
            if progress_pct > 100:
                progress_pct = 100
            df_of.at[i, "progress"] = progress_pct

    return df_of


# ------------------------------------------
# 4) Page : Déclaration des actions
# ------------------------------------------
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

    # Bouton "Démarrer l'OF"
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
        st.success(f"OF {selected_of} démarré.")

    # Bouton "Terminer l'OF"
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
        st.success(f"OF {selected_of} terminé.")

    # Déclarer un arrêt (défaut, etc.)
    st.subheader("Déclarer un arrêt ou défaut")
    arret_choice = st.selectbox("Type d'arrêt", ["Qualité", "Manque de charge", "Manque personnel", "Réunion", "Formation"])
    commentaire_arret = st.text_input("Commentaire")

    if st.button("Enregistrer l'arrêt"):
        new_event = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "OF": selected_of,
            "evenement": arret_choice,
            "commentaire": commentaire_arret
        }
        df_new = pd.DataFrame([new_event])
        df_events = pd.concat([df_events, df_new], ignore_index=True)

        # On NE modifie PAS le statut de l'OF (il reste "En cours" si vous voulez qu'il tourne toujours)
        # df_of.loc[df_of["OF"] == selected_of, "Statut"] = "En pause"  # <-- Commenté

        save_of_data(df_of)
        save_events_data(df_events)
        st.success(f"Arrêt '{arret_choice}' enregistré pour l'OF {selected_of}.")


# ------------------------------------------
# 5) Page : Kanban, Pareto, Gantt
# ------------------------------------------
def page_kanban_pareto_gantt():
    st.header("Vue Kanban, Performance & Gantt")

    df_of = load_of_data()
    df_events = load_events_data()

    # Calculer les colonnes start_dt / end_dt / progress
    df_of = compute_times_and_progress(df_of, df_events)

    # -- Kanban simple : affichage par statut
    st.subheader("Kanban des OF")
    statuts = df_of["Statut"].unique()

    for s in statuts:
        st.write(f"### {s}")
        subset = df_of[df_of["Statut"] == s].copy()

        # On affiche dans ce tableau : OF, Description, Duree_prevue, progress
        # progress = progression en %, on peut arrondir
        subset["progress"] = subset["progress"].round(1).astype(str) + " %"
        st.write(subset[["OF", "Description", "Duree_prevue", "progress"]])

    # -- Pareto des arrêts
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

        fig, ax = plt.subplots()
        ax.bar(pareto["evenement"], pareto["count"])
        ax.set_xlabel("Type d'arrêt")
        ax.set_ylabel("Nombre d'occurrences")
        ax.set_title("Pareto des causes d'arrêts")
        st.pyplot(fig)

    # -- Diagramme de Gantt
    st.subheader("Diagramme de Gantt")

    # On récupère seulement les OF qui ont start_dt et end_dt non NaN
    df_gantt = df_of.dropna(subset=["start_dt", "end_dt"]).copy()
    if df_gantt.empty:
        st.info("Aucun OF en cours ou terminé pour tracer un Gantt.")
        return

    # Convertir en format numérique pour matplotlib
    df_gantt["start_num"] = df_gantt["start_dt"].apply(mdates.date2num)
    df_gantt["end_num"] = df_gantt["end_dt"].apply(mdates.date2num)
    df_gantt["duration"] = df_gantt["end_num"] - df_gantt["start_num"]

    fig_gantt, ax_gantt = plt.subplots(figsize=(8, 4))
    # Pour tracer un barh : on fait une boucle
    # OU on peut faire un barh direct sur le DataFrame
    y_labels = df_gantt["OF"].tolist()
    y_pos = range(len(df_gantt))  # 0,1,2,...
    for i, row in df_gantt.iterrows():
        ax_gantt.barh(
            y=i,
            width=row["duration"],
            left=row["start_num"],
            height=0.4,  # épaisseur de la barre
            align='center'
        )
        # On peut aussi ajouter un texte (OF, progression, etc.) sur la barre

    ax_gantt.set_yticks(list(y_pos))
    ax_gantt.set_yticklabels(y_labels)
    ax_gantt.invert_yaxis()  # Optionnel, pour que le premier OF soit en haut

    ax_gantt.xaxis_date()  # Indique à matplotlib qu'on manipule des dates
    ax_gantt.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    fig_gantt.autofmt_xdate()

    ax_gantt.set_xlabel("Temps")
    ax_gantt.set_ylabel("OF")
    ax_gantt.set_title("Diagramme de Gantt (début-fin)")

    st.pyplot(fig_gantt)


# ------------------------------------------
# 6) Navigation principale
# ------------------------------------------
def main():
    st.title("Mini-MES : Suivi de Production")
    page = st.sidebar.selectbox(
        "Navigation",
        ["Déclaration temps réel", "Kanban / Pareto / Gantt"]
    )

    if page == "Déclaration temps réel":
        page_declaration()
    else:
        page_kanban_pareto_gantt()

if __name__ == "__main__":
    main()
