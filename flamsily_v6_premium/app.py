
from __future__ import annotations
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
import streamlit as st

# ---------- App config ----------
st.set_page_config(
    page_title="Flamsily",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "flamsily.db"

# ---------- Database ----------
def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            site_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            author_email TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            location TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            """
            INSERT INTO users
            (first_name, last_name, site_name, age, email, phone, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Admin",
                "Flamsily",
                "Siège",
                30,
                "admin@flamsily.local",
                "",
                hash_password("admin12345"),
                1,
                datetime.utcnow().isoformat(),
            ),
        )

    cur.execute("SELECT COUNT(*) AS c FROM news")
    if cur.fetchone()["c"] == 0:
        now = datetime.utcnow().isoformat()
        cur.executemany(
            "INSERT INTO news (title, category, content, created_at, author_email) VALUES (?, ?, ?, ?, ?)",
            [
                ("Bienvenue sur Flamsily", "Actualité", "Votre nouvel intranet Flam's est en ligne. Retrouvez ici les nouvelles, l'annuaire et les opportunités.", now, "admin@flamsily.local"),
                ("Soirée réseau interne", "Événement", "Un afterwork de lancement est proposé jeudi à 19h pour rencontrer les équipes et anciens collaborateurs.", now, "admin@flamsily.local"),
            ],
        )

    cur.execute("SELECT COUNT(*) AS c FROM jobs")
    if cur.fetchone()["c"] == 0:
        now = datetime.utcnow().isoformat()
        cur.executemany(
            "INSERT INTO jobs (title, location, contract_type, summary, created_at) VALUES (?, ?, ?, ?, ?)",
            [
                ("Manager de restaurant", "Bordeaux", "CDI", "Pilotage équipe, qualité de service, animation commerciale.", now),
                ("Responsable communication réseau", "Paris", "CDD", "Gestion marque employeur, actualités internes et événements.", now),
            ],
        )

    cur.execute("SELECT COUNT(*) AS c FROM events")
    if cur.fetchone()["c"] == 0:
        now = datetime.utcnow().isoformat()
        cur.executemany(
            "INSERT INTO events (title, event_date, location, summary, created_at) VALUES (?, ?, ?, ?, ?)",
            [
                ("Lancement Flamsily", "2026-05-15", "Visio", "Présentation du nouvel intranet et des modules membres.", now),
                ("Rencontre réseau Flam's", "2026-06-03", "Strasbourg", "Networking, alumni et témoignages métiers.", now),
            ],
        )
    conn.commit()
    conn.close()

def get_user_by_email(email: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (email.strip(),)).fetchone()
    conn.close()
    return row

def create_user(first_name, last_name, site_name, age, email, phone, password):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO users
        (first_name, last_name, site_name, age, email, phone, password_hash, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (first_name, last_name, site_name, age, email.strip().lower(), phone, hash_password(password), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

def authenticate(email: str, password: str):
    user = get_user_by_email(email)
    if user and user["password_hash"] == hash_password(password):
        return user
    return None

def fetch_all(query: str, params=()):
    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def execute(query: str, params=()):
    conn = get_conn()
    conn.execute(query, params)
    conn.commit()
    conn.close()

# ---------- Helpers ----------
def load_logo(path: Path) -> str | None:
    return str(path) if path.exists() else None

def fmt_dt(raw: str) -> str:
    try:
        return datetime.fromisoformat(raw).strftime("%d/%m/%Y")
    except Exception:
        return raw

def safe_count(table_name: str) -> int:
    conn = get_conn()
    n = conn.execute(f"SELECT COUNT(*) as c FROM {table_name}").fetchone()["c"]
    conn.close()
    return n

def logout():
    st.session_state["auth_user"] = None
    st.session_state["route"] = "landing"
    st.rerun()

def login_user(user_row):
    st.session_state["auth_user"] = dict(user_row)
    st.session_state["route"] = "dashboard"
    st.rerun()

# ---------- CSS ----------
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #08090d;
            --panel: rgba(13, 16, 25, 0.76);
            --panel-soft: rgba(255,255,255,0.05);
            --card: rgba(255,255,255,0.045);
            --stroke: rgba(255,255,255,0.11);
            --text: #f7f1e8;
            --muted: #b9afa3;
            --accent: #8f1020;
            --accent-2: #d83d58;
            --accent-3: #ffb58a;
            --success: #77e2b2;
            --shadow: 0 20px 60px rgba(0,0,0,.35);
            --radius-xl: 30px;
            --radius-lg: 24px;
            --radius-md: 18px;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
            background:
              radial-gradient(circle at 15% 15%, rgba(216,61,88,0.22), transparent 22%),
              radial-gradient(circle at 80% 10%, rgba(255,181,138,0.12), transparent 20%),
              radial-gradient(circle at 70% 80%, rgba(143,16,32,0.18), transparent 28%),
              linear-gradient(135deg, #06070b 0%, #0a0c12 40%, #0c0f18 100%);
            color: var(--text);
        }

        [data-testid="collapsedControl"], [data-testid="stSidebar"], header[data-testid="stHeader"] {
            display: none !important;
        }

        .block-container {
            max-width: 1440px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        .brand-shell, .glass-card, .topbar, .rail-card, .content-card, .auth-card, .metric-card, .tile-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.03));
            backdrop-filter: blur(18px);
            border: 1px solid rgba(255,255,255,.09);
            box-shadow: var(--shadow);
        }

        .topbar {
            border-radius: 28px;
            padding: 18px 22px;
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap: 18px;
            margin-bottom: 18px;
        }

        .brand-inline {
            display:flex;
            align-items:center;
            gap: 16px;
        }

        .brand-logo {
            width: 74px;
            height: 74px;
            object-fit: contain;
            border-radius: 18px;
            background: rgba(255,255,255,0.9);
            padding: 8px;
            box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
        }

        .brand-title {
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1;
            margin: 0;
        }

        .brand-subtitle {
            margin-top: 6px;
            color: var(--muted);
            font-size: 0.98rem;
        }

        .nav-pills {
            display:flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content:flex-end;
        }

        .pill {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            gap: 8px;
            min-height: 44px;
            padding: 0 18px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.04);
            color: var(--text);
            font-weight: 600;
        }

        .hero-shell {
            position: relative;
            min-height: 76vh;
            border-radius: 34px;
            overflow: hidden;
            padding: 36px;
            background:
              radial-gradient(circle at 80% 20%, rgba(255,183,140,0.24), transparent 18%),
              radial-gradient(circle at 18% 18%, rgba(216,61,88,0.25), transparent 18%),
              linear-gradient(135deg, rgba(17,18,27,0.86), rgba(10,12,18,0.74));
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: var(--shadow);
        }

        .hero-shell:before {
            content:'';
            position:absolute;
            inset:-30%;
            background:
              conic-gradient(from 180deg at 50% 50%, rgba(143,16,32,.0), rgba(143,16,32,.32), rgba(216,61,88,.0), rgba(255,181,138,.12), rgba(143,16,32,.0));
            filter: blur(50px);
            opacity:.9;
            animation: spinGlow 18s linear infinite;
            pointer-events:none;
        }

        @keyframes spinGlow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .hero-grid {
            position: relative;
            z-index: 2;
            display:grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 28px;
            align-items: stretch;
        }

        .headline {
            font-size: clamp(3rem, 5vw, 5.6rem);
            line-height: .92;
            letter-spacing: -0.06em;
            margin: 0 0 16px 0;
            font-weight: 900;
            max-width: 760px;
        }

        .headline-gradient {
            background: linear-gradient(90deg, #fff6e9 0%, #ffd7c0 36%, #ff8aa0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-copy {
            color: #d9cdbf;
            font-size: 1.12rem;
            line-height: 1.7;
            max-width: 720px;
            margin-bottom: 24px;
        }

        .eyebrow {
            display:inline-flex;
            align-items:center;
            gap: 10px;
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.08);
            color: #fff4e7;
            border-radius: 999px;
            padding: 12px 16px;
            font-weight: 700;
            margin-bottom: 18px;
        }

        .metric-row {
            display:grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 24px;
        }

        .metric-card {
            border-radius: 22px;
            padding: 18px 20px;
            background: linear-gradient(180deg, rgba(255,255,255,.09), rgba(255,255,255,.04));
            transition: transform .25s ease, border-color .25s ease, background .25s ease;
        }

        .metric-card:hover, .tile-card:hover, .content-card:hover {
            transform: translateY(-5px);
            border-color: rgba(255,181,138,.28);
            background: linear-gradient(180deg, rgba(255,255,255,.11), rgba(255,255,255,.05));
        }

        .metric-label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: .72rem;
            margin-bottom: 10px;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: #fff6ec;
        }

        .auth-card {
            position: relative;
            z-index: 2;
            border-radius: 30px;
            padding: 24px;
            background: linear-gradient(180deg, rgba(7,8,12,.82), rgba(18,21,31,.8));
        }

        .auth-title {
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .small-muted { color: var(--muted); font-size: 0.96rem; }

        .wow-strip {
            display:grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-top: 18px;
        }

        .tile-card {
            border-radius: 22px;
            padding: 18px;
            min-height: 140px;
        }

        .tile-emoji {
            font-size: 1.6rem;
            margin-bottom: 10px;
        }

        .section-title {
            font-size: 1.9rem;
            font-weight: 800;
            margin: 0 0 14px 0;
            letter-spacing: -.03em;
        }

        .dashboard-grid {
            display:grid;
            grid-template-columns: 320px 1fr;
            gap: 18px;
        }

        .rail-card, .content-card {
            border-radius: 28px;
            padding: 22px;
        }

        .profile-badge {
            display:flex;
            align-items:center;
            gap: 14px;
            margin-bottom: 20px;
        }

        .avatar-xl {
            width: 66px;
            height: 66px;
            border-radius: 22px;
            background: linear-gradient(135deg, var(--accent), #ff855f);
            display:flex;
            align-items:center;
            justify-content:center;
            font-weight: 900;
            font-size: 1.45rem;
            color: white;
            box-shadow: 0 14px 28px rgba(143,16,32,.35);
        }

        .menu-note {
            color: var(--muted);
            font-size: .88rem;
            margin-bottom: 12px;
        }

        .feature-pill {
            display:inline-flex;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,.05);
            border: 1px solid rgba(255,255,255,.08);
            color: #eee4d8;
            font-size: .85rem;
            margin: 4px 6px 0 0;
        }

        .hero-dashboard {
            border-radius: 28px;
            padding: 28px;
            background:
              radial-gradient(circle at 85% 12%, rgba(255,181,138,.18), transparent 18%),
              linear-gradient(135deg, rgba(123,10,26,.95), rgba(42,14,20,.98));
            min-height: 250px;
            display:flex;
            align-items:flex-end;
            position:relative;
            overflow:hidden;
            box-shadow: var(--shadow);
        }

        .hero-dashboard:after {
            content:"";
            position:absolute;
            inset:auto -15% -35% auto;
            width:320px;
            height:320px;
            background: radial-gradient(circle, rgba(255,255,255,0.18), transparent 60%);
            filter: blur(10px);
        }

        .hero-dashboard h1 {
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: .98;
            letter-spacing: -.05em;
            margin: 0 0 12px 0;
            max-width: 720px;
        }

        .hero-dashboard p {
            max-width: 650px;
            color: #f0ded2;
            font-size: 1.03rem;
            line-height: 1.7;
            margin: 0;
        }

        .dashboard-cards {
            display:grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 16px;
        }

        .news-item, .list-item {
            padding: 18px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,.08);
            background: rgba(255,255,255,.03);
            margin-bottom: 12px;
        }

        .eyebadge {
            display:inline-flex;
            align-items:center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.08);
            color: #f8ede2;
            font-size: .82rem;
            margin-bottom: 12px;
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 800;
            margin: 0 0 8px 0;
            letter-spacing: -.03em;
        }

        .subtle {
            color: var(--muted);
            font-size: 0.93rem;
            line-height: 1.6;
        }

        .split-2 {
            display:grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 48px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,.12);
            background: linear-gradient(135deg, #8f1020, #cd445e);
            color: white;
            font-weight: 800;
            font-size: 0.98rem;
            box-shadow: 0 18px 38px rgba(143,16,32,.28);
            transition: transform .18s ease, filter .18s ease, box-shadow .18s ease;
        }

        div[data-testid="stButton"] > button:hover {
            transform: translateY(-2px);
            filter: brightness(1.05);
            box-shadow: 0 24px 46px rgba(143,16,32,.32);
            border-color: rgba(255,255,255,.24);
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stDateInput"] input {
            border-radius: 16px !important;
            background: rgba(255,255,255,.05) !important;
            border: 1px solid rgba(255,255,255,.1) !important;
            color: #fff7ef !important;
            min-height: 48px !important;
        }

        label, .stMarkdown, .stAlert, p, li, div {
            color: inherit;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            margin-bottom: 12px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 46px;
            background: rgba(255,255,255,.04);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 999px;
            color: #f7ecdf;
            padding: 0 18px;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(143,16,32,0.95), rgba(208,70,93,0.95)) !important;
            color: white !important;
        }

        .stForm {
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
        }

        .muted-divider {
            border-top: 1px solid rgba(255,255,255,.08);
            margin: 14px 0 18px 0;
        }

        @media (max-width: 1200px) {
            .hero-grid, .dashboard-grid, .split-2, .dashboard-cards, .metric-row, .wow-strip {
                grid-template-columns: 1fr !important;
            }
            .topbar {
                flex-direction: column;
                align-items:flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------- UI bits ----------
def render_topbar(logged_in: bool = False):
    logo = load_logo(ASSETS_DIR / "logo_beige.png") or load_logo(ASSETS_DIR / "logo_bdx.png")
    left = f"""
    <div class="brand-inline">
        {'<img class="brand-logo" src="data:image/png;base64,' + img_to_base64(logo) + '">' if logo else ''}
        <div>
            <div class="brand-title">Flamsily</div>
            <div class="brand-subtitle">Intranet premium & communauté Flam's</div>
        </div>
    </div>
    """
    right = """
    <div class="nav-pills">
      <span class="pill">Actualités</span>
      <span class="pill">Annuaire</span>
      <span class="pill">Carrières</span>
      <span class="pill">Événements</span>
    </div>
    """ if not logged_in else """
    <div class="nav-pills">
      <span class="pill">Dashboard</span>
      <span class="pill">Réseau</span>
      <span class="pill">Opportunités</span>
      <span class="pill">Mon compte</span>
    </div>
    """
    st.markdown(f'<div class="topbar">{left}{right}</div>', unsafe_allow_html=True)

def img_to_base64(path: str) -> str:
    import base64
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def auth_panel():
    tab1, tab2 = st.tabs(["Connexion", "Créer mon compte"])

    with tab1:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Adresse e-mail", placeholder="vous@flamsily.com")
            password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            submitted = st.form_submit_button("Entrer dans l’espace membre")
        if submitted:
            user = authenticate(email, password)
            if user:
                login_user(user)
            else:
                st.error("E-mail ou mot de passe incorrect.")

    with tab2:
        with st.form("signup_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input("Prénom", placeholder="Prénom")
                site_name = st.text_input("Flam's / site", placeholder="Ex: Bordeaux Centre")
                email = st.text_input("E-mail", placeholder="email@exemple.com")
                password = st.text_input("Mot de passe", type="password", placeholder="Minimum 8 caractères")
            with c2:
                last_name = st.text_input("Nom", placeholder="Nom")
                age = st.number_input("Âge", min_value=16, max_value=90, value=25)
                phone = st.text_input("Téléphone (facultatif)", placeholder="06...")
                confirm = st.text_input("Confirmer le mot de passe", type="password", placeholder="Confirmation")
            submitted = st.form_submit_button("Créer mon compte")
        if submitted:
            if not all([first_name.strip(), last_name.strip(), site_name.strip(), email.strip(), password]):
                st.error("Merci de remplir les champs obligatoires.")
            elif password != confirm:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(password) < 8:
                st.error("Le mot de passe doit contenir au moins 8 caractères.")
            elif get_user_by_email(email):
                st.error("Un compte existe déjà avec cet e-mail.")
            else:
                create_user(first_name.strip(), last_name.strip(), site_name.strip(), int(age), email.strip(), phone.strip(), password)
                st.success("Compte créé. Vous pouvez maintenant vous connecter.")

def render_landing():
    render_topbar(logged_in=False)
    member_count = safe_count("users")
    news_count = safe_count("news")
    jobs_count = safe_count("jobs")

    st.markdown('<div class="hero-shell"><div class="hero-grid">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div>
            <div class="eyebrow">🔥 Expérience membre premium • accès direct</div>
            <h1 class="headline">Le réseau <span class="headline-gradient">Flam's</span> dans une web app qui donne envie d’y revenir.</h1>
            <div class="hero-copy">
                Une vraie entrée wow, une inscription simple, puis un espace membre élégant avec actualités, annuaire,
                événements et opportunités. Pas de détour : on arrive, on s’inscrit, on se connecte.
            </div>
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">Accès</div>
                    <div class="metric-value">1 URL</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Communauté</div>
                    <div class="metric-value">{member_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Contenus</div>
                    <div class="metric-value">{news_count + jobs_count}</div>
                </div>
            </div>
            <div class="wow-strip">
                <div class="tile-card">
                    <div class="tile-emoji">✨</div>
                    <div class="card-title">Luxe digital</div>
                    <div class="subtle">Ambiance agence premium, glow subtil, profondeur visuelle et hiérarchie nette.</div>
                </div>
                <div class="tile-card">
                    <div class="tile-emoji">👥</div>
                    <div class="card-title">Réseau vivant</div>
                    <div class="subtle">Profils, recherche, opportunités et circulation d’information depuis un seul point d’entrée.</div>
                </div>
                <div class="tile-card">
                    <div class="tile-emoji">🚀</div>
                    <div class="card-title">Prêt à déployer</div>
                    <div class="subtle">Simple à mettre sur GitHub + Streamlit, avec une logique directe pour les membres.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Accès membre</div><div class="small-muted">Connectez-vous ou créez votre compte en moins d’une minute.</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted-divider"></div>', unsafe_allow_html=True)
    auth_panel()
    st.markdown('<div class="muted-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="small-muted">
            Compte admin de démonstration : <b>admin@flamsily.local</b> / <b>admin12345</b>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

def rail_menu(user: dict):
    initials = f"{user['first_name'][:1]}{user['last_name'][:1]}".upper()
    st.markdown(
        f"""
        <div class="rail-card">
            <div class="profile-badge">
                <div class="avatar-xl">{initials}</div>
                <div>
                    <div class="card-title" style="margin:0;">{user['first_name']} {user['last_name']}</div>
                    <div class="small-muted">{user['site_name']}</div>
                </div>
            </div>
            <div class="menu-note">Espace membre Flam's</div>
            <div>
                <span class="feature-pill">Actualités</span>
                <span class="feature-pill">Annuaire</span>
                <span class="feature-pill">Événements</span>
                <span class="feature-pill">Carrières</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigation",
        ["Accueil", "Actualités", "Annuaire", "Événements", "Carrières", "Mon profil"] + (["Admin"] if user.get("is_admin") else []),
        label_visibility="collapsed",
    )
    if st.button("Se déconnecter"):
        logout()
    return page

