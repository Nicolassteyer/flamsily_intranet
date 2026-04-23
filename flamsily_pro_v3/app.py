
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st

st.set_page_config(page_title="Flamsily", page_icon="🔥", layout="wide", initial_sidebar_state="collapsed")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "flamsily_pro.db"
LIGHT_LOGO = ASSETS_DIR / "logo_bdx.png"

DATA_DIR.mkdir(parents=True, exist_ok=True)

st.markdown("""
<style>
:root {
    --bg: #f7f4ee; --surface: #fffdf9; --surface-2: #f1ece3; --card: #ffffff; --card-2: #faf7f2;
    --text: #231815; --muted: #796d62; --line: rgba(94, 64, 48, 0.14); --brand: #7e171f;
    --brand-2: #a12732; --brand-soft: rgba(126, 23, 31, 0.09); --accent: #d3b276;
    --success: #1e8e5a; --danger: #b3261e; --shadow: 0 18px 45px rgba(48, 26, 17, 0.10);
}
html, body, [data-testid="stAppViewContainer"], .stApp { background: linear-gradient(180deg, #fbf8f2 0%, #f6f0e7 100%); color: var(--text);}
[data-testid="stSidebar"] {display:none;} #MainMenu, footer, header {visibility:hidden;}
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px;}
h1, h2, h3, h4, h5, h6 {color: var(--text);}
.stTextInput > div > div > input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 16px !important; border: 1px solid var(--line) !important; background: rgba(255,255,255,0.92) !important;
    color: var(--text) !important; min-height: 50px !important;
}
.stTextArea textarea {min-height: 110px !important;}
.stButton > button {
    border-radius: 999px !important; border: 1px solid transparent !important;
    background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%) !important; color: #fff !important;
    font-weight: 700 !important; padding: 0.78rem 1.25rem !important; min-height: 48px !important;
    box-shadow: 0 10px 24px rgba(126, 23, 31, 0.18); transition: all .18s ease !important;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 15px 28px rgba(126, 23, 31, 0.22) !important; filter: brightness(1.02);}
div[data-testid="stForm"] { border: 1px solid var(--line); border-radius: 28px; padding: 1rem; background: rgba(255,255,255,0.76); box-shadow: var(--shadow);}
.hero-shell {
    border: 1px solid var(--line);
    background: radial-gradient(circle at top right, rgba(211,178,118,0.14), transparent 32%), linear-gradient(135deg, rgba(126,23,31,0.96) 0%, rgba(88,13,19,0.98) 100%);
    color: #fff; border-radius: 34px; padding: 28px 32px; min-height: 220px; box-shadow: var(--shadow);
}
.hero-kicker { display: inline-flex; gap: 8px; align-items: center; padding: 8px 14px; border-radius: 999px; background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.16); font-size: 0.92rem; margin-bottom: 12px;}
.hero-title { font-size: 3rem; line-height: 1.04; font-weight: 800; margin: 0.25rem 0 0.9rem 0;}
.hero-subtitle { max-width: 880px; font-size: 1.08rem; color: rgba(255,255,255,0.88);}
.kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 16px; margin-top: 20px;}
.kpi-card { background: rgba(255,255,255,0.09); border: 1px solid rgba(255,255,255,0.14); border-radius: 22px; padding: 18px;}
.kpi-label {font-size: 0.9rem; color: rgba(255,255,255,0.75);} .kpi-value {font-size: 1.75rem; font-weight: 800; margin-top: 4px;}
.glass-card { background: rgba(255,255,255,0.82); border: 1px solid var(--line); border-radius: 28px; padding: 22px; box-shadow: var(--shadow);}
.section-title { font-size: 1.35rem; font-weight: 800; margin-bottom: 0.3rem;} .section-subtitle { color: var(--muted); margin-bottom: 1rem;}
.portal-shell { padding: 12px 0 10px 0;}
.topbar { background: rgba(255,255,255,0.88); border: 1px solid var(--line); border-radius: 28px; padding: 12px 18px; box-shadow: 0 10px 25px rgba(48,26,17,0.06); margin-bottom: 18px;}
.brand-title { font-size: 1.38rem; font-weight: 800; margin: 0;} .brand-sub { color: var(--muted); margin: 0; font-size: 0.95rem;}
.nav-tabs { display:flex; gap: 10px; flex-wrap: wrap; margin-top: 14px;}
.nav-pill { display:inline-flex; align-items:center; gap: 8px; background: white; border: 1px solid var(--line); border-radius: 999px; padding: 10px 14px; font-weight: 650; box-shadow: 0 6px 16px rgba(48,26,17,0.04);}
.sidebar-card { background: linear-gradient(180deg, #7e171f 0%, #651118 100%); color: #fff; border-radius: 28px; padding: 22px; border: 1px solid rgba(255,255,255,0.10); box-shadow: var(--shadow);}
.avatar { width: 62px; height: 62px; border-radius: 50%; display:flex; align-items:center; justify-content:center; background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.18); font-size: 1.3rem; font-weight: 800;}
.member-name { font-size: 1.15rem; font-weight: 800; margin-top: 12px;} .member-meta { color: rgba(255,255,255,0.78); font-size: 0.95rem;}
.progress-wrap { margin-top: 16px;} .progress-rail { height: 10px; background: rgba(255,255,255,0.16); border-radius: 999px; overflow: hidden;}
.progress-fill { height: 100%; background: linear-gradient(90deg, #f0dcb6 0%, #d3b276 100%); border-radius: 999px;}
.side-menu-card { background: rgba(255,255,255,0.72); border: 1px solid var(--line); border-radius: 28px; padding: 14px; box-shadow: var(--shadow); margin-top: 14px;}
.feature-card { background: rgba(255,255,255,0.82); border: 1px solid var(--line); border-radius: 24px; padding: 20px; height: 100%; box-shadow: 0 12px 24px rgba(48,26,17,0.05); transition: transform .18s ease, box-shadow .18s ease; margin-bottom: 12px;}
.feature-card:hover { transform: translateY(-3px); box-shadow: 0 18px 34px rgba(48,26,17,0.09);}
.feature-icon { width: 48px; height: 48px; border-radius: 16px; display:flex; align-items:center; justify-content:center; font-size: 1.35rem; background: var(--brand-soft); color: var(--brand); margin-bottom: 12px;}
.feature-title { font-size: 1.08rem; font-weight: 800; margin-bottom: 6px;} .feature-desc { color: var(--muted); line-height: 1.55;}
.news-card { background: linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(255,253,249,0.96) 100%); border: 1px solid var(--line); border-radius: 24px; padding: 18px; box-shadow: 0 12px 24px rgba(48,26,17,0.05); margin-bottom: 12px;}
.news-meta { font-size: 0.9rem; color: var(--muted); margin-bottom: 6px;} .news-title { font-size: 1.04rem; font-weight: 800; margin-bottom: 6px;} .news-body { color: var(--text); line-height: 1.6;}
.badge-soft { display:inline-flex; padding: 6px 10px; background: var(--brand-soft); color: var(--brand); border-radius: 999px; font-size: 0.84rem; font-weight: 700;}
.empty-state { text-align:center; padding: 36px 18px; color: var(--muted); border: 1px dashed var(--line); border-radius: 24px; background: rgba(255,255,255,0.55);}
@media (max-width: 1024px) {.kpi-grid {grid-template-columns: repeat(2, minmax(0,1fr));}}
@media (max-width: 800px) {.hero-title {font-size: 2.2rem;} .kpi-grid {grid-template-columns: 1fr;}}
</style>
""", unsafe_allow_html=True)

