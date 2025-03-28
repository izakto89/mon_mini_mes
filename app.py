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
                st.experimental_rerun()
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
        # Simuler des données d'OF
        data = {
            'Numéro': ['OF-2023-45', 'OF-2023-46', 'OF-2023-47', 'OF-2023-48'],
            'Poste': ['Assemblage', 'Peinture', 'Usinage', 'Contrôle'],
            'Opérateur': ['Martin Dubois', 'Julie Bernard', 'Thomas Petit', 'Sophie Grand'],
            'Date début': ['2023-10-15', '2023-10-16', '2023-10-16', '2023-10-17'],
            'Statut': ['En cours', 'Planifié', 'En cours', 'Terminé'],
            'Progression': [75, 0, 30, 100]
        }
        df = pd.DataFrame(data)
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            statut_filter = st.multiselect("Filtrer par statut", df['Statut'].unique(), default=df['Statut'].unique())
        with col2:
            poste_filter = st.multiselect("Filtrer par poste", df['Poste'].unique(), default=df['Poste'].unique())
        
        filtered_df = df[(df['Statut'].isin(statut_filter)) & (df['Poste'].isin(poste_filter))]
        
        # Afficher le tableau avec barres de progression
        for i, row in filtered_df.iterrows():
            with st.expander(f"{row['Numéro']} - {row['Poste']} ({row['Statut']})"):
                st.progress(row['Progression'] / 100)
                st.write(f"**Opérateur:** {row['Opérateur']}")
                st.write(f"**Date de début:** {row['Date début']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Modifier", key=f"mod_{i}")
                with col2:
                    st.button("Terminer", key=f"fin_{i}")
    
    with tab2:
        with st.form("new_of_form"):
            st.subheader("Créer un nouvel ordre de fabrication")
            
            col1, col2 = st.columns(2)
            with col1:
                of_num = st.text_input("Numéro OF")
                poste = st.selectbox("Poste", ["Assemblage", "Peinture", "Usinage", "Contrôle", "Emballage"])
            with col2:
                operateur = st.selectbox("Opérateur", ["Martin Dubois", "Julie Bernard", "Thomas Petit", "Sophie Grand"])
                priorite = st.slider("Priorité", 1, 5, 3)
            
            date_debut = st.date_input("Date de début")
            temps_standard = st.number_input("Temps standard (heures)", min_value=0.1, value=1.0)
            
            submit = st.form_submit_button("Créer OF")
            if submit:
                st.success(f"OF {of_num} créé avec succès!")

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
