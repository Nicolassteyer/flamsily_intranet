
from __future__ import annotations

import hashlib
import html
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Flamsily",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# Paths / DB
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "flamsily.db"
LOGO_DARK = ASSETS_DIR / "logo_bdx.png"
LOGO_LIGHT = ASSETS_DIR / "logo_beige.png"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Utilities
# -----------------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def asset_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = path.read_bytes()
    import base64
    return f"data:{mime};base64," + base64.b64encode(encoded).decode("utf-8")


LOGO_DARK_URI = asset_to_data_uri(LOGO_DARK)
LOGO_LIGHT_URI = asset_to_data_uri(LOGO_LIGHT)


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            flams_site TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Actualité',
            author TEXT NOT NULL DEFAULT 'Administration',
            created_at TEXT NOT NULL
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
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute("SELECT COUNT(*) AS c FROM users")
    user_count = cur.fetchone()["c"]
    if user_count == 0:
        cur.execute(
            """
            INSERT INTO users (
                first_name, last_name, flams_site, age, email, phone,
                password_hash, is_admin, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        seed_news = [
            ("Ouverture de Flamsily", "Bienvenue sur votre nouvel intranet. Retrouvez ici vos actualités, votre profil et l'annuaire de la communauté Flam's.", "Plateforme", "Administration"),
            ("Mise à jour communauté", "La nouvelle version de l'espace membre est désormais en ligne avec une expérience plus simple et plus premium.", "Produit", "Administration"),
        ]
        for title, content, category, author in seed_news:
            cur.execute(
                "INSERT INTO news (title, content, category, author, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, content, category, author, datetime.utcnow().isoformat()),
            )

    cur.execute("SELECT COUNT(*) AS c FROM jobs")
    if cur.fetchone()["c"] == 0:
        seed_jobs = [
            ("Manager restaurant", "Strasbourg", "CDI", "Piloter l'activité opérationnelle et manager l'équipe au quotidien."),
            ("Responsable communication locale", "Mulhouse", "CDD", "Développer les temps forts de marque et les activations locales."),
        ]
        for title, location, contract_type, summary in seed_jobs:
            cur.execute(
                "INSERT INTO jobs (title, location, contract_type, summary, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, location, contract_type, summary, datetime.utcnow().isoformat()),
            )

    cur.execute("SELECT COUNT(*) AS c FROM events")
    if cur.fetchone()["c"] == 0:
        seed_events = [
            ("Rencontre réseau Flam's", "2026-01-15", "Strasbourg", "Soirée de rencontres entre anciens collaborateurs et équipes actuelles."),
            ("Atelier carrière & mobilité", "2026-02-12", "Colmar", "Échange autour des parcours, métiers et opportunités du réseau."),
        ]
        for title, event_date, location, description in seed_events:
            cur.execute(
                "INSERT INTO events (title, event_date, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, event_date, location, description, datetime.utcnow().isoformat()),
            )

    conn.commit()
    conn.close()


# -----------------------------
# Data access
# -----------------------------
def fetch_one(query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


def fetch_all(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def execute(query: str, params: tuple = ()) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def create_user(first_name: str, last_name: str, flams_site: str, age: int, email: str, phone: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Adresse e-mail invalide."
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if fetch_one("SELECT id FROM users WHERE email = ?", (email,)):
        return False, "Un compte existe déjà avec cette adresse e-mail."

    execute(
        """
        INSERT INTO users (
            first_name, last_name, flams_site, age, email, phone,
            password_hash, is_admin, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (
            first_name.strip(),
            last_name.strip(),
            flams_site.strip(),
            age,
            email,
            phone.strip(),
            hash_password(password),
            datetime.utcnow().isoformat(),
        ),
    )
    return True, "Compte créé avec succès."


def authenticate(email: str, password: str) -> Optional[sqlite3.Row]:
    email = email.strip().lower()
    return fetch_one(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (email, hash_password(password)),
    )


def update_profile(user_id: int, first_name: str, last_name: str, flams_site: str, age: int, email: str, phone: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Adresse e-mail invalide."
    existing = fetch_one("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
    if existing:
        return False, "Cette adresse e-mail est déjà utilisée."

    execute(
        """
        UPDATE users
        SET first_name = ?, last_name = ?, flams_site = ?, age = ?, email = ?, phone = ?
        WHERE id = ?
        """,
        (
            first_name.strip(),
            last_name.strip(),
            flams_site.strip(),
            age,
            email,
            phone.strip(),
            user_id,
        ),
    )
    return True, "Profil mis à jour."


def change_password(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
    user = fetch_one("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    if not user:
        return False, "Utilisateur introuvable."
    if user["password_hash"] != hash_password(current_password):
        return False, "Mot de passe actuel incorrect."
    if len(new_password) < 8:
        return False, "Le nouveau mot de passe doit contenir au moins 8 caractères."
    execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    return True, "Mot de passe mis à jour."


# -----------------------------
# Styling
# -----------------------------
def render_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: #0f0d0d;
            --surface: rgba(255,255,255,0.08);
            --surface-2: rgba(255,255,255,0.06);
            --line: rgba(255,255,255,0.12);
            --text: #f6f1e8;
            --muted: #b9ada4;
            --brand: #7f1220;
            --brand-2: #b61d33;
            --brand-3: #e5d8ca;
            --ok: #c5ff9d;
            --shadow: 0 30px 70px rgba(0,0,0,0.38);
            --radius: 24px;
        }}

        html, body, [class*="css"] {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}

        .stApp {{
            background:
              radial-gradient(900px 420px at 10% -5%, rgba(182,29,51,0.35), transparent 45%),
              radial-gradient(1000px 500px at 90% -10%, rgba(127,18,32,0.25), transparent 40%),
              linear-gradient(180deg, #110d0e 0%, #171112 60%, #100d0d 100%);
            color: var(--text);
        }}

        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"], #MainMenu, footer {{
            display: none !important;
        }}

        [data-testid="block-container"] {{
            padding-top: 24px;
            padding-bottom: 40px;
            max-width: 1420px;
        }}

        .fl-wrap {{
            width: 100%;
            margin: 0 auto;
        }}

        .glass {{
            background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
            border: 1px solid rgba(255,255,255,0.12);
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
        }}

        .topbar {{
            border-radius: 26px;
            padding: 18px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            margin-bottom: 26px;
        }}

        .brandbox {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .logo-chip {{
            width: 72px;
            height: 72px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.97);
            box-shadow: inset 0 0 0 1px rgba(127,18,32,0.08), 0 18px 32px rgba(0,0,0,0.14);
        }}
        .logo-chip img {{
            max-width: 52px;
            max-height: 52px;
        }}

        .brand-name {{
            font-size: 38px;
            line-height: 1;
            font-weight: 800;
            letter-spacing: -0.04em;
            color: #fff8f1;
            margin: 0;
        }}

        .brand-sub {{
            margin: 6px 0 0 0;
            color: var(--muted);
            font-size: 15px;
        }}

        .nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            justify-content: flex-end;
        }}

        .nav-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 18px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.05);
            color: #f7eee5;
            font-weight: 600;
            font-size: 14px;
        }}

        .shell {{
            display: grid;
            grid-template-columns: 1.08fr 0.92fr;
            gap: 24px;
            align-items: stretch;
            min-height: calc(100vh - 160px);
        }}

        .hero {{
            position: relative;
            overflow: hidden;
            border-radius: 34px;
            padding: 34px;
            min-height: 700px;
            background:
              radial-gradient(700px 320px at 72% 14%, rgba(255,240,216,0.16), transparent 34%),
              radial-gradient(760px 360px at -10% -8%, rgba(255,255,255,0.10), transparent 30%),
              linear-gradient(135deg, #5f0f1b 0%, #7d1321 38%, #8f1626 62%, #a61d31 100%);
            box-shadow: 0 40px 90px rgba(0,0,0,0.45);
            border: 1px solid rgba(255,255,255,0.10);
        }}

        .hero::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
              linear-gradient(180deg, rgba(255,255,255,0.06), transparent 30%),
              radial-gradient(500px 260px at 100% 0%, rgba(255,255,255,0.18), transparent 38%);
            pointer-events: none;
        }}

        .hero-logo {{
            width: 180px;
            opacity: 0.14;
            filter: saturate(0) brightness(4);
            position: absolute;
            right: 28px;
            top: 22px;
        }}

        .hero-tag {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.16);
            color: #fff1df;
            font-weight: 700;
            font-size: 14px;
            margin-bottom: 24px;
        }}

        .hero h1 {{
            margin: 0 0 16px 0;
            font-size: clamp(56px, 7vw, 92px);
            line-height: 0.94;
            letter-spacing: -0.06em;
            color: #fff8f1;
            max-width: 780px;
        }}

        .hero p {{
            margin: 0;
            max-width: 620px;
            font-size: 19px;
            line-height: 1.65;
            color: rgba(255,246,237,0.88);
        }}

        .metric-row {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 14px;
            margin-top: 26px;
            max-width: 780px;
        }}

        .metric {{
            padding: 18px 18px 20px;
            border-radius: 22px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            backdrop-filter: blur(10px);
        }}

        .metric .label {{
            color: rgba(255,243,234,0.70);
            font-size: 12px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}

        .metric .value {{
            color: #fff8f1;
            font-weight: 800;
            font-size: 32px;
            letter-spacing: -0.04em;
        }}

        .signin-pane {{
            min-height: 700px;
            border-radius: 34px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .signin-shell {{
            display: grid;
            grid-template-rows: auto 1fr auto;
            height: 100%;
            gap: 18px;
        }}

        .signin-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 8px 6px 0 6px;
        }}

        .signin-title {{
            margin: 0;
            font-size: 28px;
            color: #fff8f1;
            letter-spacing: -0.03em;
        }}

        .signin-sub {{
            margin: 8px 0 0 0;
            color: var(--muted);
            font-size: 15px;
        }}

        .micro-badge {{
            padding: 10px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            font-size: 12px;
            font-weight: 700;
            color: #eedfce;
        }}

        .section-card {{
            border-radius: 28px;
            padding: 20px;
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.04));
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: 0 18px 42px rgba(0,0,0,0.18);
        }}

        .pill-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 16px;
        }}

        .label-small {{
            color: var(--muted);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            margin: 0 0 8px 0;
        }}

        .info-strip {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }}

        .info-mini {{
            border-radius: 18px;
            padding: 14px 16px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .info-mini strong {{
            display: block;
            color: #fff8f1;
            font-size: 18px;
        }}
        .info-mini span {{
            color: var(--muted);
            font-size: 12px;
        }}

        .quiet {{
            color: var(--muted);
            font-size: 14px;
        }}

        .section-title {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #fff8f1;
            margin: 0 0 6px 0;
        }}

        /* Inputs */
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div,
        .stNumberInput div[data-baseweb="input"] > div {{
            background: rgba(255,255,255,0.06) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 16px !important;
            color: #fff8f1 !important;
            min-height: 52px;
        }}

        input, textarea {{
            color: #fff8f1 !important;
            caret-color: #fff8f1 !important;
        }}

        input::placeholder, textarea::placeholder {{
            color: #c9b9ab !important;
        }}

        label, .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label {{
            color: #dcccbf !important;
            font-weight: 600 !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
            background: transparent;
        }}

        .stTabs [data-baseweb="tab"] {{
            padding: 12px 16px;
            border-radius: 999px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.10);
            color: #ebdfd1;
        }}

        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #9b1c2f, #bf2640) !important;
            color: white !important;
            border-color: rgba(255,255,255,0.10) !important;
        }}

        .stButton > button {{
            width: 100%;
            min-height: 52px;
            border: none;
            border-radius: 16px;
            color: #fffaf3;
            font-weight: 800;
            font-size: 15px;
            letter-spacing: -0.01em;
            background: linear-gradient(135deg, #9c1b2e 0%, #bc2740 100%);
            box-shadow: 0 18px 38px rgba(156,27,46,0.30);
            transition: transform .16s ease, box-shadow .18s ease, filter .18s ease;
        }}

        .stButton > button:hover {{
            transform: translateY(-1px);
            filter: brightness(1.04);
            box-shadow: 0 24px 50px rgba(156,27,46,0.38);
        }}

        .stButton > button:focus {{
            box-shadow: 0 0 0 2px rgba(255,255,255,0.16), 0 20px 40px rgba(156,27,46,0.40);
        }}

        .ghost button {{
            background: rgba(255,255,255,0.06) !important;
            box-shadow: none !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: #f0e4d9 !important;
        }}

        .small-link {{
            color: #ecd7c5;
            font-weight: 600;
            font-size: 13px;
            text-decoration: none;
        }}

        .panel {{
            border-radius: 28px;
            padding: 22px;
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.04));
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: var(--shadow);
        }}

        .member-grid {{
            display: grid;
            grid-template-columns: 312px minmax(0, 1fr);
            gap: 22px;
            align-items: start;
        }}

        .member-aside {{
            position: sticky;
            top: 18px;
            border-radius: 30px;
            padding: 18px;
            background:
                radial-gradient(260px 160px at 80% 0%, rgba(255,255,255,0.10), transparent 44%),
                linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.05));
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: var(--shadow);
        }}

        .member-card {{
            border-radius: 24px;
            padding: 18px;
            background: linear-gradient(135deg, #7f1220, #a81f34);
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: 0 22px 50px rgba(0,0,0,0.28);
            margin-bottom: 18px;
        }}

        .avatar {{
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.16);
            color: white;
            font-weight: 800;
            font-size: 22px;
            margin-bottom: 12px;
        }}

        .member-name {{
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #fff9f4;
            margin: 0;
        }}
        .member-meta {{
            color: rgba(255,244,234,0.82);
            font-size: 14px;
            margin-top: 6px;
        }}

        .nav-vertical {{
            display: grid;
            gap: 10px;
            margin-top: 10px;
        }}

        .nav-card {{
            padding: 12px 14px;
            border-radius: 18px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            color: #f2e5d8;
            font-weight: 700;
            font-size: 14px;
        }}

        .page-title {{
            font-size: clamp(34px, 4vw, 56px);
            line-height: 1;
            font-weight: 900;
            letter-spacing: -0.06em;
            margin: 0 0 10px 0;
            color: #fff8f1;
        }}

        .page-sub {{
            color: var(--muted);
            max-width: 820px;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 22px;
        }}

        .dashboard-hero {{
            border-radius: 30px;
            padding: 26px;
            background:
              radial-gradient(500px 220px at 88% 10%, rgba(255,255,255,0.11), transparent 34%),
              linear-gradient(135deg, #64101c 0%, #7e1422 50%, #ab2337 100%);
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: var(--shadow);
            margin-bottom: 20px;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0,1fr));
            gap: 14px;
            margin: 18px 0 0 0;
        }}

        .kpi {{
            border-radius: 22px;
            padding: 18px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.10);
        }}
        .kpi .k {{
            color: rgba(255,243,234,0.70);
            font-size: 12px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .kpi .v {{
            color: #fff8f1;
            font-weight: 800;
            font-size: 28px;
            letter-spacing: -0.04em;
        }}

        .card-grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0,1fr));
            gap: 18px;
        }}

        .list-card {{
            border-radius: 26px;
            padding: 22px;
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.04));
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: 0 20px 45px rgba(0,0,0,0.18);
            height: 100%;
        }}
        .list-card h3 {{
            margin: 0 0 6px 0;
            color: #fff8f1;
            font-size: 24px;
            letter-spacing: -0.03em;
        }}
        .list-card p {{
            margin: 0 0 14px 0;
            color: var(--muted);
            font-size: 14px;
        }}

        .news-item, .entry-item {{
            border-top: 1px solid rgba(255,255,255,0.08);
            padding-top: 14px;
            margin-top: 14px;
        }}
        .news-item:first-child, .entry-item:first-child {{
            border-top: none;
            padding-top: 0;
            margin-top: 0;
        }}

        .chip {{
            display: inline-flex;
            align-items: center;
            padding: 7px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.10);
            color: #efe3d7;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .entry-title {{
            color: #fff8f1;
            font-weight: 800;
            font-size: 18px;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
        }}

        .entry-text {{
            color: #d9cbbb;
            line-height: 1.65;
            font-size: 14px;
        }}

        .toolbar-row {{
            display: flex;
            gap: 12px;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}

        .soft {{
            color: var(--muted);
        }}

        .muted-note {{
            color: var(--muted);
            font-size: 13px;
        }}

        .sep {{
            height: 1px;
            background: rgba(255,255,255,0.08);
            margin: 12px 0 18px 0;
        }}

        @media (max-width: 1180px) {{
            .shell {{
                grid-template-columns: 1fr;
            }}
            .hero, .signin-pane {{
                min-height: auto;
            }}
            .member-grid {{
                grid-template-columns: 1fr;
            }}
            .member-aside {{
                position: relative;
                top: auto;
            }}
            .kpi-grid {{
                grid-template-columns: repeat(2, minmax(0,1fr));
            }}
            .card-grid-2 {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 760px) {{
            .topbar {{
                padding: 16px;
                border-radius: 22px;
            }}
            .brand-name {{
                font-size: 30px;
            }}
            .logo-chip {{
                width: 60px;
                height: 60px;
            }}
            .hero {{
                padding: 22px;
                border-radius: 26px;
            }}
            .signin-pane {{
                padding: 14px;
                border-radius: 26px;
            }}
            .metric-row, .info-strip, .kpi-grid {{
                grid-template-columns: 1fr;
            }}
            .page-title {{
                font-size: 34px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Session
# -----------------------------
def ensure_session() -> None:
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "page" not in st.session_state:
        st.session_state.page = "Accueil"
    if "public_tab" not in st.session_state:
        st.session_state.public_tab = "Connexion"
    if "auth_notice" not in st.session_state:
        st.session_state.auth_notice = ""


def current_user() -> Optional[sqlite3.Row]:
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    return fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))


def login_user(user_id: int) -> None:
    st.session_state.user_id = user_id


def logout_user() -> None:
    st.session_state.user_id = None
    st.session_state.page = "Accueil"


# -----------------------------
# Public page
# -----------------------------
def render_public_topbar() -> None:
    st.markdown(
        f"""
        <div class="fl-wrap">
            <div class="topbar glass">
                <div class="brandbox">
                    <div class="logo-chip">
                        <img src="{html.escape(LOGO_DARK_URI)}" alt="Flam's logo">
                    </div>
                    <div>
                        <h1 class="brand-name">Flamsily</h1>
                        <p class="brand-sub">Accès membre · Communauté Flam's</p>
                    </div>
                </div>
                <div class="nav">
                    <div class="nav-pill">Accès membre</div>
                    <div class="nav-pill">Inscription</div>
                    <div class="nav-pill">Connexion sécurisée</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_public_page() -> None:
    render_public_topbar()

    total_users = fetch_one("SELECT COUNT(*) AS c FROM users")["c"]
    total_news = fetch_one("SELECT COUNT(*) AS c FROM news")["c"]
    total_jobs = fetch_one("SELECT COUNT(*) AS c FROM jobs")["c"]

    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="hero">
                <img class="hero-logo" src="{html.escape(LOGO_LIGHT_URI)}" alt="Flam's">
                <div class="hero-tag">🔥 Espace membre Flam's</div>
                <h1>Connexion premium.<br>Accès immédiat.</h1>
                <p>Un accès simple et direct à l'intranet de la communauté Flam's. Connectez-vous ou créez votre compte pour entrer dans votre espace membre.</p>
                <div class="metric-row">
                    <div class="metric">
                        <div class="label">Accès</div>
                        <div class="value">Direct</div>
                    </div>
                    <div class="metric">
                        <div class="label">Membres</div>
                        <div class="value">{total_users}</div>
                    </div>
                    <div class="metric">
                        <div class="label">Contenus</div>
                        <div class="value">{total_news + total_jobs}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="signin-pane glass"><div class="signin-shell">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="signin-head">
                <div>
                    <h2 class="signin-title">Accès membre</h2>
                    <p class="signin-sub">Connectez-vous ou créez votre compte.</p>
                </div>
                <div class="micro-badge">Flamsily Secure</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tabs = st.tabs(["Connexion", "Créer un compte"])

        with tabs[0]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Adresse e-mail", placeholder="prenom.nom@email.com", key="login_email")
                password = st.text_input("Mot de passe", type="password", placeholder="••••••••", key="login_password")
                submitted = st.form_submit_button("Se connecter")
                if submitted:
                    user = authenticate(email, password)
                    if user:
                        login_user(user["id"])
                        st.success("Connexion réussie.")
                        st.rerun()
                    else:
                        st.error("Adresse e-mail ou mot de passe incorrect.")
            st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
            st.markdown('<div class="muted-note">Mot de passe oublié ? Contactez l’administration pour une réinitialisation.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with tabs[1]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            with st.form("signup_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("Prénom", placeholder="Prénom")
                    flams_site = st.text_input("Dans quelle Flam's avez-vous travaillé ?", placeholder="Ex. Strasbourg")
                    email = st.text_input("Adresse e-mail", placeholder="prenom.nom@email.com")
                    password = st.text_input("Mot de passe", type="password", placeholder="8 caractères minimum")
                with col2:
                    last_name = st.text_input("Nom", placeholder="Nom")
                    age = st.number_input("Âge", min_value=16, max_value=90, value=25, step=1)
                    phone = st.text_input("Téléphone (facultatif)", placeholder="06 00 00 00 00")
                    password_confirm = st.text_input("Confirmer le mot de passe", type="password", placeholder="Retapez le mot de passe")

                submitted = st.form_submit_button("Créer mon compte")
                if submitted:
                    if password != password_confirm:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif not first_name.strip() or not last_name.strip() or not flams_site.strip():
                        st.error("Merci de remplir tous les champs obligatoires.")
                    else:
                        ok, msg = create_user(first_name, last_name, flams_site, int(age), email, phone, password)
                        if ok:
                            st.success(msg + " Vous pouvez maintenant vous connecter.")
                        else:
                            st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="info-strip">
                <div class="info-mini"><strong>1 URL</strong><span>Accès unique</span></div>
                <div class="info-mini"><strong>E-mail</strong><span>Connexion sécurisée</span></div>
                <div class="info-mini"><strong>Profil</strong><span>Espace personnel</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div></div>', unsafe_allow_html=True)


# -----------------------------
# Member UI
# -----------------------------
PAGES = ["Accueil", "Actualités", "Annuaire", "Événements", "Carrières", "Mon profil"]
ADMIN_PAGES = ["Administration"]


def aside_navigation(user: sqlite3.Row) -> None:
    initials = f"{(user['first_name'] or 'U')[:1]}{(user['last_name'] or '')[:1]}".upper()
    st.markdown(
        f"""
        <div class="member-aside">
            <div class="member-card">
                <div class="avatar">{html.escape(initials)}</div>
                <div class="member-name">{html.escape(user['first_name'])} {html.escape(user['last_name'])}</div>
                <div class="member-meta">{html.escape(user['flams_site'])} · {html.escape(user['email'])}</div>
            </div>
            <div class="quiet">Navigation</div>
            <div style="height:10px;"></div>
        """,
        unsafe_allow_html=True,
    )

    for label in PAGES:
        if st.button(label, key=f"nav_{label}"):
            st.session_state.page = label
            st.rerun()

    if user["is_admin"]:
        st.markdown('<div style="height:8px;"></div><div class="quiet">Admin</div><div style="height:10px;"></div>', unsafe_allow_html=True)
        for label in ADMIN_PAGES:
            if st.button(label, key=f"nav_{label}"):
                st.session_state.page = label
                st.rerun()

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Déconnexion", key="logout_btn"):
            logout_user()
            st.rerun()
    with c2:
        st.markdown('<div class="muted-note" style="padding-top:14px;text-align:right;">Session active</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_member_header(user: sqlite3.Row) -> None:
    page = st.session_state.get("page", "Accueil")
    top_pills = "".join([f'<div class="nav-pill">{html.escape(p)}</div>' for p in ["Réseau Flam's", page, "Espace membre"]])
    st.markdown(
        f"""
        <div class="topbar glass">
            <div class="brandbox">
                <div class="logo-chip">
                    <img src="{html.escape(LOGO_DARK_URI)}" alt="Flam's logo">
                </div>
                <div>
                    <h1 class="brand-name" style="font-size:34px;">Flamsily</h1>
                    <p class="brand-sub">{html.escape(user['first_name'])}, bienvenue dans votre espace membre</p>
                </div>
            </div>
            <div class="nav">{top_pills}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(user: sqlite3.Row) -> None:
    member_count = fetch_one("SELECT COUNT(*) AS c FROM users")["c"]
    news_count = fetch_one("SELECT COUNT(*) AS c FROM news")["c"]
    jobs_count = fetch_one("SELECT COUNT(*) AS c FROM jobs")["c"]
    event_count = fetch_one("SELECT COUNT(*) AS c FROM events")["c"]
    latest_news = fetch_all("SELECT * FROM news ORDER BY id DESC LIMIT 3")
    latest_jobs = fetch_all("SELECT * FROM jobs ORDER BY id DESC LIMIT 3")

    st.markdown(
        f"""
        <div class="dashboard-hero">
            <div class="hero-tag">🔥 Bonjour {html.escape(user['first_name'])}</div>
            <h2 class="page-title" style="margin-bottom:10px;">Bienvenue dans l’intranet Flam’s</h2>
            <div class="page-sub" style="margin-bottom:0;color:rgba(255,246,237,0.84);">
                Retrouvez les actualités de la communauté, l’annuaire des membres, les événements et les opportunités du réseau.
            </div>
            <div class="kpi-grid">
                <div class="kpi"><div class="k">Membres</div><div class="v">{member_count}</div></div>
                <div class="kpi"><div class="k">Actualités</div><div class="v">{news_count}</div></div>
                <div class="kpi"><div class="k">Événements</div><div class="v">{event_count}</div></div>
                <div class="kpi"><div class="k">Carrières</div><div class="v">{jobs_count}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="list-card"><h3>Actualités récentes</h3><p>Les dernières publications de la communauté.</p>', unsafe_allow_html=True)
        for item in latest_news:
            st.markdown(
                f"""
                <div class="news-item">
                    <div class="chip">{html.escape(item['category'])}</div>
                    <div class="entry-title">{html.escape(item['title'])}</div>
                    <div class="entry-text">{html.escape(item['content'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="list-card"><h3>Opportunités</h3><p>Les offres actuellement visibles dans le réseau.</p>', unsafe_allow_html=True)
        for item in latest_jobs:
            st.markdown(
                f"""
                <div class="entry-item">
                    <div class="chip">{html.escape(item['contract_type'])} · {html.escape(item['location'])}</div>
                    <div class="entry-title">{html.escape(item['title'])}</div>
                    <div class="entry-text">{html.escape(item['summary'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)


def render_news() -> None:
    st.markdown('<div class="page-title">Actualités</div><div class="page-sub">Toutes les publications récentes de la communauté Flam’s.</div>', unsafe_allow_html=True)
    items = fetch_all("SELECT * FROM news ORDER BY id DESC")
    for item in items:
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:16px;">
                <div class="chip">{html.escape(item['category'])}</div>
                <div class="entry-title" style="font-size:26px;">{html.escape(item['title'])}</div>
                <div class="soft" style="font-size:13px;margin-bottom:12px;">Publié par {html.escape(item['author'])}</div>
                <div class="entry-text">{html.escape(item['content'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_directory() -> None:
    st.markdown('<div class="page-title">Annuaire</div><div class="page-sub">Retrouvez les membres de la communauté par nom, e-mail ou établissement.</div>', unsafe_allow_html=True)
    q = st.text_input("Rechercher un membre", placeholder="Nom, prénom, e-mail ou Flam's")
    query = "SELECT first_name, last_name, email, flams_site, age, phone, created_at FROM users"
    params: tuple = ()
    if q.strip():
        query += " WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR flams_site LIKE ?"
        like = f"%{q.strip()}%"
        params = (like, like, like, like)
    query += " ORDER BY last_name, first_name"

    rows = fetch_all(query, params)
    data = [
        {
            "Prénom": r["first_name"],
            "Nom": r["last_name"],
            "E-mail": r["email"],
            "Flam's": r["flams_site"],
            "Âge": r["age"],
            "Téléphone": r["phone"] or "",
        }
        for r in rows
    ]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def render_events() -> None:
    st.markdown('<div class="page-title">Événements</div><div class="page-sub">Les prochains rendez-vous du réseau Flam’s.</div>', unsafe_allow_html=True)
    items = fetch_all("SELECT * FROM events ORDER BY event_date ASC")
    if not items:
        st.info("Aucun événement pour le moment.")
        return
    for item in items:
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:16px;">
                <div class="chip">{html.escape(item['event_date'])} · {html.escape(item['location'])}</div>
                <div class="entry-title" style="font-size:24px;">{html.escape(item['title'])}</div>
                <div class="entry-text">{html.escape(item['description'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_jobs() -> None:
    st.markdown('<div class="page-title">Carrières</div><div class="page-sub">Consultez les opportunités et mobilités partagées dans le réseau.</div>', unsafe_allow_html=True)
    items = fetch_all("SELECT * FROM jobs ORDER BY id DESC")
    if not items:
        st.info("Aucune offre pour le moment.")
        return
    for item in items:
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:16px;">
                <div class="chip">{html.escape(item['contract_type'])} · {html.escape(item['location'])}</div>
                <div class="entry-title" style="font-size:24px;">{html.escape(item['title'])}</div>
                <div class="entry-text">{html.escape(item['summary'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_profile(user: sqlite3.Row) -> None:
    st.markdown('<div class="page-title">Mon profil</div><div class="page-sub">Mettez à jour vos informations personnelles et votre mot de passe.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1.2, 0.8], gap="large")
    with col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        with st.form("profile_form"):
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input("Prénom", value=user["first_name"])
                flams_site = st.text_input("Flam's", value=user["flams_site"])
                email = st.text_input("Adresse e-mail", value=user["email"])
            with c2:
                last_name = st.text_input("Nom", value=user["last_name"])
                age = st.number_input("Âge", min_value=16, max_value=90, value=int(user["age"]), step=1)
                phone = st.text_input("Téléphone", value=user["phone"] or "")
            submitted = st.form_submit_button("Enregistrer les modifications")
            if submitted:
                ok, msg = update_profile(user["id"], first_name, last_name, flams_site, int(age), email, phone)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        with st.form("pwd_form"):
            current_password = st.text_input("Mot de passe actuel", type="password")
            new_password = st.text_input("Nouveau mot de passe", type="password")
            submitted = st.form_submit_button("Changer le mot de passe")
            if submitted:
                ok, msg = change_password(user["id"], current_password, new_password)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)


def render_admin() -> None:
    st.markdown('<div class="page-title">Administration</div><div class="page-sub">Publiez les contenus de la communauté et suivez les membres inscrits.</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Actualités", "Événements", "Carrières", "Membres"])

    with tabs[0]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        with st.form("admin_news_form", clear_on_submit=True):
            title = st.text_input("Titre")
            category = st.text_input("Catégorie", value="Actualité")
            content = st.text_area("Contenu", height=180)
            submitted = st.form_submit_button("Publier l’actualité")
            if submitted:
                if title.strip() and content.strip():
                    execute(
                        "INSERT INTO news (title, content, category, author, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title.strip(), content.strip(), category.strip() or "Actualité", "Administration", datetime.utcnow().isoformat()),
                    )
                    st.success("Actualité publiée.")
                    st.rerun()
                else:
                    st.error("Merci de renseigner le titre et le contenu.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        with st.form("admin_events_form", clear_on_submit=True):
            title = st.text_input("Nom de l’événement")
            event_date = st.date_input("Date")
            location = st.text_input("Lieu")
            description = st.text_area("Description", height=160)
            submitted = st.form_submit_button("Publier l’événement")
            if submitted:
                if title.strip() and location.strip() and description.strip():
                    execute(
                        "INSERT INTO events (title, event_date, location, description, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title.strip(), str(event_date), location.strip(), description.strip(), datetime.utcnow().isoformat()),
                    )
                    st.success("Événement publié.")
                    st.rerun()
                else:
                    st.error("Merci de remplir tous les champs.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        with st.form("admin_jobs_form", clear_on_submit=True):
            title = st.text_input("Titre du poste")
            location = st.text_input("Lieu")
            contract_type = st.selectbox("Type de contrat", ["CDI", "CDD", "Alternance", "Stage", "Freelance"])
            summary = st.text_area("Résumé", height=160)
            submitted = st.form_submit_button("Publier l’offre")
            if submitted:
                if title.strip() and location.strip() and summary.strip():
                    execute(
                        "INSERT INTO jobs (title, location, contract_type, summary, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title.strip(), location.strip(), contract_type, summary.strip(), datetime.utcnow().isoformat()),
                    )
                    st.success("Offre publiée.")
                    st.rerun()
                else:
                    st.error("Merci de remplir tous les champs.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        users = fetch_all("SELECT first_name, last_name, email, flams_site, age, phone, is_admin, created_at FROM users ORDER BY id DESC")
        data = [
            {
                "Prénom": u["first_name"],
                "Nom": u["last_name"],
                "E-mail": u["email"],
                "Flam's": u["flams_site"],
                "Âge": u["age"],
                "Téléphone": u["phone"] or "",
                "Admin": "Oui" if u["is_admin"] else "Non",
            }
            for u in users
        ]
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def render_member_app(user: sqlite3.Row) -> None:
    render_member_header(user)
    left, right = st.columns([0.28, 0.72], gap="large")
    with left:
        aside_navigation(user)
    with right:
        page = st.session_state.get("page", "Accueil")
        if page == "Accueil":
            render_dashboard(user)
        elif page == "Actualités":
            render_news()
        elif page == "Annuaire":
            render_directory()
        elif page == "Événements":
            render_events()
        elif page == "Carrières":
            render_jobs()
        elif page == "Mon profil":
            render_profile(user)
        elif page == "Administration" and user["is_admin"]:
            render_admin()
        else:
            render_dashboard(user)


# -----------------------------
# App
# -----------------------------
def main() -> None:
    ensure_session()
    init_db()
    render_css()
    user = current_user()
    if user:
        render_member_app(user)
    else:
        render_public_page()


if __name__ == "__main__":
    main()