def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL, last_name TEXT NOT NULL, flams_site TEXT NOT NULL, age INTEGER NOT NULL,
        email TEXT NOT NULL UNIQUE, phone TEXT, password_hash TEXT NOT NULL, is_admin INTEGER DEFAULT 0, created_at TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, body TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'Actualité', author TEXT NOT NULL, created_at TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, place TEXT NOT NULL, event_date TEXT NOT NULL, description TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, company TEXT NOT NULL, location TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT NOT NULL
    )""")
    cur.execute("SELECT id FROM users WHERE email = ?", ("admin@flamsily.local",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (first_name, last_name, flams_site, age, email, phone, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("Admin", "Flamsily", "Siège", 30, "admin@flamsily.local", "", hash_password("admin12345"), 1, datetime.utcnow().isoformat())
        )
    cur.execute("SELECT COUNT(*) AS c FROM news")
    if cur.fetchone()["c"] == 0:
        for title, body, category, author in [
            ("Bienvenue sur Flamsily", "Votre nouvel intranet réunit actualités, profils, événements et opportunités carrière dans un espace plus moderne et plus clair.", "À la une", "Équipe Flamsily"),
            ("Ouverture des inscriptions", "Les anciens et actuels collaborateurs peuvent désormais créer leur compte avec une simple adresse e-mail.", "Communauté", "Équipe Flamsily"),
            ("Lancement du nouvel annuaire", "Retrouvez les membres par prénom, nom, e-mail ou site Flam's pour faciliter les échanges.", "Annuaire", "Équipe Flamsily"),
        ]:
            cur.execute("INSERT INTO news (title, body, category, author, created_at) VALUES (?, ?, ?, ?, ?)", (title, body, category, author, datetime.utcnow().isoformat()))
    cur.execute("SELECT COUNT(*) AS c FROM events")
    if cur.fetchone()["c"] == 0:
        for title, place, event_date, description in [
            ("Afterwork Flamsily", "Strasbourg", (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%d"), "Rencontre réseau entre anciens collaborateurs."),
            ("Soirée communauté", "Lyon", (datetime.utcnow() + timedelta(days=34)).strftime("%Y-%m-%d"), "Moment d’échange autour des parcours et opportunités."),
        ]:
            cur.execute("INSERT INTO events (title, place, event_date, description) VALUES (?, ?, ?, ?)", (title, place, event_date, description))
    cur.execute("SELECT COUNT(*) AS c FROM jobs")
    if cur.fetchone()["c"] == 0:
        for title, company, location, description in [
            ("Responsable de salle", "Flam's Strasbourg", "Strasbourg", "Superviser le service, l’équipe et l’expérience client."),
            ("Chef de rang", "Flam's Colmar", "Colmar", "Assurer un service fluide et premium sur le terrain."),
            ("Assistant communication", "Flamsily", "Télétravail partiel", "Animer la communauté, rédiger des contenus et valoriser les actualités."),
        ]:
            cur.execute("INSERT INTO jobs (title, company, location, description, created_at) VALUES (?, ?, ?, ?, ?)", (title, company, location, description, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def fetch_one(query, params=()):
    conn = get_conn()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row

def fetch_all(query, params=()):
    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def execute(query, params=()):
    conn = get_conn()
    conn.execute(query, params)
    conn.commit()
    conn.close()

def ensure_state():
    for k, v in {"auth_user_id": None, "page": "Accueil"}.items():
        if k not in st.session_state:
            st.session_state[k] = v

def login(email: str, password: str):
    user = fetch_one("SELECT * FROM users WHERE lower(email) = lower(?) AND password_hash = ?", (email.strip(), hash_password(password)))
    if user:
        st.session_state.auth_user_id = user["id"]
        st.session_state.page = "Accueil"
        return True
    return False

def logout():
    st.session_state.auth_user_id = None
    st.session_state.page = "Accueil"

def current_user():
    uid = st.session_state.get("auth_user_id")
    return fetch_one("SELECT * FROM users WHERE id = ?", (uid,)) if uid else None

def profile_completion(user):
    score = 0
    for key, pts in [("first_name",15),("last_name",15),("flams_site",20),("age",15),("email",20),("phone",15)]:
        if user[key]:
            score += pts
    return score

def load_logo():
    return str(LIGHT_LOGO) if LIGHT_LOGO.exists() else None

def initials(user):
    return f"{(user['first_name'] or 'F')[:1]}{(user['last_name'] or 'L')[:1]}".upper()

def render_public_top():
    logo = load_logo()
    c1, c2 = st.columns([0.60, 0.40], vertical_alignment="center")
    with c1:
        if logo:
            st.image(logo, width=170)
        st.markdown("""
        <div class="hero-shell">
            <div class="hero-kicker">🔥 Réseau Flam's • Intranet & communauté</div>
            <div class="hero-title">Bienvenue sur Flamsily</div>
            <div class="hero-subtitle">Une web app plus premium pour réunir les collaborateurs et anciens Flam's : inscription simple, espace membre, actualités, annuaire, événements et opportunités carrière.</div>
            <div class="kpi-grid">
                <div class="kpi-card"><div class="kpi-label">Accès</div><div class="kpi-value">1 URL</div></div>
                <div class="kpi-card"><div class="kpi-label">Inscription</div><div class="kpi-value">30 sec</div></div>
                <div class="kpi-card"><div class="kpi-label">Modules</div><div class="kpi-value">6</div></div>
                <div class="kpi-card"><div class="kpi-label">Expérience</div><div class="kpi-value">Premium</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="glass-card"><div class="section-title">Pourquoi cette V3 est meilleure</div><div class="section-subtitle">Une interface plus finie, plus élégante, plus simple à utiliser.</div></div>', unsafe_allow_html=True)
        for cols_html in [
            [("🎨","Design plus pro","Palette cohérente, hover subtils, cartes mieux dessinées, hiérarchie visuelle plus claire."),
             ("🔐","Connexion simple","Une seule URL, inscription libre, puis connexion avec e-mail et mot de passe.")],
            [("👥","Annuaire intégré","Recherche rapide par nom, e-mail ou site pour retrouver la communauté."),
             ("📣","Actualités & jobs","Contenus publiables par l’admin avec affichage premium dans l’espace membre.")]
        ]:
            c3, c4 = st.columns(2)
            for col, item in zip([c3, c4], cols_html):
                with col:
                    icon, title, desc = item
                    st.markdown(f'<div class="feature-card"><div class="feature-icon">{icon}</div><div class="feature-title">{title}</div><div class="feature-desc">{desc}</div></div>', unsafe_allow_html=True)

