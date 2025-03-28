import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

# Configuration de la page
st.set_page_config(
    page_title="Pilotage Atelier",
    page_icon="🏭",
    layout="wide"
)

# Connexion à Supabase (remplacez par vos identifiants)
@st.cache_resource
def init_connection():
    url = "https://htuushiicomwzaisupmx.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0dXVzaGlpY29td3phaXN1cG14Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMyMDAzMDQsImV4cCI6MjA1ODc3NjMwNH0.mAZxwZnaEKax5UxkiZVp7dHW8CRM8d6rPktpLBpN3VU"
    return create_client(url, key)

supabase = init_connection()

# Authentification basique
def login():
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Connexion")
        
        if submit:
            # Dans une vraie application, vérifiez les identifiants
            # contre votre base de données
            if username == "admin" and password == "admin":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Identifiants incorrects")

# Menu principal
def main_menu():
    st.sidebar.title("Menu")
    page = st.sidebar.selectbox(
        "Navigation",
        ["Tableau de bord", "Ordres de fabrication", "Ressources humaines", "Qualité", "Équipements", "Analyses"]
    )
    
    if page == "Tableau de bord":
        dashboard_page()
    elif page == "Ordres de fabrication":
        of_page()
    elif page == "Ressources humaines":
        rh_page()
    elif page == "Qualité":
        quality_page()
    elif page == "Équipements":
        equipment_page()
    elif page == "Analyses":
        analysis_page()

# Pages de l'application
def dashboard_page():
    st.title("Tableau de bord - Pilotage d'Atelier")
    
    # Métriques clés
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Productivité", "85%", "+2%")
    with col2:
        st.metric("Respect délais", "92%", "-3%")
    with col3:
        st.metric("Taux retouche", "4.3%", "+0.5%")
    with col4:
        st.metric("Taux occupation", "78%", "+5%")
    
    # Graphiques
    st.subheader("Productivité par poste")
    # Données fictives pour démonstration
    data = {
        'Poste': ['Assemblage', 'Peinture', 'Contrôle', 'Emballage', 'Usinage'],
        'Productivité': [87, 75, 92, 81, 79]
    }
    df = pd.DataFrame(data)
    st.bar_chart(df.set_index('Poste'))
    
    # Alertes
    st.subheader("Alertes actives")
    st.warning("⚠️ Retard sur OF-2023-45: temps réel > 125% du standard")
    st.warning("⚠️ Absence critique: Jean Dupont (Assemblage) - Formation requise")