def dashboard_home(user):
    st.markdown(
        f"""
        <div class="hero-dashboard">
            <div>
                <div class="eyebadge">🔥 Bonjour {user['first_name']}</div>
                <h1>Votre espace Flam's, pensé comme un vrai produit premium.</h1>
                <p>Suivez les actualités du réseau, retrouvez les membres, parcourez les opportunités et gardez votre profil à jour dans une interface plus ambitieuse.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dashboard-cards">', unsafe_allow_html=True)
    for label, value in [("Membres", safe_count("users")), ("Actualités", safe_count("news")), ("Opportunités", safe_count("jobs"))]:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Dernières actualités</div>', unsafe_allow_html=True)
        for row in fetch_all("SELECT * FROM news ORDER BY id DESC LIMIT 4"):
            st.markdown(
                f"""
                <div class="news-item">
                    <div class="eyebadge">{row['category']} • {fmt_dt(row['created_at'])}</div>
                    <div class="card-title">{row['title']}</div>
                    <div class="subtle">{row['content']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">À venir</div>', unsafe_allow_html=True)
        for row in fetch_all("SELECT * FROM events ORDER BY event_date ASC LIMIT 4"):
            st.markdown(
                f"""
                <div class="list-item">
                    <div class="card-title">{row['title']}</div>
                    <div class="subtle">{row['location']} • {row['event_date']}</div>
                    <div class="subtle" style="margin-top:8px;">{row['summary']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

def page_news():
    st.markdown('<div class="content-card"><div class="section-title">Actualités</div>', unsafe_allow_html=True)
    for row in fetch_all("SELECT * FROM news ORDER BY id DESC"):
        st.markdown(
            f"""
            <div class="news-item">
                <div class="eyebadge">{row['category']} • {fmt_dt(row['created_at'])}</div>
                <div class="card-title">{row['title']}</div>
                <div class="subtle">{row['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

def page_directory():
    q = st.text_input("Rechercher un membre", placeholder="Nom, prénom, email ou site")
    if q.strip():
        like = f"%{q.strip()}%"
        rows = fetch_all(
            """
            SELECT * FROM users
            WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR site_name LIKE ?
            ORDER BY last_name, first_name
            """,
            (like, like, like, like),
        )
    else:
        rows = fetch_all("SELECT * FROM users ORDER BY last_name, first_name")
    st.markdown('<div class="content-card"><div class="section-title">Annuaire</div>', unsafe_allow_html=True)
    for row in rows:
        phone = row["phone"] if row["phone"] else "Non renseigné"
        st.markdown(
            f"""
            <div class="list-item">
                <div class="card-title">{row['first_name']} {row['last_name']}</div>
                <div class="subtle">{row['site_name']} • {row['email']} • {phone}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

def page_events():
    st.markdown('<div class="content-card"><div class="section-title">Événements</div>', unsafe_allow_html=True)
    for row in fetch_all("SELECT * FROM events ORDER BY event_date ASC"):
        st.markdown(
            f"""
            <div class="list-item">
                <div class="eyebadge">📅 {row['event_date']}</div>
                <div class="card-title">{row['title']}</div>
                <div class="subtle">{row['location']}</div>
                <div class="subtle" style="margin-top:8px;">{row['summary']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

def page_jobs():
    st.markdown('<div class="content-card"><div class="section-title">Carrières</div>', unsafe_allow_html=True)
    for row in fetch_all("SELECT * FROM jobs ORDER BY id DESC"):
        st.markdown(
            f"""
            <div class="list-item">
                <div class="eyebadge">💼 {row['contract_type']} • {row['location']}</div>
                <div class="card-title">{row['title']}</div>
                <div class="subtle">{row['summary']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

def page_profile(user):
    st.markdown('<div class="content-card"><div class="section-title">Mon profil</div>', unsafe_allow_html=True)
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Prénom", value=user["first_name"])
            site_name = st.text_input("Site Flam's", value=user["site_name"])
            email = st.text_input("E-mail", value=user["email"], disabled=True)
        with c2:
            last_name = st.text_input("Nom", value=user["last_name"])
            age = st.number_input("Âge", min_value=16, max_value=90, value=int(user["age"]))
            phone = st.text_input("Téléphone", value=user["phone"] or "")
        submitted = st.form_submit_button("Enregistrer")
    if submitted:
        execute(
            "UPDATE users SET first_name=?, last_name=?, site_name=?, age=?, phone=? WHERE id=?",
            (first_name.strip(), last_name.strip(), site_name.strip(), int(age), phone.strip(), user["id"]),
        )
        refreshed = get_user_by_email(user["email"])
        st.session_state["auth_user"] = dict(refreshed)
        st.success("Profil mis à jour.")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def page_admin():
    st.markdown('<div class="split-2">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="content-card"><div class="section-title">Publier une actualité</div>', unsafe_allow_html=True)
        with st.form("news_form"):
            title = st.text_input("Titre")
            category = st.selectbox("Catégorie", ["Actualité", "Événement", "Interne", "RH", "Réseau"])
            content = st.text_area("Contenu", height=150)
            submitted = st.form_submit_button("Publier")
        if submitted and title.strip() and content.strip():
            user = st.session_state["auth_user"]
            execute(
                "INSERT INTO news (title, category, content, created_at, author_email) VALUES (?, ?, ?, ?, ?)",
                (title.strip(), category, content.strip(), datetime.utcnow().isoformat(), user["email"]),
            )
            st.success("Actualité publiée.")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="content-card"><div class="section-title">Publier une offre</div>', unsafe_allow_html=True)
        with st.form("job_form"):
            title = st.text_input("Poste")
            location = st.text_input("Lieu")
            contract_type = st.selectbox("Contrat", ["CDI", "CDD", "Alternance", "Stage", "Freelance"])
            summary = st.text_area("Résumé", height=150)
            submitted = st.form_submit_button("Ajouter l’offre")
        if submitted and title.strip() and location.strip() and summary.strip():
            execute(
                "INSERT INTO jobs (title, location, contract_type, summary, created_at) VALUES (?, ?, ?, ?, ?)",
                (title.strip(), location.strip(), contract_type, summary.strip(), datetime.utcnow().isoformat()),
            )
            st.success("Offre ajoutée.")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="content-card"><div class="section-title">Membres inscrits</div>', unsafe_allow_html=True)
    rows = fetch_all("SELECT first_name, last_name, email, site_name, created_at, is_admin FROM users ORDER BY id DESC")
    for row in rows:
        role = "Admin" if row["is_admin"] else "Membre"
        st.markdown(
            f"""
            <div class="list-item">
                <div class="card-title">{row['first_name']} {row['last_name']} <span class="small-muted">• {role}</span></div>
                <div class="subtle">{row['email']} • {row['site_name']} • inscrit le {fmt_dt(row['created_at'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

def render_dashboard():
    render_topbar(logged_in=True)
    user = st.session_state["auth_user"]
    left, right = st.columns([0.26, 0.74], gap="large")
    with left:
        page = rail_menu(user)
    with right:
        if page == "Accueil":
            dashboard_home(user)
        elif page == "Actualités":
            page_news()
        elif page == "Annuaire":
            page_directory()
        elif page == "Événements":
            page_events()
        elif page == "Carrières":
            page_jobs()
        elif page == "Mon profil":
            page_profile(user)
        elif page == "Admin":
            page_admin()

# ---------- Main ----------
init_db()
inject_css()

if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None
if "route" not in st.session_state:
    st.session_state["route"] = "dashboard" if st.session_state["auth_user"] else "landing"

if st.session_state["auth_user"]:
    render_dashboard()
else:
    render_landing()