def render_auth_forms():
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown('<div class="glass-card"><div class="section-title">Accès membre</div><div class="section-subtitle">Connectez-vous ou créez votre compte pour rejoindre l’intranet Flamsily.</div></div>', unsafe_allow_html=True)
        tabs = st.tabs(["Connexion", "Créer un compte"])
        with tabs[0]:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Adresse e-mail", placeholder="prenom.nom@email.com")
                password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
                ok = st.form_submit_button("Me connecter", use_container_width=True)
                if ok:
                    if login(email, password):
                        st.success("Connexion réussie.")
                        st.rerun()
                    else:
                        st.error("E-mail ou mot de passe incorrect.")
            st.caption("Compte admin de test : admin@flamsily.local / admin12345")
        with tabs[1]:
            with st.form("signup_form", clear_on_submit=False):
                c1, c2 = st.columns(2)
                with c1:
                    first_name = st.text_input("Prénom")
                with c2:
                    last_name = st.text_input("Nom")
                c3, c4 = st.columns([1.5, 1])
                with c3:
                    flams_site = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
                with c4:
                    age = st.number_input("Âge", min_value=16, max_value=99, step=1)
                email = st.text_input("E-mail")
                phone = st.text_input("Téléphone (facultatif)")
                p1, p2 = st.columns(2)
                with p1:
                    password = st.text_input("Mot de passe", type="password")
                with p2:
                    password_confirm = st.text_input("Confirmer le mot de passe", type="password")
                create = st.form_submit_button("Créer mon compte", use_container_width=True)
                if create:
                    if not all([first_name.strip(), last_name.strip(), flams_site.strip(), email.strip(), password.strip()]):
                        st.error("Merci de remplir tous les champs obligatoires.")
                    elif "@" not in email or "." not in email:
                        st.error("Merci de saisir une adresse e-mail valide.")
                    elif len(password) < 8:
                        st.error("Le mot de passe doit contenir au moins 8 caractères.")
                    elif password != password_confirm:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif fetch_one("SELECT id FROM users WHERE lower(email) = lower(?)", (email.strip(),)):
                        st.error("Un compte existe déjà avec cette adresse e-mail.")
                    else:
                        execute("INSERT INTO users (first_name, last_name, flams_site, age, email, phone, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)",
                                (first_name.strip(), last_name.strip(), flams_site.strip(), int(age), email.strip(), phone.strip(), hash_password(password), datetime.utcnow().isoformat()))
                        st.success("Compte créé avec succès. Vous pouvez maintenant vous connecter.")
    with right:
        latest = fetch_all("SELECT * FROM news ORDER BY datetime(created_at) DESC LIMIT 3")
        st.markdown('<div class="glass-card"><div class="section-title">À la une</div><div class="section-subtitle">Les dernières informations disponibles dès la page d’accueil.</div></div>', unsafe_allow_html=True)
        if latest:
            for item in latest:
                created = item["created_at"][:10]
                st.markdown(f'<div class="news-card"><div class="news-meta"><span class="badge-soft">{item["category"]}</span> &nbsp;•&nbsp; {created}</div><div class="news-title">{item["title"]}</div><div class="news-body">{item["body"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">Aucune actualité pour le moment.</div>', unsafe_allow_html=True)