def of_page():
    st.title("Gestion des Ordres de Fabrication")
    
    tab1, tab2 = st.tabs(["Liste des OF", "Nouvel OF"])
    
    with tab1:
        # Récupérer les données réelles
        ofs_df = get_all_ofs()
        
        if not ofs_df.empty:
            # Préparation des données pour l'affichage
            if 'date_debut' in ofs_df.columns and pd.api.types.is_datetime64_any_dtype(ofs_df['date_debut']):
                ofs_df['date_debut'] = ofs_df['date_debut'].dt.strftime('%Y-%m-%d')
            
            # Filtres
            col1, col2 = st.columns(2)
            with col1:
                if 'statut' in ofs_df.columns:
                    statut_filter = st.multiselect(
                        "Filtrer par statut", 
                        ofs_df['statut'].unique(), 
                        default=ofs_df['statut'].unique()
                    )
                else:
                    statut_filter = ["Tous"]
            with col2:
                if 'poste' in ofs_df.columns:
                    poste_filter = st.multiselect(
                        "Filtrer par poste", 
                        ofs_df['poste'].unique(), 
                        default=ofs_df['poste'].unique()
                    )
                else:
                    poste_filter = ["Tous"]
            
            # Application des filtres
            filtered_df = ofs_df
            if 'statut' in ofs_df.columns and statut_filter != ["Tous"]:
                filtered_df = filtered_df[filtered_df['statut'].isin(statut_filter)]
            if 'poste' in ofs_df.columns and poste_filter != ["Tous"]:
                filtered_df = filtered_df[filtered_df['poste'].isin(poste_filter)]
            
            # Tri par priorité si disponible
            if 'priorite' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('priorite', ascending=False)
            
            # Afficher le tableau avec barres de progression
            for i, row in filtered_df.iterrows():
                of_num = row.get('numero_of', f"OF-{i}")
                poste = row.get('poste', 'Non spécifié')
                statut = row.get('statut', 'Non spécifié')
                
                with st.expander(f"{of_num} - {poste} ({statut})"):
                    # Progression (si disponible ou simulée)
                    if 'progression' in row:
                        st.progress(row['progression'] / 100)
                    
                    # Informations détaillées
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Opérateur:** {row.get('id_operateur', 'Non assigné')}")
                        st.write(f"**Date de début:** {row.get('date_debut', 'Non définie')}")
                        if 'temps_standard' in row:
                            st.write(f"**Temps standard:** {row['temps_standard']} heures")
                    
                    with col2:
                        st.write(f"**Priorité:** {row.get('priorite', 'Non définie')}")
                        if 'date_fin' in row and pd.notna(row['date_fin']):
                            st.write(f"**Date de fin:** {row['date_fin']}")
                        if 'temps_reel' in row and pd.notna(row['temps_reel']):
                            st.write(f"**Temps réel:** {row['temps_reel']} heures")
                    
                    # Actions
                    action_col1, action_col2, action_col3 = st.columns(3)
                    with action_col1:
                        if st.button("Modifier", key=f"mod_{i}"):
                            st.session_state.edit_of = row.get('id', i)
                            st.rerun()
                    
                    with action_col2:
                        if statut != "Terminé" and st.button("Terminer", key=f"fin_{i}"):
                            # Mettre à jour le statut
                            update_of(row.get('id'), {
                                'statut': 'Terminé',
                                'date_fin': pd.Timestamp.now(),
                                'progression': 100
                            })
                            st.success(f"OF {of_num} marqué comme terminé.")
                            st.rerun()
                    
                    with action_col3:
                        if st.button("Supprimer", key=f"del_{i}"):
                            delete_of(row.get('id'))
                            st.success(f"OF {of_num} supprimé.")
                            st.rerun()
        else:
            st.info("Aucun ordre de fabrication trouvé. Créez-en un avec l'onglet 'Nouvel OF'.")
    
    with tab2:
        with st.form("new_of_form"):
            st.subheader("Créer un nouvel ordre de fabrication")
            
            col1, col2 = st.columns(2)
            with col1:
                of_num = st.text_input("Numéro OF")
                
                # Liste des postes depuis la base de données ou valeurs par défaut
                postes = ["Assemblage", "Peinture", "Usinage", "Contrôle", "Emballage"]
                poste = st.selectbox("Poste", postes)
            
            with col2:
                # Liste des opérateurs depuis la base de données
                operators_df = get_all_operators()
                if not operators_df.empty and 'nom' in operators_df.columns:
                    operateurs = operators_df['nom'].tolist()
                else:
                    operateurs = ["Martin Dubois", "Julie Bernard", "Thomas Petit", "Sophie Grand"]
                
                operateur = st.selectbox("Opérateur", operateurs)
                priorite = st.slider("Priorité", 1, 5, 3)
            
            date_debut = st.date_input("Date de début")
            temps_standard = st.number_input("Temps standard (heures)", min_value=0.1, value=1.0)
            
            submit = st.form_submit_button("Créer OF")
            if submit:
                # Créer un nouvel OF dans la base de données
                new_of = {
                    'numero_of': of_num,
                    'poste': poste,
                    'id_operateur': operateur,
                    'date_debut': date_debut.isoformat(),
                    'temps_standard': temps_standard,
                    'statut': 'Planifié',
                    'priorite': priorite,
                    'progression': 0
                }
                
                create_new_of(new_of)
                st.success(f"OF {of_num} créé avec succès!")
                st.rerun()

