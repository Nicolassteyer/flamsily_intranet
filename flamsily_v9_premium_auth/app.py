
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "flamsily.db"
LOGO_DARK = ASSETS_DIR / "logo_bdx.png"
LOGO_LIGHT = ASSETS_DIR / "logo_beige.png"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Page ----------
st.set_page_config(
    page_title="Flamsily",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Database ----------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone TEXT,
            flams_site TEXT NOT NULL,
            city TEXT NOT NULL,
            role_title TEXT NOT NULL,
            entry_year TEXT NOT NULL,
            exit_year TEXT NOT NULL,
            bio TEXT DEFAULT '',
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            category TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            event_date TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed admin
    cur.execute("SELECT id FROM users WHERE email = ?", ("admin@flamsily.local",))
    if cur.fetchone() is None:
        cur.execute("""
            INSERT INTO users (
                first_name, last_name, email, password_hash, age, phone, flams_site,
                city, role_title, entry_year, exit_year, bio, is_admin, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Admin", "Flamsily", "admin@flamsily.local", hash_password("admin12345"),
            30, "", "Siège", "Bordeaux", "Administrateur", "2020", "—",
            "Compte administrateur de démonstration.", 1, datetime.utcnow().isoformat()
        ))
        conn.commit()

    # Seed content
    cur.execute("SELECT COUNT(*) AS n FROM news")
    if cur.fetchone()["n"] == 0:
        news_rows = [
            ("Ouverture de Flamsily", "Bienvenue sur le nouvel intranet Flam's. Retrouvez ici les actualités, l'annuaire, les opportunités et la communauté.", "À la une", "Admin Flamsily", datetime.utcnow().isoformat()),
            ("Soirée réseau de rentrée", "Une soirée réseau sera organisée à Bordeaux le mois prochain. Les détails seront publiés très bientôt.", "Événement", "Admin Flamsily", datetime.utcnow().isoformat()),
            ("Recrutement en cuisine et salle", "Plusieurs opportunités sont ouvertes dans différents établissements. Consultez la rubrique Carrières.", "Carrière", "Admin Flamsily", datetime.utcnow().isoformat()),
        ]
        cur.executemany("INSERT INTO news (title, body, category, author, created_at) VALUES (?, ?, ?, ?, ?)", news_rows)
        conn.commit()

    cur.execute("SELECT COUNT(*) AS n FROM events")
    if cur.fetchone()["n"] == 0:
        event_rows = [
            ("Afterwork communauté Flam's", "Bordeaux", "2025-10-12 19:00", "Un rendez-vous pour réunir les anciens et les équipes actuelles."),
            ("Rencontre managers", "Strasbourg", "2025-11-04 14:00", "Atelier d'échange sur les bonnes pratiques terrain."),
        ]
        for row in event_rows:
            cur.execute(
                "INSERT INTO events (title, location, event_date, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (*row, datetime.utcnow().isoformat())
            )
        conn.commit()

    cur.execute("SELECT COUNT(*) AS n FROM jobs")
    if cur.fetchone()["n"] == 0:
        job_rows = [
            ("Responsable de salle", "Flam's Bordeaux", "Bordeaux", "Pilotage d'équipe, service premium et suivi opérationnel."),
            ("Assistant marketing local", "Flam's Réseau", "Paris", "Création de contenus locaux, animation et visibilité des points de vente."),
        ]
        for row in job_rows:
            cur.execute(
                "INSERT INTO jobs (title, company, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (*row, datetime.utcnow().isoformat())
            )
        conn.commit()

    conn.close()


# ---------- Helpers ----------
def logo_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    import base64
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


def fmt_date(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", ""))
        return dt.strftime("%d/%m/%Y • %H:%M")
    except Exception:
        return value


def count_rows(table: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
    value = cur.fetchone()["n"]
    conn.close()
    return value


def get_user_by_email(email: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (email.strip(),))
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def create_user(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (
            first_name, last_name, email, password_hash, age, phone, flams_site,
            city, role_title, entry_year, exit_year, bio, is_admin, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["first_name"], data["last_name"], data["email"], hash_password(data["password"]),
        int(data["age"]), data["phone"], data["flams_site"], data["city"], data["role_title"],
        data["entry_year"], data["exit_year"], "", 0, datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def authenticate(email: str, password: str):
    row = get_user_by_email(email)
    if not row:
        return None
    if row["password_hash"] != hash_password(password):
        return None
    return row


def fetch_news():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM news ORDER BY datetime(created_at) DESC, id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_events():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY event_date ASC, id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_jobs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY datetime(created_at) DESC, id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_users_df():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT id, first_name, last_name, email, age, phone, flams_site, city,
               role_title, entry_year, exit_year, is_admin, created_at
        FROM users
        ORDER BY last_name ASC, first_name ASC
    """, conn)
    conn.close()
    return df


def seed_session():
    defaults = {
        "auth_user_id": None,
        "auth_mode": "Connexion",
        "nav_page": "Actualités",
        "menu_open": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------- Style ----------
def inject_css():
    logo_dark = logo_data_uri(LOGO_DARK)
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --bg: #0d0a0b;
            --bg-2: #151011;
            --panel: rgba(18, 13, 14, 0.72);
            --panel-solid: #151112;
            --panel-soft: rgba(255,255,255,0.06);
            --line: rgba(255, 245, 236, 0.10);
            --text: #f7f1ea;
            --muted: #d9cfc4;
            --muted-2: #a69183;
            --brand: #7d1422;
            --brand-2: #a51d31;
            --brand-3: #d06a78;
            --cream: #f7f0e7;
            --chip: rgba(255,255,255,0.07);
            --success: #7bd389;
            --danger: #ff7b7b;
            --shadow: 0 24px 80px rgba(0,0,0,.35);
            --radius-xl: 28px;
            --radius-lg: 22px;
            --radius-md: 16px;
            --radius-sm: 12px;
            --sidebar-w: 280px;
        }}

        * {{
            font-family: 'Inter', sans-serif;
        }}

        html, body, [class*="css"] {{
            color: var(--text);
        }}

        .stApp {{
            background:
                radial-gradient(circle at 18% 18%, rgba(165,29,49,0.35), transparent 32%),
                radial-gradient(circle at 80% 12%, rgba(208,106,120,0.18), transparent 24%),
                radial-gradient(circle at 70% 80%, rgba(125,20,34,0.24), transparent 28%),
                linear-gradient(135deg, #0b0909 0%, #120d0e 38%, #1a1013 100%);
        }}

        .block-container {{
            max-width: 100% !important;
            padding-top: 1.2rem !important;
            padding-bottom: 1.4rem !important;
            padding-left: 1.4rem !important;
            padding-right: 1.4rem !important;
        }}

        header[data-testid="stHeader"] {{
            background: rgba(0,0,0,0) !important;
        }}

        [data-testid="stSidebar"] {{
            display: none;
        }}

        section[data-testid="stToolbar"] {{
            right: 0.75rem;
        }}

        div[data-testid="stDecoration"] {{
            display: none;
        }}

        /* Inputs and buttons */
        .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextArea label {{
            color: rgba(247,241,234,0.88) !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
        }}

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {{
            background: rgba(255,255,255,0.06) !important;
            border: 1px solid rgba(255,245,236,0.12) !important;
            color: var(--text) !important;
            border-radius: 16px !important;
            min-height: 52px !important;
        }}

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus {{
            border-color: rgba(208,106,120,0.6) !important;
            box-shadow: 0 0 0 1px rgba(208,106,120,0.36) !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.55rem;
            padding-bottom: 0.6rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 46px;
            border-radius: 14px;
            background: rgba(255,255,255,0.04);
            color: var(--muted);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 0 1rem;
            font-weight: 600;
        }}

        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, rgba(125,20,34,0.92), rgba(165,29,49,0.85));
            color: white !important;
            border-color: rgba(255,255,255,0.18) !important;
        }}

        .stButton > button,
        .stDownloadButton > button {{
            border-radius: 14px !important;
            min-height: 48px;
            border: 1px solid rgba(255,255,255,0.1) !important;
            background: linear-gradient(135deg, #7d1422 0%, #a51d31 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            transition: all .18s ease;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(125,20,34,.24);
            border-color: rgba(255,255,255,0.18) !important;
        }}

        .ghost-btn button {{
            background: rgba(255,255,255,0.04) !important;
            color: var(--text) !important;
            border-color: rgba(255,255,255,0.1) !important;
        }}

        .stDataFrame, .stTable {{
            background: rgba(255,255,255,0.04);
            border-radius: 18px;
            overflow: hidden;
        }}

        .muted {{
            color: var(--muted-2);
            font-size: 0.96rem;
        }}

        /* Auth page */
        .auth-shell {{
            min-height: calc(100vh - 60px);
            display: grid;
            grid-template-columns: 1fr;
            align-items: center;
        }}

        .auth-wrap {{
            position: relative;
            min-height: 86vh;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 2rem 2rem 2rem 5vw;
        }}

        .auth-glow {{
            position: absolute;
            inset: 0;
            pointer-events: none;
            background:
                radial-gradient(circle at 25% 35%, rgba(165,29,49,.22), transparent 30%),
                radial-gradient(circle at 72% 28%, rgba(125,20,34,.18), transparent 22%),
                radial-gradient(circle at 80% 80%, rgba(208,106,120,.10), transparent 22%);
            filter: blur(10px);
        }}

        .auth-card {{
            width: min(480px, 92vw);
            padding: 28px 28px 24px;
            background: linear-gradient(180deg, rgba(23,17,18,0.78) 0%, rgba(17,13,14,0.80) 100%);
            border: 1px solid rgba(255,245,236,0.1);
            border-radius: 28px;
            box-shadow: 0 30px 90px rgba(0,0,0,.45);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            position: relative;
            z-index: 2;
        }}

        .auth-logo {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 18px;
        }}

        .auth-logo img {{
            height: 98px;
            width: auto;
            display: block;
            filter: drop-shadow(0 8px 22px rgba(0,0,0,.18));
        }}

        .auth-subline {{
            display: none;
        }}

        .auth-frame {{
            position: absolute;
            right: 4vw;
            top: 10vh;
            bottom: 10vh;
            width: min(38vw, 540px);
            border-radius: 34px;
            background:
                linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)),
                radial-gradient(circle at 20% 20%, rgba(208,106,120,0.26), transparent 18%),
                radial-gradient(circle at 80% 28%, rgba(125,20,34,0.34), transparent 24%),
                radial-gradient(circle at 32% 78%, rgba(255,245,236,0.08), transparent 18%);
            border: 1px solid rgba(255,245,236,0.08);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.06), 0 20px 60px rgba(0,0,0,.30);
            opacity: .95;
        }}

        .auth-frame::before {{
            content: "";
            position: absolute;
            inset: 22px;
            border-radius: 26px;
            border: 1px solid rgba(255,245,236,0.06);
            background:
                linear-gradient(transparent 95%, rgba(255,255,255,.05) 96%),
                linear-gradient(90deg, transparent 95%, rgba(255,255,255,.05) 96%);
            background-size: 34px 34px;
            opacity: .45;
        }}

        .auth-frame::after {{
            content: "";
            position: absolute;
            width: 180px;
            height: 180px;
            right: 34px;
            bottom: 30px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(208,106,120,.24), rgba(208,106,120,0));
            filter: blur(16px);
        }}

        /* App shell */
        .shell {{
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 1rem;
            min-height: calc(100vh - 48px);
        }}

        .sidebar {{
            position: sticky;
            top: 20px;
            align-self: start;
            width: var(--sidebar-w);
            background: linear-gradient(180deg, rgba(18,13,14,0.86), rgba(14,10,11,0.86));
            border: 1px solid rgba(255,245,236,0.08);
            border-radius: 26px;
            box-shadow: var(--shadow);
            overflow: hidden;
            transition: width .22s ease;
        }}

        .sidebar.compact {{
            width: 94px;
        }}

        .sidebar-head {{
            padding: 18px 16px 14px;
            border-bottom: 1px solid rgba(255,245,236,0.08);
        }}

        .brandline {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .brandmark {{
            width: 46px;
            height: 46px;
            border-radius: 14px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,245,236,0.08);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            flex: 0 0 auto;
        }}

        .brandmark img {{
            width: 78%;
        }}

        .brandtitle {{
            font-weight: 800;
            font-size: 1.1rem;
            line-height: 1.1;
        }}

        .brandcaption {{
            color: var(--muted-2);
            font-size: .82rem;
            margin-top: 4px;
        }}

        .compact .brandcopy {{
            display: none;
        }}

        .user-pill {{
            margin-top: 14px;
            padding: 12px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(125,20,34,.85), rgba(165,29,49,.72));
            border: 1px solid rgba(255,245,236,0.12);
        }}

        .user-name {{
            font-weight: 700;
            font-size: .98rem;
        }}

        .user-role {{
            color: rgba(255,245,236,0.82);
            font-size: .84rem;
            margin-top: 4px;
        }}

        .compact .user-pill {{
            padding: 10px 8px;
            text-align: center;
        }}

        .compact .user-role, .compact .user-extra {{
            display: none;
        }}

        .menu-wrap {{
            padding: 10px 10px 12px;
        }}

        .menu-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 12px;
            border-radius: 16px;
            color: var(--muted);
            cursor: default;
            font-weight: 600;
            border: 1px solid transparent;
            margin-bottom: 6px;
            background: rgba(255,255,255,0.02);
        }}

        .menu-item.active {{
            background: rgba(255,255,255,0.07);
            border-color: rgba(255,245,236,0.08);
            color: white;
        }}

        .menu-item .icon {{
            width: 22px;
            text-align: center;
            flex: 0 0 auto;
        }}

        .compact .menu-item {{
            justify-content: center;
            padding: 12px 8px;
        }}

        .compact .menu-label {{
            display: none;
        }}

        .sidebar-foot {{
            padding: 12px 10px 14px;
            border-top: 1px solid rgba(255,245,236,0.08);
        }}

        .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            padding: 10px 6px 18px 6px;
        }}

        .topbar-card {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border-radius: 20px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,245,236,0.08);
        }}

        .page-title {{
            font-size: 1.25rem;
            font-weight: 800;
            margin: 0;
        }}

        .page-caption {{
            color: var(--muted-2);
            font-size: .92rem;
        }}

        .content-stack {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .card {{
            background: linear-gradient(180deg, rgba(18,13,14,0.88), rgba(15,11,12,0.9));
            border: 1px solid rgba(255,245,236,0.08);
            border-radius: 24px;
            padding: 18px;
            box-shadow: var(--shadow);
        }}

        .hero {{
            border-radius: 28px;
            padding: 28px;
            min-height: 220px;
            background:
                radial-gradient(circle at 75% 18%, rgba(208,106,120,.28), transparent 16%),
                radial-gradient(circle at 22% 68%, rgba(125,20,34,.24), transparent 20%),
                linear-gradient(135deg, rgba(18,13,14,0.96), rgba(34,15,20,0.94));
            border: 1px solid rgba(255,245,236,0.08);
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }}

        .hero::after {{
            content: "";
            position: absolute;
            right: -40px;
            bottom: -40px;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(208,106,120,.18), rgba(208,106,120,0));
        }}

        .eyebrow {{
            display: inline-flex;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,245,236,0.08);
            color: var(--muted);
            font-weight: 600;
            font-size: .86rem;
            margin-bottom: 14px;
        }}

        .hero h1 {{
            margin: 0 0 10px 0;
            font-size: clamp(1.9rem, 3vw, 3rem);
            line-height: 1.02;
            font-weight: 800;
            max-width: 800px;
        }}

        .hero p {{
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.65;
            max-width: 760px;
            margin-bottom: 0;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0,1fr));
            gap: 14px;
        }}

        .stat-card {{
            padding: 16px;
            border-radius: 20px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,245,236,0.08);
        }}

        .stat-label {{
            color: var(--muted-2);
            font-size: .82rem;
            text-transform: uppercase;
            letter-spacing: .12em;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 1.7rem;
            font-weight: 800;
        }}

        .news-card, .event-card, .job-card, .placeholder-card {{
            padding: 18px;
            border-radius: 22px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,245,236,0.08);
            height: 100%;
        }}

        .pill {{
            display: inline-flex;
            padding: 7px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,245,236,0.08);
            color: var(--muted);
            font-size: .84rem;
            font-weight: 600;
        }}

        .section-title {{
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 12px;
        }}

        .news-title, .event-title, .job-title {{
            font-weight: 700;
            font-size: 1.08rem;
            margin: 12px 0 8px 0;
        }}

        .meta {{
            color: var(--muted-2);
            font-size: .84rem;
            margin-bottom: 12px;
        }}

        .divider {{
            height: 1px;
            background: rgba(255,245,236,0.08);
            margin: 10px 0;
        }}

        @media (max-width: 1180px) {{
            .auth-wrap {{
                padding: 1.4rem;
                justify-content: center;
            }}
            .auth-frame {{
                display: none;
            }}
            .shell {{
                grid-template-columns: 1fr;
            }}
            .sidebar {{
                position: relative;
                width: 100% !important;
            }}
            .stats-grid {{
                grid-template-columns: repeat(2, minmax(0,1fr));
            }}
        }}

        @media (max-width: 760px) {{
            .auth-card {{
                width: 100%;
                padding: 22px 18px 18px;
            }}
            .auth-wrap {{
                min-height: auto;
                padding-top: 12vh;
                padding-bottom: 10vh;
            }}
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            .topbar {{
                flex-direction: column;
                align-items: stretch;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)


# ---------- UI ----------
def render_auth_page():
    light_logo = logo_data_uri(LOGO_LIGHT if LOGO_LIGHT.exists() else LOGO_DARK)

    st.markdown("""
        <div class="auth-shell">
            <div class="auth-wrap">
                <div class="auth-glow"></div>
                <div class="auth-frame"></div>
                <div class="auth-card">
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="auth-logo">
            <img src="{light_logo}" alt="Flam's logo">
        </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Connexion", "Créer un compte", "Mot de passe oublié"])

    with tabs[0]:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("E-mail", placeholder="prenom.nom@email.com")
            password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            submit = st.form_submit_button("Se connecter", use_container_width=True)
            if submit:
                user = authenticate(email, password)
                if user:
                    st.session_state.auth_user_id = user["id"]
                    st.session_state.nav_page = "Actualités"
                    st.success("Connexion réussie.")
                    st.rerun()
                st.error("E-mail ou mot de passe incorrect.")

    with tabs[1]:
        with st.form("register_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            first_name = col1.text_input("Prénom")
            last_name = col2.text_input("Nom")

            email = st.text_input("E-mail")
            c1, c2 = st.columns(2)
            password = c1.text_input("Mot de passe", type="password")
            password_2 = c2.text_input("Confirmer le mot de passe", type="password")

            c3, c4 = st.columns(2)
            age = c3.number_input("Âge", min_value=16, max_value=99, value=25)
            phone = c4.text_input("Téléphone (facultatif)")

            flams_site = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
            c5, c6 = st.columns(2)
            city = c5.text_input("Ville")
            role_title = c6.text_input("Poste / rôle")

            c7, c8 = st.columns(2)
            entry_year = c7.text_input("Année d'entrée", placeholder="2021")
            exit_year = c8.text_input("Année de sortie", placeholder="2024")

            submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
            if submitted:
                values = {
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "email": email.strip().lower(),
                    "password": password,
                    "age": age,
                    "phone": phone.strip(),
                    "flams_site": flams_site.strip(),
                    "city": city.strip(),
                    "role_title": role_title.strip(),
                    "entry_year": entry_year.strip(),
                    "exit_year": exit_year.strip(),
                }
                missing = [k for k, v in values.items() if k != "phone" and (v == "" or v is None)]
                if missing:
                    st.error("Merci de remplir tous les champs obligatoires.")
                elif password != password_2:
                    st.error("Les deux mots de passe ne correspondent pas.")
                elif len(password) < 8:
                    st.error("Le mot de passe doit contenir au moins 8 caractères.")
                elif get_user_by_email(values["email"]):
                    st.error("Un compte existe déjà avec cet e-mail.")
                else:
                    try:
                        create_user(values)
                        st.success("Compte créé. Vous pouvez maintenant vous connecter.")
                    except sqlite3.IntegrityError:
                        st.error("Cet e-mail est déjà utilisé.")

    with tabs[2]:
        with st.form("reset_form", clear_on_submit=True):
            email = st.text_input("Votre e-mail")
            submit = st.form_submit_button("Recevoir les instructions", use_container_width=True)
            if submit:
                if not email.strip():
                    st.error("Veuillez saisir votre e-mail.")
                else:
                    st.info("La réinitialisation par e-mail sera branchée sur votre service mail lors du déploiement final.")

    st.markdown("""
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def nav_button(label: str, icon: str, active: bool = False, key: str = "") -> bool:
    classes = "menu-item active" if active else "menu-item"
    st.markdown(f'<div class="{classes}"><span class="icon">{icon}</span><span class="menu-label">{label}</span></div>', unsafe_allow_html=True)
    return st.button(label, key=key or f"nav_{label}", use_container_width=True)


def render_sidebar(user):
    compact = not st.session_state.menu_open
    cls = "sidebar compact" if compact else "sidebar"
    dark_logo = logo_data_uri(LOGO_DARK)

    st.markdown(f"""
        <div class="{cls}">
            <div class="sidebar-head">
                <div class="brandline">
                    <div class="brandmark"><img src="{dark_logo}" alt="Flam's"></div>
                    <div class="brandcopy">
                        <div class="brandtitle">Flamsily</div>
                        <div class="brandcaption">Communauté Flam's</div>
                    </div>
                </div>
                <div class="user-pill">
                    <div class="user-name">{user["first_name"]} {user["last_name"]}</div>
                    <div class="user-role">{user["role_title"]}</div>
                    <div class="user-role user-extra">{user["city"]} · {user["flams_site"]}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="menu-wrap">', unsafe_allow_html=True)
    pages = [
        ("Accueil", "◻️"),
        ("Actualités", "📰"),
        ("Annuaire", "👥"),
        ("Événements", "📅"),
        ("Carrières", "💼"),
        ("Messages", "✉️"),
        ("Mon profil", "🙍"),
        ("Paramètres", "⚙️"),
    ]
    if user["is_admin"]:
        pages.append(("Admin", "🛠️"))

    for idx, (label, icon) in enumerate(pages):
        active = st.session_state.nav_page == label
        st.markdown(f"""
            <div class="menu-item {'active' if active else ''}">
                <span class="icon">{icon}</span>
                <span class="menu-label">{label}</span>
            </div>
        """, unsafe_allow_html=True)
        if st.button(label, key=f"btn_{idx}_{label}", use_container_width=True):
            st.session_state.nav_page = label
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-foot">', unsafe_allow_html=True)
    btn_text = "Réduire le menu" if st.session_state.menu_open else "Ouvrir le menu"
    if st.button(btn_text, key="toggle_menu", use_container_width=True):
        st.session_state.menu_open = not st.session_state.menu_open
        st.rerun()
    if st.button("Se déconnecter", key="logout", use_container_width=True):
        st.session_state.auth_user_id = None
        st.session_state.nav_page = "Actualités"
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_topbar(page_title: str, user):
    st.markdown(f"""
        <div class="topbar">
            <div class="topbar-card">
                <div>
                    <div class="page-title">{page_title}</div>
                    <div class="page-caption">Bonjour {user["first_name"]}, bienvenue sur votre espace Flamsily.</div>
                </div>
            </div>
            <div class="topbar-card">
                <div>
                    <div class="page-caption">Compte</div>
                    <div class="page-title" style="font-size:1rem;">{user["email"]}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_dashboard():
    st.markdown("""
        <div class="hero">
            <div class="eyebrow">Vue d'ensemble</div>
            <h1>Un espace membre plus simple, plus net, plus utile.</h1>
            <p>Retrouvez votre communauté, les nouvelles du réseau, les événements à venir et les opportunités carrière dans une interface centralisée.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
    stats = [
        ("Membres", count_rows("users")),
        ("Actualités", count_rows("news")),
        ("Événements", count_rows("events")),
        ("Offres", count_rows("jobs")),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, stats):
        with col:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">{label}</div>
                    <div class="stat-value">{value}</div>
                </div>
            """, unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="card"><div class="section-title">Dernières actualités</div>', unsafe_allow_html=True)
        for item in fetch_news()[:3]:
            st.markdown(f"""
                <div class="news-card" style="margin-bottom:12px;">
                    <div class="pill">{item["category"]}</div>
                    <div class="news-title">{item["title"]}</div>
                    <div class="meta">{item["author"]} · {fmt_date(item["created_at"])}</div>
                    <div>{item["body"]}</div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="section-title">À venir</div>', unsafe_allow_html=True)
        for item in fetch_events()[:3]:
            st.markdown(f"""
                <div class="event-card" style="margin-bottom:12px;">
                    <div class="event-title">{item["title"]}</div>
                    <div class="meta">{item["location"]} · {item["event_date"]}</div>
                    <div>{item["description"]}</div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_news_page():
    rows = fetch_news()
    st.markdown('<div class="content-stack">', unsafe_allow_html=True)
    for item in rows:
        st.markdown(f"""
            <div class="news-card">
                <div class="pill">{item["category"]}</div>
                <div class="news-title">{item["title"]}</div>
                <div class="meta">{item["author"]} · {fmt_date(item["created_at"])}</div>
                <div>{item["body"]}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_directory_page():
    df = fetch_users_df()
    search = st.text_input("Rechercher dans l'annuaire", placeholder="Nom, e-mail, ville, site, rôle, année...")
    if search.strip():
        mask = pd.Series([False] * len(df))
        for col in ["first_name", "last_name", "email", "phone", "flams_site", "city", "role_title", "entry_year", "exit_year"]:
            mask = mask | df[col].astype(str).str.contains(search, case=False, na=False)
        df = df[mask]
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_events_page():
    rows = fetch_events()
    cols = st.columns(2)
    for idx, item in enumerate(rows):
        with cols[idx % 2]:
            st.markdown(f"""
                <div class="event-card" style="margin-bottom:14px;">
                    <div class="event-title">{item["title"]}</div>
                    <div class="meta">{item["location"]} · {item["event_date"]}</div>
                    <div>{item["description"]}</div>
                </div>
            """, unsafe_allow_html=True)


def render_jobs_page():
    rows = fetch_jobs()
    cols = st.columns(2)
    for idx, item in enumerate(rows):
        with cols[idx % 2]:
            st.markdown(f"""
                <div class="job-card" style="margin-bottom:14px;">
                    <div class="job-title">{item["title"]}</div>
                    <div class="meta">{item["company"]} · {item["location"]}</div>
                    <div>{item["description"]}</div>
                </div>
            """, unsafe_allow_html=True)


def render_messages_page():
    st.markdown("""
        <div class="placeholder-card">
            <div class="section-title">Messages</div>
            <div class="muted">Le module de messagerie est prévu dans la prochaine étape. La rubrique reste visible pour préparer l'évolution de l'app.</div>
        </div>
    """, unsafe_allow_html=True)


def render_profile_page(user):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        first_name = c1.text_input("Prénom", value=user["first_name"])
        last_name = c2.text_input("Nom", value=user["last_name"])
        c3, c4 = st.columns(2)
        city = c3.text_input("Ville", value=user["city"])
        role_title = c4.text_input("Poste / rôle", value=user["role_title"])
        c5, c6 = st.columns(2)
        flams_site = c5.text_input("Flam's", value=user["flams_site"])
        phone = c6.text_input("Téléphone", value=user["phone"] or "")
        bio = st.text_area("Bio", value=user["bio"] or "", height=120)
        submitted = st.form_submit_button("Enregistrer les modifications", use_container_width=True)
        if submitted:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                UPDATE users
                SET first_name=?, last_name=?, city=?, role_title=?, flams_site=?, phone=?, bio=?
                WHERE id=?
            """, (first_name.strip(), last_name.strip(), city.strip(), role_title.strip(), flams_site.strip(), phone.strip(), bio.strip(), user["id"]))
            conn.commit()
            conn.close()
            st.success("Profil mis à jour.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_settings_page(user):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Sécurité du compte</div>', unsafe_allow_html=True)
    with st.form("password_form"):
        current_pw = st.text_input("Mot de passe actuel", type="password")
        new_pw = st.text_input("Nouveau mot de passe", type="password")
        new_pw2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
        submitted = st.form_submit_button("Changer le mot de passe", use_container_width=True)
        if submitted:
            if hash_password(current_pw) != user["password_hash"]:
                st.error("Mot de passe actuel incorrect.")
            elif len(new_pw) < 8:
                st.error("Le nouveau mot de passe doit contenir au moins 8 caractères.")
            elif new_pw != new_pw2:
                st.error("Les nouveaux mots de passe ne correspondent pas.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_pw), user["id"]))
                conn.commit()
                conn.close()
                st.success("Mot de passe modifié.")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_admin_page():
    tabs = st.tabs(["Actualités", "Événements", "Carrières", "Membres"])

    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("admin_news"):
            title = st.text_input("Titre")
            category = st.selectbox("Catégorie", ["À la une", "Événement", "Carrière", "Réseau"])
            body = st.text_area("Contenu", height=160)
            author = st.text_input("Auteur", value="Admin Flamsily")
            submitted = st.form_submit_button("Publier l'actualité", use_container_width=True)
            if submitted:
                if title.strip() and body.strip():
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO news (title, body, category, author, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title.strip(), body.strip(), category, author.strip(), datetime.utcnow().isoformat())
                    )
                    conn.commit()
                    conn.close()
                    st.success("Actualité publiée.")
                    st.rerun()
                st.error("Titre et contenu requis.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("admin_events"):
            title = st.text_input("Titre de l'événement")
            location = st.text_input("Lieu")
            event_date = st.text_input("Date / heure", placeholder="2025-11-14 19:00")
            description = st.text_area("Description", height=140)
            submitted = st.form_submit_button("Créer l'événement", use_container_width=True)
            if submitted:
                if title.strip() and location.strip() and event_date.strip() and description.strip():
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO events (title, location, event_date, description, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title.strip(), location.strip(), event_date.strip(), description.strip(), datetime.utcnow().isoformat())
                    )
                    conn.commit()
                    conn.close()
                    st.success("Événement ajouté.")
                    st.rerun()
                st.error("Tous les champs sont requis.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("admin_jobs"):
            title = st.text_input("Poste")
            company = st.text_input("Entreprise / site")
            location = st.text_input("Lieu")
            description = st.text_area("Description", height=140)
            submitted = st.form_submit_button("Publier l'offre", use_container_width=True)
            if submitted:
                if title.strip() and company.strip() and location.strip() and description.strip():
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO jobs (title, company, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title.strip(), company.strip(), location.strip(), description.strip(), datetime.utcnow().isoformat())
                    )
                    conn.commit()
                    conn.close()
                    st.success("Offre publiée.")
                    st.rerun()
                st.error("Tous les champs sont requis.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        df = fetch_users_df()
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown('<div class="card" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Supprimer un compte</div>', unsafe_allow_html=True)
        user_options = {f'{r["first_name"]} {r["last_name"]} — {r["email"]}': int(r["id"]) for _, r in df.iterrows() if r["email"] != "admin@flamsily.local"}
        if user_options:
            chosen = st.selectbox("Compte", list(user_options.keys()))
            if st.button("Supprimer le compte sélectionné", use_container_width=True):
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE id=?", (user_options[chosen],))
                conn.commit()
                conn.close()
                st.success("Compte supprimé.")
                st.rerun()
        else:
            st.info("Aucun compte utilisateur à supprimer.")
        st.markdown('</div>', unsafe_allow_html=True)


# ---------- Main ----------
init_db()
seed_session()
inject_css()

if not st.session_state.auth_user_id:
    render_auth_page()
else:
    user = get_user_by_id(st.session_state.auth_user_id)
    if user is None:
        st.session_state.auth_user_id = None
        st.rerun()

    left, right = st.columns([0.24, 0.76], gap="medium")
    with left:
        render_sidebar(user)

    with right:
        render_topbar(st.session_state.nav_page, user)

        page = st.session_state.nav_page
        if page == "Accueil":
            render_dashboard()
        elif page == "Actualités":
            render_news_page()
        elif page == "Annuaire":
            render_directory_page()
        elif page == "Événements":
            render_events_page()
        elif page == "Carrières":
            render_jobs_page()
        elif page == "Messages":
            render_messages_page()
        elif page == "Mon profil":
            render_profile_page(user)
        elif page == "Paramètres":
            render_settings_page(user)
        elif page == "Admin" and user["is_admin"]:
            render_admin_page()
        else:
            render_news_page()
