import os
import sqlite3
import secrets
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

DB_PATH = Path("data/flamsily.db")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "change-me")
INVITE_SENDER_NAME = os.getenv("INVITE_SENDER_NAME", "Flamsily")


# ----------------------------
# Database helpers
# ----------------------------
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        flams_worked TEXT NOT NULL,
        age INTEGER NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        invite_token TEXT NOT NULL UNIQUE,
        is_registered INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        published_at TEXT NOT NULL,
        author TEXT NOT NULL
    )
    """)

    conn.commit()

    cur.execute("SELECT COUNT(*) AS c FROM news")
    if cur.fetchone()["c"] == 0:
        seed_news = [
            (
                "Bienvenue sur Flamsily",
                "Votre nouvel intranet est en ligne. Vous pouvez retrouver ici les actualités internes et votre profil personnel.",
                datetime.utcnow().isoformat(),
                "Équipe Flamsily",
            ),
            (
                "Nouvelle procédure d'accueil",
                "Chaque collaborateur reçoit désormais un lien d'accès personnel pour compléter ses informations lors de sa première connexion.",
                datetime.utcnow().isoformat(),
                "Administration",
            ),
        ]
        cur.executemany(
            "INSERT INTO news(title, content, published_at, author) VALUES (?, ?, ?, ?)",
            seed_news,
        )
        conn.commit()

    conn.close()


# ----------------------------
# Invite helpers
# ----------------------------
def generate_token():
    return secrets.token_urlsafe(24)


def build_invite_link(token: str) -> str:
    return f"{APP_BASE_URL}?token={token}"


def create_invite_shell(email: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    token = generate_token()

    cur.execute("SELECT id, invite_token FROM users WHERE email = ?", (email.lower().strip(),))
    existing = cur.fetchone()

    if existing:
        cur.execute(
            "UPDATE users SET invite_token = ?, updated_at = ? WHERE id = ?",
            (token, now, existing["id"])
        )
    else:
        cur.execute("""
            INSERT INTO users (
                first_name, last_name, flams_worked, age, email, phone,
                invite_token, is_registered, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, ("", "", "", 0, email.lower().strip(), "", token, now, now))

    conn.commit()
    conn.close()
    return token, build_invite_link(token)


def get_user_by_token(token: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE invite_token = ?", (token,))
    user = cur.fetchone()
    conn.close()
    return user


def save_registration(token, first_name, last_name, flams_worked, age, email, phone):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE users
        SET first_name = ?, last_name = ?, flams_worked = ?, age = ?, email = ?,
            phone = ?, is_registered = 1, updated_at = ?
        WHERE invite_token = ?
    """, (
        first_name.strip(),
        last_name.strip(),
        flams_worked.strip(),
        int(age),
        email.lower().strip(),
        phone.strip(),
        now,
        token,
    ))
    conn.commit()
    conn.close()


def get_all_news():
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT title, content, author, published_at FROM news ORDER BY published_at DESC",
        conn
    )
    conn.close()
    return df


def add_news(title: str, content: str, author: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO news(title, content, author, published_at) VALUES (?, ?, ?, ?)",
        (title.strip(), content.strip(), author.strip(), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


# ----------------------------
# UI helpers
# ----------------------------
def inject_style():
    st.markdown("""
    <style>
    .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: white;
        margin-bottom: 1rem;
    }
    .card {
        border: 1px solid rgba(120,120,120,0.18);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        background: white;
        margin-bottom: 0.8rem;
    }
    .muted {
        color: #64748b;
        font-size: 0.92rem;
    }
    </style>
    """, unsafe_allow_html=True)


def login_with_token(token: str):
    user = get_user_by_token(token)
    if not user:
        st.error("Lien invalide ou expiré.")
        return False
    st.session_state["token"] = token
    st.session_state["user_email"] = user["email"]
    return True


def logout():
    for key in ["token", "user_email"]:
        st.session_state.pop(key, None)


def show_registration(user):
    st.subheader("Première connexion")
    st.write("Complétez vos informations pour activer votre compte personnel Flamsily.")

    with st.form("registration_form"):
        first_name = st.text_input("Prénom", value=user["first_name"] or "")
        last_name = st.text_input("Nom", value=user["last_name"] or "")
        flams_worked = st.text_area("Dans quelle Flam's avez-vous travaillé ?", value=user["flams_worked"] or "")
        age = st.number_input("Âge", min_value=16, max_value=100, value=max(18, user["age"] or 18), step=1)
        email = st.text_input("E-mail", value=user["email"] or "")
        phone = st.text_input("Numéro de téléphone (facultatif)", value=user["phone"] or "")
        submitted = st.form_submit_button("Créer mon compte")

    if submitted:
        missing = [x for x in [first_name, last_name, flams_worked, email] if not str(x).strip()]
        if missing:
            st.error("Merci de remplir tous les champs obligatoires.")
            return

        save_registration(
            st.session_state["token"],
            first_name,
            last_name,
            flams_worked,
            age,
            email,
            phone,
        )
        st.success("Compte créé avec succès. Votre espace personnel est maintenant actif.")
        st.rerun()


def show_home(user):
    st.markdown(f"""
    <div class="hero">
        <h2 style="margin-bottom:0.4rem;">Bienvenue {user["first_name"] or "sur"} Flamsily</h2>
        <div>Votre intranet interne propulsé par Streamlit.</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Actualités")
    news_df = get_all_news()

    if news_df.empty:
        st.info("Aucune actualité disponible.")
        return

    for _, row in news_df.iterrows():
        st.markdown(f"""
        <div class="card">
            <h4 style="margin-bottom:0.35rem;">{row["title"]}</h4>
            <div style="margin-bottom:0.55rem;">{row["content"]}</div>
            <div class="muted">Publié par {row["author"]} — {row["published_at"][:16].replace("T", " ")}</div>
        </div>
        """, unsafe_allow_html=True)


