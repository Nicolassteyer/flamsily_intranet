
from __future__ import annotations

import base64
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "flamsily.db"


def b64_image(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


LOGO_BDX = b64_image(ASSETS_DIR / "logo_bdx.png")
LOGO_BEIGE = b64_image(ASSETS_DIR / "logo_beige.png")


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            phone TEXT,
            age INTEGER NOT NULL,
            flams_location TEXT NOT NULL,
            city TEXT NOT NULL,
            role_title TEXT NOT NULL,
            start_year INTEGER NOT NULL,
            end_year INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            excerpt TEXT NOT NULL,
            body TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TEXT NOT NULL,
            author TEXT NOT NULL
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )

    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cur.execute(
            '''
            INSERT INTO users (
                first_name, last_name, email, password_hash, phone, age,
                flams_location, city, role_title, start_year, end_year, created_at, is_admin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                "Admin", "Flamsily", "admin@flamsily.local", hash_password("admin12345"),
                "", 30, "Strasbourg", "Strasbourg", "Administrateur", 2020, 2025, datetime.utcnow().isoformat(), 1
            ),
        )

    if cur.execute("SELECT COUNT(*) FROM news").fetchone()[0] == 0:
        rows = [
            ("Actualités du réseau", "Retrouvez les nouveautés du réseau Flam's.", "La communauté partage ses événements, actualités et opportunités.", "Actualité"),
            ("Ouverture d'un événement réseau", "Le prochain rendez-vous de la communauté est ouvert.", "Inscrivez-vous pour rencontrer les membres du réseau Flam's.", "Événement"),
            ("Offre carrière", "Une nouvelle opportunité est disponible.", "Découvrez les derniers postes publiés dans l'espace carrières.", "Carrière"),
        ]
        for title, excerpt, body, category in rows:
            cur.execute(
                "INSERT INTO news (title, excerpt, body, category, created_at, author) VALUES (?, ?, ?, ?, ?, ?)",
                (title, excerpt, body, category, datetime.utcnow().isoformat(), "Admin Flamsily"),
            )

    if cur.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO events (title, event_date, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Afterwork Flam's", "2025-09-12", "Strasbourg", "Rendez-vous du réseau dans une ambiance premium.", datetime.utcnow().isoformat()),
        )

    if cur.execute("SELECT COUNT(*) FROM careers").fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO careers (title, company, location, contract_type, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("Responsable de salle", "Flam's", "Paris", "CDI", "Poste de pilotage opérationnel et management d'équipe.", datetime.utcnow().isoformat()),
        )

    conn.commit()
    conn.close()


def query_df(sql: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute(sql: str, params: tuple[Any, ...]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


def get_user_by_email(email: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cur.fetchone()
    conn.close()
    return row


def authenticate(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return user


def register_user(data: dict[str, Any]) -> tuple[bool, str]:
    if get_user_by_email(data["email"]):
        return False, "Un compte existe déjà avec cet e-mail."
    if data["password"] != data["password_confirm"]:
        return False, "Les mots de passe ne correspondent pas."
    execute(
        '''
        INSERT INTO users (
            first_name, last_name, email, password_hash, phone, age,
            flams_location, city, role_title, start_year, end_year, created_at, is_admin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''',
        (
            data["first_name"].strip(),
            data["last_name"].strip(),
            data["email"].strip().lower(),
            hash_password(data["password"]),
            data["phone"].strip(),
            int(data["age"]),
            data["flams_location"].strip(),
            data["city"].strip(),
            data["role_title"].strip(),
            int(data["start_year"]),
            int(data["end_year"]),
            datetime.utcnow().isoformat(),
        ),
    )
    return True, "Compte créé. Vous pouvez maintenant vous connecter."


def save_profile(user_id: int, data: dict[str, Any]) -> None:
    execute(
        '''
        UPDATE users
        SET first_name=?, last_name=?, phone=?, age=?, flams_location=?, city=?, role_title=?, start_year=?, end_year=?
        WHERE id=?
        ''',
        (
            data["first_name"].strip(),
            data["last_name"].strip(),
            data["phone"].strip(),
            int(data["age"]),
            data["flams_location"].strip(),
            data["city"].strip(),
            data["role_title"].strip(),
            int(data["start_year"]),
            int(data["end_year"]),
            user_id,
        ),
    )


def seed_state() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("public_tab", "login")
    st.session_state.setdefault("page", "Actualités")
    st.session_state.setdefault("search", "")


def inject_css() -> None:
    logo = LOGO_BDX or LOGO_BEIGE
    logo_data = f"data:image/png;base64,{logo}" if logo else ""
    st.markdown(
        f'''
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background: #f3f3f3; }}
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="collapsedControl"] {{ background: transparent !important; }}
        [data-testid="stSidebar"] {{ display:none; }}
        .block-container {{ max-width: 1420px; padding-top: 0; padding-bottom: 0; }}
        .stButton > button {{
            border-radius: 999px;
            border: 1px solid #ef1f1f;
            background: white;
            color: #ef1f1f;
            font-weight: 700;
            min-height: 46px;
            box-shadow: none;
        }}
        .stButton > button:hover {{ background: #fff5f5; }}
        .red-solid .stButton > button {{
            background: #ef1f1f !important; color: white !important; border-color: #ef1f1f !important;
        }}
        .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div {{
            border-radius: 0 !important;
            border: 0 !important;
            border-bottom: 1px solid #bcbcbc !important;
            background: transparent !important;
            box-shadow: none !important;
            color: #222 !important;
        }}
        label, .stTextInput label, .stNumberInput label, .stTextArea label, .stSelectbox label {{
            color: #7a7a7a !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }}
        .top-header {{
            background: white;
            padding: 18px 28px 12px 28px;
            display:flex; align-items:center; justify-content:space-between;
        }}
        .brand-row {{ display:flex; align-items:center; gap:18px; }}
        .brand-logo {{ width: 210px; }}
        .red-badge {{
            background:#ef1f1f; color:white; border-radius:4px; padding:9px 14px; font-weight:700; font-size:14px;
        }}
        .social-strip {{ display:flex; gap:16px; align-items:center; color:#ef1f1f; font-weight:800; font-size:20px; }}
        .nav-red {{
            background:#ef1f1f; color:white; font-weight:700; display:flex; justify-content:center;
            gap:34px; padding:8px 18px; font-size:15px;
        }}
        .public-layout, .private-layout {{
            display:grid; grid-template-columns: 240px minmax(0, 1fr);
            min-height: calc(100vh - 116px);
        }}
        .left-public {{
            background:#f8f8f8; border-right:1px solid #dedede; padding: 0 14px 14px 14px;
        }}
        .public-title {{ font-size:20px; color:#555; font-weight:500; padding:18px 6px 14px 6px; }}
        .divider-or {{ text-align:center; color:#9a9a9a; margin: 12px 0; position:relative; }}
        .divider-or:before, .divider-or:after {{
            content:""; position:absolute; top: 50%; width: 36%; height:1px; background:#d7d7d7;
        }}
        .divider-or:before {{ left:0; }} .divider-or:after {{ right:0; }}
        .public-main {{
            padding: 20px 30px 40px 30px;
            background: #f3f3f3;
        }}
        .hero-public {{
            height: 330px; position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center;
            background:
                linear-gradient(0deg, rgba(45,20,22,0.28), rgba(45,20,22,0.28)),
                radial-gradient(circle at center, rgba(255,255,255,0.06), transparent 18%),
                linear-gradient(135deg, #6f2024 0%, #2b0f14 100%);
        }}
        .hero-public::after {{
            content:""; position:absolute; inset:0;
            background:
                radial-gradient(circle at 30% 40%, rgba(255,255,255,0.06), transparent 16%),
                radial-gradient(circle at 70% 26%, rgba(255,255,255,0.10), transparent 14%);
        }}
        .hero-copy {{ text-align:center; color:white; position:relative; z-index:2; }}
        .hero-copy h1 {{ margin:0 0 8px 0; font-size:56px; font-weight:800; line-height:1.0; }}
        .hero-copy p {{ margin:0; font-size:18px; }}
        .hero-cta-row {{ display:flex; gap:18px; justify-content:center; margin-top:28px; }}
        .cta-box {{
            padding:14px 24px; min-width: 300px; border:1px solid rgba(255,255,255,0.50); color:white;
            font-weight:700; text-align:center; background: rgba(255,255,255,0.06);
        }}
        .cta-box.primary {{ background: rgba(239,31,31,0.72); border-color: rgba(255,255,255,0.18); }}
        .join-title {{ text-align:center; font-size:34px; font-weight:800; color:#232323; margin:32px 0 24px; }}
        .cards-public {{ max-width:920px; margin:0 auto; display:grid; grid-template-columns:repeat(3, 1fr); gap:22px; }}
        .card-public {{
            background:white; padding:40px 24px; min-height:160px; border-radius:10px; text-align:center;
            border:1px solid #ececec;
        }}
        .card-public h3 {{ color:#1f5ca7; margin:18px 0 0 0; font-size:18px; }}
        .card-public p {{ color:#666; font-size:15px; line-height:1.5; }}
        .left-private {{ background:#f7f7f7; border-right:1px solid #d7d7d7; display:flex; flex-direction:column; }}
        .member-red {{ background:#ef1f1f; color:white; padding:14px 16px 10px; }}
        .search-ghost {{ border-bottom:1px solid rgba(255,255,255,0.4); padding-bottom:10px; font-size:15px; }}
        .profile-mini {{ display:flex; gap:12px; align-items:center; margin-top:18px; }}
        .avatar {{
            width:44px; height:44px; border-radius:50%; background:#bceac8; display:flex; align-items:center; justify-content:center;
            color:white; font-weight:700; font-size:20px;
        }}
        .profile-progress {{ padding:16px; border-bottom:1px solid #ddd; color:#555; font-size:15px; }}
        .profile-btn {{
            border:1px solid #ef1f1f; color:#ef1f1f; background:white; border-radius:999px; text-align:center; padding:8px 12px;
            margin-top:10px;
        }}
        .menu-static {{ padding:14px 16px; border-bottom:1px solid #ddd; color:#555; font-size:15px; }}
        .content-area {{ background:#f3f3f3; padding:18px 22px 36px; }}
        .page-title {{ font-size:20px; color:#444; margin-bottom:18px; }}
        .hero-banner {{
            height:168px; background:
            linear-gradient(90deg, rgba(255,255,255,0.72) 0 30%, rgba(255,255,255,0.12) 44%, rgba(255,255,255,0.02) 100%),
            linear-gradient(135deg, #d9e2e5 0%, #bcc8cc 40%, #98a4ad 100%);
            display:flex; align-items:center; padding:0 26px; margin-bottom:22px;
        }}
        .hero-title {{ font-size:20px; font-weight:700; color:#1a1a1a; }}
        .action-pill {{
            margin-left:auto; width:fit-content; background:#ef1f1f; color:white; padding:10px 18px; border-radius:999px; margin-bottom:18px;
        }}
        .grid3 {{ display:grid; grid-template-columns:repeat(3,1fr); gap:22px; }}
        .info-card, .news-card, .directory-card {{
            background:white; border:1px solid #e8e8e8;
        }}
        .info-card {{ padding:18px 16px; min-height:168px; }}
        .news-card, .directory-card {{ padding:18px; margin-bottom:14px; border-radius:6px; }}
        .news-meta {{ font-size:12px; color:#888; text-transform:uppercase; font-weight:700; margin-bottom:8px; }}
        .muted-small {{ font-size:13px; color:#777; }}
        @media (max-width: 1100px) {{
            .public-layout, .private-layout {{ grid-template-columns: 1fr; }}
            .left-public, .left-private {{ border-right:0; }}
            .cards-public, .grid3 {{ grid-template-columns: 1fr; }}
            .nav-red {{ flex-wrap:wrap; gap:14px; }}
            .hero-copy h1 {{ font-size:36px; }}
            .hero-cta-row {{ flex-direction:column; align-items:center; }}
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )


def top_header() -> None:
    logo_src = f"data:image/png;base64,{LOGO_BDX or LOGO_BEIGE}"
    st.markdown(
        f'''
        <div class="top-header">
            <div class="brand-row">
                <img class="brand-logo" src="{logo_src}" alt="Flam's">
            </div>
            <div class="social-strip">
                <div class="red-badge">JE COTISE !</div>
                <div>f</div><div>in</div><div>▶</div>
            </div>
        </div>
        <div class="nav-red">
            <span>ACTUALITÉS</span>
            <span>ÉVÉNEMENTS</span>
            <span>MENTORING</span>
            <span>L'ASSOCIATION</span>
            <span>PORTRAITS</span>
            <span>ANNUAIRE</span>
            <span>CARRIÈRES</span>
            <span>RÉSEAU</span>
            <span>CONTACT</span>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_public() -> None:
    top_header()
    st.markdown('<div class="public-layout">', unsafe_allow_html=True)
    render_public_left()
    render_public_right()
    st.markdown('</div>', unsafe_allow_html=True)


def render_public_left() -> None:
    st.markdown('<div class="left-public">', unsafe_allow_html=True)
    st.markdown('<div class="public-title">Accès membre</div>', unsafe_allow_html=True)
    if st.button("Connexion via Google", use_container_width=True):
        st.info("Connexion sociale à venir.")
    if st.button("Connexion via LinkedIn", use_container_width=True):
        st.info("Connexion sociale à venir.")
    if st.button("Connexion via Microsoft", use_container_width=True):
        st.info("Connexion sociale à venir.")
    st.markdown('<div class="divider-or">ou</div>', unsafe_allow_html=True)

    if st.session_state.public_tab == "login":
        with st.form("login_form"):
            email = st.text_input("Adresse mail")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Me connecter", use_container_width=True)
            if submitted:
                user = authenticate(email, password)
                if user:
                    st.session_state.user = dict(user)
                    st.session_state.page = "Actualités"
                    st.rerun()
                else:
                    st.error("Identifiants invalides.")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("M'inscrire", use_container_width=True):
                st.session_state.public_tab = "register"
                st.rerun()
        with c2:
            if st.button("Mot de passe oublié", use_container_width=True):
                st.session_state.public_tab = "forgot"
                st.rerun()
    elif st.session_state.public_tab == "register":
        with st.form("register_form"):
            first_name = st.text_input("Prénom")
            last_name = st.text_input("Nom")
            email = st.text_input("Adresse mail")
            password = st.text_input("Mot de passe", type="password")
            password_confirm = st.text_input("Confirmer le mot de passe", type="password")
            age = st.number_input("Âge", min_value=16, max_value=90, value=25)
            phone = st.text_input("Téléphone (facultatif)")
            flams_location = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
            city = st.text_input("Ville")
            role_title = st.text_input("Poste / rôle")
            start_year = st.number_input("Année d'entrée", min_value=1980, max_value=2100, value=2020)
            end_year = st.number_input("Année de sortie", min_value=1980, max_value=2100, value=2025)
            submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
            if submitted:
                required = [first_name, last_name, email, password, password_confirm, flams_location, city, role_title]
                if not all(v.strip() for v in required):
                    st.error("Merci de remplir tous les champs obligatoires.")
                else:
                    ok, msg = register_user({
                        "first_name": first_name, "last_name": last_name, "email": email, "password": password,
                        "password_confirm": password_confirm, "age": age, "phone": phone,
                        "flams_location": flams_location, "city": city, "role_title": role_title,
                        "start_year": start_year, "end_year": end_year
                    })
                    if ok:
                        st.success(msg)
                        st.session_state.public_tab = "login"
                        st.rerun()
                    else:
                        st.error(msg)
        if st.button("Retour connexion", use_container_width=True):
            st.session_state.public_tab = "login"
            st.rerun()
    else:
        st.info("Réinitialisation par e-mail à venir.")
        if st.button("Retour connexion", use_container_width=True):
            st.session_state.public_tab = "login"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_public_right() -> None:
    st.markdown(
        '''
        <div class="public-main">
            <div class="hero-public">
                <div class="hero-copy">
                    <h1>Je suis collaborateur<br>ou ancien Flam's</h1>
                    <p>Complétez votre profil et retrouvez les membres de votre communauté.</p>
                    <div class="hero-cta-row">
                        <div class="cta-box primary">MEMBRES<br><span style="font-weight:500;">ACCÉDEZ À VOTRE COMPTE</span></div>
                        <div class="cta-box">NOUVEAUX<br><span style="font-weight:500;">CRÉEZ VOTRE COMPTE</span></div>
                    </div>
                </div>
            </div>
            <div class="join-title">Rejoignez la communauté Flam's</div>
            <div class="cards-public">
                <div class="card-public"><div style="font-size:28px;">🪪</div><h3>Annuaire des Flam's</h3><p>Retrouvez les profils, villes, postes et parcours du réseau.</p></div>
                <div class="card-public"><div style="font-size:28px;">🌍</div><h3>Réseau & événements</h3><p>Suivez les rendez-vous, les actus et la vie de la communauté.</p></div>
                <div class="card-public"><div style="font-size:28px;">💼</div><h3>Espace carrière</h3><p>Consultez les offres et opportunités partagées dans l’intranet.</p></div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def completion_percent(user: sqlite3.Row) -> int:
    keys = ["first_name", "last_name", "email", "age", "flams_location", "city", "role_title", "start_year", "end_year", "phone"]
    filled = sum(1 for key in keys if str(user[key] or "").strip())
    return int((filled / len(keys)) * 100)


def render_private() -> None:
    user = get_user_by_email(st.session_state.user["email"])
    if not user:
        st.session_state.user = None
        st.rerun()

    top_header()
    st.markdown('<div class="private-layout">', unsafe_allow_html=True)
    render_private_left(user)
    render_private_content(user)
    st.markdown('</div>', unsafe_allow_html=True)


def render_private_left(user: sqlite3.Row) -> None:
    initials = f"{user['first_name'][:1]}{user['last_name'][:1]}".upper()
    progress = completion_percent(user)
    st.markdown(
        f'''
        <div class="left-private">
            <div class="member-red">
                <div class="search-ghost">‹ Rechercher</div>
                <div class="profile-mini">
                    <div class="avatar">{initials}</div>
                    <div>
                        <div style="font-size:16px;font-weight:700;line-height:1.05;">{user['first_name'].upper()}</div>
                        <div style="font-size:12px;">Voir mon profil</div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;padding:12px 4px 2px 4px;font-size:18px;">
                    <span>✉</span><span>🔔</span><span>👥</span>
                </div>
            </div>
            <div class="profile-progress">
                Votre profil est rempli à {progress}% !
                <div class="profile-btn">Compléter mon profil</div>
                <div style="margin-top:12px;">🤝 Merci d'avoir cotisé !</div>
            </div>
        ''',
        unsafe_allow_html=True,
    )
    items = ["Accueil", "Actualités", "Annuaire", "Événements", "Carrières", "Messages", "Mon profil", "Paramètres"]
    if int(user["is_admin"]) == 1:
        items.append("Admin")
    for item in items:
        if st.button(item, key=f"nav_{item}", use_container_width=True):
            st.session_state.page = item
            st.rerun()
        st.markdown(f'<div class="menu-static">{item}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    with c1:
        if st.button("Créez un contenu", use_container_width=True):
            st.session_state.page = "Admin"
            st.rerun()
    with c2:
        if st.button("⏻", use_container_width=True):
            st.session_state.user = None
            st.session_state.public_tab = "login"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_private_content(user: sqlite3.Row) -> None:
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    page = st.session_state.page
    if page == "Accueil":
        render_dashboard()
    elif page == "Actualités":
        render_news()
    elif page == "Annuaire":
        render_directory()
    elif page == "Événements":
        render_events()
    elif page == "Carrières":
        render_careers()
    elif page == "Messages":
        st.markdown('<div class="page-title">Messages</div>', unsafe_allow_html=True)
        st.info("La messagerie arrivera plus tard.")
    elif page == "Mon profil":
        render_profile(user)
    elif page == "Paramètres":
        st.markdown('<div class="page-title">Paramètres</div>', unsafe_allow_html=True)
        st.info("Les paramètres avancés arriveront plus tard.")
    elif page == "Admin" and int(user["is_admin"]) == 1:
        render_admin()
    else:
        render_news()
    st.markdown('</div>', unsafe_allow_html=True)


def render_dashboard() -> None:
    members = int(query_df("SELECT COUNT(*) AS c FROM users").iloc[0]["c"])
    posts = int(query_df("SELECT COUNT(*) AS c FROM news").iloc[0]["c"])
    st.markdown('<div class="page-title">Accueil</div>', unsafe_allow_html=True)
    st.markdown('<div class="action-pill">Vue d’ensemble</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-banner"><div class="hero-title">Bienvenue dans votre espace Flam's</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'''
        <div class="grid3">
            <div class="info-card"><h3 style="margin:0 0 12px 0;">Annuaire</h3><p>{members} membre(s) disponibles dans le réseau.</p></div>
            <div class="info-card"><h3 style="margin:0 0 12px 0;">Actualités</h3><p>{posts} publication(s) visibles dans le fil.</p></div>
            <div class="info-card"><h3 style="margin:0 0 12px 0;">Opportunités</h3><p>Retrouvez événements, emplois et contenus publiés par l'administration.</p></div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_news() -> None:
    st.markdown('<div class="page-title">Actualités</div>', unsafe_allow_html=True)
    df = query_df("SELECT * FROM news ORDER BY created_at DESC")
    for _, row in df.iterrows():
        st.markdown(
            f'''
            <div class="news-card">
                <div class="news-meta">{row["category"]} · {row["created_at"][:10]} · {row["author"]}</div>
                <h3 style="margin:0 0 8px 0;color:#191919;">{row["title"]}</h3>
                <p style="margin:0;color:#555;line-height:1.6;">{row["excerpt"]}</p>
                <div class="muted-small" style="margin-top:10px;">{row["body"]}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )


def render_directory() -> None:
    st.markdown('<div class="page-title">Annuaire</div>', unsafe_allow_html=True)
    search = st.text_input("Recherche", value=st.session_state.search, placeholder="Nom, ville, e-mail, Flam's, rôle…")
    st.session_state.search = search
    df = query_df("SELECT first_name, last_name, email, phone, age, flams_location, city, role_title, start_year, end_year FROM users ORDER BY first_name, last_name")
    if search.strip():
        q = search.lower().strip()
        mask = df.apply(lambda s: s.astype(str).str.lower().str.contains(q, na=False))
        df = df[mask.any(axis=1)]
    for _, row in df.iterrows():
        st.markdown(
            f'''
            <div class="directory-card">
                <h3 style="margin:0 0 6px 0;color:#222;">{row["first_name"]} {row["last_name"]}</h3>
                <div class="muted-small">{row["email"]} · {row["phone"] or "Téléphone non renseigné"}</div>
                <div class="muted-small" style="margin-top:6px;">{row["role_title"]} · {row["city"]} · Flam's {row["flams_location"]}</div>
                <div class="muted-small" style="margin-top:6px;">{int(row["start_year"])} → {int(row["end_year"])} · {int(row["age"])} ans</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )


def render_events() -> None:
    st.markdown('<div class="page-title">Événements</div>', unsafe_allow_html=True)
    df = query_df("SELECT * FROM events ORDER BY event_date ASC")
    for _, row in df.iterrows():
        st.markdown(
            f'''
            <div class="news-card">
                <div class="news-meta">{row["event_date"]} · {row["location"]}</div>
                <h3 style="margin:0 0 8px 0;color:#191919;">{row["title"]}</h3>
                <p style="margin:0;color:#555;line-height:1.6;">{row["description"]}</p>
            </div>
            ''',
            unsafe_allow_html=True,
        )


def render_careers() -> None:
    st.markdown('<div class="page-title">Carrières</div>', unsafe_allow_html=True)
    df = query_df("SELECT * FROM careers ORDER BY created_at DESC")
    for _, row in df.iterrows():
        st.markdown(
            f'''
            <div class="news-card">
                <div class="news-meta">{row["company"]} · {row["location"]} · {row["contract_type"]}</div>
                <h3 style="margin:0 0 8px 0;color:#191919;">{row["title"]}</h3>
                <p style="margin:0;color:#555;line-height:1.6;">{row["description"]}</p>
            </div>
            ''',
            unsafe_allow_html=True,
        )


def render_profile(user: sqlite3.Row) -> None:
    st.markdown('<div class="page-title">Mon profil</div>', unsafe_allow_html=True)
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Prénom", value=user["first_name"])
            email = st.text_input("Adresse mail", value=user["email"], disabled=True)
            age = st.number_input("Âge", min_value=16, max_value=90, value=int(user["age"]))
            flams_location = st.text_input("Dans quelle Flam's avez-vous travaillé ?", value=user["flams_location"])
            role_title = st.text_input("Poste / rôle", value=user["role_title"])
            end_year = st.number_input("Année de sortie", min_value=1980, max_value=2100, value=int(user["end_year"]))
        with c2:
            last_name = st.text_input("Nom", value=user["last_name"])
            phone = st.text_input("Téléphone", value=user["phone"] or "")
            city = st.text_input("Ville", value=user["city"])
            start_year = st.number_input("Année d'entrée", min_value=1980, max_value=2100, value=int(user["start_year"]))
        submitted = st.form_submit_button("Enregistrer mon profil", use_container_width=True)
        if submitted:
            save_profile(int(user["id"]), {
                "first_name": first_name, "last_name": last_name, "phone": phone, "age": age,
                "flams_location": flams_location, "city": city, "role_title": role_title,
                "start_year": start_year, "end_year": end_year
            })
            st.session_state.user = dict(get_user_by_email(user["email"]))
            st.success("Profil mis à jour.")
            st.rerun()


def render_admin() -> None:
    st.markdown('<div class="page-title">Administration</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Actualités", "Événements", "Carrières", "Membres"])
    with tabs[0]:
        with st.form("admin_news"):
            title = st.text_input("Titre")
            excerpt = st.text_input("Accroche")
            body = st.text_area("Contenu")
            category = st.selectbox("Catégorie", ["Actualité", "Événement", "Carrière", "Portrait"])
            if st.form_submit_button("Publier", use_container_width=True):
                execute("INSERT INTO news (title, excerpt, body, category, created_at, author) VALUES (?, ?, ?, ?, ?, ?)",
                        (title, excerpt, body, category, datetime.utcnow().isoformat(), "Admin Flamsily"))
                st.success("Publié.")
                st.rerun()
    with tabs[1]:
        with st.form("admin_events"):
            title = st.text_input("Titre de l'événement")
            event_date = st.date_input("Date")
            location = st.text_input("Lieu")
            description = st.text_area("Description")
            if st.form_submit_button("Ajouter", use_container_width=True):
                execute("INSERT INTO events (title, event_date, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title, str(event_date), location, description, datetime.utcnow().isoformat()))
                st.success("Ajouté.")
                st.rerun()
    with tabs[2]:
        with st.form("admin_careers"):
            title = st.text_input("Titre du poste")
            company = st.text_input("Entreprise")
            location = st.text_input("Localisation")
            contract_type = st.selectbox("Type de contrat", ["CDI", "CDD", "Stage", "Alternance", "Freelance"])
            description = st.text_area("Description")
            if st.form_submit_button("Publier l'offre", use_container_width=True):
                execute("INSERT INTO careers (title, company, location, contract_type, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (title, company, location, contract_type, description, datetime.utcnow().isoformat()))
                st.success("Offre publiée.")
                st.rerun()
    with tabs[3]:
        df = query_df("SELECT id, first_name, last_name, email, city, flams_location, role_title, is_admin FROM users ORDER BY created_at DESC")
        st.dataframe(df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Flamsily", page_icon="🔥", layout="wide")
    seed_state()
    init_db()
    inject_css()
    if st.session_state.user:
        render_private()
    else:
        render_public()


if __name__ == "__main__":
    main()
