
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Flamsily", page_icon="🔥", layout="wide", initial_sidebar_state="collapsed")

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "flamsily.db"

def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_conn():
    ensure_dirs()
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
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        age INTEGER NOT NULL,
        phone TEXT,
        flams_site TEXT NOT NULL,
        city TEXT NOT NULL,
        role TEXT NOT NULL,
        entry_year TEXT NOT NULL,
        exit_year TEXT NOT NULL,
        bio TEXT DEFAULT '',
        is_admin INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        excerpt TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        place TEXT NOT NULL,
        starts_at TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")

    admin_email = "admin@flamsily.local"
    admin_pwd = hash_password("admin12345")
    cur.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    if cur.fetchone() is None:
        cur.execute("""
            INSERT INTO users (
                first_name, last_name, email, password_hash, age, phone, flams_site,
                city, role, entry_year, exit_year, bio, is_admin, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Admin", "Flamsily", admin_email, admin_pwd, 30, "", "Flam's Strasbourg",
            "Strasbourg", "Administration", "2020", "2025",
            "Compte administrateur Flamsily.", 1, datetime.utcnow().isoformat()
        ))

    cur.execute("SELECT COUNT(*) AS c FROM news")
    if cur.fetchone()["c"] == 0:
        demo_news = [
            ("Nouveau portail Flamsily", "Le nouvel intranet Flamsily est en ligne.", "Bienvenue dans le nouveau réseau Flamsily. Retrouvez les actualités, l'annuaire et les opportunités au même endroit.", "Actualité"),
            ("Rencontre anciens Flam's", "Une soirée réseau est organisée le mois prochain.", "Inscrivez-vous à la soirée réseau et retrouvez d'anciens collègues et collaborateurs Flam's.", "Événement"),
            ("Opportunité carrière", "Un poste de responsable de site est ouvert.", "Consultez les nouvelles offres dans la rubrique Carrières pour rejoindre un établissement du réseau.", "Carrière"),
        ]
        for title, excerpt, content, category in demo_news:
            cur.execute("INSERT INTO news (title, excerpt, content, category, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title, excerpt, content, category, datetime.utcnow().isoformat()))

    cur.execute("SELECT COUNT(*) AS c FROM events")
    if cur.fetchone()["c"] == 0:
        demo_events = [
            ("Afterwork Flamsily", "Strasbourg", "2026-05-15 19:00", "Un afterwork pour réunir la communauté Flam's autour des dernières actualités du réseau."),
            ("Session recrutement", "Nancy", "2026-06-02 09:00", "Rencontre entre anciens, managers et candidats autour des opportunités du groupe."),
        ]
        for title, place, starts_at, description in demo_events:
            cur.execute("INSERT INTO events (title, place, starts_at, description, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title, place, starts_at, description, datetime.utcnow().isoformat()))

    cur.execute("SELECT COUNT(*) AS c FROM jobs")
    if cur.fetchone()["c"] == 0:
        demo_jobs = [
            ("Responsable de salle", "Flam's Nancy", "Nancy", "Encadrement de l'équipe salle et expérience client."),
            ("Manager adjoint", "Flam's Strasbourg", "Strasbourg", "Pilotage opérationnel et accompagnement terrain."),
        ]
        for title, company, location, description in demo_jobs:
            cur.execute("INSERT INTO jobs (title, company, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title, company, location, description, datetime.utcnow().isoformat()))

    cur.execute("SELECT COUNT(*) AS c FROM messages")
    if cur.fetchone()["c"] == 0:
        demo_messages = [
            ("Équipe Flamsily", "Bienvenue", "Merci d'avoir rejoint Flamsily. Complétez votre profil pour apparaître dans l'annuaire."),
            ("Direction réseau", "Prochain rendez-vous", "Le prochain temps fort réseau sera annoncé dans la rubrique Événements."),
        ]
        for sender_name, subject, body in demo_messages:
            cur.execute("INSERT INTO messages (sender_name, subject, body, created_at) VALUES (?, ?, ?, ?)",
                        (sender_name, subject, body, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_logo_path(beige=False):
    p = ASSETS_DIR / ("logo_beige.png" if beige else "logo_bdx.png")
    return str(p) if p.exists() else ""

def get_user_by_email(email):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (email,)).fetchone()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row

def create_user(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (
            first_name, last_name, email, password_hash, age, phone, flams_site,
            city, role, entry_year, exit_year, bio, is_admin, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
    """, (
        data["first_name"], data["last_name"], data["email"], hash_password(data["password"]),
        data["age"], data["phone"], data["flams_site"], data["city"], data["role"],
        data["entry_year"], data["exit_year"], "", datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def update_profile(user_id, data):
    conn = get_conn()
    conn.execute("""
        UPDATE users SET first_name=?, last_name=?, age=?, phone=?, flams_site=?, city=?, role=?, entry_year=?, exit_year=?, bio=?
        WHERE id=?
    """, (
        data["first_name"], data["last_name"], data["age"], data["phone"], data["flams_site"],
        data["city"], data["role"], data["entry_year"], data["exit_year"], data["bio"], user_id
    ))
    conn.commit()
    conn.close()

def create_news(title, excerpt, content, category):
    conn = get_conn()
    conn.execute("INSERT INTO news (title, excerpt, content, category, created_at) VALUES (?, ?, ?, ?, ?)",
                 (title, excerpt, content, category, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def create_event(title, place, starts_at, description):
    conn = get_conn()
    conn.execute("INSERT INTO events (title, place, starts_at, description, created_at) VALUES (?, ?, ?, ?, ?)",
                 (title, place, starts_at, description, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def create_job(title, company, location, description):
    conn = get_conn()
    conn.execute("INSERT INTO jobs (title, company, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
                 (title, company, location, description, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def delete_row(table, row_id):
    conn = get_conn()
    conn.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def all_rows(query, params=()):
    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def login(email, password):
    user = get_user_by_email(email)
    if not user:
        return None
    return user if user["password_hash"] == hash_password(password) else None

def set_auth(user):
    st.session_state["user_id"] = user["id"]
    st.session_state["page"] = "Actualités"

def logout():
    for key in ["user_id", "page"]:
        if key in st.session_state:
            del st.session_state[key]

def public_css():
    st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"]{
        background:
            radial-gradient(circle at 20% 20%, rgba(120, 17, 33, 0.35), transparent 28%),
            radial-gradient(circle at 80% 30%, rgba(255, 220, 190, 0.12), transparent 20%),
            linear-gradient(135deg, #0e0a0a 0%, #191111 50%, #100d0d 100%) !important;
    }
    header[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {visibility:hidden;}
    [data-testid="collapsedControl"] {display:none;}
    .block-container{padding:0 !important; max-width:100% !important;}
    .public-shell{min-height:100vh; display:grid; grid-template-columns: 320px 1fr; background:#f4f1ea;}
    .left-auth{background:#f3f1ee; border-right:1px solid rgba(0,0,0,.08); min-height:100vh; padding:18px 14px; box-sizing:border-box;}
    .access-title{font-size:20px; font-weight:700; color:#3a3838; margin:4px 0 18px 0;}
    .oauth-btn{
        display:flex; align-items:center; gap:10px; border:1.5px solid #ef3a2f; border-radius:999px; padding:14px 18px;
        color:#ef3a2f; font-weight:700; margin-bottom:12px; background:#fff; font-size:14px;
    }
    .divider{display:flex; align-items:center; gap:10px; color:#8a8580; margin:22px 0 18px;}
    .divider::before, .divider::after{content:""; flex:1; height:1px; background:#ddd6ce;}
    .left-footer{position:absolute; bottom:18px; left:14px; right:14px; color:#6f6a66; font-size:14px;}
    .public-main{background:#f5f3ef; min-height:100vh;}
    .top-white{height:110px; background:#fff; display:flex; align-items:center; justify-content:space-between; padding:0 44px;}
    .brand-wrap{display:flex; align-items:center; gap:18px;}
    .brand-logo{height:64px;}
    .brand-title{font-size:28px; font-weight:800; color:#ef3126; line-height:1;}
    .brand-sub{font-size:18px; color:#ef3126; margin-top:6px;}
    .social-row{display:flex; align-items:center; gap:22px; color:#ef3126; font-weight:700;}
    .cta{background:#ef3126; color:white; padding:10px 16px; border-radius:4px; font-weight:700;}
    .red-nav{height:34px; background:#ef3126; color:#fff; display:flex; align-items:center; justify-content:center; gap:42px; font-weight:800; letter-spacing:.02em;}
    .hero{margin:62px 70px 0; border-radius:0; overflow:hidden; position:relative; height:330px;
          background:
            linear-gradient(rgba(32,14,14,.42), rgba(32,14,14,.42)),
            radial-gradient(circle at 30% 20%, rgba(255,255,255,.12), transparent 20%),
            linear-gradient(135deg,#4b1116 0%, #8d1a2b 35%, #1c1a20 100%);
          box-shadow: inset 0 0 0 1px rgba(255,255,255,.06);}
    .hero::before{
        content:""; position:absolute; inset:0;
        background:
           radial-gradient(circle at 15% 20%, rgba(255,230,220,.25), transparent 12%),
           radial-gradient(circle at 40% 40%, rgba(255,255,255,.15), transparent 8%),
           radial-gradient(circle at 70% 30%, rgba(255,160,160,.18), transparent 10%),
           radial-gradient(circle at 85% 70%, rgba(255,255,255,.12), transparent 10%);
        mix-blend-mode:screen;
    }
    .hero-content{position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#fff; text-align:center; z-index:1; padding:22px;}
    .hero-title{font-size:32px; font-weight:900; margin-bottom:8px;}
    .hero-sub{font-size:16px; margin-bottom:20px;}
    .hero-actions{display:flex; gap:16px; margin-top:10px;}
    .hero-btn{padding:16px 26px; border:1.5px solid rgba(255,255,255,.6); color:#fff; font-weight:800; min-width:340px; background:rgba(255,255,255,.08);}
    .section-title{margin:28px 0 18px; text-align:center; font-size:32px; font-weight:900; color:#202020;}
    .feature-grid{display:grid; grid-template-columns:repeat(3, 240px); gap:18px; justify-content:center; margin-bottom:36px;}
    .feature-card{background:#f8f7f5; border-radius:18px; box-shadow:0 0 0 1px rgba(0,0,0,.05); height:146px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#2a5fa8; font-weight:800;}
    .feature-icon{font-size:28px; margin-bottom:12px;}
    .bottom-pad{height:40px;}
    .stTextInput>div>div>input, .stNumberInput input, .stSelectbox div[data-baseweb="select"]>div{
        background:#f8f8f8 !important; border:none !important; border-bottom:1px solid #b6b1ac !important; border-radius:0 !important;
        color:#2a2a2a !important; box-shadow:none !important;
    }
    .stTextInput label, .stNumberInput label, .stSelectbox label{color:#807a76 !important; font-size:13px !important;}
    .stButton>button{
        width:100%; background:#ef3126 !important; color:#fff !important; border:none !important;
        border-radius:999px !important; padding:14px 18px !important; font-weight:800 !important; margin-top:8px !important;
    }
    .small-link{color:#4f7fd1; text-decoration:none; font-size:14px;}
    .left-note{color:#8a8580; font-size:14px; margin-top:18px;}
    .spacer16{height:16px;}
    .spacer8{height:8px;}
    @media (max-width: 1100px){
        .public-shell{grid-template-columns: 1fr;}
        .left-auth{min-height:auto;}
        .feature-grid{grid-template-columns:1fr; padding:0 20px;}
        .hero-actions{flex-direction:column;}
        .hero-btn{min-width:auto; width:100%;}
        .hero{margin:20px;}
        .top-white{padding:0 18px; height:auto; min-height:90px;}
        .red-nav{gap:16px; font-size:12px; padding:0 10px; overflow:auto;}
    }
    </style>
    """, unsafe_allow_html=True)

def private_css():
    st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"]{background:#ececec !important;}
    header[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {visibility:hidden;}
    [data-testid="collapsedControl"] {display:none;}
    .block-container{padding:0 !important; max-width:100% !important;}
    .app-shell{display:grid; grid-template-columns:240px 1fr; min-height:100vh;}
    .member-side{background:#ef3126; color:white; min-height:100vh; position:sticky; top:0;}
    .search-strip{padding:14px 16px 8px; border-bottom:1px solid rgba(255,255,255,.15);}
    .search-bar{padding:6px 0; border-bottom:1px solid rgba(255,255,255,.45); color:#ffd7d2;}
    .profile-box{padding:18px 16px; display:flex; align-items:center; gap:12px;}
    .avatar{width:44px; height:44px; border-radius:50%; background:#b7e9cf; color:#fff; display:flex; align-items:center; justify-content:center; font-size:22px;}
    .profile-name{font-weight:800; font-size:17px; line-height:1.1;}
    .profile-link{font-size:12px; opacity:.95;}
    .quick-icons{display:flex; justify-content:space-around; padding:14px 12px 18px; border-bottom:1px solid rgba(255,255,255,.12);}
    .completion{background:#fff; color:#565656; padding:16px 16px 12px;}
    .completion-btn{margin-top:12px; border:1.5px solid #ef3126; color:#ef3126; border-radius:999px; padding:8px 14px; font-weight:800; text-align:center;}
    .side-nav{background:#f7f7f7; color:#696969; min-height:calc(100vh - 230px);}
    .nav-item{padding:14px 18px; border-top:1px solid #e0e0e0; font-weight:600;}
    .nav-item.active{background:#f0f0f0; color:#1f1f1f;}
    .top-white{height:110px; background:#fff; display:flex; align-items:center; justify-content:space-between; padding:0 44px;}
    .brand-wrap{display:flex; align-items:center; gap:18px;}
    .brand-logo{height:64px;}
    .brand-title{font-size:28px; font-weight:800; color:#ef3126; line-height:1;}
    .brand-sub{font-size:18px; color:#ef3126; margin-top:6px;}
    .social-row{display:flex; align-items:center; gap:22px; color:#ef3126; font-weight:700;}
    .cta{background:#ef3126; color:white; padding:10px 16px; border-radius:4px; font-weight:700;}
    .red-nav{height:34px; background:#ef3126; color:#fff; display:flex; align-items:center; justify-content:center; gap:42px; font-weight:800; letter-spacing:.02em;}
    .content-wrap{padding:18px 22px 30px;}
    .page-head{font-size:24px; color:#363636; margin-bottom:12px; font-weight:500;}
    .soft-panel{background:#fff; border:1px solid #dddddd; padding:20px; border-radius:4px;}
    .hero-banner{
       height:170px; border-radius:3px;
       background:
         linear-gradient(rgba(255,255,255,.65), rgba(255,255,255,.65)),
         radial-gradient(circle at 75% 35%, rgba(0,0,0,.15), transparent 25%),
         linear-gradient(135deg, #a0b6ba 0%, #d9dede 45%, #b1c3c7 100%);
       position:relative; overflow:hidden;
    }
    .hero-banner::before{
       content:""; position:absolute; inset:0;
       background:
         radial-gradient(circle at 30% 50%, rgba(255,255,255,.72), transparent 18%),
         radial-gradient(circle at 63% 52%, rgba(0,0,0,.38), transparent 10%),
         radial-gradient(circle at 75% 52%, rgba(0,0,0,.38), transparent 10%),
         linear-gradient(120deg, transparent 0 56%, rgba(12,40,60,.18) 56% 100%);
    }
    .hero-title{
       position:absolute; left:18px; top:50%; transform:translateY(-50%);
       font-size:28px; font-weight:800; color:#263238; z-index:1;
    }
    .triple-grid{display:grid; grid-template-columns:repeat(3,1fr); gap:22px; margin-top:22px;}
    .info-card{background:#fff; border:1px solid #ededed; padding:18px; min-height:160px;}
    .info-card h3{font-size:22px; color:#374151; margin:0 0 14px;}
    .news-feed{display:grid; grid-template-columns:1.4fr .8fr; gap:20px;}
    .news-card{background:#fff; border:1px solid #ddd; padding:18px;}
    .news-title{font-size:22px; font-weight:800; color:#262626;}
    .news-meta{font-size:13px; color:#8a8a8a; margin:6px 0 12px;}
    .tag{display:inline-block; font-size:12px; padding:6px 10px; border-radius:999px; background:#f7dbd8; color:#b42622; font-weight:800; margin-bottom:10px;}
    .stat-grid{display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:20px;}
    .stat-card{background:#fff; border:1px solid #ddd; padding:16px;}
    .stat-label{font-size:12px; color:#8a8a8a; text-transform:uppercase; letter-spacing:.08em;}
    .stat-value{font-size:30px; font-weight:900; color:#272727; margin-top:8px;}
    .mini{font-size:13px; color:#666; margin-top:6px;}
    .directory-card{background:#fff; border:1px solid #ddd; padding:14px; margin-bottom:12px;}
    .user-name{font-size:20px; font-weight:800; color:#222;}
    .user-sub{color:#6f6f6f; margin-top:4px;}
    .admin-section{margin-top:24px;}
    .logout-btn {background:#ef3126; color:#fff; padding:8px 12px; border-radius:999px;}
    @media (max-width: 1200px){
      .app-shell{grid-template-columns:1fr;}
      .member-side{min-height:auto; position:relative;}
      .news-feed,.triple-grid,.stat-grid{grid-template-columns:1fr;}
      .red-nav{gap:16px; font-size:12px; padding:0 12px; overflow:auto;}
      .top-white{padding:0 18px;}
    }
    </style>
    """, unsafe_allow_html=True)

def init_state():
    if "page" not in st.session_state:
        st.session_state["page"] = "Actualités"

def public_left_panel():
    st.markdown('<div class="access-title">Accès membre</div>', unsafe_allow_html=True)
    st.markdown('<div class="oauth-btn">🟢 Connexion via Google</div>', unsafe_allow_html=True)
    st.markdown('<div class="oauth-btn">🔵 Connexion via LinkedIn</div>', unsafe_allow_html=True)
    st.markdown('<div class="oauth-btn">🟦 Connexion via Microsoft</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider">ou</div>', unsafe_allow_html=True)

def render_login_form():
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Adresse mail", placeholder="prenom.nom@email.com")
        password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
        submitted = st.form_submit_button("Me connecter")
        if submitted:
            user = login(email.strip(), password)
            if user:
                set_auth(user)
                st.rerun()
            else:
                st.error("Identifiants invalides.")
    st.markdown('<div style="text-align:right; margin-top:6px;"><a class="small-link" href="?mode=forgot" target="_self">Mot de passe oublié ?</a></div>', unsafe_allow_html=True)
    st.markdown('<div class="left-note">Pas encore de compte ? <a class="small-link" href="?mode=register" target="_self">M’inscrire</a></div>', unsafe_allow_html=True)

def render_register_form():
    with st.form("register_form", clear_on_submit=False):
        first_name = st.text_input("Prénom")
        last_name = st.text_input("Nom")
        email = st.text_input("Adresse mail")
        age = st.number_input("Âge", min_value=16, max_value=100, value=25)
        phone = st.text_input("Téléphone (facultatif)")
        flams_site = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
        city = st.text_input("Ville")
        role = st.text_input("Poste / rôle")
        entry_year = st.text_input("Année d'entrée")
        exit_year = st.text_input("Année de sortie")
        password = st.text_input("Mot de passe", type="password")
        confirm = st.text_input("Confirmer le mot de passe", type="password")
        submitted = st.form_submit_button("Créer mon compte")
        if submitted:
            required = [first_name, last_name, email, flams_site, city, role, entry_year, exit_year, password, confirm]
            if any(not str(v).strip() for v in required):
                st.error("Complète tous les champs obligatoires.")
            elif "@" not in email:
                st.error("Adresse e-mail invalide.")
            elif password != confirm:
                st.error("Les mots de passe ne correspondent pas.")
            elif get_user_by_email(email.strip()):
                st.error("Un compte existe déjà avec cet e-mail.")
            else:
                create_user({
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "email": email.strip(),
                    "age": int(age),
                    "phone": phone.strip(),
                    "flams_site": flams_site.strip(),
                    "city": city.strip(),
                    "role": role.strip(),
                    "entry_year": entry_year.strip(),
                    "exit_year": exit_year.strip(),
                    "password": password
                })
                user = login(email.strip(), password)
                set_auth(user)
                st.rerun()
    st.markdown('<div class="left-note">Déjà membre ? <a class="small-link" href="?mode=login" target="_self">Me connecter</a></div>', unsafe_allow_html=True)

def render_forgot_form():
    with st.form("forgot_form", clear_on_submit=False):
        email = st.text_input("Adresse mail")
        st.form_submit_button("Envoyer un e-mail de réinitialisation")
    st.info("Le reset par e-mail sera branché plus tard. Pour l’instant, utilise le compte admin de test ou recrée un compte.")
    st.markdown('<div class="left-note"><a class="small-link" href="?mode=login" target="_self">Retour à la connexion</a></div>', unsafe_allow_html=True)

def render_public():
    public_css()
    logo = get_logo_path()
    query = st.query_params
    mode = query.get("mode", "login")
    left, right = st.columns([0.32, 0.68], gap="small")
    with left:
        st.markdown('<div class="left-auth">', unsafe_allow_html=True)
        public_left_panel()
        if mode == "register":
            render_register_form()
        elif mode == "forgot":
            render_forgot_form()
        else:
            render_login_form()
        st.markdown('<div class="left-footer">FR</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown(f"""
        <div class="public-main">
          <div class="top-white">
            <div class="brand-wrap">
              <img class="brand-logo" src="data:image/png;base64,{img_to_b64(logo)}" />
              <div>
                <div class="brand-title">Flamsily</div>
                <div class="brand-sub">Espace alumni & communauté Flam's</div>
              </div>
            </div>
            <div class="social-row">
              <span class="cta">👍 JE COTISE !</span><span>f</span><span>in</span><span>YouTube</span>
            </div>
          </div>
          <div class="red-nav">
            <span>EVENEMENTS</span><span>MENTORING</span><span>L'ASSOCIATION</span><span>PORTRAITS</span>
            <span>ANNUAIRE</span><span>CARRIERES</span><span>RESEAU</span><span>CONTACT</span>
          </div>
          <div class="hero">
            <div class="hero-content">
              <div class="hero-title">je suis collaborateur ou ancien Flam's</div>
              <div class="hero-sub">Complétez votre profil et retrouvez votre réseau professionnel</div>
              <div class="hero-actions">
                <div class="hero-btn">ÉTUDIANTS ET DIPLÔMÉS<br/>ACCÉDEZ À VOTRE COMPTE</div>
                <div class="hero-btn">ENTREPRISES<br/>CRÉEZ VOTRE COMPTE</div>
              </div>
            </div>
          </div>
          <div class="section-title">Rejoignez la communauté Flamsily</div>
          <div class="feature-grid">
            <div class="feature-card"><div class="feature-icon">🪪</div>Annuaire des Flam's</div>
            <div class="feature-card"><div class="feature-icon">🌍</div>Ambassades locales & réseau</div>
            <div class="feature-card"><div class="feature-icon">💼</div>Espace carrière</div>
          </div>
          <div class="bottom-pad"></div>
        </div>
        """, unsafe_allow_html=True)

def img_to_b64(path):
    if not path:
        return ""
    import base64
    p = Path(path)
    if not p.exists():
        return ""
    return base64.b64encode(p.read_bytes()).decode()

def nav_button(label):
    if st.button(label, use_container_width=True):
        st.session_state["page"] = label
        st.rerun()

def render_member_sidebar(user):
    initials = f"{user['first_name'][:1]}{user['last_name'][:1]}".upper()
    completion = 42
    st.markdown(f"""
    <div class="member-side">
      <div class="search-strip">
        <div class="search-bar">‹ &nbsp;&nbsp;🔍 Rechercher</div>
      </div>
      <div class="profile-box">
        <div class="avatar">{initials}</div>
        <div>
          <div class="profile-name">{user['first_name'].upper()}</div>
          <div class="profile-link">Voir mon profil</div>
        </div>
      </div>
      <div class="quick-icons">✉️ &nbsp;&nbsp; 🔔 &nbsp;&nbsp; 👥</div>
      <div class="completion">
        <div>Votre profil est rempli à {completion}% !</div>
        <div class="completion-btn">Compléter mon profil</div>
        <div style="margin-top:14px;">🏅 Merci d'avoir cotisé !</div>
      </div>
      <div class="side-nav">
    """, unsafe_allow_html=True)
    pages = ["Accueil", "Actualités", "Événements", "Annuaire", "Carrières", "Réseau", "Messages", "Mon profil", "Paramètres"]
    if user["is_admin"]:
        pages.append("Admin")
    for page in pages:
        active = " active" if st.session_state["page"] == page else ""
        st.markdown(f'<div class="nav-item{active}">{page}</div>', unsafe_allow_html=True)
        if st.button(page, key=f"nav_{page}", use_container_width=True):
            st.session_state["page"] = page
            st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

def render_private_shell(user):
    private_css()
    logo = get_logo_path()
    left, right = st.columns([0.19, 0.81], gap="small")
    with left:
        render_member_sidebar(user)
    with right:
        st.markdown(f"""
        <div class="top-white">
            <div class="brand-wrap">
              <img class="brand-logo" src="data:image/png;base64,{img_to_b64(logo)}" />
              <div>
                <div class="brand-title">Flamsily</div>
                <div class="brand-sub">Réseau & communauté Flam's</div>
              </div>
            </div>
            <div class="social-row">
              <span class="cta">👍 JE COTISE !</span><span>f</span><span>in</span><span>YouTube</span>
            </div>
          </div>
          <div class="red-nav">
            <span>ACTUALITES</span><span>EVENEMENTS</span><span>MENTORING</span><span>L'ASSOCIATION</span><span>PORTRAITS</span>
            <span>ANNUAIRE</span><span>CARRIERES</span><span>RESEAU</span><span>COTISER</span>
          </div>
        """, unsafe_allow_html=True)
        render_page_content(user)

def render_page_content(user):
    page = st.session_state["page"]
    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)
    if page == "Accueil":
        users = all_rows("SELECT * FROM users ORDER BY created_at DESC")
        news = all_rows("SELECT * FROM news ORDER BY created_at DESC")
        events = all_rows("SELECT * FROM events ORDER BY starts_at ASC")
        jobs = all_rows("SELECT * FROM jobs ORDER BY created_at DESC")
        st.markdown('<div class="page-head">Accueil</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-grid">
          <div class="stat-card"><div class="stat-label">Membres</div><div class="stat-value">{len(users)}</div><div class="mini">inscrits dans la communauté</div></div>
          <div class="stat-card"><div class="stat-label">Actualités</div><div class="stat-value">{len(news)}</div><div class="mini">publiées récemment</div></div>
          <div class="stat-card"><div class="stat-label">Événements</div><div class="stat-value">{len(events)}</div><div class="mini">à venir</div></div>
          <div class="stat-card"><div class="stat-label">Offres</div><div class="stat-value">{len(jobs)}</div><div class="mini">carrière & réseau</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="hero-banner"><div class="hero-title">Bienvenue sur votre réseau Flamsily</div></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="triple-grid">
          <div class="info-card"><h3>Restez connecté</h3>Suivez les actualités du réseau, les nouvelles opportunités et les temps forts à venir.</div>
          <div class="info-card"><h3>Retrouvez la communauté</h3>Explorez l'annuaire complet, par site, ville, poste ou période.</div>
          <div class="info-card"><h3>Activez votre réseau</h3>Profitez des offres, messages et événements pour rester visible.</div>
        </div>
        """, unsafe_allow_html=True)
    elif page == "Actualités":
        rows = all_rows("SELECT * FROM news ORDER BY created_at DESC")
        st.markdown('<div class="page-head">Actualités</div>', unsafe_allow_html=True)
        st.markdown('<div class="news-feed">', unsafe_allow_html=True)
        col1, col2 = st.columns([1.4, .8], gap="large")
        with col1:
            for row in rows:
                st.markdown(f"""
                <div class="news-card">
                  <div class="tag">{row['category']}</div>
                  <div class="news-title">{row['title']}</div>
                  <div class="news-meta">{row['created_at'][:10]}</div>
                  <div>{row['excerpt']}</div>
                  <div style="margin-top:12px; color:#555;">{row['content']}</div>
                </div><div style="height:14px;"></div>
                """, unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="soft-panel"><b>À la une</b><br/><br/>Toutes les nouveautés du réseau, les rendez-vous à venir et les opportunités publiées par l’équipe Flamsily.</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
            events = all_rows("SELECT * FROM events ORDER BY starts_at ASC LIMIT 3")
            for ev in events:
                st.markdown(f'<div class="soft-panel"><b>{ev["title"]}</b><br/>{ev["place"]} · {ev["starts_at"]}<br/><br/>{ev["description"]}</div><div style="height:12px;"></div>', unsafe_allow_html=True)
    elif page == "Annuaire":
        st.markdown('<div class="page-head">Annuaire</div>', unsafe_allow_html=True)
        q = st.text_input("Rechercher par nom, email, ville, site, rôle, année ou téléphone")
        users = all_rows("SELECT * FROM users ORDER BY last_name, first_name")
        ql = q.lower().strip()
        filtered = []
        for u in users:
            hay = " ".join([str(u[k] or "") for k in u.keys()]).lower()
            if not ql or ql in hay:
                filtered.append(u)
        for u in filtered:
            st.markdown(f"""
            <div class="directory-card">
              <div class="user-name">{u['first_name']} {u['last_name']}</div>
              <div class="user-sub">{u['role']} · {u['city']} · {u['flams_site']}</div>
              <div class="user-sub">{u['email']} · {u['phone'] or 'Téléphone non renseigné'}</div>
              <div class="user-sub">Entrée {u['entry_year']} · Sortie {u['exit_year']}</div>
            </div>
            """, unsafe_allow_html=True)
        if not filtered:
            st.info("Aucun membre trouvé.")
    elif page == "Événements":
        st.markdown('<div class="page-head">Événements</div>', unsafe_allow_html=True)
        rows = all_rows("SELECT * FROM events ORDER BY starts_at ASC")
        for row in rows:
            st.markdown(f'<div class="soft-panel"><b>{row["title"]}</b><br/>{row["place"]} · {row["starts_at"]}<br/><br/>{row["description"]}</div><div style="height:12px;"></div>', unsafe_allow_html=True)
    elif page == "Carrières":
        st.markdown('<div class="page-head">Carrières</div>', unsafe_allow_html=True)
        rows = all_rows("SELECT * FROM jobs ORDER BY created_at DESC")
        for row in rows:
            st.markdown(f'<div class="soft-panel"><b>{row["title"]}</b><br/>{row["company"]} · {row["location"]}<br/><br/>{row["description"]}</div><div style="height:12px;"></div>', unsafe_allow_html=True)
    elif page == "Réseau":
        st.markdown('<div class="page-head">Réseau</div>', unsafe_allow_html=True)
        st.markdown('<div class="soft-panel">Cette rubrique servira à mettre en avant les groupes, les initiatives locales et les portraits de la communauté.</div>', unsafe_allow_html=True)
    elif page == "Messages":
        st.markdown('<div class="page-head">Messages</div>', unsafe_allow_html=True)
        rows = all_rows("SELECT * FROM messages ORDER BY created_at DESC")
        for row in rows:
            st.markdown(f'<div class="soft-panel"><b>{row["subject"]}</b><br/>Par {row["sender_name"]}<br/><br/>{row["body"]}</div><div style="height:12px;"></div>', unsafe_allow_html=True)
        st.info("Le vrai module de messagerie pourra être branché plus tard.")
    elif page == "Mon profil":
        st.markdown('<div class="page-head">Mon profil</div>', unsafe_allow_html=True)
        with st.form("profile_form"):
            first_name = st.text_input("Prénom", value=user["first_name"])
            last_name = st.text_input("Nom", value=user["last_name"])
            age = st.number_input("Âge", min_value=16, max_value=100, value=int(user["age"]))
            phone = st.text_input("Téléphone", value=user["phone"] or "")
            flams_site = st.text_input("Flam's", value=user["flams_site"])
            city = st.text_input("Ville", value=user["city"])
            role = st.text_input("Poste / rôle", value=user["role"])
            entry_year = st.text_input("Année d'entrée", value=user["entry_year"])
            exit_year = st.text_input("Année de sortie", value=user["exit_year"])
            bio = st.text_area("Bio", value=user["bio"] or "")
            if st.form_submit_button("Enregistrer"):
                update_profile(user["id"], {
                    "first_name": first_name, "last_name": last_name, "age": int(age), "phone": phone,
                    "flams_site": flams_site, "city": city, "role": role, "entry_year": entry_year,
                    "exit_year": exit_year, "bio": bio
                })
                st.success("Profil mis à jour.")
                st.rerun()
    elif page == "Paramètres":
        st.markdown('<div class="page-head">Paramètres</div>', unsafe_allow_html=True)
        st.markdown('<div class="soft-panel">Paramètres du compte, préférences d’affichage et langue pourront être enrichis ici.</div>', unsafe_allow_html=True)
        if st.button("Se déconnecter"):
            logout()
            st.rerun()
    elif page == "Admin" and user["is_admin"]:
        st.markdown('<div class="page-head">Admin</div>', unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(["Actualités", "Événements", "Carrières", "Membres"])
        with tab1:
            with st.form("news_admin"):
                title = st.text_input("Titre")
                excerpt = st.text_input("Résumé")
                content = st.text_area("Contenu")
                category = st.selectbox("Catégorie", ["Actualité", "Événement", "Carrière", "Communauté"])
                if st.form_submit_button("Publier l’actualité"):
                    create_news(title, excerpt, content, category)
                    st.success("Actualité publiée.")
                    st.rerun()
            for row in all_rows("SELECT * FROM news ORDER BY created_at DESC"):
                c1, c2 = st.columns([0.9, 0.1])
                with c1:
                    st.markdown(f'<div class="soft-panel"><b>{row["title"]}</b><br/>{row["excerpt"]}</div>', unsafe_allow_html=True)
                with c2:
                    if st.button("Supprimer", key=f"del_news_{row['id']}"):
                        delete_row("news", row["id"])
                        st.rerun()
        with tab2:
            with st.form("event_admin"):
                title = st.text_input("Titre événement")
                place = st.text_input("Lieu")
                starts_at = st.text_input("Date et heure", placeholder="2026-06-01 19:00")
                description = st.text_area("Description")
                if st.form_submit_button("Publier l’événement"):
                    create_event(title, place, starts_at, description)
                    st.success("Événement publié.")
                    st.rerun()
            for row in all_rows("SELECT * FROM events ORDER BY starts_at ASC"):
                c1, c2 = st.columns([0.9, 0.1])
                with c1:
                    st.markdown(f'<div class="soft-panel"><b>{row["title"]}</b><br/>{row["place"]} · {row["starts_at"]}</div>', unsafe_allow_html=True)
                with c2:
                    if st.button("Supprimer", key=f"del_event_{row['id']}"):
                        delete_row("events", row["id"])
                        st.rerun()
        with tab3:
            with st.form("job_admin"):
                title = st.text_input("Titre offre")
                company = st.text_input("Entreprise")
                location = st.text_input("Ville")
                description = st.text_area("Description du poste")
                if st.form_submit_button("Publier l’offre"):
                    create_job(title, company, location, description)
                    st.success("Offre publiée.")
                    st.rerun()
            for row in all_rows("SELECT * FROM jobs ORDER BY created_at DESC"):
                c1, c2 = st.columns([0.9, 0.1])
                with c1:
                    st.markdown(f'<div class="soft-panel"><b>{row["title"]}</b><br/>{row["company"]} · {row["location"]}</div>', unsafe_allow_html=True)
                with c2:
                    if st.button("Supprimer", key=f"del_job_{row['id']}"):
                        delete_row("jobs", row["id"])
                        st.rerun()
        with tab4:
            rows = all_rows("SELECT * FROM users ORDER BY created_at DESC")
            for row in rows:
                c1, c2 = st.columns([0.9, 0.1])
                with c1:
                    st.markdown(f'<div class="soft-panel"><b>{row["first_name"]} {row["last_name"]}</b><br/>{row["email"]} · {row["role"]} · {row["city"]}</div>', unsafe_allow_html=True)
                with c2:
                    if row["email"] != "admin@flamsily.local" and st.button("Suppr.", key=f"del_user_{row['id']}"):
                        delete_row("users", row["id"])
                        st.rerun()
    else:
        st.session_state["page"] = "Actualités"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    init_db()
    init_state()
    if st.session_state.get("user_id"):
        user = get_user_by_id(st.session_state["user_id"])
        if not user:
            logout()
            render_public()
        else:
            render_private_shell(user)
    else:
        render_public()

if __name__ == "__main__":
    main()