def show_profile(user):
    st.subheader("Mon profil")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Prénom", value=user["first_name"], disabled=True)
        st.text_input("Anciennes Flam's", value=user["flams_worked"], disabled=True)
        st.text_input("E-mail", value=user["email"], disabled=True)
    with col2:
        st.text_input("Nom", value=user["last_name"], disabled=True)
        st.text_input("Âge", value=str(user["age"]), disabled=True)
        st.text_input("Téléphone", value=user["phone"] or "-", disabled=True)


def show_admin_panel():
    st.subheader("Administration")
    with st.expander("Créer un lien d'invitation"):
        email = st.text_input("E-mail du collaborateur", key="admin_email_input")
        if st.button("Générer le lien"):
            if not email.strip():
                st.error("Merci d'indiquer un e-mail.")
            else:
                token, link = create_invite_shell(email)
                st.success("Lien généré.")
                st.code(link, language=None)

    with st.expander("Publier une actualité"):
        with st.form("news_form"):
            title = st.text_input("Titre")
            content = st.text_area("Contenu")
            author = st.text_input("Auteur", value="Administration")
            submitted = st.form_submit_button("Publier")
        if submitted:
            if not title.strip() or not content.strip():
                st.error("Titre et contenu obligatoires.")
            else:
                add_news(title, content, author)
                st.success("Actualité publiée.")
                st.rerun()


# ----------------------------
# Main app
# ----------------------------
def main():
    st.set_page_config(page_title="Flamsily", page_icon="🔥", layout="wide")
    init_db()
    inject_style()

    st.sidebar.title("Flamsily")
    st.sidebar.caption("Intranet interne")

    query_token = st.query_params.get("token")
    if query_token and not st.session_state.get("token"):
        login_with_token(query_token)

    with st.sidebar:
        manual_token = st.text_input("Lien de connexion / token", type="password", help="Collez votre token ou ouvrez le lien reçu.")
        if st.button("Se connecter"):
            candidate = manual_token.strip()
            # accept full URL or raw token
            if "token=" in candidate:
                candidate = candidate.split("token=")[-1].split("&")[0]
            ok = login_with_token(candidate)
            if ok:
                st.success("Connexion réussie.")
                st.rerun()

        if st.button("Se déconnecter"):
            logout()
            st.rerun()

        st.divider()
        st.caption("Admin")
        admin_secret = st.text_input("Clé admin", type="password")
        if admin_secret and admin_secret == ADMIN_SECRET:
            st.session_state["is_admin"] = True

    if st.session_state.get("is_admin"):
        show_admin_panel()
        st.divider()

    token = st.session_state.get("token")
    if not token:
        st.markdown("""
        <div class="hero">
            <h2 style="margin-bottom:0.35rem;">Bienvenue sur Flamsily</h2>
            <div>Connectez-vous avec votre lien personnel pour accéder à votre intranet.</div>
        </div>
        """, unsafe_allow_html=True)

        st.info("Un collaborateur doit recevoir un lien d'invitation pour sa première connexion.")
        st.write("Une fois connecté, il pourra remplir son profil, consulter les actualités et accéder à son espace personnel.")
        return

    user = get_user_by_token(token)
    if not user:
        st.error("Utilisateur introuvable.")
        return

    if not user["is_registered"]:
        show_registration(user)
        return

    page = st.sidebar.radio("Navigation", ["Accueil", "Mon profil"])

    if page == "Accueil":
        show_home(user)
    else:
        show_profile(user)


if __name__ == "__main__":
    main()