# Si un OF est en cours d'édition
if 'edit_of' in st.session_state:
    of_id = st.session_state.edit_of
    # Récupérer les données de l'OF
    of_data = supabase.table('ordres_fabrication').select('*').eq('id', of_id).execute().data
    
    if of_data:
        of = of_data[0]
        st.subheader(f"Modifier OF {of.get('numero_of')}")
        
        with st.form("edit_of_form"):
            col1, col2 = st.columns(2)
            with col1:
                poste = st.selectbox("Poste", ["Assemblage", "Peinture", "Usinage", "Contrôle", "Emballage"], index=["Assemblage", "Peinture", "Usinage", "Contrôle", "Emballage"].index(of.get('poste', "Assemblage")))
                
                operators_df = get_all_operators()
                if not operators_df.empty and 'nom' in operators_df.columns:
                    operateurs = operators_df['nom'].tolist()
                else:
                    operateurs = ["Martin Dubois", "Julie Bernard", "Thomas Petit", "Sophie Grand"]
                
                operateur = st.selectbox("Opérateur", operateurs, index=operateurs.index(of.get('id_operateur')) if of.get('id_operateur') in operateurs else 0)
            
            with col2:
                priorite = st.slider("Priorité", 1, 5, of.get('priorite', 3))
                progression = st.slider("Progression", 0, 100, of.get('progression', 0))
            
            temps_standard = st.number_input("Temps standard (heures)", min_value=0.1, value=of.get('temps_standard', 1.0))
            temps_reel = st.number_input("Temps réel (heures)", min_value=0.0, value=of.get('temps_reel', 0.0))
            
            statut = st.selectbox("Statut", ["Planifié", "En cours", "Terminé"], index=["Planifié", "En cours", "Terminé"].index(of.get('statut', "Planifié")))
            
            save = st.form_submit_button("Enregistrer")
            if save:
                update_data = {
                    'poste': poste,
                    'id_operateur': operateur,
                    'priorite': priorite,
                    'progression': progression,
                    'temps_standard': temps_standard,
                    'temps_reel': temps_reel,
                    'statut': statut,
                }
                
                # Si l'OF est marqué comme terminé, ajouter la date de fin
                if statut == "Terminé" and of.get('statut') != "Terminé":
                    update_data['date_fin'] = pd.Timestamp.now().isoformat()
                
                update_of(of_id, update_data)
                st.success(f"OF {of.get('numero_of')} mis à jour avec succès!")
                
                # Réinitialiser l'état d'édition et rafraîchir
                del st.session_state.edit_of
                st.rerun()
        
        if st.button("Annuler"):
            del st.session_state.edit_of
            st.rerun()
def rh_page():
    st.title("Gestion des Ressources Humaines")
    st.write("Cette page permettra de gérer les opérateurs, leurs compétences et présences.")
    
    # Tableau de polyvalence (exemple)
    st.subheader("Tableau de polyvalence")
    
    data = {
        'Opérateur': ['Martin Dubois', 'Julie Bernard', 'Thomas Petit', 'Sophie Grand'],
        'Assemblage': [3, 2, 1, 3],
        'Peinture': [1, 3, 0, 2],
        'Usinage': [2, 1, 3, 0],
        'Contrôle': [2, 2, 2, 3],
        'Emballage': [3, 3, 1, 2]
    }
    df = pd.DataFrame(data)
    
    # Affichage sous forme de heatmap
    df_heatmap = df.set_index('Opérateur')
    fig = px.imshow(df_heatmap, 
                    text_auto=True, 
                    color_continuous_scale='Blues',
                    labels=dict(x="Poste", y="Opérateur", color="Niveau"))
    st.plotly_chart(fig, use_container_width=True)
    
    # Gestion des absences
    st.subheader("Déclarer une absence")
    with st.form("absence_form"):
        col1, col2 = st.columns(2)
        with col1:
            operateur = st.selectbox("Opérateur", df['Opérateur'])
            date_debut = st.date_input("Date de début", datetime.date.today())
        with col2:
            motif = st.selectbox("Motif", ["Maladie", "Congé", "Formation", "Autre"])
            date_fin = st.date_input("Date de fin", datetime.date.today() + datetime.timedelta(days=1))
        
        st.form_submit_button("Enregistrer")

