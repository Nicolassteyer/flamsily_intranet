
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
import base64

import pandas as pd
import streamlit as st

# ---------- Page config ----------
st.set_page_config(
    page_title="Flamsily",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "flamsily.db"

for p in [DATA_DIR, ASSETS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# ---------- Theme ----------
COLORS = {
    "bg": "#f7f2ec",
    "panel": "#fffaf5",
    "panel_2": "#f2e8dc",
    "ink": "#1f1617",
    "muted": "#726562",
    "line": "#eadccf",
    "brand": "#7f1d2d",
    "brand_2": "#56101d",
    "brand_soft": "#f3d9dd",
    "ok": "#1f6d48",
    "warn": "#b86c00",
}

# ---------- Helpers ----------
def b64_image(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

CONN = get_conn()

def init_db():
    CONN.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone TEXT,
            flams_location TEXT NOT NULL,
            city TEXT NOT NULL,
            role_title TEXT NOT NULL,
            start_year INTEGER NOT NULL,
            end_year INTEGER NOT NULL,
            bio TEXT DEFAULT '',
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            body TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL,
            pinned INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            event_date TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    # seed admin
    admin = CONN.execute("SELECT id FROM users WHERE email = ?", ("admin@flamsily.local",)).fetchone()
    if not admin:
        CONN.execute(
            """
            INSERT INTO users
            (first_name, last_name, email, password_hash, age, phone, flams_location, city, role_title, start_year, end_year, bio, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Admin", "Flamsily", "admin@flamsily.local", hash_password("admin12345"),
                30, "", "Bordeaux Centre", "Bordeaux", "Administrateur",
                2020, 2026, "Compte administrateur de démonstration.", 1, datetime.utcnow().isoformat()
            )
        )
    # seed content if empty
    if CONN.execute("SELECT COUNT(*) AS c FROM news").fetchone()["c"] == 0:
        seed_news = [
            ("Soirée Alumni de printemps", "Communauté", "Retrouvez l'équipe et les anciens de Flam's pour une soirée réseau dans une ambiance premium, avec espace recrutement et rencontres métiers.", "Équipe Flamsily", 1),
            ("Ouverture des candidatures mentorat", "Carrière", "Le programme mentorat 2026 ouvre. Les anciens peuvent accompagner les nouveaux talents sur 3 mois avec rendez-vous mensuels.", "Équipe Flamsily", 0),
            ("Nouveau partenariat restauration & hôtellerie", "Opportunité", "Un nouveau partenaire ouvre plusieurs postes en exploitation, management et relation client pour la communauté Flam's.", "Équipe Flamsily", 0),
        ]
        for title, category, body, author, pinned in seed_news:
            CONN.execute(
                "INSERT INTO news (title, category, body, author, created_at, pinned) VALUES (?, ?, ?, ?, ?, ?)",
                (title, category, body, author, datetime.utcnow().isoformat(), pinned)
            )
    if CONN.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"] == 0:
        CONN.execute(
            "INSERT INTO events (title, location, event_date, body, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Afterwork communauté Flam's", "Bordeaux", "2026-05-20", "Cocktail réseau, prises de parole et rencontres alumni.", datetime.utcnow().isoformat())
        )
    if CONN.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()["c"] == 0:
        CONN.execute(
            "INSERT INTO jobs (title, company, location, body, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Responsable de salle", "Partenaire Premium", "Bordeaux", "Pilotage opérationnel, gestion équipe, relation client. Expérience restauration appréciée.", datetime.utcnow().isoformat())
        )
    CONN.commit()

init_db()

# ---------- Session ----------
default_state = {
    "user_id": None,
    "user_email": None,
    "sidebar_open": True,
    "view": "Actualités",
    "auth_tab": "login",
}
for key, val in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------- Data ----------
def get_user_by_email(email: str):
    return CONN.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (email.strip(),)).fetchone()

def get_user_by_id(user_id: int):
    return CONN.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

def create_user(data: dict):
    CONN.execute(
        """
        INSERT INTO users
        (first_name, last_name, email, password_hash, age, phone, flams_location, city, role_title, start_year, end_year, bio, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["first_name"], data["last_name"], data["email"], hash_password(data["password"]),
            int(data["age"]), data["phone"], data["flams_location"], data["city"], data["role_title"],
            int(data["start_year"]), int(data["end_year"]), data.get("bio", ""), 0, datetime.utcnow().isoformat()
        )
    )
    CONN.commit()

def update_user_profile(user_id: int, payload: dict):
    CONN.execute(
        """
        UPDATE users
        SET first_name=?, last_name=?, age=?, phone=?, flams_location=?, city=?, role_title=?, start_year=?, end_year=?, bio=?
        WHERE id=?
        """,
        (
            payload["first_name"], payload["last_name"], int(payload["age"]), payload["phone"],
            payload["flams_location"], payload["city"], payload["role_title"], int(payload["start_year"]),
            int(payload["end_year"]), payload["bio"], user_id
        )
    )
    CONN.commit()

def delete_user(user_id: int):
    CONN.execute("DELETE FROM users WHERE id=?", (user_id,))
    CONN.commit()

def update_user_admin(user_id: int, is_admin: int):
    CONN.execute("UPDATE users SET is_admin=? WHERE id=?", (is_admin, user_id))
    CONN.commit()

def fetch_news():
    return CONN.execute("SELECT * FROM news ORDER BY pinned DESC, datetime(created_at) DESC").fetchall()

def fetch_events():
    return CONN.execute("SELECT * FROM events ORDER BY event_date ASC").fetchall()

def fetch_jobs():
    return CONN.execute("SELECT * FROM jobs ORDER BY datetime(created_at) DESC").fetchall()

def fetch_users_df():
    df = pd.read_sql_query("SELECT id, first_name, last_name, email, age, phone, flams_location, city, role_title, start_year, end_year, bio, is_admin, created_at FROM users ORDER BY datetime(created_at) DESC", CONN)
    return df

def insert_news(title, category, body, author, pinned):
    CONN.execute(
        "INSERT INTO news (title, category, body, author, created_at, pinned) VALUES (?, ?, ?, ?, ?, ?)",
        (title, category, body, author, datetime.utcnow().isoformat(), int(pinned))
    )
    CONN.commit()

def insert_event(title, location, event_date, body):
    CONN.execute(
        "INSERT INTO events (title, location, event_date, body, created_at) VALUES (?, ?, ?, ?, ?)",
        (title, location, event_date, body, datetime.utcnow().isoformat())
    )
    CONN.commit()

def insert_job(title, company, location, body):
    CONN.execute(
        "INSERT INTO jobs (title, company, location, body, created_at) VALUES (?, ?, ?, ?, ?)",
        (title, company, location, body, datetime.utcnow().isoformat())
    )
    CONN.commit()

def delete_row(table: str, row_id: int):
    assert table in {"news", "events", "jobs"}
    CONN.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))
    CONN.commit()

# ---------- UI styles ----------
def inject_css():
    logo_beige = b64_image(ASSETS_DIR / "logo_beige.png")
    st.markdown(
        f"""
        <style>
            :root {{
                --bg: {COLORS["bg"]};
                --panel: {COLORS["panel"]};
                --panel2: {COLORS["panel_2"]};
                --ink: {COLORS["ink"]};
                --muted: {COLORS["muted"]};
                --line: {COLORS["line"]};
                --brand: {COLORS["brand"]};
                --brand2: {COLORS["brand_2"]};
                --brandSoft: {COLORS["brand_soft"]};
                --ok: {COLORS["ok"]};
                --warn: {COLORS["warn"]};
            }}

            .stApp {{
                background:
                  radial-gradient(circle at 0% 0%, rgba(127,29,45,.13), transparent 30%),
                  radial-gradient(circle at 100% 20%, rgba(127,29,45,.11), transparent 28%),
                  linear-gradient(180deg, #fbf7f2 0%, #f6efe7 100%);
                color: var(--ink);
            }}

            [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
            [data-testid="collapsedControl"], [data-testid="stSidebarNav"] {{
                display: none !important;
            }}

            .block-container {{
                padding-top: 1.4rem !important;
                padding-bottom: 2rem !important;
                max-width: 1380px !important;
            }}

            div[data-testid="stVerticalBlock"] > div:has(.public-shell) {{
                margin-top: 0.2rem;
            }}

            .public-shell {{
                min-height: 84vh;
                display: flex;
                align-items: stretch;
                gap: 1.2rem;
            }}

            .left-auth {{
                background: rgba(255,250,245,0.88);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(127,29,45,.08);
                box-shadow: 0 30px 80px rgba(89, 32, 43, 0.12);
                border-radius: 28px;
                padding: 1.7rem 1.7rem 1.3rem;
                height: 100%;
            }}

            .brand-mini {{
                display:flex;
                align-items:center;
                gap:.85rem;
                margin-bottom:1.1rem;
            }}

            .brand-logo {{
                width: 54px; height: 54px; border-radius: 16px;
                background: linear-gradient(135deg, rgba(127,29,45,.14), rgba(127,29,45,.04));
                border: 1px solid rgba(127,29,45,.10);
                display:flex; align-items:center; justify-content:center;
                overflow:hidden;
                flex-shrink:0;
            }}

            .brand-logo img {{
                width: 86%;
                height: auto;
                object-fit: contain;
            }}

            .brand-copy h1 {{
                font-size: 1.35rem; line-height:1.05; margin:0; color:var(--ink); font-weight:800;
                letter-spacing:-0.03em;
            }}
            .brand-copy p {{
                margin:.25rem 0 0; color:var(--muted); font-size:.93rem;
            }}

            .auth-segment {{
                background: var(--panel2);
                border: 1px solid rgba(127,29,45,.08);
                border-radius: 18px;
                padding: .35rem;
                display:flex;
                gap:.35rem;
                margin:.8rem 0 1.2rem;
            }}

            .split-art {{
                min-height: 84vh;
                border-radius: 32px;
                position: relative;
                overflow: hidden;
                border: 1px solid rgba(255,255,255,.24);
                background:
                  radial-gradient(circle at 20% 20%, rgba(255,255,255,.16), transparent 20%),
                  radial-gradient(circle at 80% 30%, rgba(255,255,255,.18), transparent 16%),
                  radial-gradient(circle at 55% 70%, rgba(255,232,215,.14), transparent 22%),
                  linear-gradient(135deg, #6e1027 0%, #891f37 24%, #3f0c17 100%);
                box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 30px 80px rgba(52, 12, 20, .28);
            }}

            .split-art::before {{
                content:"";
                position:absolute; inset:-12%;
                background:
                  radial-gradient(circle at 20% 50%, rgba(255,240,224,.22), transparent 22%),
                  radial-gradient(circle at 60% 20%, rgba(255,255,255,.14), transparent 18%),
                  radial-gradient(circle at 80% 80%, rgba(255,255,255,.09), transparent 26%);
                filter: blur(18px);
            }}

            .art-grid {{
                position:absolute; inset:0;
                background-image:
                  linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px);
                background-size: 44px 44px;
                mask-image: radial-gradient(circle at center, black 38%, transparent 92%);
                opacity:.22;
            }}

            .art-content {{
                position: absolute;
                inset: 0;
                padding: 2rem;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            }}

            .art-badge {{
                width: fit-content;
                border-radius: 999px;
                padding: .55rem .85rem;
                color: #fff4ec;
                background: rgba(255,255,255,.10);
                border: 1px solid rgba(255,255,255,.18);
                backdrop-filter: blur(10px);
                font-weight:600;
                font-size:.86rem;
            }}

            .art-bottom {{
                max-width: 560px;
                color: #fff7f1;
            }}

            .art-bottom h2 {{
                margin:0 0 .7rem;
                font-size: clamp(2.2rem, 5vw, 4.1rem);
                line-height: .96;
                font-weight: 900;
                letter-spacing:-0.05em;
            }}

            .art-bottom p {{
                margin:0;
                color: rgba(255,247,241,.78);
                font-size: 1rem;
                line-height: 1.65;
                max-width: 510px;
            }}

            .glass-chip {{
                display:inline-block;
                margin-top:1.3rem;
                border-radius: 999px;
                padding: .65rem 1rem;
                background: rgba(255,255,255,.08);
                border: 1px solid rgba(255,255,255,.18);
                color:#fff7f1;
                font-size:.9rem;
            }}

            .kpi-strip {{
                display:grid;
                grid-template-columns: repeat(3, minmax(0,1fr));
                gap:.75rem;
                margin-top:1.2rem;
                max-width:560px;
            }}

            .kpi {{
                background: rgba(255,255,255,.07);
                border:1px solid rgba(255,255,255,.13);
                border-radius:18px;
                padding:.9rem 1rem;
                color:#fff7f1;
            }}
            .kpi strong {{
                display:block;
                font-size:1.15rem;
                margin-bottom:.18rem;
            }}
            .kpi span {{
                color:rgba(255,247,241,.74);
                font-size:.85rem;
            }}

            .topbar {{
                position: sticky;
                top: 0.8rem;
                z-index: 10;
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:1rem;
                padding: .85rem 1rem;
                border-radius: 22px;
                background: rgba(255,250,245,.88);
                border:1px solid rgba(127,29,45,.08);
                box-shadow: 0 14px 40px rgba(89,32,43,.08);
                backdrop-filter: blur(10px);
                margin-bottom: 1rem;
            }}

            .topbar-left {{
                display:flex; align-items:center; gap:.8rem;
            }}

            .burger {{
                width:42px; height:42px;
                border-radius:14px;
                background: linear-gradient(180deg, #fff, #f8efe7);
                border:1px solid rgba(127,29,45,.10);
                display:flex; align-items:center; justify-content:center;
                color:var(--brand);
                font-weight:900;
                box-shadow: inset 0 1px 0 rgba(255,255,255,.75);
            }}

            .title-stack h2 {{
                margin:0; font-size:1.05rem; line-height:1.05; font-weight:800;
            }}
            .title-stack p {{
                margin:.18rem 0 0; color:var(--muted); font-size:.86rem;
            }}

            .topbar-right {{
                display:flex; align-items:center; gap:.65rem;
                flex-wrap: wrap;
            }}

            .pill {{
                background: var(--panel2);
                border: 1px solid rgba(127,29,45,.08);
                color: var(--ink);
                border-radius: 999px;
                padding: .5rem .8rem;
                font-size: .84rem;
            }}

            .app-shell {{
                display:grid;
                grid-template-columns: 290px minmax(0,1fr);
                gap: 1rem;
                align-items:start;
            }}

            .app-shell.compact {{
                grid-template-columns: 96px minmax(0,1fr);
            }}

            .nav-panel {{
                background: rgba(255,250,245,.88);
                border:1px solid rgba(127,29,45,.08);
                box-shadow: 0 18px 40px rgba(89,32,43,.07);
                border-radius: 28px;
                padding: 1rem;
                position: sticky;
                top: 5.4rem;
                min-height: 76vh;
            }}

            .member-card {{
                background:
                  linear-gradient(180deg, rgba(127,29,45,.98), rgba(93,18,33,.98));
                color:#fff7f1;
                border-radius: 24px;
                padding: 1rem;
                border:1px solid rgba(255,255,255,.10);
                box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
                margin-bottom: .95rem;
            }}
            .member-card h3 {{
                margin: 0;
                font-size: 1.15rem;
                line-height:1.1;
            }}
            .member-card p {{
                margin:.45rem 0 0;
                color: rgba(255,247,241,.72);
                font-size:.88rem;
                line-height:1.5;
            }}

            .menu-note {{
                color: var(--muted);
                font-size: .82rem;
                margin: .55rem 0 .8rem;
                padding-left: .2rem;
            }}

            .content-panel {{
                min-width: 0;
            }}

            .hero-card {{
                border-radius: 28px;
                background:
                  radial-gradient(circle at 100% 0%, rgba(127,29,45,.08), transparent 25%),
                  linear-gradient(180deg, rgba(255,250,245,.96), rgba(248,240,232,.96));
                border:1px solid rgba(127,29,45,.08);
                box-shadow: 0 24px 55px rgba(89,32,43,.08);
                padding: 1.25rem 1.25rem 1.1rem;
                margin-bottom: 1rem;
            }}
            .hero-card h1 {{
                margin:0;
                font-size: clamp(1.7rem, 4vw, 2.6rem);
                line-height:.95;
                letter-spacing:-0.045em;
            }}
            .hero-card p {{
                margin:.65rem 0 0;
                color:var(--muted);
                max-width:680px;
                line-height:1.65;
            }}

            .stat-grid {{
                display:grid;
                grid-template-columns: repeat(4, minmax(0,1fr));
                gap:.85rem;
                margin-top: 1rem;
            }}
            .stat-card {{
                background: rgba(255,255,255,.6);
                border:1px solid rgba(127,29,45,.08);
                border-radius: 22px;
                padding: 1rem;
            }}
            .stat-card strong {{
                display:block;
                font-size:1.35rem;
                line-height:1;
                margin-bottom:.35rem;
                letter-spacing:-0.04em;
            }}
            .stat-card span {{
                color:var(--muted);
                font-size:.86rem;
            }}

            .soft-card {{
                background: rgba(255,250,245,.82);
                border:1px solid rgba(127,29,45,.08);
                border-radius: 24px;
                box-shadow: 0 18px 40px rgba(89,32,43,.06);
                padding: 1rem;
                margin-bottom: 1rem;
            }}
            .soft-card h3, .soft-card h4 {{
                margin:0 0 .65rem;
                letter-spacing:-0.03em;
            }}

            .section-head {{
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:1rem;
                margin-bottom:.85rem;
            }}

            .news-card, .job-card, .event-card {{
                background: rgba(255,255,255,.78);
                border:1px solid rgba(127,29,45,.08);
                border-radius: 22px;
                padding: 1rem;
                margin-bottom: .85rem;
                box-shadow: 0 14px 28px rgba(89,32,43,.04);
            }}

            .tag {{
                display:inline-flex;
                align-items:center;
                gap:.35rem;
                padding:.38rem .7rem;
                border-radius:999px;
                background: var(--brandSoft);
                color:var(--brand);
                border:1px solid rgba(127,29,45,.08);
                font-size:.77rem;
                font-weight:700;
                text-transform:uppercase;
                letter-spacing:.05em;
            }}

            .news-card h4, .job-card h4, .event-card h4 {{
                margin:.7rem 0 .4rem;
                font-size:1.18rem;
                line-height:1.18;
                letter-spacing:-0.03em;
            }}
            .meta {{
                color: var(--muted);
                font-size: .84rem;
                margin-bottom:.55rem;
            }}
            .body-copy {{
                color: #3b2b2d;
                line-height:1.68;
                font-size:.96rem;
            }}

            .directory-card {{
                background: rgba(255,255,255,.75);
                border:1px solid rgba(127,29,45,.08);
                border-radius: 24px;
                padding: 1rem;
                box-shadow: 0 14px 28px rgba(89,32,43,.04);
                height: 100%;
            }}
            .directory-card h4 {{
                margin:0;
                font-size:1.08rem;
                letter-spacing:-0.03em;
            }}
            .directory-card p {{
                color:var(--muted);
                margin:.32rem 0 0;
                line-height:1.5;
                font-size:.9rem;
            }}

            .empty-box {{
                border:1px dashed rgba(127,29,45,.16);
                background: rgba(255,255,255,.42);
                border-radius: 24px;
                padding: 1.4rem;
                text-align:center;
                color:var(--muted);
            }}

            .footer-note {{
                color: var(--muted);
                font-size: .82rem;
                margin-top: .7rem;
            }}

            div[data-baseweb="tab-list"] {{
                gap:.45rem !important;
                background: transparent !important;
            }}

            button[data-baseweb="tab"] {{
                height:auto !important;
                padding: .75rem .9rem !important;
                border-radius: 15px !important;
                background: #f3eadf !important;
                border: 1px solid rgba(127,29,45,.08) !important;
                color: var(--ink) !important;
                font-weight:700 !important;
            }}

            button[data-baseweb="tab"][aria-selected="true"] {{
                background: linear-gradient(180deg, #7f1d2d, #5b1321) !important;
                color: #fff9f3 !important;
                border-color: transparent !important;
            }}

            div[data-testid="stForm"] {{
                border: none !important;
                background: transparent !important;
                padding: 0 !important;
            }}

            .stTextInput > div > div, .stNumberInput > div > div,
            .stTextArea textarea, .stSelectbox [data-baseweb="select"], .stDateInput > div > div {{
                background: rgba(255,255,255,.86) !important;
                border-radius: 16px !important;
                border: 1px solid rgba(127,29,45,.10) !important;
            }}

            .stTextInput input, .stNumberInput input, .stTextArea textarea {{
                color: var(--ink) !important;
            }}

            .stButton > button, .stDownloadButton > button {{
                border-radius: 16px !important;
                padding: .72rem 1rem !important;
                border: 1px solid transparent !important;
                font-weight: 700 !important;
                background: linear-gradient(180deg, #7f1d2d, #5b1321) !important;
                color: #fffaf4 !important;
                box-shadow: 0 12px 24px rgba(89,32,43,.15) !important;
                transition: all .18s ease !important;
            }}

            .stButton > button:hover, .stDownloadButton > button:hover {{
                transform: translateY(-1px) !important;
                box-shadow: 0 16px 28px rgba(89,32,43,.20) !important;
                filter: brightness(1.03);
            }}

            .ghost-btn > button {{
                background: #f5ebdf !important;
                color: var(--brand) !important;
                border: 1px solid rgba(127,29,45,.12) !important;
                box-shadow: none !important;
            }}

            [data-testid="stMetric"] {{
                background: rgba(255,255,255,.74);
                border:1px solid rgba(127,29,45,.08);
                padding: .9rem 1rem;
                border-radius: 20px;
            }}

            @media (max-width: 980px) {{
                .public-shell {{
                    min-height: auto;
                }}
                .split-art {{
                    min-height: 320px;
                }}
                .app-shell, .app-shell.compact {{
                    grid-template-columns: 1fr;
                }}
                .nav-panel {{
                    position: static;
                    min-height: auto;
                }}
                .stat-grid, .kpi-strip {{
                    grid-template-columns: repeat(2, minmax(0,1fr));
                }}
            }}
            @media (max-width: 680px) {{
                .stat-grid, .kpi-strip {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# ---------- Auth ----------
def login(email: str, password: str) -> bool:
    user = get_user_by_email(email)
    if not user:
        return False
    if user["password_hash"] != hash_password(password):
        return False
    st.session_state.user_id = user["id"]
    st.session_state.user_email = user["email"]
    st.session_state.view = "Actualités"
    return True

def logout():
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.view = "Actualités"
    st.session_state.auth_tab = "login"

def current_user():
    if st.session_state.user_id is None:
        return None
    return get_user_by_id(st.session_state.user_id)

# ---------- Layout bits ----------
def public_page():
    logo_beige = b64_image(ASSETS_DIR / "logo_beige.png")
    col1, col2 = st.columns([1.02, 1.18], gap="large")

    with col1:
        st.markdown('<div class="public-shell"><div class="left-auth">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="brand-mini">
                <div class="brand-logo">
                    {f'<img src="data:image/png;base64,{logo_beige}" alt="Flamsily logo" />' if logo_beige else 'F'}
                </div>
                <div class="brand-copy">
                    <h1>Flamsily</h1>
                    <p>Espace alumni & communauté Flam&apos;s</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tabs = st.tabs(["Connexion", "Créer un compte", "Mot de passe oublié"])
        with tabs[0]:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("E-mail", placeholder="prenom.nom@email.com")
                password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Se connecter", use_container_width=True)
            if submitted:
                if login(email, password):
                    st.success("Connexion réussie.")
                    st.rerun()
                else:
                    st.error("E-mail ou mot de passe incorrect.")

        with tabs[1]:
            with st.form("register_form", clear_on_submit=False):
                c1, c2 = st.columns(2)
                first_name = c1.text_input("Prénom")
                last_name = c2.text_input("Nom")

                email = st.text_input("E-mail")
                c3, c4 = st.columns(2)
                password = c3.text_input("Mot de passe", type="password")
                password2 = c4.text_input("Confirmer le mot de passe", type="password")

                c5, c6 = st.columns(2)
                age = c5.number_input("Âge", min_value=16, max_value=100, step=1)
                phone = c6.text_input("Téléphone (facultatif)")

                flams_location = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
                c7, c8 = st.columns(2)
                city = c7.text_input("Ville")
                role_title = c8.text_input("Poste / rôle")

                c9, c10 = st.columns(2)
                start_year = c9.number_input("Année d'entrée", min_value=1980, max_value=2100, step=1)
                end_year = c10.number_input("Année de sortie", min_value=1980, max_value=2100, step=1)
                bio = st.text_area("Bio", placeholder="Présentez-vous en quelques lignes.", height=90)

                submitted = st.form_submit_button("Créer mon compte", use_container_width=True)

            if submitted:
                required = [first_name, last_name, email, password, password2, flams_location, city, role_title]
                if any(not str(v).strip() for v in required):
                    st.error("Merci de remplir tous les champs obligatoires.")
                elif password != password2:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password) < 8:
                    st.error("Le mot de passe doit contenir au moins 8 caractères.")
                elif end_year < start_year:
                    st.error("L'année de sortie doit être supérieure ou égale à l'année d'entrée.")
                elif get_user_by_email(email):
                    st.error("Un compte existe déjà avec cet e-mail.")
                else:
                    create_user(
                        {
                            "first_name": first_name.strip(),
                            "last_name": last_name.strip(),
                            "email": email.strip().lower(),
                            "password": password,
                            "age": age,
                            "phone": phone.strip(),
                            "flams_location": flams_location.strip(),
                            "city": city.strip(),
                            "role_title": role_title.strip(),
                            "start_year": start_year,
                            "end_year": end_year,
                            "bio": bio.strip(),
                        }
                    )
                    login(email.strip().lower(), password)
                    st.success("Compte créé avec succès.")
                    st.rerun()

        with tabs[2]:
            st.info("Le reset par e-mail sera branché dans la version de déploiement finale.")
            with st.form("forgot_form"):
                reset_email = st.text_input("Votre e-mail")
                st.form_submit_button("Recevoir un lien de réinitialisation", use_container_width=True)
            st.caption("Pour le moment, l'administrateur peut vous aider à réinitialiser le compte.")
        st.markdown('</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div class="split-art">
                <div class="art-grid"></div>
                <div class="art-content">
                    <div class="art-badge">Communauté • Réseau • Opportunités</div>
                    <div class="art-bottom">
                        <h2>Le réseau Flam&apos;s, dans une expérience plus premium.</h2>
                        <p>Un accès simple, une identité forte et un espace pensé pour créer du lien, faire circuler les actualités et garder la communauté active.</p>
                        <div class="glass-chip">Fond abstrait remplaçable par une photo plus tard</div>
                        <div class="kpi-strip">
                            <div class="kpi"><strong>01</strong><span>Entrée simple</span></div>
                            <div class="kpi"><strong>02</strong><span>Connexion directe</span></div>
                            <div class="kpi"><strong>03</strong><span>Expérience membre</span></div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_topbar(user):
    st.markdown(
        f"""
        <div class="topbar">
            <div class="topbar-left">
                <div class="burger">☰</div>
                <div class="title-stack">
                    <h2>Flamsily</h2>
                    <p>{datetime.now().strftime("%d/%m/%Y")} • Réseau alumni Flam&apos;s</p>
                </div>
            </div>
            <div class="topbar-right">
                <div class="pill">{user["first_name"]} {user["last_name"]}</div>
                <div class="pill">{user["flams_location"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_sidebar(user):
    with st.sidebar:
        st.markdown("### Navigation")
    # Custom panel in main area
    menu = ["Accueil", "Actualités", "Annuaire", "Événements", "Carrières", "Messages", "Mon profil", "Paramètres"]
    if user["is_admin"]:
        menu.append("Admin")

    st.markdown(
        f"""
        <div class="nav-panel">
            <div class="member-card">
                <h3>{user["first_name"]} {user["last_name"]}</h3>
                <p>{user["role_title"]} • {user["city"]}<br>{user["flams_location"]}</p>
            </div>
            <div class="menu-note">Navigation</div>
        """,
        unsafe_allow_html=True,
    )

    for label in menu:
        cols = st.columns([1, 0.01])
        with cols[0]:
            btn_type = "primary" if st.session_state.view == label else "secondary"
            if st.button(label, key=f"nav_{label}", use_container_width=True, type=btn_type):
                st.session_state.view = label
                st.rerun()
    st.markdown('<div class="footer-note">Flamsily • réseau privé</div></div>', unsafe_allow_html=True)

    ghost = st.container()
    with ghost:
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        if st.button("Réduire / ouvrir le menu", use_container_width=True, key="toggle_sidebar"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
            st.rerun()
        if st.button("Se déconnecter", use_container_width=True, key="logout_btn"):
            logout()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def section_header(title: str, sub: str = ""):
    st.markdown(
        f"""
        <div class="section-head">
            <div>
                <h3 style="margin:0; letter-spacing:-0.03em;">{title}</h3>
                {f'<div class="meta" style="margin-top:.25rem;">{sub}</div>' if sub else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Views ----------
def view_dashboard(user):
    news = fetch_news()
    events = fetch_events()
    jobs = fetch_jobs()
    users_df = fetch_users_df()
    st.markdown(
        f"""
        <div class="hero-card">
            <h1>Bienvenue, {user["first_name"]}.</h1>
            <p>Votre espace résumé : les derniers mouvements de la communauté, les opportunités et ce qui mérite votre attention aujourd&apos;hui.</p>
            <div class="stat-grid">
                <div class="stat-card"><strong>{len(news)}</strong><span>Actualités publiées</span></div>
                <div class="stat-card"><strong>{len(events)}</strong><span>Événements à venir</span></div>
                <div class="stat-card"><strong>{len(jobs)}</strong><span>Offres en ligne</span></div>
                <div class="stat-card"><strong>{len(users_df)}</strong><span>Membres inscrits</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1.15, 0.85], gap="large")
    with c1:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        section_header("À la une", "Les contenus les plus récents de la communauté.")
        for row in news[:2]:
            st.markdown(
                f"""
                <div class="news-card">
                    <span class="tag">{row["category"]}</span>
                    <h4>{row["title"]}</h4>
                    <div class="meta">Par {row["author"]} • {row["created_at"][:10]}</div>
                    <div class="body-copy">{row["body"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        section_header("Prochains repères", "Événements et opportunités à surveiller.")
        for ev in events[:2]:
            st.markdown(
                f"""
                <div class="event-card">
                    <span class="tag">Événement</span>
                    <h4>{ev["title"]}</h4>
                    <div class="meta">{ev["location"]} • {ev["event_date"]}</div>
                    <div class="body-copy">{ev["body"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        for job in jobs[:1]:
            st.markdown(
                f"""
                <div class="job-card">
                    <span class="tag">Carrière</span>
                    <h4>{job["title"]}</h4>
                    <div class="meta">{job["company"]} • {job["location"]}</div>
                    <div class="body-copy">{job["body"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

def view_news():
    section_header("Actualités", "Le fil principal à l’arrivée après connexion.")
    for row in fetch_news():
        pinned = " • mis en avant" if row["pinned"] else ""
        st.markdown(
            f"""
            <div class="news-card">
                <span class="tag">{row["category"]}</span>
                <h4>{row["title"]}</h4>
                <div class="meta">Par {row["author"]} • {row["created_at"][:10]}{pinned}</div>
                <div class="body-copy">{row["body"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def view_events():
    section_header("Événements", "Rendez-vous communauté, afterworks et rencontres.")
    rows = fetch_events()
    if not rows:
        st.markdown('<div class="empty-box">Aucun événement pour le moment.</div>', unsafe_allow_html=True)
    for row in rows:
        st.markdown(
            f"""
            <div class="event-card">
                <span class="tag">Événement</span>
                <h4>{row["title"]}</h4>
                <div class="meta">{row["location"]} • {row["event_date"]}</div>
                <div class="body-copy">{row["body"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def view_jobs():
    section_header("Carrières", "Offres, mobilités et opportunités du réseau.")
    rows = fetch_jobs()
    if not rows:
        st.markdown('<div class="empty-box">Aucune offre pour le moment.</div>', unsafe_allow_html=True)
    for row in rows:
        st.markdown(
            f"""
            <div class="job-card">
                <span class="tag">Offre</span>
                <h4>{row["title"]}</h4>
                <div class="meta">{row["company"]} • {row["location"]}</div>
                <div class="body-copy">{row["body"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def view_directory():
    section_header("Annuaire", "Recherche sur tous les champs.")
    df = fetch_users_df()
    q = st.text_input("Rechercher un membre", placeholder="Nom, e-mail, ville, Flam's, rôle, téléphone…")
    if q.strip():
        mask = pd.Series(False, index=df.index)
        for col in df.columns:
            mask = mask | df[col].astype(str).str.contains(q, case=False, na=False)
        df = df[mask]
    cols = st.columns(3, gap="large")
    for idx, row in df.iterrows():
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="directory-card">
                    <h4>{row["first_name"]} {row["last_name"]}</h4>
                    <p><strong>{row["role_title"]}</strong><br>{row["city"]} • {row["flams_location"]}</p>
                    <p>{row["email"]}<br>{row["phone"] or "Téléphone non renseigné"}</p>
                    <p>{row["start_year"]} → {row["end_year"]}</p>
                    <p>{row["bio"] or "Aucune bio renseignée."}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

def view_messages():
    section_header("Messages", "Rubrique visible, module à connecter plus tard.")
    st.markdown(
        """
        <div class="empty-box">
            La messagerie sera branchée dans une prochaine version.<br>
            La rubrique reste visible pour préparer l’expérience finale.
        </div>
        """,
        unsafe_allow_html=True,
    )

def view_profile(user):
    section_header("Mon profil", "Modifier vos informations personnelles.")
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        first_name = c1.text_input("Prénom", value=user["first_name"])
        last_name = c2.text_input("Nom", value=user["last_name"])
        c3, c4 = st.columns(2)
        age = c3.number_input("Âge", min_value=16, max_value=100, value=int(user["age"]), step=1)
        phone = c4.text_input("Téléphone", value=user["phone"] or "")
        flams_location = st.text_input("Flam's", value=user["flams_location"])
        c5, c6 = st.columns(2)
        city = c5.text_input("Ville", value=user["city"])
        role_title = c6.text_input("Poste / rôle", value=user["role_title"])
        c7, c8 = st.columns(2)
        start_year = c7.number_input("Année d'entrée", min_value=1980, max_value=2100, value=int(user["start_year"]), step=1)
        end_year = c8.number_input("Année de sortie", min_value=1980, max_value=2100, value=int(user["end_year"]), step=1)
        bio = st.text_area("Bio", value=user["bio"] or "", height=110)
        submit = st.form_submit_button("Enregistrer les modifications", use_container_width=True)
    if submit:
        update_user_profile(
            user["id"],
            {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "age": age,
                "phone": phone.strip(),
                "flams_location": flams_location.strip(),
                "city": city.strip(),
                "role_title": role_title.strip(),
                "start_year": start_year,
                "end_year": end_year,
                "bio": bio.strip(),
            },
        )
        st.success("Profil mis à jour.")
        st.rerun()

def view_settings(user):
    section_header("Paramètres", "Préférences générales du compte.")
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.write("E-mail du compte :", user["email"])
    st.write("Type de compte :", "Administrateur" if user["is_admin"] else "Membre")
    with st.expander("Changer mon mot de passe"):
        old_pwd = st.text_input("Mot de passe actuel", type="password", key="old_pwd")
        new_pwd = st.text_input("Nouveau mot de passe", type="password", key="new_pwd")
        new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password", key="new_pwd2")
        if st.button("Mettre à jour le mot de passe", use_container_width=True, key="pwd_update"):
            user_fresh = get_user_by_id(user["id"])
            if user_fresh["password_hash"] != hash_password(old_pwd):
                st.error("Mot de passe actuel incorrect.")
            elif len(new_pwd) < 8:
                st.error("Le nouveau mot de passe doit contenir au moins 8 caractères.")
            elif new_pwd != new_pwd2:
                st.error("Les nouveaux mots de passe ne correspondent pas.")
            else:
                CONN.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_pwd), user["id"]))
                CONN.commit()
                st.success("Mot de passe mis à jour.")
    st.markdown('</div>', unsafe_allow_html=True)

def view_admin(user):
    if not user["is_admin"]:
        st.error("Accès réservé à l’administrateur.")
        return
    section_header("Admin", "Gestion des contenus et des membres.")
    tabs = st.tabs(["Actualités", "Événements", "Carrières", "Membres"])

    with tabs[0]:
        with st.form("news_admin_form"):
            title = st.text_input("Titre")
            c1, c2 = st.columns([1, 1])
            category = c1.text_input("Catégorie", value="Communauté")
            pinned = c2.checkbox("Mettre en avant")
            body = st.text_area("Contenu", height=140)
            if st.form_submit_button("Publier l’actualité", use_container_width=True):
                if title.strip() and body.strip():
                    insert_news(title.strip(), category.strip(), body.strip(), f"{user['first_name']} {user['last_name']}", pinned)
                    st.success("Actualité publiée.")
                    st.rerun()
                else:
                    st.error("Titre et contenu requis.")
        for row in fetch_news():
            cols = st.columns([5, 1])
            with cols[0]:
                st.markdown(f"**{row['title']}** — {row['category']} • {row['created_at'][:10]}")
            with cols[1]:
                if st.button("Supprimer", key=f"del_news_{row['id']}"):
                    delete_row("news", row["id"])
                    st.rerun()

    with tabs[1]:
        with st.form("event_admin_form"):
            title = st.text_input("Titre de l’événement")
            c1, c2 = st.columns(2)
            location = c1.text_input("Lieu")
            event_date = c2.date_input("Date")
            body = st.text_area("Description", height=120)
            if st.form_submit_button("Créer l’événement", use_container_width=True):
                if title.strip() and location.strip() and body.strip():
                    insert_event(title.strip(), location.strip(), str(event_date), body.strip())
                    st.success("Événement créé.")
                    st.rerun()
                else:
                    st.error("Tous les champs sont requis.")
        for row in fetch_events():
            cols = st.columns([5, 1])
            with cols[0]:
                st.markdown(f"**{row['title']}** — {row['location']} • {row['event_date']}")
            with cols[1]:
                if st.button("Supprimer", key=f"del_event_{row['id']}"):
                    delete_row("events", row["id"])
                    st.rerun()

    with tabs[2]:
        with st.form("job_admin_form"):
            title = st.text_input("Titre du poste")
            c1, c2 = st.columns(2)
            company = c1.text_input("Entreprise")
            location = c2.text_input("Lieu")
            body = st.text_area("Description", height=120)
            if st.form_submit_button("Publier l’offre", use_container_width=True):
                if title.strip() and company.strip() and location.strip() and body.strip():
                    insert_job(title.strip(), company.strip(), location.strip(), body.strip())
                    st.success("Offre publiée.")
                    st.rerun()
                else:
                    st.error("Tous les champs sont requis.")
        for row in fetch_jobs():
            cols = st.columns([5, 1])
            with cols[0]:
                st.markdown(f"**{row['title']}** — {row['company']} • {row['location']}")
            with cols[1]:
                if st.button("Supprimer", key=f"del_job_{row['id']}"):
                    delete_row("jobs", row["id"])
                    st.rerun()

    with tabs[3]:
        df = fetch_users_df()
        st.dataframe(df, use_container_width=True, hide_index=True)
        user_options = {f"{r['first_name']} {r['last_name']} — {r['email']}": int(r["id"]) for _, r in df.iterrows()}
        if user_options:
            selected_label = st.selectbox("Choisir un membre", list(user_options.keys()))
            selected_id = user_options[selected_label]
            selected_user = get_user_by_id(selected_id)
            c1, c2 = st.columns(2)
            with c1:
                admin_val = st.checkbox("Administrateur", value=bool(selected_user["is_admin"]))
                if st.button("Mettre à jour le rôle", use_container_width=True):
                    update_user_admin(selected_id, int(admin_val))
                    st.success("Rôle mis à jour.")
                    st.rerun()
            with c2:
                if selected_user["email"] != "admin@flamsily.local":
                    if st.button("Supprimer ce membre", use_container_width=True):
                        delete_user(selected_id)
                        st.success("Membre supprimé.")
                        st.rerun()
                else:
                    st.info("Le compte admin de démonstration ne peut pas être supprimé.")

def private_app():
    user = current_user()
    if not user:
        logout()
        st.rerun()

    render_topbar(user)
    shell_class = "app-shell" if st.session_state.sidebar_open else "app-shell compact"
    st.markdown(f'<div class="{shell_class}">', unsafe_allow_html=True)
    nav_col, content_col = st.columns([0.72, 2.1] if st.session_state.sidebar_open else [0.38, 2.44], gap="large")
    with nav_col:
        render_sidebar(user)
    with content_col:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        view = st.session_state.view
        if view == "Accueil":
            view_dashboard(user)
        elif view == "Actualités":
            view_news()
        elif view == "Annuaire":
            view_directory()
        elif view == "Événements":
            view_events()
        elif view == "Carrières":
            view_jobs()
        elif view == "Messages":
            view_messages()
        elif view == "Mon profil":
            view_profile(user)
        elif view == "Paramètres":
            view_settings(user)
        elif view == "Admin":
            view_admin(user)
        else:
            view_news()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- App ----------
if current_user():
    private_app()
else:
    public_page()
