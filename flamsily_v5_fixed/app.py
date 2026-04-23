
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Flamsily", page_icon="🔥", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "flamsily.db"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
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
            flams_site TEXT NOT NULL,
            age INTEGER,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'Actualité',
            created_at TEXT NOT NULL,
            author_email TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT,
            location TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("SELECT id FROM users WHERE email = ?", ("admin@flamsily.local",))
    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO users(first_name,last_name,flams_site,age,email,phone,password_hash,is_admin,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                "Admin", "Flamsily", "Siège", 30, "admin@flamsily.local", "",
                hash_password("admin12345"), 1, datetime.utcnow().isoformat()
            )
        )

    cur.execute("SELECT COUNT(*) as c FROM posts")
    if cur.fetchone()["c"] == 0:
        samples = [
            ("Ouverture de Flamsily", "Bienvenue sur le nouvel intranet Flam's. Retrouvez ici les actus, les membres et les opportunités.", "Actualité"),
            ("Soirée réseau", "Un afterwork sera organisé le mois prochain pour rassembler les collaborateurs et anciens.", "Événement"),
        ]
        for title, content, cat in samples:
            cur.execute(
                "INSERT INTO posts(title, content, category, created_at, author_email) VALUES(?,?,?,?,?)",
                (title, content, cat, datetime.utcnow().isoformat(), "admin@flamsily.local")
            )
    conn.commit()
    conn.close()