def quality_page():
    st.title("Suivi Qualité")
    st.write("Suivi des défauts et des retouches")
    
    # Exemple de données
    data = {
        'Date': ['2023-10-15', '2023-10-15', '2023-10-16', '2023-10-17', '2023-10-17'],
        'OF': ['OF-2023-42', 'OF-2023-42', 'OF-2023-43', 'OF-2023-45', 'OF-2023-46'],
        'Poste': ['Assemblage', 'Assemblage', 'Peinture', 'Contrôle', 'Usinage'],
        'Type défaut': ['Vissage incorrect', 'Pièce manquante', 'Surface irrégulière', 'Dimensions hors tolérance', 'Finition brute'],
        'Gravité': ['Moyenne', 'Majeure', 'Mineure', 'Majeure', 'Mineure']
    }
    df = pd.DataFrame(data)
    
    # Graphique des défauts par poste
    st.subheader("Défauts par poste")
    counts = df['Poste'].value_counts().reset_index()
    counts.columns = ['Poste', 'Nombre de défauts']
    st.bar_chart(counts.set_index('Poste'))
    
    # Formulaire de déclaration de défaut
    st.subheader("Déclarer un nouveau défaut")
    with st.form("defect_form"):
        col1, col2 = st.columns(2)
        with col1:
            of = st.text_input("Numéro OF")
            poste = st.selectbox("Poste concerné", ["Assemblage", "Peinture", "Usinage", "Contrôle", "Emballage"])
        with col2:
            type_defaut = st.text_input("Type de défaut")
            gravite = st.select_slider("Gravité", options=["Mineure", "Moyenne", "Majeure"])
        
        description = st.text_area("Description du défaut")
        action = st.text_area("Action corrective")
        
        st.form_submit_button("Enregistrer")

