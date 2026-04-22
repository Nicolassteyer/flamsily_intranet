# Flamsily - version simple

Application intranet simple en Streamlit.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Crée le fichier `.streamlit/secrets.toml` :

```toml
APP_BASE_URL = "http://localhost:8501"
ADMIN_SECRET = "ma-cle-admin"
```

## Lancer l'application

```bash
streamlit run app.py
```

## Fonctionnement

### 1) Admin
- Ouvre l'application.
- Clique sur **Connexion administrateur** au centre.
- Entre la valeur de `ADMIN_SECRET`.
- Dans **Créer un lien**, saisis l'e-mail puis clique sur **Générer le lien**.
- Envoie le lien au collaborateur.

### 2) Collaborateur
- Ouvre le lien reçu.
- Remplit le formulaire de première connexion.
- Son compte est créé automatiquement.
- Ensuite il voit :
  - Accueil
  - Mon profil

### 3) Connexions suivantes
- Le collaborateur peut réutiliser son lien/token pour revenir sur son espace.

## Déploiement GitHub + Streamlit Cloud

1. Mets ces fichiers dans un dépôt GitHub.
2. Va sur Streamlit Community Cloud.
3. Connecte ton dépôt GitHub.
4. Choisis `app.py`.
5. Ajoute les secrets :

```toml
APP_BASE_URL = "https://ton-app.streamlit.app"
ADMIN_SECRET = "ma-cle-admin"
```