def css():
    logo_bdx = ASSETS_DIR / "logo_bdx.png"
    logo_url = ""
    if logo_bdx.exists():
        import base64
        logo_url = base64.b64encode(logo_bdx.read_bytes()).decode()

    st.markdown(f"""
    <style>
    :root {{
      --bg: #f6f1e8;
      --panel: #fffaf4;
      --panel-2: #fff;
      --line: #e8dccd;
      --text: #201814;
      --muted: #7f695d;
      --brand: #7b1620;
      --brand-2: #a1232f;
      --accent: #caa574;
      --success: #285c3b;
      --shadow: 0 12px 30px rgba(69, 28, 18, 0.08);
      --radius: 22px;
    }}
    .stApp {{
      background: linear-gradient(180deg, #f7f2ea 0%, #f3ede5 100%);
      color: var(--text);
    }}
    [data-testid="stSidebar"], header[data-testid="stHeader"] {{
      display: none;
    }}
    .block-container {{
      padding-top: 1.1rem;
      padding-bottom: 2rem;
      max-width: 1320px;
    }}
    .topbar {{
      background: rgba(255,250,244,.88);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(123,22,32,.08);
      border-radius: 24px;
      padding: 14px 20px;
      box-shadow: var(--shadow);
      display:flex; align-items:center; justify-content:space-between;
      margin-bottom: 20px;
    }}
    .brand {{
      display:flex; align-items:center; gap:14px;
    }}
    .brand-logo {{
      width:54px; height:54px; border-radius:16px; background:#fff; border:1px solid var(--line);
      background-image: url("data:image/png;base64,{logo_url}");
      background-size: contain; background-repeat: no-repeat; background-position: center;
    }}
    .brand-title {{ font-size: 28px; font-weight: 800; color: var(--brand); line-height:1; }}
    .brand-sub {{ font-size: 13px; color: var(--muted); margin-top:4px; }}
    .nav-pill {{
      display:inline-block; padding:10px 16px; margin-left:8px; background:#fff;
      border:1px solid var(--line); border-radius:999px; color:var(--text); font-weight:600;
      text-decoration:none;
    }}
    .auth-wrap {{
      min-height: 82vh; display:grid; grid-template-columns: 1.08fr .92fr; gap: 28px; align-items: stretch;
    }}
    .visual {{
      border-radius: 32px;
      background: linear-gradient(135deg, rgba(123,22,32,.98), rgba(161,35,47,.95));
      padding: 40px;
      box-shadow: var(--shadow);
      position:relative;
      overflow:hidden;
      color: white;
      border:1px solid rgba(255,255,255,.1);
    }}
    .visual::after {{
      content:""; position:absolute; inset:auto -60px -60px auto; width:220px; height:220px;
      background: radial-gradient(circle, rgba(255,255,255,.15), transparent 70%);
      border-radius:50%;
    }}
    .visual-logo {{
      width: 180px; margin-bottom: 28px;
      filter: drop-shadow(0 10px 30px rgba(0,0,0,.2));
    }}
    .visual h1 {{ font-size:56px; line-height:1.02; margin: 0 0 14px 0; letter-spacing:-1.5px; }}
    .visual p {{ font-size:20px; line-height:1.6; max-width: 640px; color: rgba(255,255,255,.92); }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top: 28px; }}
    .kpi {{
      background: rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.18); border-radius: 20px;
      padding:18px;
    }}
    .kpi .label {{ font-size:12px; text-transform:uppercase; letter-spacing:.12em; opacity:.78; }}
    .kpi .value {{ font-size:30px; font-weight:800; margin-top:8px; }}
    .auth-card {{
      background: rgba(255,250,244,.95);
      border:1px solid var(--line); border-radius: 32px; padding: 28px 28px 20px;
      box-shadow: var(--shadow);
      min-height: 720px;
    }}
    .auth-head h2 {{ margin:0; font-size:34px; color: var(--text); }}
    .auth-head p {{ color: var(--muted); margin: 8px 0 20px 0; font-size:16px; }}
    .subtle {{
      display:inline-flex; align-items:center; gap:8px; background:#fff; color:var(--brand);
      border:1px solid rgba(123,22,32,.12); border-radius:999px; padding:8px 14px; font-weight:700;
      margin-bottom:16px;
    }}
    .section-title {{
      font-size: 28px; font-weight: 800; color: var(--text); margin: 8px 0 16px 0;
    }}
    .surface {{
      background: rgba(255,255,255,.72); border:1px solid var(--line); border-radius: 24px; padding: 22px;
      box-shadow: var(--shadow);
    }}
    .side-card {{
      background: linear-gradient(180deg, #7b1620 0%, #951f2b 100%); color: white;
      border-radius: 28px; padding: 24px; box-shadow: var(--shadow); border:1px solid rgba(255,255,255,.08);
    }}
    .avatar {{
      width:60px; height:60px; background: rgba(255,255,255,.14); border-radius:50%;
      display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:800;
      border:1px solid rgba(255,255,255,.2); margin-bottom: 14px;
    }}
    .menu-btn button, .cta-btn button {{
      width:100%; border-radius: 16px !important; height: 48px;
      border:1px solid var(--line) !important; background:#fff !important; color:var(--text) !important;
      font-weight:700 !important;
      transition: all .18s ease;
    }}
    .menu-btn button:hover {{
      border-color: rgba(123,22,32,.35) !important;
      color: var(--brand) !important;
      box-shadow: 0 10px 22px rgba(123,22,32,.08);
      transform: translateY(-1px);
    }}
    .cta-btn button {{
      background: linear-gradient(135deg, #7b1620 0%, #a1232f 100%) !important;
      color: #fff !important;
      border: none !important;
      box-shadow: 0 12px 24px rgba(123,22,32,.22);
    }}
    .cta-btn button:hover {{
      filter: brightness(1.03);
      transform: translateY(-1px);
    }}
    .stTabs [data-baseweb="tab-list"] {{
      gap: 10px;
      background: transparent;
      padding-bottom: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
      height: 48px; padding: 0 18px; border-radius: 999px; background: #fff;
      border:1px solid var(--line);
      font-weight: 700;
    }}
    .stTabs [aria-selected="true"] {{
      background: linear-gradient(135deg, #7b1620 0%, #a1232f 100%) !important;
      color: #fff !important;
      border-color: transparent !important;
    }}
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
      border-radius: 16px !important;
      border: 1px solid var(--line) !important;
      background: #fffdf9 !important;
    }}
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stSelectbox"] label {{
      font-weight: 700 !important;
      color: var(--text) !important;
    }}
    .card {{
      background:#fff; border:1px solid var(--line); border-radius:24px; padding:22px; box-shadow: var(--shadow); height:100%;
    }}
    .card h4 {{ margin:0 0 10px 0; font-size:22px; }}
    .meta {{ color: var(--muted); font-size: 14px; margin-bottom: 12px; }}
    .hero {{
      background: linear-gradient(135deg, rgba(123,22,32,1), rgba(161,35,47,.92));
      border-radius: 28px; color:white; padding: 32px; box-shadow: var(--shadow); margin-bottom: 18px;
      border:1px solid rgba(255,255,255,.1);
    }}
    .hero h1 {{ margin:0; font-size: 44px; }}
    .hero p {{ margin:10px 0 0 0; font-size: 18px; color: rgba(255,255,255,.92); }}
    .badge {{
      display:inline-block; background: rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.16);
      padding:8px 12px; border-radius:999px; font-size: 13px; font-weight:700; margin-bottom:14px;
    }}
    .small-muted {{ color: var(--muted); font-size: 14px; }}
    </style>
    """, unsafe_allow_html=True)

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