def render_topbar(user):
    logo = load_logo()
    st.markdown('<div class="portal-shell"><div class="topbar">', unsafe_allow_html=True)
    c1, c2 = st.columns([0.72, 0.28], vertical_alignment="center")
    with c1:
        left, title = st.columns([0.18, 0.82], vertical_alignment="center")
        with left:
            if logo:
                st.image(logo, width=130)
        with title:
            st.markdown(f'<div class="brand-title">Flamsily</div><div class="brand-sub">Communauté Flam\'s • {user["first_name"]} {user["last_name"]}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap;"><div class="badge-soft">Intranet premium</div><div class="badge-soft">1 URL</div><div class="badge-soft">Communauté</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-tabs"><div class="nav-pill">🏠 Accueil</div><div class="nav-pill">📰 Actualités</div><div class="nav-pill">📅 Événements</div><div class="nav-pill">👥 Annuaire</div><div class="nav-pill">💼 Carrières</div><div class="nav-pill">🙍 Mon profil</div></div></div>', unsafe_allow_html=True)

def render_member_sidebar(user):
    completion = profile_completion(user)
    st.markdown(f'<div class="sidebar-card"><div class="avatar">{initials(user)}</div><div class="member-name">{user["first_name"]} {user["last_name"]}</div><div class="member-meta">{user["email"]}</div><div class="member-meta">Site : {user["flams_site"]}</div><div class="progress-wrap"><div style="display:flex;justify-content:space-between;margin-bottom:8px;"><div style="font-weight:700;">Profil complété</div><div>{completion}%</div></div><div class="progress-rail"><div class="progress-fill" style="width:{completion}%;"></div></div></div></div>', unsafe_allow_html=True)
    pages = ["Accueil", "Actualités", "Événements", "Annuaire", "Carrières", "Mon profil"] + (["Admin"] if user["is_admin"] else [])
    st.markdown('<div class="side-menu-card">', unsafe_allow_html=True)
    for page in pages:
        label = {"Accueil":"🏠 Accueil","Actualités":"📰 Actualités","Événements":"📅 Événements","Annuaire":"👥 Annuaire","Carrières":"💼 Carrières","Mon profil":"🙍 Mon profil","Admin":"⚙️ Administration"}[page]
        if st.button(label, key=f"nav_{page}", use_container_width=True):
            st.session_state.page = page
            st.rerun()
    if st.button("Se déconnecter", key="logout_btn", use_container_width=True):
        logout()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_home():
    total_users = fetch_one("SELECT COUNT(*) AS c FROM users")["c"]
    total_news = fetch_one("SELECT COUNT(*) AS c FROM news")["c"]
    total_events = fetch_one("SELECT COUNT(*) AS c FROM events")["c"]
    total_jobs = fetch_one("SELECT COUNT(*) AS c FROM jobs")["c"]
    st.markdown('<div class="hero-shell"><div class="hero-kicker">🔥 Tableau de bord membre</div><div class="hero-title">Votre communauté Flam\'s, enfin dans une interface plus premium</div><div class="hero-subtitle">Consultez les dernières actualités, trouvez des anciens collègues, repérez les événements à venir et explorez les opportunités carrière dans un seul espace.</div></div>', unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    for col, label, value, icon in [(a,"Membres",total_users,"👥"),(b,"Actualités",total_news,"📰"),(c,"Événements",total_events,"📅"),(d,"Offres",total_jobs,"💼")]:
        with col:
            st.markdown(f'<div class="feature-card"><div class="feature-icon">{icon}</div><div class="feature-title">{label}</div><div style="font-size:2rem;font-weight:800;">{value}</div></div>', unsafe_allow_html=True)
    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        st.markdown('<div class="section-title">Dernières actualités</div><div class="section-subtitle">Les informations importantes de la communauté.</div>', unsafe_allow_html=True)
        items = fetch_all("SELECT * FROM news ORDER BY datetime(created_at) DESC LIMIT 5")
        if items:
            for item in items:
                st.markdown(f'<div class="news-card"><div class="news-meta"><span class="badge-soft">{item["category"]}</span> &nbsp;•&nbsp; {item["created_at"][:10]} &nbsp;•&nbsp; {item["author"]}</div><div class="news-title">{item["title"]}</div><div class="news-body">{item["body"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">Aucune actualité pour le moment.</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-title">Prochains événements</div><div class="section-subtitle">Les rendez-vous réseau à venir.</div>', unsafe_allow_html=True)
        events = fetch_all("SELECT * FROM events ORDER BY event_date ASC LIMIT 4")
        if events:
            for ev in events:
                st.markdown(f'<div class="feature-card"><div class="feature-title">{ev["title"]}</div><div class="feature-desc"><strong>Date :</strong> {ev["event_date"]}<br><strong>Lieu :</strong> {ev["place"]}<br>{ev["description"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">Aucun événement programmé.</div>', unsafe_allow_html=True)

def render_news():
    st.markdown('<div class="section-title">Actualités</div><div class="section-subtitle">Toutes les communications diffusées sur Flamsily.</div>', unsafe_allow_html=True)
    items = fetch_all("SELECT * FROM news ORDER BY datetime(created_at) DESC")
    if items:
        for item in items:
            st.markdown(f'<div class="news-card"><div class="news-meta"><span class="badge-soft">{item["category"]}</span> &nbsp;•&nbsp; {item["created_at"][:10]} &nbsp;•&nbsp; {item["author"]}</div><div class="news-title">{item["title"]}</div><div class="news-body">{item["body"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">Aucune actualité pour le moment.</div>', unsafe_allow_html=True)

def render_events():
    st.markdown('<div class="section-title">Événements</div><div class="section-subtitle">Les moments de rencontre de la communauté Flam’s.</div>', unsafe_allow_html=True)
    events = fetch_all("SELECT * FROM events ORDER BY event_date ASC")
    if events:
        cols = st.columns(2)
        for i, ev in enumerate(events):
            with cols[i % 2]:
                st.markdown(f'<div class="feature-card"><div class="feature-icon">📅</div><div class="feature-title">{ev["title"]}</div><div class="feature-desc"><strong>Date :</strong> {ev["event_date"]}<br><strong>Lieu :</strong> {ev["place"]}<br><br>{ev["description"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">Aucun événement enregistré.</div>', unsafe_allow_html=True)

def render_directory():
    st.markdown('<div class="section-title">Annuaire</div><div class="section-subtitle">Retrouvez facilement les membres de la communauté.</div>', unsafe_allow_html=True)
    q1, q2 = st.columns([1.4, 1])
    with q1:
        query = st.text_input("Rechercher", placeholder="Prénom, nom, e-mail…")
    with q2:
        site_filter = st.text_input("Filtrer par site Flam's", placeholder="Ex : Strasbourg")
    sql = "SELECT first_name, last_name, flams_site, email, phone, age, created_at FROM users WHERE 1=1"
    params = []
    if query.strip():
        sql += " AND (lower(first_name) LIKE ? OR lower(last_name) LIKE ? OR lower(email) LIKE ?)"
        q = f"%{query.strip().lower()}%"
        params.extend([q, q, q])
    if site_filter.strip():
        sql += " AND lower(flams_site) LIKE ?"
        params.append(f"%{site_filter.strip().lower()}%")
    sql += " ORDER BY first_name ASC, last_name ASC"
    members = fetch_all(sql, tuple(params))
    if members:
        cols = st.columns(2)
        for i, m in enumerate(members):
            phone = m["phone"] if m["phone"] else "Non renseigné"
            with cols[i % 2]:
                st.markdown(f'<div class="feature-card"><div class="feature-icon">👤</div><div class="feature-title">{m["first_name"]} {m["last_name"]}</div><div class="feature-desc"><strong>Site :</strong> {m["flams_site"]}<br><strong>E-mail :</strong> {m["email"]}<br><strong>Téléphone :</strong> {phone}<br><strong>Âge :</strong> {m["age"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">Aucun membre ne correspond à votre recherche.</div>', unsafe_allow_html=True)

def render_jobs():
    st.markdown('<div class="section-title">Carrières</div><div class="section-subtitle">Des opportunités pour continuer l’aventure ou évoluer dans le réseau.</div>', unsafe_allow_html=True)
    jobs = fetch_all("SELECT * FROM jobs ORDER BY datetime(created_at) DESC")
    if jobs:
        for job in jobs:
            st.markdown(f'<div class="feature-card"><div class="feature-icon">💼</div><div class="feature-title">{job["title"]}</div><div class="feature-desc"><strong>Entreprise :</strong> {job["company"]}<br><strong>Localisation :</strong> {job["location"]}<br><br>{job["description"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">Aucune offre disponible.</div>', unsafe_allow_html=True)

def render_profile(user):
    st.markdown('<div class="section-title">Mon profil</div><div class="section-subtitle">Mettez à jour vos informations personnelles.</div>', unsafe_allow_html=True)
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Prénom", value=user["first_name"])
        with c2:
            last_name = st.text_input("Nom", value=user["last_name"])
        c3, c4 = st.columns([1.4, 0.6])
        with c3:
            flams_site = st.text_input("Dans quelle Flam's avez-vous travaillé ?", value=user["flams_site"])
        with c4:
            age = st.number_input("Âge", min_value=16, max_value=99, value=int(user["age"]))
        st.text_input("E-mail", value=user["email"], disabled=True)
        phone = st.text_input("Téléphone", value=user["phone"] or "")
        new_password = st.text_input("Nouveau mot de passe (facultatif)", type="password")
        save = st.form_submit_button("Enregistrer les modifications", use_container_width=True)
        if save:
            if new_password.strip():
                execute("UPDATE users SET first_name=?, last_name=?, flams_site=?, age=?, phone=?, password_hash=? WHERE id=?", (first_name.strip(), last_name.strip(), flams_site.strip(), int(age), phone.strip(), hash_password(new_password), user["id"]))
            else:
                execute("UPDATE users SET first_name=?, last_name=?, flams_site=?, age=?, phone=? WHERE id=?", (first_name.strip(), last_name.strip(), flams_site.strip(), int(age), phone.strip(), user["id"]))
            st.success("Profil mis à jour.")
            st.rerun()

def render_admin(user):
    if not user["is_admin"]:
        st.warning("Accès réservé à l’administrateur.")
        return
    st.markdown('<div class="section-title">Administration</div><div class="section-subtitle">Publiez du contenu et pilotez l’intranet.</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Publier une actualité", "Créer un événement", "Créer une offre", "Utilisateurs"])
    with tabs[0]:
        with st.form("news_admin"):
            title = st.text_input("Titre")
            category = st.selectbox("Catégorie", ["À la une", "Communauté", "Annuaire", "RH", "Événement"])
            body = st.text_area("Contenu")
            submit = st.form_submit_button("Publier l’actualité", use_container_width=True)
            if submit:
                if title.strip() and body.strip():
                    execute("INSERT INTO news (title, body, category, author, created_at) VALUES (?, ?, ?, ?, ?)", (title.strip(), body.strip(), category, f"{user['first_name']} {user['last_name']}", datetime.utcnow().isoformat()))
                    st.success("Actualité publiée.")
                    st.rerun()
                else:
                    st.error("Merci de remplir le titre et le contenu.")
    with tabs[1]:
        with st.form("event_admin"):
            title = st.text_input("Titre de l’événement")
            place = st.text_input("Lieu")
            event_date = st.date_input("Date")
            description = st.text_area("Description")
            submit = st.form_submit_button("Créer l’événement", use_container_width=True)
            if submit:
                if title.strip() and place.strip() and description.strip():
                    execute("INSERT INTO events (title, place, event_date, description) VALUES (?, ?, ?, ?)", (title.strip(), place.strip(), str(event_date), description.strip()))
                    st.success("Événement créé.")
                    st.rerun()
                else:
                    st.error("Merci de remplir tous les champs.")
    with tabs[2]:
        with st.form("job_admin"):
            title = st.text_input("Titre du poste")
            company = st.text_input("Entreprise")
            location = st.text_input("Localisation")
            description = st.text_area("Description")
            submit = st.form_submit_button("Publier l’offre", use_container_width=True)
            if submit:
                if title.strip() and company.strip() and location.strip() and description.strip():
                    execute("INSERT INTO jobs (title, company, location, description, created_at) VALUES (?, ?, ?, ?, ?)", (title.strip(), company.strip(), location.strip(), description.strip(), datetime.utcnow().isoformat()))
                    st.success("Offre publiée.")
                    st.rerun()
                else:
                    st.error("Merci de remplir tous les champs.")
    with tabs[3]:
        members = fetch_all("SELECT id, first_name, last_name, flams_site, email, is_admin, created_at FROM users ORDER BY datetime(created_at) DESC")
        if members:
            for m in members:
                admin_badge = " • Admin" if m["is_admin"] else ""
                st.markdown(f'<div class="news-card"><div class="news-title">{m["first_name"]} {m["last_name"]}{admin_badge}</div><div class="news-body"><strong>E-mail :</strong> {m["email"]}<br><strong>Site :</strong> {m["flams_site"]}<br><strong>Inscription :</strong> {m["created_at"][:10]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">Aucun utilisateur enregistré.</div>', unsafe_allow_html=True)

def render_member_portal(user):
    render_topbar(user)
    left, right = st.columns([0.28, 0.72], gap="large")
    with left:
        render_member_sidebar(user)
    with right:
        page = st.session_state.page
        if page == "Accueil":
            render_home()
        elif page == "Actualités":
            render_news()
        elif page == "Événements":
            render_events()
        elif page == "Annuaire":
            render_directory()
        elif page == "Carrières":
            render_jobs()
        elif page == "Mon profil":
            render_profile(user)
        elif page == "Admin":
            render_admin(user)

init_db()
ensure_state()
user = current_user()
if user is None:
    render_public_top()
    st.write("")
    render_auth_forms()
else:
    render_member_portal(user)
