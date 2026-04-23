
import base64
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Flam'sily", page_icon="🔥", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "flamsily_v2.db"


# -----------------------------
# Utilities
# -----------------------------
def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def image_to_base64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


LOGO_DARK = image_to_base64(ASSETS_DIR / "logo_bdx.png")
LOGO_LIGHT = image_to_base64(ASSETS_DIR / "logo_beige.png")


# -----------------------------
# Database
# -----------------------------
def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            flams_site TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            password_hash TEXT NOT NULL,
            bio TEXT DEFAULT '',
            role TEXT NOT NULL DEFAULT 'member',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    admin = cur.execute("SELECT id FROM users WHERE email = ?", ("admin@flamsily.local",)).fetchone()
    if not admin:
        cur.execute("""
            INSERT INTO users (
                first_name, last_name, flams_site, age, email, phone, password_hash, bio, role, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Admin",
            "Flam'sily",
            "Siège",
            30,
            "admin@flamsily.local",
            "",
            hash_password("admin12345"),
            "Compte administrateur de démonstration.",
            "admin",
            datetime.utcnow().isoformat()
        ))

    news_count = cur.execute("SELECT COUNT(*) AS c FROM news").fetchone()["c"]
    if news_count == 0:
        sample_news = [
            ("Bienvenue sur Flam'sily", "Vie interne", "Le nouvel intranet Flam's est en ligne. Retrouvez vos actualités, votre profil et l'annuaire de la communauté.", "Admin"),
            ("Ouverture des inscriptions", "Réseau", "Les anciens et collaborateurs peuvent désormais créer leur compte directement depuis l'URL principale.", "Admin"),
            ("Semaine du terrain", "Événement", "Partagez vos souvenirs, vos photos et vos conseils dans l'espace communauté.", "Admin"),
        ]
        for title, category, content, author in sample_news:
            cur.execute("""
                INSERT INTO news (title, category, content, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title, category, content, author, datetime.utcnow().isoformat()))

    jobs_count = cur.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()["c"]
    if jobs_count == 0:
        sample_jobs = [
            ("Responsable de salle", "Strasbourg", "CDI", "Piloter l'équipe en salle, assurer l'expérience client et coordonner le service."),
            ("Manager adjoint", "Mulhouse", "CDI", "Accompagner le manager de site et suivre les indicateurs opérationnels."),
            ("Chargé(e) communication réseau", "Siège", "Alternance", "Valoriser les actualités du réseau Flam's et animer l'intranet."),
        ]
        for title, location, contract_type, description in sample_jobs:
            cur.execute("""
                INSERT INTO jobs (title, location, contract_type, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title, location, contract_type, description, datetime.utcnow().isoformat()))

    events_count = cur.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"]
    if events_count == 0:
        sample_events = [
            ("Afterwork Flam'sily", "2025-09-12", "Strasbourg", "Rencontre du réseau autour des actualités du groupe."),
            ("Session mentoring", "2025-10-03", "En ligne", "Échanges entre anciens, managers et nouveaux arrivants."),
        ]
        for title, event_date, location, description in sample_events:
            cur.execute("""
                INSERT INTO events (title, event_date, location, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title, event_date, location, description, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


# -----------------------------
# Data Access
# -----------------------------
def create_user(first_name: str, last_name: str, flams_site: str, age: int, email: str, phone: str, password: str) -> tuple[bool, str]:
    conn = get_conn()
    cur = conn.cursor()
    existing = cur.execute("SELECT id FROM users WHERE lower(email) = lower(?)", (email.strip(),)).fetchone()
    if existing:
        conn.close()
        return False, "Cet e-mail existe déjà."

    cur.execute("""
        INSERT INTO users (
            first_name, last_name, flams_site, age, email, phone, password_hash, bio, role, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        first_name.strip(),
        last_name.strip(),
        flams_site.strip(),
        int(age),
        email.strip().lower(),
        phone.strip(),
        hash_password(password),
        "",
        "member",
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    return True, "Compte créé avec succès."


def authenticate_user(email: str, password: str):
    conn = get_conn()
    row = conn.execute("""
        SELECT * FROM users WHERE lower(email) = lower(?) AND password_hash = ?
    """, (email.strip(), hash_password(password))).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def update_profile(user_id: int, flams_site: str, age: int, phone: str, bio: str) -> None:
    conn = get_conn()
    conn.execute("""
        UPDATE users
        SET flams_site = ?, age = ?, phone = ?, bio = ?
        WHERE id = ?
    """, (flams_site.strip(), int(age), phone.strip(), bio.strip(), user_id))
    conn.commit()
    conn.close()


def list_news():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM news ORDER BY datetime(created_at) DESC").fetchall()
    conn.close()
    return rows


def add_news(title: str, category: str, content: str, created_by: str) -> None:
    conn = get_conn()
    conn.execute("""
        INSERT INTO news (title, category, content, created_by, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (title.strip(), category.strip(), content.strip(), created_by.strip(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def list_jobs():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM jobs ORDER BY datetime(created_at) DESC").fetchall()
    conn.close()
    return rows


def add_job(title: str, location: str, contract_type: str, description: str) -> None:
    conn = get_conn()
    conn.execute("""
        INSERT INTO jobs (title, location, contract_type, description, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (title.strip(), location.strip(), contract_type.strip(), description.strip(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def list_events():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM events ORDER BY event_date ASC").fetchall()
    conn.close()
    return rows


def add_event(title: str, event_date: str, location: str, description: str) -> None:
    conn = get_conn()
    conn.execute("""
        INSERT INTO events (title, event_date, location, description, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (title.strip(), event_date, location.strip(), description.strip(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def list_members(search: str = ""):
    conn = get_conn()
    if search.strip():
        pattern = f"%{search.strip().lower()}%"
        rows = conn.execute("""
            SELECT id, first_name, last_name, flams_site, email, phone, role, created_at
            FROM users
            WHERE lower(first_name) LIKE ?
               OR lower(last_name) LIKE ?
               OR lower(flams_site) LIKE ?
               OR lower(email) LIKE ?
            ORDER BY first_name ASC, last_name ASC
        """, (pattern, pattern, pattern, pattern)).fetchall()
    else:
        rows = conn.execute("""
            SELECT id, first_name, last_name, flams_site, email, phone, role, created_at
            FROM users
            ORDER BY first_name ASC, last_name ASC
        """).fetchall()
    conn.close()
    return rows


# -----------------------------
# Session helpers
# -----------------------------
def init_session():
    if "auth_user_id" not in st.session_state:
        st.session_state.auth_user_id = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Accueil"


def current_user():
    user_id = st.session_state.auth_user_id
    if not user_id:
        return None
    return get_user_by_id(user_id)


def login_user(user_id: int):
    st.session_state.auth_user_id = user_id
    st.session_state.current_page = "Accueil"


def logout():
    st.session_state.auth_user_id = None
    st.session_state.auth_mode = "login"
    st.session_state.current_page = "Accueil"


# -----------------------------
# Styling
# -----------------------------
def inject_css():
    st.markdown(f"""
    <style>
    :root {{
        --bg: #f3f1eb;
        --card: #ffffff;
        --muted: #6f6c66;
        --text: #1e1b18;
        --red: #8e1d25;
        --red-2: #a82b33;
        --beige: #ece7d4;
        --line: #ded8cd;
        --soft: #f8f6f1;
    }}

    .stApp {{
        background: var(--bg);
        color: var(--text);
    }}

    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}

    [data-testid="stSidebar"] {{
        display: none;
    }}

    .block-container {{
        max-width: 1400px;
        padding-top: 0.8rem;
        padding-bottom: 2rem;
    }}

    div[data-testid="stForm"] {{
        border: 1px solid var(--line);
        background: var(--card);
        padding: 1.1rem 1.1rem 0.4rem 1.1rem;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(50,40,30,0.06);
    }}

    .hero-wrap {{
        display: grid;
        grid-template-columns: 390px 1fr;
        min-height: 92vh;
        background: var(--bg);
        gap: 24px;
        align-items: stretch;
    }}

    .auth-panel {{
        background: #f0efec;
        border-right: 1px solid #ddd6ca;
        padding: 24px 18px;
        min-height: 88vh;
    }}

    .auth-title {{
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 18px;
        color: #38342f;
    }}

    .auth-small {{
        color: var(--muted);
        font-size: 0.95rem;
        margin-bottom: 18px;
    }}

    .oauth-btn {{
        border: 1.5px solid #cb4a47;
        border-radius: 999px;
        padding: 14px 18px;
        background: white;
        font-weight: 700;
        margin-bottom: 12px;
        color: #cb4a47;
        text-align: center;
    }}

    .oauth-btn.primary {{
        background: #7b7575;
        color: white;
        border-color: #7b7575;
    }}

    .divider {{
        display:flex;
        align-items:center;
        color:#8a857f;
        font-size:0.9rem;
        margin: 18px 0;
    }}
    .divider:before, .divider:after {{
        content:"";
        flex:1;
        height:1px;
        background:#cfc8bc;
    }}
    .divider span {{ padding:0 10px; }}

    .hero-main {{
        padding: 20px 26px 24px 0;
    }}

    .top-brand {{
        background: #f7f4ed;
        border-radius: 0 0 24px 24px;
        padding: 20px 28px 14px 28px;
        border-bottom: 1px solid #e4ddcf;
    }}

    .brand-row {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 24px;
    }}

    .brand-left {{
        display:flex;
        align-items:center;
        gap: 18px;
    }}

    .brand-logo {{
        height: 84px;
        object-fit: contain;
    }}

    .brand-copy h1 {{
        margin:0;
        font-size: 2rem;
        color: var(--red);
        line-height: 1;
        font-weight: 900;
        letter-spacing: 0.2px;
    }}

    .brand-copy p {{
        margin: 8px 0 0 0;
        color: #7f7468;
        font-size: 0.98rem;
    }}

    .top-actions {{
        display:flex;
        align-items:center;
        gap: 12px;
    }}

    .pill {{
        background: var(--red);
        color: white;
        padding: 10px 16px;
        border-radius: 10px;
        font-weight: 800;
        display:inline-block;
        font-size: 0.92rem;
    }}

    .social-chip {{
        color: var(--red);
        font-weight: 900;
        font-size: 1.1rem;
    }}

    .main-nav {{
        margin-top: 14px;
        background: linear-gradient(90deg, var(--red), var(--red-2));
        border-radius: 10px;
        padding: 0;
        display:flex;
        align-items:center;
        overflow:hidden;
        min-height: 52px;
    }}

    .main-nav-item {{
        color: white;
        padding: 15px 20px;
        font-weight: 800;
        border-right: 1px solid rgba(255,255,255,0.15);
        font-size: 0.95rem;
    }}

    .landing-hero {{
        position: relative;
        margin-top: 26px;
        min-height: 420px;
        border-radius: 22px;
        overflow:hidden;
        background:
            linear-gradient(120deg, rgba(0,0,0,0.55), rgba(142,29,37,0.45)),
            radial-gradient(circle at 20% 30%, rgba(255,255,255,0.08), transparent 30%),
            linear-gradient(135deg, #3a1c1f 0%, #5d1e23 38%, #8e1d25 100%);
        box-shadow: 0 18px 50px rgba(60,35,25,0.18);
    }}

    .landing-hero-inner {{
        padding: 60px 54px;
        color: white;
        max-width: 720px;
    }}

    .landing-hero h2 {{
        font-size: 3rem;
        line-height: 1.05;
        margin: 0 0 12px 0;
        font-weight: 900;
    }}

    .landing-hero p {{
        font-size: 1.1rem;
        color: rgba(255,255,255,0.92);
        margin-bottom: 24px;
    }}

    .cta-row {{
        display:flex;
        gap: 14px;
        flex-wrap: wrap;
    }}

    .cta-main, .cta-alt {{
        display:inline-block;
        border-radius: 12px;
        padding: 14px 18px;
        font-weight: 800;
        text-decoration: none;
    }}

    .cta-main {{
        background: var(--beige);
        color: #34251d;
    }}

    .cta-alt {{
        border: 1px solid rgba(255,255,255,0.4);
        color: white;
        background: rgba(255,255,255,0.08);
    }}

    .cards-grid {{
        display:grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 18px;
        margin-top: 28px;
    }}

    .info-card {{
        background: #faf8f4;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 22px;
        min-height: 170px;
        box-shadow: 0 8px 24px rgba(70,50,35,0.06);
    }}

    .info-card h3 {{
        margin: 0 0 10px 0;
        color: #23313e;
        font-size: 1.35rem;
    }}

    .info-card p {{
        color: #5f5a54;
        font-size: 1rem;
        line-height: 1.55;
    }}

    .dashboard {{
        display:grid;
        grid-template-columns: 310px 1fr;
        gap: 20px;
        align-items: start;
    }}

    .sidebar {{
        background: #f4f1ea;
        border-radius: 22px;
        overflow: hidden;
        border: 1px solid #ddd4c6;
        position: sticky;
        top: 12px;
    }}

    .sidebar-top {{
        background: linear-gradient(180deg, #b22731, #8e1d25);
        color: white;
        padding: 20px 18px 18px 18px;
    }}

    .search-badge {{
        border-bottom: 1px solid rgba(255,255,255,0.3);
        padding-bottom: 10px;
        margin-bottom: 16px;
        color: rgba(255,255,255,0.92);
    }}

    .profile-chip {{
        display:flex;
        align-items:center;
        gap: 12px;
    }}

    .avatar {{
        width: 56px;
        height: 56px;
        border-radius: 999px;
        background: rgba(255,255,255,0.2);
        display:flex;
        align-items:center;
        justify-content:center;
        font-weight: 900;
        font-size: 1.4rem;
    }}

    .side-progress {{
        background: white;
        padding: 16px 18px;
        border-bottom: 1px solid #e2dbcf;
    }}

    .progress-pill {{
        border: 1.5px solid #c53f42;
        color: #c53f42;
        border-radius: 999px;
        text-align:center;
        font-weight: 800;
        padding: 8px 12px;
        margin-top: 10px;
    }}

    .side-link {{
        padding: 14px 18px;
        border-bottom: 1px solid #e7e0d4;
        cursor: pointer;
        color: #4b4641;
        font-weight: 700;
    }}

    .side-link.active {{
        background: #fffdf9;
        color: var(--red);
    }}

    .side-footer {{
        padding: 16px 18px;
        display:flex;
        align-items:center;
        justify-content:space-between;
    }}

    .page-shell {{
        background: transparent;
    }}

    .page-top {{
        background: #f7f4ed;
        border-radius: 22px 22px 0 0;
        padding: 18px 24px 10px 24px;
        border: 1px solid #e1d9cc;
        border-bottom: none;
    }}

    .page-title {{
        font-size: 2rem;
        font-weight: 900;
        color: #3a332d;
        margin: 0;
    }}

    .page-content {{
        background: #fffdf8;
        border: 1px solid #e1d9cc;
        border-radius: 0 0 22px 22px;
        padding: 24px;
        min-height: 70vh;
    }}

    .content-hero {{
        background:
            linear-gradient(120deg, rgba(255,255,255,0.88), rgba(255,255,255,0.58)),
            linear-gradient(120deg, #dfd4c0 0%, #f7efe0 50%, #d4c0aa 100%);
        border-radius: 18px;
        padding: 34px 36px;
        margin-bottom: 20px;
        border: 1px solid #e1d8cb;
    }}

    .content-hero h2 {{
        margin:0;
        font-size: 2rem;
        color:#2f2a25;
    }}

    .content-hero p {{
        margin: 10px 0 0 0;
        color:#5e564f;
        font-size:1.05rem;
    }}

    .grid-3 {{
        display:grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 18px;
    }}

    .mini-card {{
        background: #fff;
        border: 1px solid #e5ddcf;
        border-radius: 18px;
        padding: 22px;
        min-height: 180px;
        box-shadow: 0 8px 24px rgba(70,50,35,0.05);
    }}

    .mini-card h4 {{
        margin:0 0 8px 0;
        font-size:1.25rem;
        color:#2d323f;
    }}

    .mini-card p {{
        color:#655f58;
        line-height:1.6;
    }}

    .news-card {{
        background:#fff;
        border:1px solid #e5ddcf;
        border-radius:18px;
        padding:18px;
        margin-bottom:14px;
    }}

    .tag {{
        display:inline-block;
        background:#f3e5d8;
        color:#7a4930;
        padding:6px 10px;
        border-radius:999px;
        font-size:0.82rem;
        font-weight:800;
        margin-bottom:10px;
    }}

    .muted {{
        color: var(--muted);
    }}

    .logo-light-block {{
        display:flex;
        align-items:center;
        gap: 14px;
        margin-bottom: 16px;
    }}

    .logo-light {{
        height: 62px;
        object-fit: contain;
    }}

    .kpi-grid {{
        display:grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 18px;
    }}

    .kpi {{
        background:#fff;
        border:1px solid #e4dccf;
        border-radius:18px;
        padding:18px;
        text-align:center;
    }}

    .kpi .n {{
        font-size:2rem;
        font-weight:900;
        color:var(--red);
        line-height:1;
    }}

    .kpi .l {{
        margin-top:6px;
        color:#6a635c;
        font-weight:700;
    }}

    @media (max-width: 1100px) {{
        .hero-wrap, .dashboard {{
            grid-template-columns: 1fr;
        }}
        .cards-grid, .grid-3, .kpi-grid {{
            grid-template-columns: 1fr;
        }}
        .hero-main {{
            padding: 0 0 20px 0;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


# -----------------------------
# Components
# -----------------------------
def nav_button(label: str):
    if st.button(label, use_container_width=True):
        st.session_state.current_page = label
        st.rerun()


def render_public_shell():
    logo_html = f'<img class="brand-logo" src="data:image/png;base64,{LOGO_DARK}" />' if LOGO_DARK else ""
    st.markdown(f"""
    <div class="hero-wrap">
        <div class="auth-panel">
            <div class="auth-title">Accès membre</div>
            <div class="auth-small">Connectez-vous à l'intranet Flam'sily ou créez votre compte depuis l'URL principale.</div>
            <div class="oauth-btn primary">Connexion via Google</div>
            <div class="oauth-btn">Connexion via LinkedIn</div>
            <div class="oauth-btn">Connexion via Microsoft</div>
            <div class="divider"><span>ou</span></div>
        </div>
        <div class="hero-main">
            <div class="top-brand">
                <div class="brand-row">
                    <div class="brand-left">
                        {logo_html}
                        <div class="brand-copy">
                            <h1>Flam'sily</h1>
                            <p>Le réseau interne Flam's. Actualités, profils, annuaire, carrières et vie du réseau.</p>
                        </div>
                    </div>
                    <div class="top-actions">
                        <div class="pill">JE CONTRIBUE</div>
                        <div class="social-chip">f</div>
                        <div class="social-chip">in</div>
                        <div class="social-chip">▶</div>
                    </div>
                </div>
                <div class="main-nav">
                    <div class="main-nav-item">ACTUALITÉS</div>
                    <div class="main-nav-item">ÉVÉNEMENTS</div>
                    <div class="main-nav-item">MENTORING</div>
                    <div class="main-nav-item">L'ASSOCIATION</div>
                    <div class="main-nav-item">ANNUAIRE</div>
                    <div class="main-nav-item">CARRIÈRES</div>
                    <div class="main-nav-item">RÉSEAU</div>
                    <div class="main-nav-item">CONTACT</div>
                </div>
            </div>
            <div class="landing-hero">
                <div class="landing-hero-inner">
                    <h2>Je suis collaborateur, ancien ou membre du réseau Flam's</h2>
                    <p>Complétez votre profil, retrouvez la communauté, consultez les actualités du groupe et accédez à votre espace personnel.</p>
                    <div class="cta-row">
                        <a class="cta-main" href="#signup">Créer mon compte</a>
                        <a class="cta-alt" href="#login">Accéder à mon compte</a>
                    </div>
                </div>
            </div>
            <div class="cards-grid">
                <div class="info-card">
                    <h3>Annuaire Flam's</h3>
                    <p>Retrouvez les membres du réseau par site, nom ou e-mail et gardez le contact avec la communauté.</p>
                </div>
                <div class="info-card">
                    <h3>Actualités internes</h3>
                    <p>Suivez les annonces, les événements, les ouvertures et les temps forts du réseau Flam's.</p>
                </div>
                <div class="info-card">
                    <h3>Espace carrière</h3>
                    <p>Découvrez les opportunités internes, les besoins du siège et les ouvertures sur les établissements.</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_auth_forms():
    public_left, public_right = st.columns([0.95, 2.05], gap="large")

    with public_left:
        st.markdown('<div id="login"></div>', unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Connexion")
            email = st.text_input("Adresse mail")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Me connecter", use_container_width=True)
            if submitted:
                user = authenticate_user(email, password)
                if user:
                    login_user(user["id"])
                    st.success("Connexion réussie.")
                    st.rerun()
                else:
                    st.error("Identifiants invalides.")

        st.caption("Compte admin de test : admin@flamsily.local / admin12345")

    with public_right:
        st.markdown('<div id="signup"></div>', unsafe_allow_html=True)
        with st.form("signup_form", clear_on_submit=True):
            st.subheader("Créer mon compte")
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input("Prénom")
                flams_site = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
                email = st.text_input("E-mail")
                password = st.text_input("Mot de passe", type="password")
            with c2:
                last_name = st.text_input("Nom")
                age = st.number_input("Âge", min_value=16, max_value=90, value=25, step=1)
                phone = st.text_input("Téléphone (facultatif)")
                password_confirm = st.text_input("Confirmer le mot de passe", type="password")

            submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
            if submitted:
                missing = not all([first_name.strip(), last_name.strip(), flams_site.strip(), email.strip(), password.strip(), password_confirm.strip()])
                if missing:
                    st.error("Merci de remplir tous les champs obligatoires.")
                elif password != password_confirm:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password) < 8:
                    st.error("Le mot de passe doit contenir au moins 8 caractères.")
                else:
                    ok, message = create_user(first_name, last_name, flams_site, int(age), email, phone, password)
                    if ok:
                        st.success("Compte créé. Vous pouvez maintenant vous connecter.")
                    else:
                        st.error(message)


def render_sidebar(user):
    initials = f"{user['first_name'][:1]}{user['last_name'][:1]}".upper()
    progress = 42
    if user["phone"]:
        progress += 18
    if user["bio"]:
        progress += 20
    if user["age"]:
        progress += 10
    progress = min(progress, 100)

    st.markdown(f"""
    <div class="sidebar">
        <div class="sidebar-top">
            <div class="search-badge">◀︎ &nbsp; Rechercher</div>
            <div class="profile-chip">
                <div class="avatar">{initials}</div>
                <div>
                    <div style="font-size:1.55rem;font-weight:900;line-height:1;">{user['first_name'].upper()}</div>
                    <div style="font-size:0.96rem;opacity:0.92;">Voir mon profil</div>
                </div>
            </div>
        </div>
        <div class="side-progress">
            <div style="font-weight:700;color:#5e5750;">Votre profil est rempli à {progress}% !</div>
            <div class="progress-pill">Compléter mon profil</div>
        </div>
    """, unsafe_allow_html=True)

    pages = ["Accueil", "Actualités", "Événements", "Annuaire", "Carrières", "Mon profil"]
    if user["role"] == "admin":
        pages.append("Admin")

    for page in pages:
        active = "active" if st.session_state.current_page == page else ""
        st.markdown(f'<div class="side-link {active}">{page}</div>', unsafe_allow_html=True)
        if st.button(page, key=f"btn_{page}", use_container_width=True):
            st.session_state.current_page = page
            st.rerun()

    st.markdown(f"""
        <div class="side-footer">
            <span style="color:#8d857d;font-weight:700;">FR</span>
            <span style="color:#cc2f35;font-weight:900;">Flam'sily</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Se déconnecter", use_container_width=True):
        logout()
        st.rerun()


def render_kpis():
    users = list_members()
    news = list_news()
    jobs = list_jobs()
    events = list_events()
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi"><div class="n">{len(users)}</div><div class="l">membres</div></div>
        <div class="kpi"><div class="n">{len(news)}</div><div class="l">actualités</div></div>
        <div class="kpi"><div class="n">{len(events)}</div><div class="l">événements</div></div>
        <div class="kpi"><div class="n">{len(jobs)}</div><div class="l">offres</div></div>
    </div>
    """, unsafe_allow_html=True)


def render_home(user):
    st.markdown("""
    <div class="content-hero">
        <h2>Bienvenue sur votre intranet Flam'sily</h2>
        <p>Retrouvez vos actualités, votre réseau, les événements à venir et les opportunités du groupe dans un espace unique.</p>
    </div>
    """, unsafe_allow_html=True)

    render_kpis()

    st.markdown('<div class="grid-3">', unsafe_allow_html=True)
    st.markdown("""
        <div class="mini-card">
            <h4>Actualités du réseau</h4>
            <p>Consultez les dernières annonces du groupe, les temps forts internes et les messages importants du siège.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="mini-card">
            <h4>Mentoring & communauté</h4>
            <p>Créez des liens entre anciens, collaborateurs et managers pour partager conseils, expériences et opportunités.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="mini-card">
            <h4>Espace carrière</h4>
            <p>Découvrez les postes disponibles, les opportunités d'évolution et les besoins des établissements Flam's.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Dernières actualités")
    for item in list_news()[:3]:
        st.markdown(f"""
        <div class="news-card">
            <div class="tag">{item['category']}</div>
            <h4 style="margin:0 0 8px 0;">{item['title']}</h4>
            <div class="muted" style="margin-bottom:10px;">Publié par {item['created_by']} · {item['created_at'][:10]}</div>
            <div>{item['content']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_news_page():
    st.markdown("""
    <div class="content-hero">
        <h2>Actualités</h2>
        <p>Suivez les nouveautés du réseau, les ouvertures, les projets internes et les annonces importantes.</p>
    </div>
    """, unsafe_allow_html=True)
    for item in list_news():
        st.markdown(f"""
        <div class="news-card">
            <div class="tag">{item['category']}</div>
            <h4 style="margin:0 0 8px 0;">{item['title']}</h4>
            <div class="muted" style="margin-bottom:10px;">Publié par {item['created_by']} · {item['created_at'][:10]}</div>
            <div>{item['content']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_events_page():
    st.markdown("""
    <div class="content-hero">
        <h2>Événements</h2>
        <p>Retrouvez les dates importantes, les rencontres du réseau et les rendez-vous de la communauté Flam's.</p>
    </div>
    """, unsafe_allow_html=True)
    for item in list_events():
        st.markdown(f"""
        <div class="news-card">
            <div class="tag">{item['event_date']}</div>
            <h4 style="margin:0 0 8px 0;">{item['title']}</h4>
            <div class="muted" style="margin-bottom:10px;">{item['location']}</div>
            <div>{item['description']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_directory_page():
    st.markdown("""
    <div class="content-hero">
        <h2>Annuaire</h2>
        <p>Recherchez les membres du réseau Flam's par nom, établissement ou e-mail.</p>
    </div>
    """, unsafe_allow_html=True)
    search = st.text_input("Rechercher un membre")
    rows = list_members(search)
    if rows:
        data = []
        for row in rows:
            data.append({
                "Prénom": row["first_name"],
                "Nom": row["last_name"],
                "Flam's": row["flams_site"],
                "E-mail": row["email"],
                "Téléphone": row["phone"] or "",
                "Rôle": row["role"],
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("Aucun membre trouvé.")


def render_jobs_page():
    st.markdown("""
    <div class="content-hero">
        <h2>Carrières</h2>
        <p>Consultez les opportunités ouvertes au sein du réseau Flam's et du siège.</p>
    </div>
    """, unsafe_allow_html=True)
    for item in list_jobs():
        st.markdown(f"""
        <div class="news-card">
            <div class="tag">{item['contract_type']}</div>
            <h4 style="margin:0 0 8px 0;">{item['title']}</h4>
            <div class="muted" style="margin-bottom:10px;">{item['location']}</div>
            <div>{item['description']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_profile_page(user):
    st.markdown("""
    <div class="content-hero">
        <h2>Mon profil</h2>
        <p>Mettez à jour vos informations pour apparaître correctement dans l'annuaire et le réseau.</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Prénom", value=user["first_name"], disabled=True)
            st.text_input("Nom", value=user["last_name"], disabled=True)
            flams_site = st.text_input("Dans quelle Flam's avez-vous travaillé ?", value=user["flams_site"])
        with c2:
            age = st.number_input("Âge", min_value=16, max_value=90, value=int(user["age"]), step=1)
            st.text_input("E-mail", value=user["email"], disabled=True)
            phone = st.text_input("Téléphone", value=user["phone"] or "")
        bio = st.text_area("Bio / Présentation", value=user["bio"] or "", height=140)
        submitted = st.form_submit_button("Enregistrer mon profil", use_container_width=True)
        if submitted:
            update_profile(user["id"], flams_site, int(age), phone, bio)
            st.success("Profil mis à jour.")
            st.rerun()


def render_admin_page(user):
    st.markdown("""
    <div class="content-hero">
        <h2>Administration</h2>
        <p>Gérez les contenus de l'intranet : actualités, offres et événements.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Publier une actualité", "Ajouter une offre", "Ajouter un événement"])

    with tab1:
        with st.form("admin_news_form", clear_on_submit=True):
            title = st.text_input("Titre")
            category = st.selectbox("Catégorie", ["Vie interne", "Réseau", "Événement", "Carrière", "Annonce"])
            content = st.text_area("Contenu", height=150)
            if st.form_submit_button("Publier", use_container_width=True):
                if title.strip() and content.strip():
                    add_news(title, category, content, f"{user['first_name']} {user['last_name']}")
                    st.success("Actualité publiée.")
                    st.rerun()
                else:
                    st.error("Titre et contenu obligatoires.")

    with tab2:
        with st.form("admin_job_form", clear_on_submit=True):
            title = st.text_input("Poste")
            location = st.text_input("Lieu")
            contract_type = st.selectbox("Type de contrat", ["CDI", "CDD", "Alternance", "Stage", "Extra"])
            description = st.text_area("Description", height=150)
            if st.form_submit_button("Ajouter l'offre", use_container_width=True):
                if title.strip() and location.strip() and description.strip():
                    add_job(title, location, contract_type, description)
                    st.success("Offre ajoutée.")
                    st.rerun()
                else:
                    st.error("Merci de remplir tous les champs.")

    with tab3:
        with st.form("admin_event_form", clear_on_submit=True):
            title = st.text_input("Titre de l'événement")
            event_date = st.date_input("Date")
            location = st.text_input("Lieu")
            description = st.text_area("Description", height=150)
            if st.form_submit_button("Ajouter l'événement", use_container_width=True):
                if title.strip() and location.strip() and description.strip():
                    add_event(title, str(event_date), location, description)
                    st.success("Événement ajouté.")
                    st.rerun()
                else:
                    st.error("Merci de remplir tous les champs.")


def render_private_app():
    user = current_user()
    if not user:
        logout()
        st.rerun()

    left, right = st.columns([0.95, 2.05], gap="large")
    with left:
        render_sidebar(user)

    with right:
        page = st.session_state.current_page
        st.markdown(f"""
        <div class="page-shell">
            <div class="page-top"><h1 class="page-title">{page}</h1></div>
            <div class="page-content">
        """, unsafe_allow_html=True)

        if page == "Accueil":
            render_home(user)
        elif page == "Actualités":
            render_news_page()
        elif page == "Événements":
            render_events_page()
        elif page == "Annuaire":
            render_directory_page()
        elif page == "Carrières":
            render_jobs_page()
        elif page == "Mon profil":
            render_profile_page(user)
        elif page == "Admin" and user["role"] == "admin":
            render_admin_page(user)
        else:
            render_home(user)

        st.markdown("</div></div>", unsafe_allow_html=True)


# -----------------------------
# Main
# -----------------------------
init_db()
init_session()
inject_css()

if current_user():
    render_private_app()
else:
    render_public_shell()
    render_auth_forms()
