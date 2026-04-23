
import sqlite3
from datetime import datetime
import hashlib
import pandas as pd
import streamlit as st

DB_PATH = "data/flamsily.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(first_name, last_name, flams_worked, age, email, phone, password, bio="", city="", role="member"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (
            first_name, last_name, flams_worked, age, email, phone, password_hash, bio, city, role, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            first_name.strip(),
            last_name.strip(),
            flams_worked.strip(),
            int(age),
            email.strip().lower(),
            phone.strip(),
            hash_password(password),
            bio.strip(),
            city.strip(),
            role,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            flams_worked TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            password_hash TEXT NOT NULL,
            bio TEXT DEFAULT '',
            city TEXT DEFAULT '',
            role TEXT DEFAULT 'member',
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
            author TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) AS c FROM news")
    if cur.fetchone()["c"] == 0:
        for t, c, a in [
            ("Bienvenue sur Flamsily", "Votre nouvel intranet Flam's est en ligne. Retrouvez ici les actualités, votre profil et les informations internes importantes.", "Administration"),
            ("Ouverture des inscriptions", "Les anciens et actuels collaborateurs peuvent désormais créer leur compte directement depuis l'URL principale de l'application.", "Administration"),
            ("Nouveautés à venir", "Une prochaine version ajoutera les groupes, les événements et un annuaire interne plus complet.", "Administration"),
        ]:
            cur.execute(
                "INSERT INTO news (title, content, author, created_at) VALUES (?, ?, ?, ?)",
                (t, c, a, datetime.now().isoformat()),
            )
        conn.commit()

    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        create_user(
            first_name="Admin",
            last_name="Flamsily",
            flams_worked="Siège",
            age=30,
            email="admin@flamsily.local",
            phone="",
            password="admin12345",
            bio="Compte administrateur de démonstration.",
            city="Strasbourg",
            role="admin",
        )
    conn.close()