def equipment_page():
    st.title("Gestion des Équipements")
    
    # État des machines
    st.subheader("État des machines")
    
    data = {
        'Machine': ['Machine 1', 'Machine 2', 'Machine 3', 'Machine 4', 'Machine 5'],
        'Statut': ['En production', 'En maintenance', 'En production', 'Arrêtée', 'En production'],
        'Dernière maintenance': ['2023-09-15', '2023-10-17', '2023-10-01', '2023-09-20', '2023-10-10'],
        'Prochaine maintenance': ['2023-11-15', '2023-12-17', '2023-12-01', '2023-11-20', '2023-12-10'],
        'Taux utilisation': [85, 0, 92, 0, 78]
    }
    df = pd.DataFrame(data)
    
    for i, row in df.iterrows():
        color = "green" if row['Statut'] == "En production" else "orange" if row['Statut'] == "En maintenance" else "red"
        
        st.markdown(f"""
        <div style="border-left: 5px solid {color}; padding-left: 10px;">
            <h3>{row['Machine']} - <span style="color: {color};">{row['Statut']}</span></h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Dernière maintenance:** {row['Dernière maintenance']}")
        with col2:
            st.write(f"**Prochaine maintenance:** {row['Prochaine maintenance']}")
        with col3:
            st.write(f"**Taux d'utilisation:** {row['Taux utilisation']}%")
        
        # Boutons d'action
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            st.button("Déclarer panne", key=f"panne_{i}")
        with action_col2:
            st.button("Planifier maintenance", key=f"maint_{i}")
        with action_col3:
            st.button("Voir historique", key=f"hist_{i}")
        
        st.markdown("---")

def analysis_page():
    st.title("Analyses et Simulations")
    
    st.subheader("Charge vs Capacité")
    
    # Données fictives pour le graphique
    dates = pd.date_range(start="2023-10-01", end="2023-10-31", freq="D")
    capacite = [40] * len(dates)
    charge = [38, 35, 42, 39, 36, 30, 28, 45, 43, 41, 37, 36, 39, 40, 
              42, 44, 37, 35, 33, 30, 36, 38, 41, 43, 45, 42, 39, 37, 36, 35, 34]
    
    df = pd.DataFrame({
        'Date': dates,
        'Capacité (h)': capacite,
        'Charge (h)': charge
    })
    
    fig = px.line(df, x='Date', y=['Capacité (h)', 'Charge (h)'])
    st.plotly_chart(fig, use_container_width=True)
    
    # Section de simulation
    st.subheader("Simulation \"Et si...\"")
    
    with st.form("simulation_form"):
        st.write("Simulez l'impact d'un changement sur votre production")
        
        col1, col2 = st.columns(2)
        with col1:
            scenario = st.selectbox("Type de scénario", [
                "Absence d'un opérateur clé", 
                "Ajout d'un opérateur", 
                "Panne machine", 
                "Commande urgente"
            ])
        with col2:
            duree = st.slider("Durée (jours)", 1, 14, 5)
        
        if scenario == "Absence d'un opérateur clé":
            operateur = st.selectbox("Opérateur absent", ["Martin Dubois", "Julie Bernard", "Thomas Petit"])
        elif scenario == "Panne machine":
            machine = st.selectbox("Machine en panne", ["Machine 1", "Machine 2", "Machine 3"])
        elif scenario == "Commande urgente":
            volume = st.number_input("Volume (heures)", min_value=1, value=24)
        
        submit = st.form_submit_button("Simuler")
        
        if submit:
            st.info("Simulation en cours... Cette fonctionnalité sera implémentée dans une version future.")
            st.metric("Impact sur les délais", "+2 jours")
            st.metric("Taux d'occupation", "92%", "+14%")
def add_exports_to_sidebar():
    with st.sidebar.expander("Exporter des données"):
        export_type = st.selectbox(
            "Type de données à exporter",
            ["Ordres de fabrication", "Ressources humaines", "Qualité", "Équipements"]
        )
        
        date_range = st.date_input(
            "Période (optionnel)",
            value=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now()),
            help="Laissez vide pour tout exporter"
        )
        
        if st.button("Exporter en CSV"):
            # Récupérer les données selon le type
            if export_type == "Ordres de fabrication":
                data = get_all_ofs()
                filename = "ordres_fabrication.csv"
            elif export_type == "Ressources humaines":
                data = get_all_operators()
                filename = "ressources_humaines.csv"
            elif export_type == "Qualité":
                data = get_all_defects()
                filename = "qualite.csv"
            else:  # Équipements
                data = get_all_equipment()
                filename = "equipements.csv"
            
            # Filtrer par date si applicable
            if not data.empty and 'date_debut' in data.columns:
                start_date, end_date = date_range
                data = data[(data['date_debut'] >= pd.Timestamp(start_date)) & 
                           (data['date_debut'] <= pd.Timestamp(end_date))]
            
            # Vérifier si des données existent
            if not data.empty:
                # Convertir en CSV
                csv = data.to_csv(index=False)
                
                # Bouton de téléchargement
                st.download_button(
                    label="Télécharger CSV",
                    data=csv,
                    file_name=filename,
                    mime='text/csv',
                )
            else:
                st.error("Aucune donnée disponible pour cette sélection")

# Ajoutez ceci à votre fonction main_menu
def main_menu():
    st.sidebar.title("Menu")
    page = st.sidebar.selectbox(
        "Navigation",
        ["Tableau de bord", "Ordres de fabrication", "Ressources humaines", "Qualité", "Équipements", "Analyses"]
    )
    
    # Ajouter les exports
    add_exports_to_sidebar()
    
    # Afficher l'utilisateur connecté
    if "user" in st.session_state:
        st.sidebar.write(f"Connecté en tant que: **{st.session_state.user['username']}**")
        if st.sidebar.button("Déconnexion"):
            st.session_state.logged_in = False
            st.session_state.pop("user", None)
            st.rerun()
    
    # Afficher la page sélectionnée
    if page == "Tableau de bord":
        dashboard_page()
    elif page == "Ordres de fabrication":
        of_page()
    elif page == "Ressources humaines":
        rh_page()
    elif page == "Qualité":
        quality_page()
    elif page == "Équipements":
        equipment_page()
    elif page == "Analyses":
        analysis_page()
# Application principale
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.title("Système Intelligent de Pilotage d'Atelier")
        login()
    else:
        main_menu()

if __name__ == "__main__":
    main()