def create_user(first_name, last_name, flams_site, age, email, phone, password):
    if fetch_one("SELECT id FROM users WHERE email = ?", (email.lower().strip(),)):
        return False, "Un compte existe déjà avec cet e-mail."
    execute(
        """
        INSERT INTO users(first_name,last_name,flams_site,age,email,phone,password_hash,is_admin,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            first_name.strip(), last_name.strip(), flams_site.strip(), int(age) if age else None,
            email.lower().strip(), phone.strip(), hash_password(password), 0, datetime.utcnow().isoformat()
        )
    )
    return True, "Compte créé avec succès."

def authenticate(email, password):
    row = fetch_one(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (email.lower().strip(), hash_password(password))
    )
    return row

def login(user):
    st.session_state.user = dict(user)
    st.session_state.logged_in = True
    st.rerun()

def logout():
    st.session_state.clear()
    st.rerun()

def topbar():
    st.markdown("""
    <div class="topbar">
        <div class="brand">
            <div class="brand-logo"></div>
            <div>
                <div class="brand-title">Flamsily</div>
                <div class="brand-sub">Intranet & communauté Flam's</div>
            </div>
        </div>
        <div>
            <span class="nav-pill">Actualités</span>
            <span class="nav-pill">Annuaire</span>
            <span class="nav-pill">Carrières</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def auth_screen():
    topbar()
    all_users = fetch_one("SELECT COUNT(*) as c FROM users")["c"]
    all_posts = fetch_one("SELECT COUNT(*) as c FROM posts")["c"]

    left, right = st.columns([1.12, 0.88], gap="large")
    with left:
        st.markdown('<div class="visual">', unsafe_allow_html=True)
        logo_beige = ASSETS_DIR / "logo_beige.png"
        if logo_beige.exists():
            st.image(str(logo_beige), width=200, use_container_width=False)
        st.markdown("""
        <div class="subtle">🔥 Communauté Flam's</div>
        <h1>Connecte-toi<br>à l’intranet</h1>
        <p>Une seule URL. Les membres s’inscrivent, se connectent et accèdent immédiatement à leur espace, aux actualités, à l’annuaire et aux opportunités.</p>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="kpi-grid">
          <div class="kpi"><div class="label">Accès</div><div class="value">Direct</div></div>
          <div class="kpi"><div class="label">Membres</div><div class="value">{all_users}</div></div>
          <div class="kpi"><div class="label">Actualités</div><div class="value">{all_posts}</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-head">
            <div class="subtle">Accès membre</div>
            <h2>Bienvenue</h2>
            <p>Connectez-vous ou créez votre compte Flam’s.</p>
        </div>
        """, unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs(["Connexion", "Créer un compte"])

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Adresse e-mail", placeholder="prenom.nom@email.com")
                password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
                submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            if submitted:
                user = authenticate(email, password)
                if user:
                    login(user)
                else:
                    st.error("E-mail ou mot de passe incorrect.")

            st.caption("Compte admin de test : admin@flamsily.local / admin12345")

        with tab_signup:
            with st.form("signup_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                first_name = col1.text_input("Prénom")
                last_name = col2.text_input("Nom")
                col3, col4 = st.columns([1.3, .7])
                flams_site = col3.text_input("Dans quelle Flam's avez-vous travaillé ?")
                age = col4.number_input("Âge", min_value=16, max_value=100, step=1)
                email2 = st.text_input("E-mail")
                phone = st.text_input("Téléphone (facultatif)")
                pw1 = st.text_input("Mot de passe", type="password")
                pw2 = st.text_input("Confirmer le mot de passe", type="password")
                create = st.form_submit_button("Créer mon compte", use_container_width=True, type="primary")
            if create:
                if not all([first_name, last_name, flams_site, email2, pw1, pw2]):
                    st.error("Merci de remplir tous les champs obligatoires.")
                elif pw1 != pw2:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(pw1) < 8:
                    st.error("Le mot de passe doit contenir au moins 8 caractères.")
                else:
                    ok, msg = create_user(first_name, last_name, flams_site, age, email2, phone, pw1)
                    if ok:
                        st.success(msg + " Vous pouvez maintenant vous connecter.")
                    else:
                        st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

def render_post_card(row):
    st.markdown(f"""
    <div class="card">
        <div class="meta">{row['category']} • {row['created_at'][:10]}</div>
        <h4>{row['title']}</h4>
        <div>{row['content']}</div>
    </div>
    """, unsafe_allow_html=True)

def member_sidebar(user):
    with st.container():
        st.markdown('<div class="side-card">', unsafe_allow_html=True)
        initials = (user["first_name"][:1] + user["last_name"][:1]).upper()
        st.markdown(f'<div class="avatar">{initials}</div>', unsafe_allow_html=True)
        st.markdown(f"### {user['first_name']} {user['last_name']}")
        st.markdown(f"**{user['flams_site']}**")
        st.markdown(f"<div class='small-muted'>{user['email']}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.write("")
        for key, label in [
            ("home","Accueil"),
            ("news","Actualités"),
            ("directory","Annuaire"),
            ("events","Événements"),
            ("jobs","Carrières"),
            ("profile","Mon profil"),
        ]:
            with st.container():
                st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        if user["is_admin"]:
            st.write("")
            st.markdown("##### Administration")
            for key, label in [("admin_news","Publier"),("admin_users","Utilisateurs")]:
                st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        if st.button("Se déconnecter", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)

def page_home(user):
    posts = fetch_all("SELECT * FROM posts ORDER BY created_at DESC LIMIT 3")
    st.markdown("""
    <div class="hero">
        <div class="badge">Réseau Flam’s</div>
        <h1>Bonjour et bienvenue</h1>
        <p>Retrouvez ici les dernières actualités, les membres de la communauté et les nouvelles opportunités.</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    metrics = [
        ("Membres", fetch_one("SELECT COUNT(*) as c FROM users")["c"]),
        ("Actualités", fetch_one("SELECT COUNT(*) as c FROM posts")["c"]),
        ("Événements", fetch_one("SELECT COUNT(*) as c FROM events")["c"]),
    ]
    for col, (label, value) in zip([c1,c2,c3], metrics):
        with col:
            st.markdown(f"""<div class="card"><div class="meta">{label}</div><h4>{value}</h4></div>""", unsafe_allow_html=True)
    st.markdown("### À la une")
    cols = st.columns(3)
    for i, post in enumerate(posts):
        with cols[i % 3]:
            render_post_card(post)

def page_news():
    posts = fetch_all("SELECT * FROM posts ORDER BY created_at DESC")
    st.markdown('<div class="section-title">Actualités</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, post in enumerate(posts):
        with cols[i % 2]:
            render_post_card(post)

def page_directory():
    st.markdown('<div class="section-title">Annuaire</div>', unsafe_allow_html=True)
    q = st.text_input("Rechercher un membre", placeholder="Nom, prénom, e-mail, site Flam's")
    params = []
    query = "SELECT first_name,last_name,flams_site,email,phone,age,created_at FROM users WHERE is_admin = 0"
    if q:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR flams_site LIKE ?)"
        like = f"%{q}%"
        params = [like, like, like, like]
    rows = fetch_all(query + " ORDER BY last_name, first_name", params)
    for row in rows:
        st.markdown(f"""
        <div class="card" style="margin-bottom:14px;">
            <h4>{row['first_name']} {row['last_name']}</h4>
            <div class="meta">{row['flams_site']} • {row['email']}</div>
            <div>Âge : {row['age'] or '—'} • Téléphone : {row['phone'] or '—'}</div>
        </div>
        """, unsafe_allow_html=True)

def page_events():
    st.markdown('<div class="section-title">Événements</div>', unsafe_allow_html=True)
    events = fetch_all("SELECT * FROM events ORDER BY COALESCE(event_date, created_at) DESC")
    if not events:
        st.info("Aucun événement pour le moment.")
    for ev in events:
        st.markdown(f"""
        <div class="card" style="margin-bottom:14px;">
            <div class="meta">{ev['event_date'] or 'Date à venir'} • {ev['location'] or 'Lieu à confirmer'}</div>
            <h4>{ev['title']}</h4>
            <div>{ev['content']}</div>
        </div>
        """, unsafe_allow_html=True)

def page_jobs():
    st.markdown('<div class="section-title">Carrières</div>', unsafe_allow_html=True)
    jobs = fetch_all("SELECT * FROM jobs ORDER BY created_at DESC")
    if not jobs:
        st.info("Aucune offre pour le moment.")
    for job in jobs:
        st.markdown(f"""
        <div class="card" style="margin-bottom:14px;">
            <div class="meta">{job['company']} • {job['location'] or 'Localisation à confirmer'}</div>
            <h4>{job['title']}</h4>
            <div>{job['content']}</div>
        </div>
        """, unsafe_allow_html=True)

def page_profile(user):
    st.markdown('<div class="section-title">Mon profil</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        first_name = c1.text_input("Prénom", value=user["first_name"])
        last_name = c2.text_input("Nom", value=user["last_name"])
        c3, c4 = st.columns([1.3, .7])
        flams_site = c3.text_input("Flam's", value=user["flams_site"])
        age = c4.number_input("Âge", min_value=16, max_value=100, value=int(user["age"] or 18))
        email = st.text_input("E-mail", value=user["email"], disabled=True)
        phone = st.text_input("Téléphone", value=user["phone"] or "")
        save = st.form_submit_button("Enregistrer les modifications", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if save:
        execute("UPDATE users SET first_name=?, last_name=?, flams_site=?, age=?, phone=? WHERE id=?",
                (first_name, last_name, flams_site, age, phone, user["id"]))
        fresh = fetch_one("SELECT * FROM users WHERE id=?", (user["id"],))
        st.session_state.user = dict(fresh)
        st.success("Profil mis à jour.")
        st.rerun()

def page_admin_news(user):
    st.markdown('<div class="section-title">Administration</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["Actualité", "Événement", "Offre"])
    with t1:
        with st.form("new_post"):
            title = st.text_input("Titre")
            category = st.selectbox("Catégorie", ["Actualité", "Info interne", "Événement"])
            content = st.text_area("Contenu", height=160)
            ok = st.form_submit_button("Publier l’actualité", type="primary")
        if ok and title and content:
            execute("INSERT INTO posts(title,content,category,created_at,author_email) VALUES(?,?,?,?,?)",
                    (title, content, category, datetime.utcnow().isoformat(), user["email"]))
            st.success("Actualité publiée.")
            st.rerun()
    with t2:
        with st.form("new_event"):
            title = st.text_input("Nom de l’événement")
            event_date = st.text_input("Date", placeholder="Ex: 2025-09-12 19:00")
            location = st.text_input("Lieu")
            content = st.text_area("Description", height=140)
            ok2 = st.form_submit_button("Publier l’événement", type="primary")
        if ok2 and title and content:
            execute("INSERT INTO events(title,event_date,location,content,created_at) VALUES(?,?,?,?,?)",
                    (title, event_date, location, content, datetime.utcnow().isoformat()))
            st.success("Événement publié.")
            st.rerun()
    with t3:
        with st.form("new_job"):
            title = st.text_input("Poste")
            company = st.text_input("Entreprise")
            location = st.text_input("Lieu")
            content = st.text_area("Description", height=140)
            ok3 = st.form_submit_button("Publier l’offre", type="primary")
        if ok3 and title and company and content:
            execute("INSERT INTO jobs(title,company,location,content,created_at) VALUES(?,?,?,?,?)",
                    (title, company, location, content, datetime.utcnow().isoformat()))
            st.success("Offre publiée.")
            st.rerun()

def page_admin_users():
    st.markdown('<div class="section-title">Utilisateurs</div>', unsafe_allow_html=True)
    rows = fetch_all("SELECT first_name,last_name,email,flams_site,created_at,is_admin FROM users ORDER BY created_at DESC")
    for row in rows:
        role = "Admin" if row["is_admin"] else "Membre"
        st.markdown(f"""
        <div class="card" style="margin-bottom:14px;">
            <h4>{row['first_name']} {row['last_name']}</h4>
            <div class="meta">{role} • {row['email']}</div>
            <div>{row['flams_site']} • créé le {row['created_at'][:10]}</div>
        </div>
        """, unsafe_allow_html=True)

def member_app():
    user = st.session_state.user
    topbar()
    if "page" not in st.session_state:
        st.session_state.page = "home"
    left, right = st.columns([0.28, 0.72], gap="large")
    with left:
        member_sidebar(user)
    with right:
        page = st.session_state.page
        if page == "home":
            page_home(user)
        elif page == "news":
            page_news()
        elif page == "directory":
            page_directory()
        elif page == "events":
            page_events()
        elif page == "jobs":
            page_jobs()
        elif page == "profile":
            page_profile(user)
        elif page == "admin_news" and user["is_admin"]:
            page_admin_news(user)
        elif page == "admin_users" and user["is_admin"]:
            page_admin_users()
        else:
            page_home(user)

init_db()
css()

if st.session_state.get("logged_in"):
    member_app()
else:
    auth_screen()
