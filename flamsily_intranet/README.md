# Flamsily

Intranet simple en **Streamlit** avec :

- lien d'invitation personnel
- première connexion avec formulaire :
  - prénom
  - nom
  - dans quelle Flam's la personne a travaillé
  - âge
  - e-mail
  - téléphone facultatif
- création automatique d'un compte personnel
- page d'accueil avec actualités
- page profil utilisateur
- mini panneau admin pour :
  - générer les liens d'invitation
  - publier des actualités

## Structure

```txt
flamsily_intranet/
├── .streamlit/
│   └── secrets.toml.example
├── data/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Lancer en local

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
streamlit run app.py
```

## Variables de configuration

Créer `.streamlit/secrets.toml` à partir de `secrets.toml.example` :

```toml
APP_BASE_URL = "http://localhost:8501"
ADMIN_SECRET = "votre-cle-admin-secrete"
INVITE_SENDER_NAME = "Flamsily"
```

## Utilisation

### 1) Connexion admin
Dans la barre latérale, saisir la **clé admin** définie dans `ADMIN_SECRET`.

### 2) Générer un lien d'invitation
Dans **Administration > Créer un lien d'invitation**, saisir l'e-mail du collaborateur.
Le système génère un lien du type :

```txt
http://localhost:8501/?token=xxxxxxxx
```

Ce lien peut être envoyé par mail, WhatsApp ou tout autre canal.

### 3) Première connexion utilisateur
Le collaborateur ouvre le lien et complète le formulaire.
Son compte personnel est activé automatiquement.

### 4) Espace utilisateur
Après inscription :
- **Accueil** : actualités internes
- **Mon profil** : informations personnelles

## Déploiement GitHub + Streamlit Community Cloud

1. Créer un dépôt GitHub
2. Pousser ce projet dans le dépôt
3. Aller sur Streamlit Community Cloud
4. Connecter le dépôt GitHub
5. Déployer `app.py`
6. Ajouter les secrets dans l'interface Streamlit :

```toml
APP_BASE_URL = "https://votre-app.streamlit.app"
ADMIN_SECRET = "une-cle-forte"
INVITE_SENDER_NAME = "Flamsily"
```

## Évolutions possibles

- envoi automatique des invitations par e-mail SMTP
- rôles utilisateur (employé / manager / admin)
- modification du profil
- pièces jointes RH
- annuaire interne
- stockage PostgreSQL au lieu de SQLite
- authentification GitHub OAuth / Google OAuth