def authenticate(email: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    user = cur.fetchone()
    conn.close()
    if user and user["password_hash"] == hash_password(password):
        return dict(user)
    return None

def get_user_by_id(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_news():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM news ORDER BY datetime(created_at) DESC", conn)
    conn.close()
    return df

def add_news(title: str, content: str, author: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO news (title, content, author, created_at) VALUES (?, ?, ?, ?)",
        (title.strip(), content.strip(), author, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()

def update_profile(user_id: int, flams_worked: str, age: int, phone: str, bio: str, city: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET flams_worked = ?, age = ?, phone = ?, bio = ?, city = ?
        WHERE id = ?
        """,
        (flams_worked, int(age), phone, bio, city, user_id),
    )
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, first_name, last_name, email, flams_worked, city, role, created_at
        FROM users
        ORDER BY datetime(created_at) DESC
        """,
        conn,
    )
    conn.close()
    return df

def inject_css():
    st.markdown(
        """
        <style>
        .stApp { background: #f4f4f4; }
        header[data-testid="stHeader"] { background: transparent; }
        section[data-testid="stSidebar"] {
            background: #f3f3f3;
            border-right: 1px solid #dedede;
            width: 320px !important;
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }
        .flam-header {
            background: white;
            border-bottom: 1px solid #ececec;
            padding: 12px 28px;
            border-radius: 0 0 10px 10px;
        }
        .brand-wrap{ display:flex; align-items:center; gap:16px; }
        .brand-logo {
            width: 64px; height: 64px; border-radius: 14px;
            background: #ef2b2d; color:white; display:flex;
            align-items:center; justify-content:center;
            font-size: 28px; font-weight: 800;
            box-shadow: 0 8px 24px rgba(239,43,45,.18);
        }
        .brand-text h1{ margin:0; font-size: 2rem; line-height:1; color:#ef2b2d; font-weight:800; }
        .brand-text div{ color:#666; font-size:1rem; }
        .topnav {
            background:#ef2b2d; color:white; padding: 12px 24px; border-radius: 0 0 10px 10px;
            margin-bottom: 20px; font-weight:700;
        }
        .topnav span { margin-right: 26px; font-size: 0.98rem; }
        .hero {
            background: linear-gradient(120deg, rgba(30,30,30,.72), rgba(239,43,45,.40)),
                        url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1600&q=80');
            background-size: cover;
            background-position: center;
            min-height: 290px;
            border-radius: 18px;
            padding: 40px;
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 16px 40px rgba(0,0,0,.10);
        }
        .hero h2 { margin:0; font-size:2.35rem; }
        .hero p { font-size:1.1rem; max-width:760px; }
        .hero-badges { display:flex; gap:16px; flex-wrap:wrap; margin-top:12px; }
        .hero-badge {
            background: rgba(255,255,255,.16);
            border: 1px solid rgba(255,255,255,.28);
            padding: 10px 16px;
            border-radius: 999px;
            font-weight: 600;
        }
        .card {
            background:white;
            border-radius:18px;
            padding:22px;
            box-shadow:0 10px 28px rgba(0,0,0,.05);
            border:1px solid #efefef;
            height:100%;
        }
        .news-card{
            background:white;
            border-radius:16px;
            padding:18px 18px 14px 18px;
            margin-bottom:16px;
            box-shadow:0 8px 24px rgba(0,0,0,.04);
            border-left:6px solid #ef2b2d;
        }
        .news-card h4{ margin:0 0 6px 0; color:#222; }
        .muted { color:#767676; }
        .section-title{ font-size:2rem; font-weight:800; color:#222; margin: 22px 0 14px 0; }
        .login-shell { min-height: 78vh; display:flex; align-items:center; justify-content:center; }
        .login-card {
            width:100%; max-width:1050px; background:white; border-radius:24px; overflow:hidden;
            box-shadow:0 22px 60px rgba(0,0,0,.12); border:1px solid #ededed;
        }
        .login-title{ color:#ef2b2d; font-weight:800; font-size:2.2rem; margin-bottom:.2rem; }
        .login-sub{ color:#666; margin-bottom:1rem; }
        .left-panel{ background: linear-gradient(160deg, #ef2b2d 0%, #ff5757 100%); color:white; height:100%; padding:36px; }
        .pill{
            display:inline-block; padding:8px 14px; border-radius:999px; background:rgba(255,255,255,.18);
            border:1px solid rgba(255,255,255,.26); margin-right:8px; margin-bottom:8px; font-weight:600;
        }
        .small-card{
            background: rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.22);
            border-radius:18px; padding:18px; margin-top:18px;
        }
        .sidebar-profile{ background:#ef2b2d; color:white; padding:18px; border-radius:18px; margin-bottom:12px; }
        .completion{ background:white; border-radius:14px; padding:14px; border:1px solid #ececec; margin-bottom:14px; }
        .meter { width:100%; height:10px; background:#f0f0f0; border-radius:999px; overflow:hidden; margin-top:8px; }
        .meter > div { height:100%; background:#ef2b2d; }
        .stButton button {
            border-radius: 14px !important;
            font-weight: 700 !important;
            min-height: 2.9rem !important;
            border: 1px solid #ef2b2d !important;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 12px; }
        .stTabs [data-baseweb="tab"] {
            background: white; border-radius: 12px; border: 1px solid #ededed; padding: 8px 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def init_state():
    for k, v in {"user_id": None, "menu": "Accueil"}.items():
        if k not in st.session_state:
            st.session_state[k] = v

def set_user(user_dict):
    st.session_state.user_id = user_dict["id"]

def logout():
    st.session_state.user_id = None
    st.session_state.menu = "Accueil"

def current_user():
    if st.session_state.user_id:
        return get_user_by_id(st.session_state.user_id)
    return None

def profile_completion(user):
    fields = [
        bool(user.get("first_name")),
        bool(user.get("last_name")),
        bool(user.get("flams_worked")),
        bool(user.get("age")),
        bool(user.get("email")),
        bool(user.get("phone")),
        bool(user.get("bio")),
        bool(user.get("city")),
    ]
    return int(sum(fields) / len(fields) * 100)

def render_top_header():
    st.markdown(
        """
        <div class="flam-header">
            <div class="brand-wrap">
                <div class="brand-logo">F</div>
                <div class="brand-text">
                    <h1>Flamsily</h1>
                    <div>Intranet des équipes Flam's</div>
                </div>
            </div>
        </div>
        <div class="topnav">
            <span>ACTUALITÉS</span>
            <span>PROFIL</span>
            <span>ANNUAIRE</span>
            <span>CARRIÈRES</span>
            <span>RÉSEAU</span>
            <span>CONTACT</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def auth_page():
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([0.05, 0.90, 0.05])
    with c2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        left, right = st.columns([1.05, 1], gap="large")

        with left:
            st.markdown(
                """
                <div class="left-panel">
                    <div style="font-size:2.3rem;font-weight:800;line-height:1.1;">Bienvenue sur<br>Flamsily</div>
                    <div style="margin-top:10px;font-size:1.05rem;opacity:.95;">
                        L'intranet principal des équipes Flam's. Une seule URL pour s'inscrire, se connecter,
                        retrouver les actualités internes et gérer son profil.
                    </div>
                    <div style="margin-top:18px;">
                        <span class="pill">Inscription libre</span>
                        <span class="pill">Connexion simple</span>
                        <span class="pill">Profil personnel</span>
                    </div>
                    <div class="small-card">
                        <div style="font-weight:700; margin-bottom:6px;">Comment ça marche ?</div>
                        <div>1. J'ouvre l'URL principale de Flamsily</div>
                        <div>2. Je crée mon compte</div>
                        <div>3. Je me connecte</div>
                        <div>4. J'accède à mon intranet</div>
                    </div>
                    <div class="small-card">
                        <div style="font-weight:700; margin-bottom:6px;">Compte de démonstration</div>
                        <div>Email : admin@flamsily.local</div>
                        <div>Mot de passe : admin12345</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:
            st.markdown('<div style="padding:34px 28px 28px 8px;">', unsafe_allow_html=True)
            st.markdown('<div class="login-title">Accès membre</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-sub">Inscription et connexion depuis l’URL principale.</div>', unsafe_allow_html=True)

            login_tab, register_tab = st.tabs(["Connexion", "Créer un compte"])

            with login_tab:
                with st.form("login_form", clear_on_submit=False):
                    email = st.text_input("Adresse e-mail", placeholder="prenom.nom@email.com")
                    password = st.text_input("Mot de passe", type="password")
                    submitted = st.form_submit_button("Me connecter", use_container_width=True)
                    if submitted:
                        user = authenticate(email, password)
                        if user:
                            set_user(user)
                            st.success("Connexion réussie.")
                            st.rerun()
                        else:
                            st.error("E-mail ou mot de passe incorrect.")

            with register_tab:
                with st.form("register_form", clear_on_submit=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        first_name = st.text_input("Prénom")
                        flams_worked = st.text_input("Dans quelle Flam's avez-vous travaillé ?")
                        email = st.text_input("E-mail")
                        password = st.text_input("Mot de passe", type="password")
                        city = st.text_input("Ville", placeholder="Ex. Strasbourg")
                    with col2:
                        last_name = st.text_input("Nom")
                        age = st.number_input("Âge", min_value=16, max_value=100, step=1)
                        phone = st.text_input("Téléphone (facultatif)")
                        password2 = st.text_input("Confirmer le mot de passe", type="password")
                        bio = st.text_area("Présentation rapide", height=100)

                    submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
                    if submitted:
                        errors = []
                        if not first_name.strip():
                            errors.append("Le prénom est obligatoire.")
                        if not last_name.strip():
                            errors.append("Le nom est obligatoire.")
                        if not flams_worked.strip():
                            errors.append("Le champ Flam's est obligatoire.")
                        if not email.strip() or "@" not in email:
                            errors.append("L'e-mail est invalide.")
                        if len(password) < 6:
                            errors.append("Le mot de passe doit contenir au moins 6 caractères.")
                        if password != password2:
                            errors.append("Les mots de passe ne correspondent pas.")

                        if errors:
                            for err in errors:
                                st.error(err)
                        else:
                            try:
                                create_user(first_name, last_name, flams_worked, age, email, phone, password, bio, city)
                                st.success("Compte créé. Vous pouvez maintenant vous connecter.")
                            except sqlite3.IntegrityError:
                                st.error("Un compte existe déjà avec cet e-mail.")

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def sidebar(user):
    with st.sidebar:
        initials = f"{user['first_name'][:1]}{user['last_name'][:1]}".upper()
        st.markdown(
            f"""
            <div class="sidebar-profile">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:52px;height:52px;border-radius:999px;background:#ffd6d6;color:#ef2b2d;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.2rem;">
                        {initials}
                    </div>
                    <div>
                        <div style="font-weight:800;font-size:1.15rem;">{user['first_name']} {user['last_name']}</div>
                        <div style="opacity:.9;">Voir mon profil</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        completion = profile_completion(user)
        st.markdown(
            f"""
            <div class="completion">
                <div style="font-weight:700;">Votre profil est rempli à {completion}%</div>
                <div class="meter"><div style="width:{completion}%"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        menu = st.radio("Navigation", ["Accueil", "Mon profil", "Annuaire", "Carrières", "Admin"], index=["Accueil", "Mon profil", "Annuaire", "Carrières", "Admin"].index(st.session_state.menu) if st.session_state.menu in ["Accueil", "Mon profil", "Annuaire", "Carrières", "Admin"] else 0)
        st.session_state.menu = menu

        st.divider()
        st.caption("Flamsily • Intranet interne")
        if st.button("Se déconnecter", use_container_width=True):
            logout()
            st.rerun()

def home_page(user):
    render_top_header()
    st.markdown(
        """
        <div class="hero">
            <h2>Bienvenue sur votre intranet Flamsily</h2>
            <p>Retrouvez les actualités internes, votre espace personnel et les informations utiles de la communauté Flam's dans une interface inspirée d’un portail alumni moderne.</p>
            <div class="hero-badges">
                <div class="hero-badge">Actualités</div>
                <div class="hero-badge">Réseau interne</div>
                <div class="hero-badge">Profil membre</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Rejoignez la communauté Flam\'s</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    items = [
        ("Actualités internes", "Suivez les annonces et nouveautés de l’entreprise."),
        ("Annuaire membre", "Retrouvez les collaborateurs et anciens de votre réseau."),
        ("Espace carrière", "Découvrez les opportunités et informations métiers."),
    ]
    for col, (title, text) in zip([c1, c2, c3], items):
        with col:
            st.markdown(f'<div class="card"><div style="font-size:1.25rem;font-weight:800;margin-bottom:10px;">{title}</div><div class="muted">{text}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Actualités</div>', unsafe_allow_html=True)
    news_df = get_news()
    if news_df.empty:
        st.info("Aucune actualité pour le moment.")
    else:
        for _, row in news_df.iterrows():
            created = row["created_at"][:16].replace("T", " ")
            st.markdown(
                f"""
                <div class="news-card">
                    <h4>{row['title']}</h4>
                    <div class="muted" style="margin-bottom:10px;">Par {row['author']} • {created}</div>
                    <div>{row['content']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

def profile_page(user):
    render_top_header()
    st.markdown('<div class="section-title">Mon profil</div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, 1])

    with left:
        st.markdown(
            f"""
            <div class="card">
                <div style="font-size:1.5rem;font-weight:800;">{user['first_name']} {user['last_name']}</div>
                <div class="muted" style="margin-top:6px;">{user['email']}</div>
                <div style="margin-top:18px;"><b>Flam's :</b> {user['flams_worked']}</div>
                <div><b>Âge :</b> {user['age']}</div>
                <div><b>Téléphone :</b> {user['phone'] or 'Non renseigné'}</div>
                <div><b>Ville :</b> {user['city'] or 'Non renseignée'}</div>
                <div><b>Rôle :</b> {user['role']}</div>
                <div style="margin-top:14px;"><b>Présentation :</b><br>{user['bio'] or 'Aucune présentation.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Mettre à jour mon profil")
        with st.form("profile_form"):
            flams_worked = st.text_input("Dans quelle Flam's avez-vous travaillé ?", value=user["flams_worked"])
            age = st.number_input("Âge", min_value=16, max_value=100, value=int(user["age"]))
            phone = st.text_input("Téléphone", value=user["phone"] or "")
            city = st.text_input("Ville", value=user["city"] or "")
            bio = st.text_area("Présentation", value=user["bio"] or "", height=120)
            submitted = st.form_submit_button("Enregistrer", use_container_width=True)
            if submitted:
                update_profile(user["id"], flams_worked, age, phone, bio, city)
                st.success("Profil mis à jour.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def directory_page():
    render_top_header()
    st.markdown('<div class="section-title">Annuaire</div>', unsafe_allow_html=True)
    users = get_all_users()
    search = st.text_input("Rechercher un membre", placeholder="Nom, e-mail, ville, Flam's...")
    if search:
        mask = users.apply(lambda row: search.lower() in " ".join([str(x).lower() for x in row.values]), axis=1)
        users = users[mask]
    st.dataframe(users, use_container_width=True, hide_index=True)

def careers_page():
    render_top_header()
    st.markdown('<div class="section-title">Carrières</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    items = [
        ("Mobilité interne", "Consultez les postes et perspectives d’évolution."),
        ("Parcours métiers", "Retrouvez les passerelles entre établissements et fonctions."),
        ("Formations", "Accédez aux ressources utiles pour monter en compétences."),
    ]
    for col, (title, text) in zip([c1, c2, c3], items):
        with col:
            st.markdown(f'<div class="card"><div style="font-size:1.2rem;font-weight:800;margin-bottom:8px;">{title}</div><div class="muted">{text}</div></div>', unsafe_allow_html=True)

def admin_page(user):
    render_top_header()
    if user["role"] != "admin":
        st.warning("Cette section est réservée aux administrateurs.")
        return

    st.markdown('<div class="section-title">Administration</div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["Publier une actualité", "Voir les membres"])

    with t1:
        with st.form("news_form"):
            title = st.text_input("Titre")
            content = st.text_area("Contenu", height=160)
            submitted = st.form_submit_button("Publier l\'actualité", use_container_width=True)
            if submitted:
                if title.strip() and content.strip():
                    add_news(title, content, f"{user['first_name']} {user['last_name']}")
                    st.success("Actualité publiée.")
                    st.rerun()
                else:
                    st.error("Merci de remplir le titre et le contenu.")

    with t2:
        st.dataframe(get_all_users(), use_container_width=True, hide_index=True)

def private_app(user):
    sidebar(user)
    menu = st.session_state.menu
    if menu == "Accueil":
        home_page(user)
    elif menu == "Mon profil":
        profile_page(user)
    elif menu == "Annuaire":
        directory_page()
    elif menu == "Carrières":
        careers_page()
    elif menu == "Admin":
        admin_page(user)

st.set_page_config(page_title="Flamsily", page_icon="🔥", layout="wide")
init_db()
inject_css()
init_state()

user = current_user()
if user:
    private_app(user)
else:
    auth_page()
