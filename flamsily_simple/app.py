import os
import sqlite3
import secrets
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Flamsily", page_icon="🔥", layout="wide")

DB_PATH = Path("data/flamsily.db")
DB_PATH.parent.mkdir(exist_ok=True)

APP_BASE_URL = st.secrets.get("APP_BASE_URL", "http://localhost:8501")
ADMIN_SECRET = st.secrets.get("ADMIN_SECRET", "change-moi")
APP_NAME = "Flamsily"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invites (
        token TEXT PRIMARY KEY,
        email TEXT,
        created_at TEXT,
        used_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        token TEXT PRIMARY KEY,
        prenom TEXT NOT NULL,
        nom TEXT NOT NULL,
        flams TEXT NOT NULL,
        age INTEGER NOT NULL,
        email TEXT NOT NULL,
        telephone TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        contenu TEXT NOT NULL,
        created_at TEXT
    )
    """)

    cur.execute("SELECT COUNT(*) FROM news")
    count = cur.fetchone()[0]
    if count == 0:
        samples = [
            ("Bienvenue sur Flamsily", "Votre intranet est en ligne. Ici, vous retrouverez les actualités et votre profil personnel."),
            ("Première connexion", "Lors de la première visite, chaque collaborateur remplit son formulaire. Ensuite, il retrouve directement son espace personnel.")
        ]
        for titre, contenu in samples:
            cur.execute("INSERT INTO news (titre, contenu, created_at) VALUES (?, ?, ?)", (titre, contenu, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_query_token():
    try:
        return st.query_params.get("token")
    except Exception:
        params = st.experimental_get_query_params()
        return params.get("token", [None])[0]


def set_query_token(token: str):
    try:
        st.query_params["token"] = token
    except Exception:
        st.experimental_set_query_params(token=token)


def clear_query_token():
    try:
        if "token" in st.query_params:
            del st.query_params["token"]
    except Exception:
        st.experimental_set_query_params()


def get_user(token):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT token, prenom, nom, flams, age, email, telephone, created_at FROM users WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    return row


def get_invite(token):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT token, email, created_at, used_at FROM invites WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    return row


def create_invite(email):
    token = secrets.token_urlsafe(16)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO invites (token, email, created_at, used_at) VALUES (?, ?, ?, ?)",
        (token, email, datetime.utcnow().isoformat(), None)
    )
    conn.commit()
    conn.close()
    return token


def mark_invite_used(token):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE invites SET used_at = ? WHERE token = ?", (datetime.utcnow().isoformat(), token))
    conn.commit()
    conn.close()


def create_user(token, prenom, nom, flams, age, email, telephone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO users (token, prenom, nom, flams, age, email, telephone, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (token, prenom, nom, flams, age, email, telephone, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    mark_invite_used(token)


def get_news():
    conn = get_conn()
    df = pd.read_sql_query("SELECT titre, contenu, created_at FROM news ORDER BY id DESC", conn)
    conn.close()
    return df


def add_news(titre, contenu):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO news (titre, contenu, created_at) VALUES (?, ?, ?)", (titre, contenu, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def list_users():
    conn = get_conn()
    df = pd.read_sql_query("SELECT prenom, nom, flams, age, email, telephone, created_at FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df


def center_card_open():
    st.markdown("""
    <style>
        .main > div {padding-top: 2rem;}
        [data-testid="stSidebar"] {display: none;}
        .fl-card {
            max-width: 760px;
            margin: 2rem auto;
            padding: 2.2rem 2rem;
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(16,24,40,.98), rgba(11,18,32,.98));
            border: 1px solid rgba(255,255,255,.07);
            box-shadow: 0 20px 50px rgba(0,0,0,.25);
        }
        .fl-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: .4rem;
        }
        .fl-sub {
            color: #b7c1d1;
            margin-bottom: 1.2rem;
        }
        .fl-badge {
            display: inline-block;
            background: rgba(59,130,246,.15);
            border: 1px solid rgba(59,130,246,.25);
            color: #93c5fd;
            padding: .35rem .7rem;
            border-radius: 999px;
            font-size: .9rem;
            margin-bottom: 1rem;
        }
        .small-muted {color:#9aa4b2; font-size:.95rem;}
    </style>
    <div class="fl-card">
    """, unsafe_allow_html=True)


def center_card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def render_login():
    center_card_open()
    st.markdown(f'<div class="fl-badge">🔥 {APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="fl-title">Connexion à votre intranet</div>', unsafe_allow_html=True)
    st.markdown('<div class="fl-sub">Entrez votre lien personnel ou votre token de connexion.</div>', unsafe_allow_html=True)

    existing = get_query_token() or ""
    with st.form("login_form", clear_on_submit=False):
        token_input = st.text_input("Lien de connexion ou token", value=existing, placeholder="Collez ici le lien complet ou juste le token")
        submitted = st.form_submit_button("Se connecter", use_container_width=True)

    if submitted:
        value = (token_input or "").strip()
        if "token=" in value:
            token = value.split("token=", 1)[1].split("&", 1)[0].strip()
        else:
            token = value

        if not token:
            st.error("Ajoute un lien ou un token.")
        else:
            if get_invite(token) or get_user(token):
                st.session_state["token"] = token
                set_query_token(token)
                st.rerun()
            else:
                st.error("Lien invalide. Demande un nouveau lien à l’administrateur.")

    st.markdown("---")
    with st.expander("Connexion administrateur"):
        with st.form("admin_form"):
            admin_key = st.text_input("Clé admin", type="password")
            admin_submitted = st.form_submit_button("Ouvrir l’administration", use_container_width=True)

        if admin_submitted:
            if admin_key == ADMIN_SECRET:
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                st.error("Clé admin incorrecte.")

    st.markdown('<div class="small-muted">Première visite : le collaborateur ouvre son lien, remplit son profil, puis retrouve ensuite directement son espace personnel.</div>', unsafe_allow_html=True)
    center_card_close()


def render_registration(token, invite):
    center_card_open()
    st.markdown('<div class="fl-badge">Première connexion</div>', unsafe_allow_html=True)
    st.markdown('<div class="fl-title">Complétez votre profil</div>', unsafe_allow_html=True)
    st.markdown('<div class="fl-sub">Une seule fois. Ensuite vous accéderez directement à votre espace.</div>', unsafe_allow_html=True)

    default_email = invite[1] if invite and invite[1] else ""

    with st.form("register_form"):
        col1, col2 = st.columns(2)
        prenom = col1.text_input("Prénom")
        nom = col2.text_input("Nom")
        flams = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
        col3, col4 = st.columns(2)
        age = col3.number_input("Âge", min_value=14, max_value=100, value=18)
        email = col4.text_input("E-mail", value=default_email)
        telephone = st.text_input("Numéro de téléphone (facultatif)")
        submitted = st.form_submit_button("Créer mon compte", use_container_width=True)

    if submitted:
        if not prenom or not nom or not flams or not email:
            st.error("Merci de remplir tous les champs obligatoires.")
        else:
            create_user(token, prenom, nom, flams, int(age), email, telephone)
            st.success("Compte créé avec succès.")
            st.rerun()
    center_card_close()


def render_home(user):
    prenom, nom = user[1], user[2]
    st.markdown(f"## Bonjour {prenom}")
    st.write("Bienvenue sur votre intranet Flamsily.")
    st.info("Vous pouvez consulter les actualités ci-dessous et accéder à votre profil dans l’onglet dédié.")

    news = get_news()
    if news.empty:
        st.write("Aucune actualité pour le moment.")
    else:
        for _, row in news.iterrows():
            with st.container(border=True):
                st.subheader(row["titre"])
                st.write(row["contenu"])
                st.caption(f"Publié le : {row['created_at'][:19].replace('T',' ')}")


def render_profile(user):
    _, prenom, nom, flams, age, email, telephone, created_at = user
    st.markdown("## Mon profil")
    c1, c2 = st.columns(2)
    c1.metric("Prénom", prenom)
    c2.metric("Nom", nom)
    c1.metric("Flam's", flams)
    c2.metric("Âge", age)
    c1.write(f"**E-mail** : {email}")
    c2.write(f"**Téléphone** : {telephone or 'Non renseigné'}")
    st.caption(f"Compte créé le : {created_at[:19].replace('T',' ')}")


def render_admin():
    st.markdown("## Administration")
    st.write("Ici vous créez les liens d’inscription et publiez les actualités.")

    tab1, tab2, tab3 = st.tabs(["Créer un lien", "Publier une actualité", "Voir les inscrits"])

    with tab1:
        with st.form("invite_form"):
            email = st.text_input("E-mail du collaborateur")
            submitted = st.form_submit_button("Générer le lien", use_container_width=True)
        if submitted:
            token = create_invite(email)
            link = f"{APP_BASE_URL}?token={token}"
            st.success("Lien généré.")
            st.code(link, language=None)
            st.write("Envoie ce lien à la personne. À sa première ouverture, elle remplit son profil.")

    with tab2:
        with st.form("news_form"):
            titre = st.text_input("Titre")
            contenu = st.text_area("Contenu")
            sub = st.form_submit_button("Publier", use_container_width=True)
        if sub:
            if not titre or not contenu:
                st.error("Titre et contenu obligatoires.")
            else:
                add_news(titre, contenu)
                st.success("Actualité publiée.")

    with tab3:
        users = list_users()
        if users.empty:
            st.write("Aucun inscrit pour le moment.")
        else:
            st.dataframe(users, use_container_width=True)


def main():
    init_db()

    token = st.session_state.get("token") or get_query_token()
    is_admin = st.session_state.get("is_admin", False)

    if is_admin and not token:
        render_admin()
        st.divider()
        if st.button("Fermer l’administration"):
            st.session_state["is_admin"] = False
            st.rerun()
        return

    if not token:
        render_login()
        return

    user = get_user(token)
    invite = get_invite(token)

    if not user:
        if invite:
            render_registration(token, invite)
            return
        else:
            st.session_state.pop("token", None)
            clear_query_token()
            st.error("Lien invalide ou inconnu.")
            render_login()
            return

    # user connected
    st.sidebar.title("Flamsily")
    st.sidebar.write(f"Connecté : {user[1]} {user[2]}")
    page = st.sidebar.radio("Navigation", ["Accueil", "Mon profil"])
    if st.sidebar.button("Se déconnecter"):
        st.session_state.pop("token", None)
        clear_query_token()
        st.rerun()

    if page == "Accueil":
        render_home(user)
    elif page == "Mon profil":
        render_profile(user)


if __name__ == "__main__":
    main()
