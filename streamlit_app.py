import streamlit as st
import json
import csv
import io
import os
import base64
import calendar as cal_module
from datetime import datetime, timedelta, date as date_type
import difflib
import qrcode
import qrcode.image.pil
from io import BytesIO

# ── Gestion accès protégé ──────────────────────────────────────────────────────
if "access_mode" not in st.session_state:
    st.session_state["access_mode"] = None

MOT_DE_PASSE_ADMIN = "pharmaCHBA"

# ── SUPABASE ───────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
try:
    from supabase import create_client
    _supabase_client = None
except Exception:
    create_client = None
    _supabase_client = None

def get_supabase_client():
    global _supabase_client
    if not create_client or not SUPABASE_URL or not SUPABASE_KEY:
        return None
    if _supabase_client is None:
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            _supabase_client = None
    return _supabase_client

# ── JOURS FÉRIÉS & JOURS TRAVAILLÉS ───────────────────────────────────────────
def get_french_holidays(year):
    h = set()
    h.add(date_type(year, 1, 1))
    h.add(date_type(year, 5, 1))
    h.add(date_type(year, 5, 8))
    h.add(date_type(year, 7, 14))
    h.add(date_type(year, 8, 15))
    h.add(date_type(year, 11, 1))
    h.add(date_type(year, 11, 11))
    h.add(date_type(year, 12, 25))
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    hh = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - hh - k) % 7
    m = (a + 11 * hh + 22 * l) // 451
    month = (hh + l - 7 * m + 114) // 31
    day = ((hh + l - 7 * m + 114) % 31) + 1
    easter = date_type(year, month, day)
    h.add(easter + timedelta(days=1))
    h.add(easter + timedelta(days=39))
    h.add(easter + timedelta(days=50))
    return h

_HOLIDAY_CACHE = {}

def get_holidays_cached(year):
    if year not in _HOLIDAY_CACHE:
        _HOLIDAY_CACHE[year] = get_french_holidays(year)
    return _HOLIDAY_CACHE[year]

def is_working_day(d):
    if d.weekday() >= 5:
        return False
    return d not in get_holidays_cached(d.year)

def next_working_day_offset(d, offset_working_days):
    current = d
    counted = 0
    while counted < offset_working_days:
        current += timedelta(days=1)
        if is_working_day(current):
            counted += 1
    return current

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="MicroSurveillance URC", page_icon="🦠")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;font-size:17px}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#f8fafc!important}
[data-testid="stHeader"]{background:#f8fafc!important;border-bottom:1px solid #e2e8f0!important}
#MainMenu,footer{visibility:hidden}
.block-container{max-width:100%!important;padding-left:1rem!important;padding-right:1rem!important}
p,li,div{color:#1e293b;font-size:1rem}
h1,h2,h3,h4{color:#0f172a!important;font-size:1.15rem!important}
.stMarkdown p,.stMarkdown li{color:#0f172a;font-size:1rem}
[data-testid="stSidebar"]{background:#ffffff!important;border-right:2px solid #e2e8f0!important;box-shadow:2px 0 12px rgba(0,0,0,.07)!important}
[data-testid="stSidebar"] *{color:#1e293b!important;font-size:.95rem!important}
[data-testid="stSidebar"] p{color:#0f172a!important;font-size:.95rem!important}
[data-testid="collapsedControl"]{background:#2563eb!important;border-radius:0 12px 12px 0!important;width:32px!important;min-width:32px!important;box-shadow:4px 0 16px rgba(37,99,235,.5)!important;border:none!important}
[data-testid="collapsedControl"]:hover{background:#1d4ed8!important}
[data-testid="collapsedControl"] svg{fill:#ffffff!important;stroke:#ffffff!important;width:20px!important;height:20px!important;opacity:1!important}
[data-testid="stSidebarCollapsedControl"]{background:#2563eb!important;border-radius:0 12px 12px 0!important;width:32px!important;box-shadow:4px 0 16px rgba(37,99,235,.5)!important}
[data-testid="stSidebarCollapsedControl"] svg{fill:#ffffff!important;stroke:#ffffff!important}
[data-testid="stSidebarCollapsedControl"]:hover{background:#1d4ed8!important}
.stButton>button{border-radius:8px!important;font-size:.95rem!important;font-weight:600!important;border:1.5px solid #e2e8f0!important;color:#1e293b!important;background:#ffffff!important;transition:all .15s;padding:8px 16px!important}
.stButton>button:hover{background:#f1f5f9!important;border-color:#0f172a!important}
.stButton>button[kind="primary"]{background:#2563eb!important;color:#fff!important;border-color:#2563eb!important}
.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;border-color:#1d4ed8!important}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div,.stNumberInput>div>div>input{background:#ffffff!important;color:#1e293b!important;border:1.5px solid #cbd5e1!important;border-radius:8px!important;font-size:1rem!important}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:#2563eb!important;box-shadow:0 0 0 3px rgba(37,99,235,.15)!important}
label{color:#374151!important;font-size:.95rem!important;font-weight:600!important}
.stCheckbox label{color:#374151!important;font-size:.95rem!important}
.stCheckbox span{color:#374151!important;font-size:.95rem!important}
div[data-testid="stExpander"]{background:#ffffff!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;box-shadow:0 1px 4px rgba(0,0,0,.06)!important}
div[data-testid="stExpander"] summary,div[data-testid="stExpander"] summary *{color:#1e293b!important;font-size:1rem!important}
div[data-testid="stExpander"] summary svg{fill:#0f172a!important;stroke:#0f172a!important}
.stTabs [data-baseweb="tab-list"]{background:#f1f5f9!important;border-radius:10px!important;padding:3px!important;border:1.5px solid #e2e8f0!important}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#0f172a!important;border-radius:8px!important;font-weight:600!important;font-size:1rem!important;padding:8px 18px!important}
.stTabs [aria-selected="true"]{background:#ffffff!important;color:#2563eb!important;box-shadow:0 1px 4px rgba(0,0,0,.1)!important}
[data-testid="stMetric"]{background:#fff!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;padding:16px!important}
[data-testid="stMetricValue"]{color:#0f172a!important;font-size:1.6rem!important}
[data-testid="stMetricLabel"]{color:#0f172a!important;font-size:.9rem!important}
[data-testid="stMetricDelta"]{font-size:.85rem!important}
.stAlert{border-radius:10px!important}
.stSuccess>div{background:#f0fdf4!important;border:1px solid #86efac!important;color:#166534!important;font-size:1rem!important}
.stWarning>div{background:#fffbeb!important;border:1px solid #fcd34d!important;color:#92400e!important;font-size:1rem!important}
.stInfo>div{background:#eff6ff!important;border:1px solid #93c5fd!important;color:#1e40af!important;font-size:1rem!important}
.stError>div{background:#fef2f2!important;border:1px solid #fca5a5!important;color:#991b1b!important;font-size:1rem!important}
hr{border-color:#e2e8f0!important}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:#2563eb!important;color:#fff!important;border-color:#2563eb!important}
[data-testid="stSidebar"] .stButton>button{background:#f8fafc!important;color:#374151!important;border:1.5px solid #e2e8f0!important;font-size:1rem!important;padding:12px 8px!important}
[data-testid="stSidebar"] .stButton>button:hover{background:#eff6ff!important;border-color:#93c5fd!important}
[data-testid="stSidebar"] p{font-size:.95rem!important}
.stSlider [data-testid="stThumbValue"]{color:#2563eb!important}
.stNumberInput button{background:#f1f5f9!important;border-color:#e2e8f0!important;color:#1e293b!important;font-size:1rem!important}
.stNumberInput button:hover{background:#e2e8f0!important}
.stDownloadButton>button{color:#2563eb!important;border-color:#93c5fd!important;background:#eff6ff!important;font-size:.95rem!important}
.stDownloadButton>button:hover{background:#dbeafe!important}
.stCaption{font-size:.88rem!important}
[data-testid="stSelectbox"] div,[data-testid="stSelectbox"] span{font-size:1rem!important}
[data-testid="stRadio"] label,[data-testid="stRadio"] span{font-size:1rem!important}
[data-testid="stDateInput"] input{font-size:1rem!important}
/* ── Cacher le bouton FAQ dans la nav ──────────────────────────────────── */
[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:has(div p) {
    display: block;
}
/* ── Bouton champignon FAQ ───────────────────────────────────────────────── */
@keyframes mush-bounce {
    0%,100%{ transform:translateY(0) rotate(0deg) scale(1); }
    25%     { transform:translateY(-7px) rotate(-6deg) scale(1.05); }
    50%     { transform:translateY(-10px) rotate(0deg) scale(1.08); }
    75%     { transform:translateY(-7px) rotate(6deg) scale(1.05); }
}
@keyframes mush-glow {
    0%,100%{ box-shadow:0 0 0 0 rgba(124,58,237,0); }
    50%    { box-shadow:0 0 22px 6px rgba(124,58,237,.45); }
}
@keyframes mush-dance {
    0%  { transform:rotate(-14deg) scale(1); }
    20% { transform:rotate(14deg) scale(1.12); }
    40% { transform:rotate(-9deg) scale(1); }
    60% { transform:rotate(9deg) scale(1.08); }
    80% { transform:rotate(-4deg) scale(1); }
    100%{ transform:rotate(0deg) scale(1); }
}
</style>""", unsafe_allow_html=True)

# ── CONSTANTES ─────────────────────────────────────────────────────────────────
RISK_COLORS = {1:"#22c55e",2:"#84cc16",3:"#f59e0b",4:"#f97316",5:"#ef4444"}
RISK_LABELS = {1:"Limité",2:"Modéré",3:"Important",4:"Majeur",5:"Critique"}
CSV_FILE          = "surveillance_data.csv"
GERMS_FILE        = "germs_data.json"
THRESHOLDS_FILE   = "thresholds_config.json"
MEASURES_FILE     = "measures_config.json"
POINTS_FILE       = "points.json"
PRELEVEMENTS_FILE = "prelevements.json"
SCHEDULES_FILE    = "schedules.json"
PENDING_FILE      = "pending_identifications.json"
ARCHIVED_FILE     = "archived_samples.json"
OPERATORS_FILE    = "operators.json"
PLANS_FILE        = "plans_data.json"

DEFAULT_THRESHOLDS = {
    5: {"alert": 1,  "action": 1},
    4: {"alert": 10, "action": 25},
    3: {"alert": 25, "action": 40},
    2: {"alert": 25, "action": 40},
    1: {"alert": 40, "action": 50},
}

DEFAULT_MEASURES = {
    5: {
        "alert": "• Informer immédiatement le responsable qualité\n• Vérifier et renforcer le bionettoyage de la zone\n• Contrôler l'intégrité des filtres HEPA\n• Augmenter la fréquence de surveillance\n• Documenter l'événement dans le registre qualité",
        "action": "• ARRÊT IMMÉDIAT des activités si possible\n• Alerter le pharmacien responsable et la direction\n• Isoler la zone contaminée\n• Décontamination renforcée avec désinfectant adapté\n• Recherche de la source de contamination\n• Bilan mycologique complet\n• Ne pas reprendre l'activité avant résultat conforme\n• Déclaration d'événement indésirable"
    },
    4: {
        "alert": "• Informer le responsable qualité\n• Renforcer le bionettoyage de la zone concernée\n• Vérifier les procédures d'habillage et d'hygiène\n• Contrôler les flux d'air et la pression différentielle\n• Programmer un prélèvement de contrôle sous 48h",
        "action": "• Alerter le pharmacien responsable\n• Suspendre les préparations critiques si nécessaire\n• Nettoyage et désinfection renforcés de la zone\n• Vérification complète de l'installation\n• Enquête sur l'origine de la contamination\n• Prélèvements de contrôle avant reprise\n• Enregistrement et analyse des causes"
    },
    3: {
        "alert": "• Informer le responsable d'équipe\n• Renforcer les mesures d'hygiène du personnel\n• Vérifier le respect des procédures de bionettoyage\n• Programmer un prélèvement de contrôle\n• Surveiller l'évolution",
        "action": "• Informer le responsable qualité\n• Nettoyage et désinfection de la zone\n• Vérification des procédures en vigueur\n• Renforcer la formation du personnel si nécessaire\n• Prélèvements de contrôle sous 72h\n• Documentation et analyse de tendance"
    },
    2: {
        "alert": "• Surveiller l'évolution des résultats\n• Vérifier le respect des procédures de bionettoyage\n• Contrôler l'hygiène du personnel\n• Programmer un prélèvement de contrôle",
        "action": "• Informer le responsable d'équipe\n• Renforcer le bionettoyage de la zone\n• Vérifier les procédures d'habillage\n• Prélèvements de contrôle sous 5 jours\n• Analyse de tendance sur les derniers résultats"
    },
    1: {
        "alert": "• Surveiller l'évolution\n• Vérifier les procédures de nettoyage\n• Prélèvement de contrôle à planifier",
        "action": "• Renforcer le bionettoyage\n• Vérifier l'hygiène du personnel\n• Prélèvement de contrôle sous 1 semaine\n• Documentation dans le registre de surveillance"
    },
}

ALL_ORIGINS = [
    "Air","Humidité","Flore fécale","Oropharynx / Gouttelettes",
    "Peau / Muqueuse","Sol / Carton / Surface sèche",
]

# ── DONNÉES FAQ ────────────────────────────────────────────────────────────────
FAQ_CATEGORIES = [
    "Général", "Score & Seuils", "Prélèvements",
    "Paramètres", "Données", "Mesures correctives",
]

DEFAULT_FAQ = [
    {
        "id": "faq_001", "category": "Général", "order": 0,
        "question": "À quoi sert cette application ?",
        "answer": (
            "Cette application permet de **suivre la surveillance microbiologique** "
            "de votre environnement pharmaceutique. Elle gère les prélèvements d'air "
            "et de surface, l'identification des germes, le calcul automatique des scores "
            "de criticité et le déclenchement des alertes et actions correctives."
        ),
    },
    {
        "id": "faq_002", "category": "Score & Seuils", "order": 1,
        "question": "Comment est calculé le score de criticité ?",
        "answer": (
            "Le score total est calculé selon la formule :\n\n"
            "**Score = Criticité lieu (1–3) × Pathogénicité (1–3) × Résistance (1–3) × Dissémination (1–3)**\n\n"
            "- Score **< seuil alerte** → ✅ Conforme\n"
            "- Score entre les deux seuils → ⚠️ Alerte\n"
            "- Score **> seuil action** → 🚨 Action immédiate\n\n"
            "Les seuils sont configurables dans **Paramètres → Seuils d'alerte**."
        ),
    },
    {
        "id": "faq_003", "category": "Score & Seuils", "order": 2,
        "question": "Que signifie la criticité du lieu (1–3) ?",
        "answer": (
            "La criticité du lieu qualifie l'importance environnementale du point de prélèvement :\n\n"
            "- **Niveau 1** 🟢 — Limité\n"
            "- **Niveau 2** 🔵 — Modéré\n"
            "- **Niveau 3** 🟠 — Important\n"
            "- **Niveau 4** 🔴 — Critique\n"
            "Ce niveau est défini dans **Paramètres → Points de prélèvement** et est "
            "automatiquement repris lors de l'identification microbiologique."
        ),
    },
    {
        "id": "faq_004", "category": "Prélèvements", "order": 3,
        "question": "Comment ajouter un nouveau prélèvement ?",
        "answer": (
            "Rendez-vous dans **Surveillance → Nouveau prélèvement**, puis :\n\n"
            "1. Sélectionnez le point de prélèvement dans le menu déroulant\n"
            "2. Choisissez l'opérateur et la date\n"
            "3. Sélectionnez éventuellement un plan de localisation\n"
            "4. Validez le formulaire\n\n"
            "Le prélèvement apparaîtra dans la liste en attente d'identification microbiologique."
        ),
    },
    {
        "id": "faq_005", "category": "Prélèvements", "order": 4,
        "question": "Qu'est-ce qu'une identification microbiologique ?",
        "answer": (
            "Après la lecture des géloses, vous saisissez les germes identifiés pour chaque prélèvement. "
            "L'application calcule alors automatiquement le **score de criticité** pour chaque germe "
            "trouvé et déclenche les alertes ou actions appropriées.\n\n"
            "Accès : **Surveillance → Identifier** sur un prélèvement en attente."
        ),
    },
    {
        "id": "faq_006", "category": "Paramètres", "order": 5,
        "question": "Comment configurer les points de prélèvement ?",
        "answer": (
            "Dans **Paramètres → Points de prélèvement** :\n\n"
            "- Cliquez sur **➕ Ajouter** pour créer un nouveau point\n"
            "- Renseignez le nom, le type (Air / Surface), la classe ISO/GMP, "
            "la criticité du lieu, la gélose utilisée et la fréquence de prélèvement\n"
            "- Modifiez (✏️) ou supprimez (🗑️) les points existants\n\n"
            "Les points sont synchronisés automatiquement avec Supabase si configuré."
        ),
    },
    {
        "id": "faq_007", "category": "Paramètres", "order": 6,
        "question": "Comment ajouter un plan de localisation ?",
        "answer": (
            "Dans **Paramètres → Plans** :\n\n"
            "1. Cliquez sur **➕ Ajouter un plan**\n"
            "2. Donnez un nom au plan\n"
            "3. Importez une image (PNG, JPG) ou un PDF (la première page sera utilisée)\n"
            "4. Validez\n\n"
            "Le plan sera disponible lors de la création d'un prélèvement pour "
            "visualiser et positionner le point sur la carte."
        ),
    },
    {
        "id": "faq_008", "category": "Données", "order": 7,
        "question": "Comment sauvegarder et restaurer mes données ?",
        "answer": (
            "Dans **Paramètres → Sauvegarde** :\n\n"
            "- **⬇️ Exporter** : télécharge un fichier JSON contenant toutes vos données "
            "(germes, prélèvements, points, opérateurs, historique...)\n"
            "- **⬆️ Restaurer** : importez un fichier de sauvegarde pour remplacer "
            "toutes les données actuelles\n\n"
            "⚠️ La restauration est irréversible — effectuez toujours une exportation avant."
        ),
    },
    {
        "id": "faq_009", "category": "Données", "order": 8,
        "question": "Pourquoi configurer Supabase ?",
        "answer": (
            "Sans Supabase, les données sont **perdues à chaque redémarrage** de l'application "
            "(mise à jour du code, timeout Streamlit Cloud...).\n\n"
            "Supabase est une base de données cloud **gratuite** qui garantit la persistance. "
            "Configuration dans **Paramètres → Base de données** — il suffit de coller "
            "votre `SUPABASE_URL` et `SUPABASE_KEY` dans les secrets Streamlit."
        ),
    },
    {
        "id": "faq_010", "category": "Mesures correctives", "order": 9,
        "question": "Comment fonctionnent les mesures correctives ?",
        "answer": (
            "Les mesures correctives sont des actions prédéfinies suggérées automatiquement "
            "lors d'une alerte ou d'une action microbiologique.\n\n"
            "Chaque mesure est associée à :\n"
            "- Une **origine** (Air, Surface, Flore fécale...)\n"
            "- Un **niveau de criticité** (1 à 5)\n"
            "- Un **type** (⚠️ Alerte ou 🚨 Action)\n\n"
            "Gérez-les dans **Paramètres → Mesures correctives**."
        ),
    },
]

DEFAULT_ORIGIN_MEASURES = [
    {"id":"m001","text":"Documenter l'événement dans le registre qualité","scope":"all","risk":"all","type":"alert"},
    {"id":"m002","text":"Programmer un prélèvement de contrôle","scope":"all","risk":"all","type":"alert"},
    {"id":"m003","text":"Surveiller l'évolution des prochains résultats","scope":"all","risk":"all","type":"alert"},
    {"id":"m004","text":"Informer le responsable qualité","scope":"all","risk":[3,4,5],"type":"alert"},
    {"id":"m005","text":"Augmenter la fréquence de surveillance","scope":"all","risk":[3,4,5],"type":"alert"},
    {"id":"m006","text":"Renforcer le bionettoyage de la zone concernée","scope":"all","risk":[3,4,5],"type":"alert"},
    {"id":"m010","text":"Alerter le pharmacien responsable et la direction","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m011","text":"Isoler la zone contaminée","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m012","text":"ARRÊT des préparations critiques si nécessaire","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m013","text":"Décontamination renforcée avec désinfectant adapté (Surfa'Safe / APA)","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m014","text":"Ne pas reprendre l'activité avant résultat conforme","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m015","text":"Déclaration d'événement indésirable (fiche EI)","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m016","text":"Renforcer le bionettoyage de la zone","scope":"all","risk":[1,2,3],"type":"action"},
    {"id":"m017","text":"Vérifier les procédures de bionettoyage en vigueur","scope":"all","risk":[1,2,3],"type":"action"},
    {"id":"m018","text":"Informer le responsable d'équipe","scope":"all","risk":[1,2,3],"type":"action"},
    {"id":"m020","text":"Contrôler l'intégrité des filtres HEPA","scope":"Air","risk":"all","type":"alert"},
    {"id":"m021","text":"Vérifier les flux d'air et la pression différentielle","scope":"Air","risk":"all","type":"alert"},
    {"id":"m022","text":"Contrôler les entrées / sorties de matériel (cartons, vêtements)","scope":"Air","risk":[3,4,5],"type":"alert"},
    {"id":"m023","text":"Contrôler l'étanchéité des jonctions de filtres HEPA","scope":"Air","risk":[4,5],"type":"action"},
    {"id":"m024","text":"Bilan fongique complet (Aspergillus, Fusarium, Penicillium)","scope":"Air","risk":[4,5],"type":"action"},
    {"id":"m025","text":"Décontamination par nébulisation H2O2 si moisissure critique","scope":"Air","risk":[5],"type":"action"},
    {"id":"m030","text":"Identifier et traiter les sources d'humidité","scope":"Humidité","risk":"all","type":"alert"},
    {"id":"m031","text":"Vérifier l'étanchéité des canalisations et conduites d'eau","scope":"Humidité","risk":"all","type":"alert"},
    {"id":"m032","text":"Contrôler le taux d'humidité relative de la salle","scope":"Humidité","risk":[3,4,5],"type":"alert"},
    {"id":"m033","text":"Nettoyage et désinfection renforcés des surfaces humides","scope":"Humidité","risk":"all","type":"action"},
    {"id":"m034","text":"Décontamination au peroxyde d'hydrogène si Pseudomonas/Mycobactérie","scope":"Humidité","risk":[4,5],"type":"action"},
    {"id":"m035","text":"Recherche et élimination de tout biofilm résiduel","scope":"Humidité","risk":[4,5],"type":"action"},
    {"id":"m040","text":"Contrôler les entrées de matières premières et emballages","scope":"Sol / Carton / Surface sèche","risk":"all","type":"alert"},
    {"id":"m041","text":"Renforcer le bionettoyage des sols et surfaces","scope":"Sol / Carton / Surface sèche","risk":"all","type":"alert"},
    {"id":"m042","text":"Vérifier le protocole de dé-cartonnage à l'entrée","scope":"Sol / Carton / Surface sèche","risk":[3,4,5],"type":"alert"},
    {"id":"m043","text":"Retrait et destruction des cartons et emballages suspects","scope":"Sol / Carton / Surface sèche","risk":"all","type":"action"},
    {"id":"m044","text":"Décontamination sporicide si spores détectées (Bacillus, Clostridium)","scope":"Sol / Carton / Surface sèche","risk":[4,5],"type":"action"},
    {"id":"m045","text":"Bilan sporal complet de la zone","scope":"Sol / Carton / Surface sèche","risk":[5],"type":"action"},
    {"id":"m050","text":"Vérifier les procédures d'habillage et port des EPI","scope":"Peau / Muqueuse","risk":"all","type":"alert"},
    {"id":"m051","text":"Contrôler la technique de friction hydro-alcoolique","scope":"Peau / Muqueuse","risk":"all","type":"alert"},
    {"id":"m052","text":"Renforcer la formation du personnel (hygiène des mains)","scope":"Peau / Muqueuse","risk":[3,4,5],"type":"action"},
    {"id":"m053","text":"Vérifier l'absence de lésion cutanée chez le personnel","scope":"Peau / Muqueuse","risk":[4,5],"type":"action"},
    {"id":"m054","text":"Enquête sur le personnel intervenant dans la zone","scope":"Peau / Muqueuse","risk":[4,5],"type":"action"},
    {"id":"m055","text":"Vérifier les procédures d'habillage et port des EPI","scope":"Peau / Muqueuse","risk":"all","type":"alert"},
    {"id":"m056","text":"Contrôler la technique de friction hydro-alcoolique","scope":"Peau / Muqueuse","risk":"all","type":"alert"},
    {"id":"m057","text":"Renforcer la formation du personnel (hygiène des mains)","scope":"Peau / Muqueuse","risk":[3,4,5],"type":"action"},
    {"id":"m058","text":"Vérifier l'absence de lésion cutanée ou infection fongique","scope":"Peau / Muqueuse","risk":[4,5],"type":"action"},
    {"id":"m060","text":"Vérifier les procédures de lavage des mains","scope":"Flore fécale","risk":"all","type":"alert"},
    {"id":"m061","text":"Contrôler la chaîne de décontamination des équipements","scope":"Flore fécale","risk":"all","type":"alert"},
    {"id":"m062","text":"Recherche de source de contamination fécale","scope":"Flore fécale","risk":[3,4,5],"type":"action"},
    {"id":"m063","text":"Nettoyage désinfectant à spectre large (entérobactéries/ERV)","scope":"Flore fécale","risk":"all","type":"action"},
    {"id":"m064","text":"Test de portage pour le personnel si E. coli / Entérocoque multirésistant","scope":"Flore fécale","risk":[4,5],"type":"action"},
    {"id":"m070","text":"Vérifier le port correct du masque FFP2 ou chirurgical","scope":"Oropharynx / Gouttelettes","risk":"all","type":"alert"},
    {"id":"m071","text":"Rappeler l'interdiction de parler dans la ZAC","scope":"Oropharynx / Gouttelettes","risk":"all","type":"alert"},
    {"id":"m072","text":"Enquête sur le personnel présent lors du prélèvement positif","scope":"Oropharynx / Gouttelettes","risk":[3,4,5],"type":"action"},
    {"id":"m073","text":"Contrôle de santé du personnel (angine, rhino-pharyngite)","scope":"Oropharynx / Gouttelettes","risk":[3,4,5],"type":"action"},
    {"id":"m074","text":"Éviction temporaire du personnel symptomatique","scope":"Oropharynx / Gouttelettes","risk":[4,5],"type":"action"},
]

DEFAULT_GERMS = [
    dict(name="Staphylococcus spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuse"],notes=None,comment=None),
    dict(name="Corynebacterium spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuse"],notes=None,comment=None),
    dict(name="Cutibacterium acnes",path=["Germes","Bactéries","Humains","Peau / Muqueuse"],notes=None,comment=None),
    dict(name="Micrococcus spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuse"],notes=None,comment=None),
    dict(name="Dermabacter hominis",path=["Germes","Bactéries","Humains","Peau / Muqueuse"],notes=None,comment=None),
    dict(name="Brevibacterium epidermidis",path=["Germes","Bactéries","Humains","Peau / Muqueuse"],notes=None,comment=None),
    dict(name="Streptococcus mitis/salivarius/sanguinis/anginosus",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],notes=None,comment=None),
    dict(name="Streptococcus pyogenes/agalactiae/pneumoniae",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],notes=None,comment=None),
    dict(name="Escherichia coli",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Enterococcus spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Enterobacter spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Citrobacter spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Klebsiella pneumoniae",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Proteus spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Morganella spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Providencia spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Salmonella spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Shigella spp.",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Yersinia enterocolitica",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Pseudomonas spp.",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Acinetobacter spp.",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Paenibacillus spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Hafnia alvei",path=["Germes","Bactéries","Humains","Flore fécale"],notes=None,comment=None),
    dict(name="Sphingomonas paucimobilis",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Sphingobium spp.",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Methylobacterium spp.",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Caulobacter crescentus",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Mycobacterium non tuberculeux",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Burkholderia cepacia",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Massilia spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Bacillus spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes="Sporulé",comment=None),
    dict(name="Clostridium spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes="Sporulé",comment=None),
    dict(name="Geobacillus stearothermophilus (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes="Sporulé thermophile",comment=None),
    dict(name="Arthrobacter spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Cellulomonas spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Curtobacterium spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Agrococcus spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Microbacterium spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Brevibacterium linens/casei",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Georgenia spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Candida spp.",path=["Germes","Champignons","Humain","Peau / Muqueuse"],notes="Levure",comment="Levures = pas de production de spores"),
    dict(name="Trichosporon spp.",path=["Germes","Champignons","Humain","Peau / Muqueuse"],notes="Levure",comment="Levures = pas de production de spores"),
    dict(name="Rhodotorula spp.",path=["Germes","Champignons","Environnemental","Humidité"],notes="Levure",comment="Levures = pas de production de spores"),
    dict(name="Fusarium spp.",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],notes="Conidies 2-4um",comment="Production de spores (conidies) => dissémination dans l'air facilitée par petite taille (2-4 µm) + Résistance aux agents oxydants"),
    dict(name="Aureobasidium spp.",path=["Germes","Champignons","Environnemental","Humidité"],notes="Blastospores + biofilm",comment="Production de blastospores (moins résistante aux agents oxydants et ne se dissémine pas dans l'air comme les conidies d'Aspergillus ou Fusarium) et production de biofilm"),
    dict(name="Mucorales",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],notes="Sporangiospores",comment="Production de sporangiospores (moins résistant aux agents oxydants que les conidies d'Aspergillus ou Fusarium)"),
    dict(name="Alternaria spp.",path=["Germes","Champignons","Environnemental","Air"],notes="Conidies grandes",comment="Production de spores (conidies) mais de plus grande taille, moins déshydratées et moins mélanisées que celles de Fusarium ou Aspergillus => Moins résistante à l'oxydation"),
    dict(name="Aspergillus spp.",path=["Germes","Champignons","Environnemental","Air"],notes="Conidies 2-4um",comment="Production de spores (conidies) => dissémination dans l'air facilitée par petite taille (2-4 µm) + Résistance aux agents oxydants"),
    dict(name="Cladosporium spp.",path=["Germes","Champignons","Environnemental","Air"],notes="Conidies grandes",comment="Production de spores (conidies) mais de plus grande taille, moins déshydratées et moins mélanisées => Moins résistante à l'oxydation"),
    dict(name="Penicillium spp.",path=["Germes","Champignons","Environnemental","Air"],notes="Conidies",comment="Production de spores (conidies) mais moins déshydratées et moins mélanisées que celles de Fusarium ou Aspergillus => Moins résistantes à l'oxydation"),
    dict(name="Wallemia sebi",path=["Germes","Champignons","Environnemental","Air"],notes="Arthroconidies",comment=None),
]

DEFAULT_GERM_NAMES = {g["name"] for g in DEFAULT_GERMS}

# ── PERSISTENCE ────────────────────────────────────────────────────────────────
def _supa_upsert(key, value_json):
    supa = get_supabase_client()
    if supa is None:
        return False
    try:
        supa.table('app_state').upsert(
            {'key': key, 'value': value_json}, on_conflict='key'
        ).execute()
        return True
    except Exception as e:
        print(f"[SUPA ERROR] key={key} : {e}")
        return False

def _supa_get(key):
    supa = get_supabase_client()
    if supa is None:
        return None
    try:
        res = supa.table('app_state').select('value').eq('key', key).execute()
        if res and getattr(res, 'data', None):
            row = res.data[0]
            return row.get('value') if isinstance(row, dict) else row['value']
    except Exception:
        pass
    return None

def save_germs(germs):
    known_default_names = sorted(DEFAULT_GERM_NAMES)
    payload = {"germs": germs, "known_defaults": known_default_names}
    js = json.dumps(payload, ensure_ascii=False)
    _supa_upsert('germs', js)
    try:
        with open(GERMS_FILE, "w") as f:
            f.write(js)
    except Exception:
        pass

def load_germs():
    defaults_by_name = {d["name"]: d for d in DEFAULT_GERMS}
    saved_germs = []
    known_defaults = set()
    raw_json = _supa_get('germs')
    if raw_json:
        try:
            raw = json.loads(raw_json)
            if isinstance(raw, dict):
                saved_germs  = raw.get("germs", [])
                known_defaults = set(raw.get("known_defaults", []))
            elif isinstance(raw, list):
                saved_germs = raw
        except Exception:
            saved_germs = []
    if not saved_germs and os.path.exists(GERMS_FILE):
        try:
            with open(GERMS_FILE) as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                saved_germs    = raw.get("germs", [])
                known_defaults = set(raw.get("known_defaults", []))
            elif isinstance(raw, list):
                saved_germs = raw
        except Exception:
            saved_germs = []
    if not saved_germs:
        return [dict(d) for d in DEFAULT_GERMS], len(DEFAULT_GERMS)
    saved_by_name = {g.get("name", ""): g for g in saved_germs}
    merged = []
    new_defaults_added = 0
    for dflt in DEFAULT_GERMS:
        name = dflt["name"]
        if name in saved_by_name:
            merged.append(dict(saved_by_name[name]))
        elif name not in known_defaults:
            merged.append(dict(dflt))
            new_defaults_added += 1
    for g in saved_germs:
        name = g.get("name", "")
        if name and name not in defaults_by_name:
            merged.append(dict(g))
    return merged, new_defaults_added

def load_thresholds():
    saved = {}
    raw_json = _supa_get('thresholds')
    if raw_json:
        try:
            raw = json.loads(raw_json)
            saved = {int(k): v for k, v in raw.items() if k != 'measures'}
        except Exception:
            saved = {}
    if not saved and os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            saved = {int(k): v for k, v in raw.items() if k != 'measures'}
        except Exception:
            saved = {}
    merged = {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}
    merged.update(saved)
    return merged

def load_measures():
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            if "measures" in raw:
                return {int(k): v for k, v in raw["measures"].items()}
        except Exception:
            pass
    return {k: dict(v) for k, v in DEFAULT_MEASURES.items()}

def save_thresholds_and_measures(thresholds, measures):
    data = {str(k): v for k, v in thresholds.items()}
    data["measures"] = {str(k): v for k, v in measures.items()}
    js = json.dumps(data, ensure_ascii=False)
    _supa_upsert('thresholds', js)
    try:
        with open(THRESHOLDS_FILE, "w") as f:
            f.write(js)
    except Exception:
        pass

def get_thresholds_for_risk(risk, thresholds):
    return thresholds.get(risk, {"alert": 25, "action": 40})

def load_origin_measures():
    raw_json = _supa_get('measures')
    if raw_json:
        try:
            raw = json.loads(raw_json)
            if isinstance(raw, list) and raw:
                return raw
        except Exception:
            pass
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            if "measures" in raw and isinstance(raw["measures"], list) and raw["measures"]:
                return raw["measures"]
        except Exception:
            pass
    return [dict(m) for m in DEFAULT_ORIGIN_MEASURES]

def save_origin_measures(measures, supa=True):
    if supa:
        try:
            result = _supa_upsert('measures', json.dumps(measures, ensure_ascii=False))
            if not result:
                st.warning("⚠️ Supabase non connecté — sauvegarde locale uniquement.")
        except Exception as e:
            st.error(f"❌ Erreur Supabase : {e}")
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
        except Exception:
            raw = {}
    else:
        raw = {}
    raw["measures"] = measures
    try:
        with open(THRESHOLDS_FILE, "w") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _load_json_key(key, local_file):
    raw_json = _supa_get(key)
    if raw_json:
        try:
            raw = json.loads(raw_json)
            if isinstance(raw, list):
                return [dict(x) for x in raw]
        except Exception:
            pass
    if os.path.exists(local_file):
        try:
            with open(local_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, list):
                return [dict(x) for x in raw]
        except Exception:
            pass
    return []

def _save_json_key(key, data, local_file):
    js = json.dumps(data, ensure_ascii=False)
    _supa_upsert(key, js)
    try:
        with open(local_file, 'w', encoding='utf-8') as f:
            f.write(js)
    except Exception:
        pass

def load_points():  return _load_json_key('points', POINTS_FILE)
def save_points(d, supa=True):
    _save_json_key('points', d, POINTS_FILE)
    if supa: _supa_upsert('points', json.dumps(d, ensure_ascii=False))

def load_prelevements():  return _load_json_key('prelevements', PRELEVEMENTS_FILE)
def save_prelevements(d, supa=True):
    _save_json_key('prelevements', d, PRELEVEMENTS_FILE)
    if supa: _supa_upsert('prelevements', json.dumps(d, ensure_ascii=False))

def load_schedules():  return _load_json_key('schedules', SCHEDULES_FILE)
def save_schedules(d, supa=True):
    _save_json_key('schedules', d, SCHEDULES_FILE)
    if supa: _supa_upsert('schedules', json.dumps(d, ensure_ascii=False))

def load_pending_identifications():  return _load_json_key('pending_identifications', PENDING_FILE)
def save_pending_identifications(d, supa=True):
    _save_json_key('pending_identifications', d, PENDING_FILE)
    if supa: _supa_upsert('pending_identifications', json.dumps(d, ensure_ascii=False))

def load_archived_samples():  return _load_json_key('archived_samples', ARCHIVED_FILE)
def save_archived_samples(d, supa=True):
    _save_json_key('archived_samples', d, ARCHIVED_FILE)
    if supa: _supa_upsert('archived_samples', json.dumps(d, ensure_ascii=False))

def load_operators():  return _load_json_key('operators', OPERATORS_FILE)
def save_operators(d, supa=True):
    _save_json_key('operators', d, OPERATORS_FILE)
    if supa: _supa_upsert('operators', json.dumps(d, ensure_ascii=False))

def load_plans():  return _load_json_key('plans', PLANS_FILE)
def save_plans(d, supa=True):
    _save_json_key('plans', d, PLANS_FILE)
    if supa: _supa_upsert('plans', json.dumps(d, ensure_ascii=False))

def load_faq():
    raw_json = _supa_get('faq')
    if raw_json:
        try:
            raw = json.loads(raw_json)
            if isinstance(raw, list) and raw:
                return raw
        except Exception:
            pass
    return [dict(f) for f in DEFAULT_FAQ]

def save_faq(faq_items, supa=True):
    if supa:
        _supa_upsert('faq', json.dumps(faq_items, ensure_ascii=False))

def load_surveillance():
    raw_json = _supa_get('surveillance')
    if raw_json:
        try:
            return json.loads(raw_json)
        except Exception:
            pass
    if os.path.exists(CSV_FILE):
        try:
            rows = []
            with open(CSV_FILE, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            return rows
        except Exception:
            pass
    return []

def save_surveillance(records):
    js = json.dumps(records, ensure_ascii=False)
    _supa_upsert('surveillance', js)
    try:
        if not records:
            if os.path.exists(CSV_FILE):
                os.remove(CSV_FILE)
        else:
            all_keys = list(dict.fromkeys(k for r in records for k in r.keys()))
            with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(records)
    except Exception:
        pass

def export_all_data():
    return {
        "_meta": {
            "version": "5.0",
            "exported_at": datetime.now().isoformat(),
            "app": "MicroSurveillance URC"
        },
        "germs":                   st.session_state.germs,
        "thresholds":              {str(k): v for k, v in st.session_state.thresholds.items()},
        "measures":                {str(k): v for k, v in st.session_state.measures.items()},
        "origin_measures":         st.session_state.origin_measures,
        "points":                  st.session_state.points,
        "operators":               st.session_state.operators,
        "plans":                   st.session_state.plans,
        "prelevements":            st.session_state.prelevements,
        "schedules":               st.session_state.schedules,
        "pending_identifications": st.session_state.pending_identifications,
        "archived_samples":        st.session_state.archived_samples,
        "surveillance":            st.session_state.surveillance,
        "planning_overrides":      st.session_state.get("planning_overrides", {}),
    }

def import_all_data(data: dict):
    try:
        required = ["germs", "points", "operators", "prelevements", "schedules", "surveillance"]
        for key in required:
            if key not in data:
                return False, f"Clé manquante dans le fichier : '{key}'"
        st.session_state.germs = [dict(g) for g in data["germs"]]
        _germs_sync, _ = load_germs()
        _default_names = {d["name"] for d in DEFAULT_GERMS}
        _custom = [g for g in st.session_state.germs if g.get("name") not in _default_names]
        st.session_state.germs = _germs_sync + [g for g in _custom if g.get("name") not in {x["name"] for x in _germs_sync}]
        st.session_state.origin_measures         = [dict(m) for m in data.get("origin_measures", [])] or [dict(m) for m in DEFAULT_ORIGIN_MEASURES]
        st.session_state.points                  = [dict(p) for p in data.get("points", [])]
        st.session_state.operators               = [dict(o) for o in data.get("operators", [])]
        st.session_state.plans                   = [dict(p) for p in data.get("plans", [])]
        st.session_state.prelevements            = [dict(p) for p in data.get("prelevements", [])]
        st.session_state.schedules               = [dict(s) for s in data.get("schedules", [])]
        st.session_state.pending_identifications = [dict(x) for x in data.get("pending_identifications", [])]
        st.session_state.archived_samples        = [dict(x) for x in data.get("archived_samples", [])]
        st.session_state.surveillance            = list(data.get("surveillance", []))
        if "thresholds" in data:
            st.session_state.thresholds = {int(k): v for k, v in data["thresholds"].items()}
        if "measures" in data:
            st.session_state.measures   = {int(k): v for k, v in data["measures"].items()}
        save_germs(st.session_state.germs)
        save_origin_measures(st.session_state.origin_measures)
        save_points(st.session_state.points)
        save_operators(st.session_state.operators)
        save_plans(st.session_state.plans)
        save_prelevements(st.session_state.prelevements)
        save_schedules(st.session_state.schedules)
        save_pending_identifications(st.session_state.pending_identifications)
        save_archived_samples(st.session_state.archived_samples)
        save_surveillance(st.session_state.surveillance)
        save_thresholds_and_measures(st.session_state.thresholds, st.session_state.measures)
        n_p = len(st.session_state.prelevements)
        n_s = len(st.session_state.schedules)
        n_g = len(st.session_state.germs)
        n_h = len(st.session_state.surveillance)
        return True, (f"Restauration réussie — {n_g} germes, {n_p} prélèvements, "
                      f"{n_s} lectures planifiées, {n_h} entrées historique.")
    except Exception as e:
        return False, f"Erreur lors de la restauration : {e}"

def find_germ_match(query, germs):
    query_low  = query.lower().strip()
    query_genus = query_low.split()[0] if query_low else ""
    best_score = 0
    best_match = None
    for g in germs:
        name_low = g["name"].lower()
        genus    = name_low.split()[0]
        if query_genus and query_genus == genus:
            score = 0.9
        else:
            score       = difflib.SequenceMatcher(None, query_low, name_low).ratio()
            genus_score = difflib.SequenceMatcher(None, query_genus, genus).ratio()
            score       = max(score, genus_score * 0.85)
        if score > best_score:
            best_score = score
            best_match = g
    return best_match, best_score

# ── Helpers scoring ────────────────────────────────────────────────────────────
def _get_location_criticality(sample):
    if "location_criticality" in sample:
        try:
            return int(sample["location_criticality"])
        except Exception:
            pass
    pt = next((p for p in st.session_state.points
               if p.get("label") == sample.get("label")), None)
    if pt and "location_criticality" in pt:
        try:
            return int(pt["location_criticality"])
        except Exception:
            pass
    rc = str(sample.get("room_class", "")).strip().upper()
    return {"A": 3, "B": 2, "C": 2, "D": 1}.get(rc, 1)

def _get_germ_score(germ):
    if all(k in germ for k in ("pathogenicity", "resistance", "dissemination")):
        return int(germ["pathogenicity"]) * int(germ["resistance"]) * int(germ["dissemination"])
    old = germ.get("risk", 1)
    return {1: 1, 2: 2, 3: 6, 4: 12, 5: 18}.get(old, old)

def _evaluate_score(total):
    _sa = st.session_state.get("_seuil_alerte", 24)
    _sc = st.session_state.get("_seuil_action", 36)
    if total > _sc:  return "action", "🚨 ACTION",  "#ef4444"
    if total >= _sa: return "alert",  "⚠️ ALERTE",  "#f59e0b"
    return "ok", "✅ Conforme", "#22c55e"

def _loc_crit_label(n):
    return {1: "Non critique", 2: "Semi-critique", 3: "Critique"}.get(n, str(n))

# ── CONTRÔLE D'ACCÈS PROTÉGÉ ───────────────────────────────────────────────────
def check_access_protege(onglet_nom: str) -> bool:
    key_mode = f"access_mode_{onglet_nom}"
    key_pwd  = f"pwd_input_{onglet_nom}"
    key_err  = f"pwd_error_{onglet_nom}"
    if st.session_state.get(key_mode) == "admin":
        col_info, col_lock = st.columns([5, 1])
        with col_info:
            st.success("🔓 Mode administrateur — modifications autorisées")
        with col_lock:
            if st.button("🔒 Verrouiller", key=f"lock_{onglet_nom}", use_container_width=True):
                st.session_state[key_mode] = None
                st.rerun()
        return True
    if st.session_state.get(key_mode) == "lecture":
        col_info, col_conn = st.columns([5, 1])
        with col_info:
            st.info("👁️ Mode lecture seule — aucune modification possible")
        with col_conn:
            if st.button("🔑 Se connecter", key=f"connect_{onglet_nom}", use_container_width=True):
                st.session_state[key_mode] = None
                st.rerun()
        return False
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='background:#fff;border:1.5px solid #e2e8f0;border-radius:14px;"
        "padding:28px 32px;max-width:460px;margin:0 auto;box-shadow:0 4px 20px rgba(0,0,0,.08)'>"
        "<div style='text-align:center;font-size:2.2rem;margin-bottom:8px'>🔐</div>"
        f"<div style='text-align:center;font-weight:800;font-size:1.15rem;color:#0f172a'>"
        f"Accès protégé — {onglet_nom}</div>"
        "<div style='text-align:center;font-size:.85rem;color:#64748b;margin:8px 0 20px'>"
        "Cet onglet est restreint. Connectez-vous pour modifier,<br>ou continuez en lecture seule.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔑 Accès administrateur**")
        pwd = st.text_input(
            "Mot de passe", type="password", key=key_pwd,
            placeholder="Entrez le mot de passe", label_visibility="collapsed"
        )
        if st.button("✅ Connexion", key=f"btn_admin_{onglet_nom}",
                     use_container_width=True, type="primary"):
            if pwd == MOT_DE_PASSE_ADMIN:
                st.session_state[key_mode] = "admin"
                st.session_state[key_err]  = False
                st.rerun()
            else:
                st.session_state[key_err] = True
                st.rerun()
        if st.session_state.get(key_err):
            st.error("❌ Mot de passe incorrect")
    with col2:
        st.markdown("**👁️ Lecture seule**")
        st.markdown(
            "<div style='font-size:.82rem;color:#64748b;margin-bottom:10px'>"
            "Consultez le contenu sans pouvoir effectuer de modifications.</div>",
            unsafe_allow_html=True,
        )
        if st.button("👁️ Continuer en lecture", key=f"btn_lecture_{onglet_nom}",
                     use_container_width=True):
            st.session_state[key_mode] = "lecture"
            st.rerun()
    st.stop()
    return False

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "germs" not in st.session_state:
    _germs, _new = load_germs()
    st.session_state.germs = _germs
    st.session_state.germs_synced_count = _new
    if _new > 0:
        save_germs(st.session_state.germs)
if "thresholds" not in st.session_state:
    st.session_state.thresholds = load_thresholds()
if "measures" not in st.session_state:
    st.session_state.measures = load_measures()
if "surveillance" not in st.session_state:
    st.session_state.surveillance = load_surveillance()
if "show_add" not in st.session_state:
    st.session_state.show_add = False
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None
if "map_points" not in st.session_state:
    st.session_state.map_points = []
if "map_image" not in st.session_state:
    st.session_state.map_image = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "logigramme"
if "origin_measures" not in st.session_state:
    st.session_state.origin_measures = load_origin_measures()
if "show_new_measure" not in st.session_state:
    st.session_state.show_new_measure = False
if "prelevements" not in st.session_state:
    st.session_state.prelevements = load_prelevements()
if "schedules" not in st.session_state:
    st.session_state.schedules = load_schedules()
if "pending_identifications" not in st.session_state:
    st.session_state.pending_identifications = load_pending_identifications()
if "archived_samples" not in st.session_state:
    st.session_state.archived_samples = load_archived_samples()
if "points" not in st.session_state:
    st.session_state.points = load_points()
if "operators" not in st.session_state:
    st.session_state.operators = load_operators()
if "plans" not in st.session_state:
    st.session_state.plans = load_plans()
if "faq_items" not in st.session_state:
    st.session_state.faq_items = load_faq()
if "_seuil_alerte" not in st.session_state:
    _raw_seuils = _supa_get('seuils')
    if _raw_seuils:
        try:
            _s = json.loads(_raw_seuils)
            st.session_state["_seuil_alerte"] = int(_s.get("alerte", 24))
            st.session_state["_seuil_action"] = int(_s.get("action", 36))
        except Exception:
            st.session_state["_seuil_alerte"] = 24
            st.session_state["_seuil_action"] = 36
    else:
        st.session_state["_seuil_alerte"] = 24
        st.session_state["_seuil_action"] = 36
if "due_alert_shown" not in st.session_state:
    st.session_state.due_alert_shown = False
if "current_process" not in st.session_state:
    st.session_state.current_process = None
if "cal_year" not in st.session_state:
    st.session_state.cal_year = datetime.today().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = datetime.today().month
if "planning_overrides" not in st.session_state:
    raw = _supa_get('planning_overrides')
    st.session_state["planning_overrides"] = json.loads(raw) if raw else {}
if "class_constraints_loaded" not in st.session_state:
    raw_cc = _supa_get('class_constraints')
    if raw_cc:
        try:
            for cls, val in json.loads(raw_cc).items():
                st.session_state[f"class_max_{cls}"] = int(val)
        except Exception:
            pass
    st.session_state["class_constraints_loaded"] = True

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:.85rem;letter-spacing:.1em;text-transform:uppercase;'
        'color:#94a3b8;margin-bottom:12px;font-weight:700">NAVIGATION</p>',
        unsafe_allow_html=True,
    )
    tabs_cfg = [
        ("logigramme",   "📊", "Logigramme"),
        ("surveillance", "🔍", "Identification & Surveillance"),
        ("planning",     "📅", "Planning"),
        ("historique",   "📋", "Historique"),
        ("parametres",   "⚙️", "Paramètres & Seuils"),
    ]
    for key, icon, label in tabs_cfg:
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.active_tab = key
            st.rerun()

    st.divider()

    supa_ok   = get_supabase_client() is not None
    supa_icon = "🟢" if supa_ok else "🔴"
    supa_txt  = "Supabase connecté" if supa_ok else "Mode local (fichiers)"
    st.markdown(
        f'<p style="font-size:.7rem;color:#94a3b8;text-align:center">{supa_icon} {supa_txt}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size:.75rem;color:#94a3b8;text-align:center">'
        'MicroSurveillance URC v5.0</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        '<p style="font-size:.7rem;color:#f59e0b;font-weight:700;text-align:center;'
        'text-transform:uppercase;letter-spacing:.08em">💾 Sauvegarde données</p>',
        unsafe_allow_html=True,
    )
    _backup_data = json.dumps(export_all_data(), ensure_ascii=False, indent=2)
    _backup_name = f"backup_URC_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    st.download_button(
        label="⬇️ Exporter toutes les données",
        data=_backup_data,
        file_name=_backup_name,
        mime="application/json",
        use_container_width=True,
        key="sidebar_export",
        help="Téléchargez ce fichier avant toute modification du code.",
    )
    if not supa_ok:
        st.markdown(
            '<p style="font-size:.6rem;color:#f59e0b;text-align:center;margin-top:4px">'
            '⚠️ Sans Supabase, exportez régulièrement vos données !</p>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── 🍄 Champignon + bouton FAQ en 2 colonnes ──────────────────────────
    col_gif, col_btn = st.columns([1, 2])
    with col_gif:
        st.components.v1.html("""
<div style="display:flex;justify-content:center;align-items:center;padding-top:4px">
  <iframe src="https://giphy.com/embed/bSEkPdQfsSHCMYn7fD"
          width="90" height="90"
          style="border:none;pointer-events:none;display:block"
          frameBorder="0"></iframe>
</div>
""", height=100, scrolling=False)

    with col_btn:
        st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
        if st.button(
            "Si tu as besoin\nd'aide, je suis là !",
            key="faq_open_btn",
            use_container_width=True,
        ):
            st.session_state.active_tab = "faq"
            st.rerun()

# ── HEADER ─────────────────────────────────────────────────────────────────────
active = st.session_state.active_tab
today  = datetime.today().date()

st.markdown(
    '<h1 style="font-size:1.3rem;letter-spacing:.1em;text-transform:uppercase;'
    'color:#1e40af!important;margin-bottom:0">🦠 MicroSurveillance URC</h1>',
    unsafe_allow_html=True,
)
st.caption("Surveillance microbiologique — Unité de Reconstitution des Chimiothérapies")

# ── ONGLET FAQ ─────────────────────────────────────────────────────────────────
if active == "faq":
    from collections import defaultdict
    import re as _re

    faq_items = sorted(
        st.session_state.get("faq_items", DEFAULT_FAQ),
        key=lambda x: x.get("order", 999),
    )

    if st.button("← Retour", key="faq_back"):
        st.session_state.active_tab = "logigramme"
        st.rerun()

    st.markdown(
        "<div style='background:linear-gradient(135deg,#7c3aed,#a855f7);"
        "border-radius:14px;padding:20px 28px;margin:12px 0 16px 0'>"
        "<div style='color:#fff;font-size:1.3rem;font-weight:900'>🍄 Centre d'aide — FAQ</div>"
        f"<div style='color:#e9d5ff;font-size:.8rem;margin-top:3px'>"
        f"{len(faq_items)} questions & réponses disponibles</div>"
        "</div>",
        unsafe_allow_html=True)

    fc1, fc2 = st.columns([3, 1])
    with fc1:
        faq_query = st.text_input(
            "search", placeholder="🔍 Rechercher...",
            label_visibility="collapsed", key="faq_page_search")
    with fc2:
        all_cats_p = ["Toutes les catégories"] + sorted(
            set(f.get("category", "Général") for f in faq_items))
        sel_cat_p = st.selectbox(
            "cat", all_cats_p,
            label_visibility="collapsed", key="faq_page_cat")

    st.markdown(
        "<hr style='margin:8px 0 16px;border-color:#e2e8f0'>",
        unsafe_allow_html=True)

    q_p = faq_query.strip().lower()

    def _faq_match(item):
        if sel_cat_p != "Toutes les catégories" and item.get("category") != sel_cat_p:
            return False
        if q_p:
            return (q_p in item["question"].lower()
                    or q_p in item["answer"].lower()
                    or q_p in item.get("category", "").lower())
        return True

    filtered = [f for f in faq_items if _faq_match(f)]

    if not filtered:
        st.markdown(
            "<div style='text-align:center;padding:48px 0;color:#94a3b8'>"
            "<div style='font-size:2.5rem;margin-bottom:10px'>🔍</div>"
            f"<div style='font-size:.9rem'>Aucun résultat pour "
            f"<strong>« {faq_query} »</strong></div></div>",
            unsafe_allow_html=True)
    else:
        CAT_COLORS = {
            "Général":            "#2563eb",
            "Score & Seuils":     "#7c3aed",
            "Prélèvements":       "#0891b2",
            "Paramètres":         "#059669",
            "Données":            "#d97706",
            "Mesures correctives":"#dc2626",
        }
        grouped = defaultdict(list)
        for item in filtered:
            grouped[item.get("category", "Général")].append(item)

        cats_sorted = sorted(grouped.keys())
        mid = (len(cats_sorted) + 1) // 2
        col_left, col_right = st.columns(2)

        for ci, cat in enumerate(cats_sorted):
            col = col_left if ci < mid else col_right
            c   = CAT_COLORS.get(cat, "#475569")
            with col:
                st.markdown(
                    f"<div style='display:inline-block;background:{c}12;color:{c};"
                    f"border:1px solid {c}44;border-radius:20px;padding:3px 14px;"
                    f"font-size:.68rem;font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:.06em;margin:12px 0 6px'>📂 {cat}</div>",
                    unsafe_allow_html=True)
                for item in grouped[cat]:
                    q_display = item["question"]
                    if q_p:
                        q_display = _re.sub(
                            f"({_re.escape(faq_query)})",
                            r"<mark style='background:#fef08a;border-radius:3px;"
                            r"padding:0 2px'>\1</mark>",
                            q_display, flags=_re.IGNORECASE)
                    with st.expander(item["question"]):
                        st.markdown(item["answer"])

    st.markdown(
        "<div style='margin-top:24px;padding:12px 16px;background:#f8fafc;"
        "border:1px solid #e2e8f0;border-radius:10px;"
        "font-size:.72rem;color:#94a3b8;text-align:center'>"
        "Vous ne trouvez pas votre réponse ? Contactez votre pharmacien référent.</div>",
        unsafe_allow_html=True)

# ── RENDER FAQ TAB (appelé dans parametres) ────────────────────────────────────
def render_faq_tab(can_edit: bool):
    faq_items = st.session_state.get("faq_items", [])

    st.markdown("### ❓ Gestion de la FAQ")
    st.markdown("""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
    padding:12px 16px;margin-bottom:16px;font-size:.82rem;color:#1e40af">
    ℹ️ Les questions et réponses définies ici apparaissent dans la fenêtre
    d'aide accessible via le <strong>🍄 champignon</strong> en bas de la sidebar.
    Le formatage <strong>Markdown</strong> est supporté dans les réponses.
    </div>""", unsafe_allow_html=True)

    cats_count = {}
    for f in faq_items:
        c = f.get("category", "Général")
        cats_count[c] = cats_count.get(c, 0) + 1
    stat_cols = st.columns(min(len(cats_count) + 1, 5))
    with stat_cols[0]:
        st.metric("Total Q&R", len(faq_items))
    for i, (cat, cnt) in enumerate(list(cats_count.items())[:4], 1):
        with stat_cols[i]:
            st.metric(cat[:14], cnt)

    st.divider()

    edit_idx = st.session_state.get("_faq_edit_idx")

    if can_edit and st.session_state.get("_faq_show_form", False):
        is_edit  = edit_idx is not None
        existing = faq_items[edit_idx] if is_edit else {}
        form_bg  = "#eff6ff" if is_edit else "#f0fdf4"
        form_bdr = "#93c5fd" if is_edit else "#86efac"
        form_ttl = "✏️ Modifier la question" if is_edit else "➕ Nouvelle question"
        st.markdown(
            f"<div style='background:{form_bg};border:1.5px solid {form_bdr};"
            f"border-radius:12px;padding:18px;margin-bottom:16px'>",
            unsafe_allow_html=True,
        )
        st.markdown(f"#### {form_ttl}")
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            faq_q = st.text_input(
                "Question *", value=existing.get("question", ""),
                placeholder="Ex: Comment ajouter un point de prélèvement ?",
                key="faq_form_q",
            )
        with fc2:
            cur_cat = existing.get("category", "Général")
            faq_c = st.selectbox(
                "Catégorie", FAQ_CATEGORIES,
                index=FAQ_CATEGORIES.index(cur_cat) if cur_cat in FAQ_CATEGORIES else 0,
                key="faq_form_c",
            )
        faq_a = st.text_area(
            "Réponse * (Markdown supporté)", value=existing.get("answer", ""),
            height=160,
            placeholder="Décrivez la réponse. **Gras**, *italique*, listes...",
            key="faq_form_a",
        )
        if faq_a.strip():
            with st.expander("👁️ Aperçu du rendu", expanded=False):
                st.markdown(faq_a)
        fb1, fb2 = st.columns(2)
        with fb1:
            if st.button(
                "✔️ Mettre à jour" if is_edit else "✅ Ajouter",
                use_container_width=True, type="primary", key="faq_form_submit",
            ):
                if not faq_q.strip():
                    st.error("La question est obligatoire.")
                elif not faq_a.strip():
                    st.error("La réponse est obligatoire.")
                else:
                    if is_edit:
                        faq_items[edit_idx].update(
                            question=faq_q.strip(), answer=faq_a.strip(), category=faq_c
                        )
                    else:
                        faq_items.append({
                            "id":       f"faq_{int(datetime.now().timestamp())}",
                            "category": faq_c,
                            "question": faq_q.strip(),
                            "answer":   faq_a.strip(),
                            "order":    len(faq_items),
                        })
                    save_faq(faq_items, supa=True)
                    st.session_state["faq_items"]      = faq_items
                    st.session_state["_faq_show_form"] = False
                    st.session_state["_faq_edit_idx"]  = None
                    st.success("✅ FAQ mise à jour !")
                    st.rerun()
        with fb2:
            if st.button("✕ Annuler", use_container_width=True, key="faq_form_cancel"):
                st.session_state["_faq_show_form"] = False
                st.session_state["_faq_edit_idx"]  = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif can_edit and not st.session_state.get("_faq_show_form", False):
        if st.button("➕ Ajouter une question", key="faq_add_btn", use_container_width=True):
            st.session_state["_faq_show_form"] = True
            st.session_state["_faq_edit_idx"]  = None
            st.rerun()

    if not faq_items:
        st.markdown(
            "<div style='background:#f8fafc;border:1.5px dashed #cbd5e1;"
            "border-radius:12px;padding:32px;text-align:center;margin-top:12px'>"
            "<div style='font-size:2.5rem;margin-bottom:8px'>❓</div>"
            "<div style='font-weight:700;color:#475569'>Aucune question définie</div>"
            "<div style='font-size:.8rem;color:#94a3b8;margin-top:4px'>"
            "Cliquez sur ➕ Ajouter une question ci-dessus</div></div>",
            unsafe_allow_html=True,
        )
    else:
        all_cats_f = ["Toutes"] + sorted(
            set(f.get("category", "Général") for f in faq_items))
        sel_f = st.selectbox(
            "Filtrer", all_cats_f, key="faq_tab_cat", label_visibility="collapsed"
        )
        st.markdown(
            "<div style='display:grid;grid-template-columns:2.2fr 1fr 1fr;"
            "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;"
            "padding:10px 14px;margin-top:8px'>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff'>Question</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Catégorie</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Actions</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        CAT_COL = {
            "Général":            "#2563eb",
            "Score & Seuils":     "#7c3aed",
            "Prélèvements":       "#0891b2",
            "Paramètres":         "#059669",
            "Données":            "#d97706",
            "Mesures correctives":"#dc2626",
        }
        displayed = [
            (i, f) for i, f in enumerate(faq_items)
            if sel_f == "Toutes" or f.get("category") == sel_f
        ]
        for dp, (ri, item) in enumerate(displayed):
            cc      = CAT_COL.get(item.get("category", "Général"), "#475569")
            row_bg  = "#f8fafc" if dp % 2 == 0 else "#ffffff"
            is_last = dp == len(displayed) - 1
            r_bdr   = "border-radius:0 0 10px 10px" if is_last else ""
            rc1, rc2 = st.columns([7, 1])
            with rc1:
                st.markdown(
                    f"<div style='display:grid;grid-template-columns:2.2fr 1fr;"
                    f"gap:4px;background:{row_bg};border:1px solid #e2e8f0;"
                    f"border-top:none;padding:10px 14px;align-items:center;{r_bdr}'>"
                    f"<div style='font-size:.83rem;font-weight:600;color:#0f172a'>"
                    f"{item['question']}</div>"
                    f"<div style='text-align:center'>"
                    f"<span style='background:{cc}14;color:{cc};border:1px solid {cc}44;"
                    f"border-radius:12px;padding:2px 10px;font-size:.65rem;font-weight:700'>"
                    f"{item.get('category','Général')}</span></div></div>",
                    unsafe_allow_html=True,
                )
            with rc2:
                a1, a2, a3, a4 = st.columns(4)
                with a1:
                    if can_edit and ri > 0:
                        if st.button("↑", key=f"faq_up_{ri}", help="Monter"):
                            faq_items[ri], faq_items[ri-1] = faq_items[ri-1], faq_items[ri]
                            for k, f in enumerate(faq_items): f["order"] = k
                            save_faq(faq_items, supa=True)
                            st.session_state["faq_items"] = faq_items
                            st.rerun()
                with a2:
                    if can_edit and ri < len(faq_items) - 1:
                        if st.button("↓", key=f"faq_dn_{ri}", help="Descendre"):
                            faq_items[ri], faq_items[ri+1] = faq_items[ri+1], faq_items[ri]
                            for k, f in enumerate(faq_items): f["order"] = k
                            save_faq(faq_items, supa=True)
                            st.session_state["faq_items"] = faq_items
                            st.rerun()
                with a3:
                    if can_edit:
                        if st.button("✏️", key=f"faq_ed_{ri}"):
                            st.session_state["_faq_edit_idx"]  = ri
                            st.session_state["_faq_show_form"] = True
                            st.rerun()
                with a4:
                    if can_edit:
                        if st.button("🗑️", key=f"faq_dl_{ri}"):
                            faq_items.pop(ri)
                            for k, f in enumerate(faq_items): f["order"] = k
                            save_faq(faq_items, supa=True)
                            st.session_state["faq_items"] = faq_items
                            st.rerun()
        st.markdown(
            f"<div style='background:#1e293b;border-radius:0 0 10px 10px;"
            f"padding:8px 14px'><div style='font-size:.75rem;color:#94a3b8'>"
            f"{len(faq_items)} question(s) · {len(displayed)} affichée(s)"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    if can_edit:
        st.markdown("#### ↩️ Réinitialiser la FAQ")
        st.caption("Recharge les 10 questions prédéfinies et efface vos personnalisations.")
        if st.button("↩️ Remettre les questions par défaut", key="faq_reset"):
            st.session_state["faq_items"] = [dict(f) for f in DEFAULT_FAQ]
            save_faq(st.session_state["faq_items"], supa=True)
            st.success("✅ FAQ réinitialisée.")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB : LOGIGRAMME — COMPLET
# Criticité germe = Pathogénicité × Résistance × Dissémination 
# ═══════════════════════════════════════════════════════════════════════════════

if active == "logigramme":
    can_edit = check_access_protege("Logigramme")

    # ── Constantes ─────────────────────────────────────────────────────────────
    PATHO_OPTS = [
        "1 — Non pathogène",
        "2 — Pathogène opportuniste",
        "3 — Pathogène opportuniste multirésistant / Pathogène primaire",
    ]
    RESIST_OPTS = [
        "1 — Sensible",
        "2 — Résistant au Surfa'Safe",
        "3 — Résistant au Surfa'Safe et Acide Peracétique",
    ]
    DISSEM_OPTS = [
        "1 — Environnemental",
        "2 — Manuporté",
        "3 — Aéroporté",
    ]

    def _risk_color(score):
        if score <= 4:   return "#22c55e"
        if score <= 8:   return "#84cc16"
        if score <= 12:  return "#f59e0b"
        if score <= 18:  return "#f97316"
        return "#ef4444"

    def _risk_label(score):
        if score <= 4:   return "Faible"
        if score <= 8:   return "Modéré"
        if score <= 12:  return "Important"
        if score <= 18:  return "Majeur"
        return "Critique"

    def _infer_resistance(surfa, apa):
        """Migration : déduit la résistance depuis surfa/apa existants."""
        s = (surfa or "").lower()
        a = (apa  or "").lower()
        if "risque" in s and "risque" in a:
            return 3
        if "risque" in s:
            return 2
        return 1

    def _germ_score(g):
        if all(k in g for k in ("pathogenicity", "resistance", "dissemination")):
            return int(g["pathogenicity"]) * int(g["resistance"]) * int(g["dissemination"])
        # Migration ancien modèle
        old = g.get("risk", 1)
        return {1: 1, 2: 2, 3: 6, 4: 12, 5: 18}.get(old, old)

    # ── Bandeau récapitulatif ───────────────────────────────────────────────────
    _synced        = st.session_state.get("germs_synced_count", 0)
    _total_default = len(DEFAULT_GERMS)
    _total_germs   = len(st.session_state.germs)
    _custom_count  = max(0, _total_germs - _total_default)

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);border:1.5px solid #93c5fd;
    border-radius:12px;padding:12px 18px;margin-bottom:14px;display:flex;align-items:center;
    justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
        <span style="font-size:1.4rem">🦠</span>
        <div>
          <div style="font-weight:800;color:#1e40af;font-size:.88rem">Base de données germes</div>
          <div style="font-size:.7rem;color:#3b82f6;margin-top:2px">
            {_total_default} standards · {_custom_count} personnalisé(s) · {_total_germs} au total
          </div>
          <div style="font-size:.65rem;color:#64748b;margin-top:1px">
            Score criticité = Pathogénicité × Résistance × Dissémination (1–27)
          </div>
        </div>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <div style="background:#fff;border:1px solid #93c5fd;border-radius:8px;padding:6px 12px;text-align:center">
          <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase;font-weight:700">Standard</div>
          <div style="font-size:1.1rem;font-weight:800;color:#1e40af">{_total_default}</div>
        </div>
        <div style="background:#fff;border:1px solid #86efac;border-radius:8px;padding:6px 12px;text-align:center">
          <div style="font-size:.6rem;color:#166534;text-transform:uppercase;font-weight:700">Custom</div>
          <div style="font-size:1.1rem;font-weight:800;color:#166534">{_custom_count}</div>
        </div>
        <div style="background:#fff;border:1px solid #fcd34d;border-radius:8px;padding:6px 12px;text-align:center">
          <div style="font-size:.6rem;color:#92400e;text-transform:uppercase;font-weight:700">Total</div>
          <div style="font-size:1.1rem;font-weight:800;color:#92400e">{_total_germs}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    if _synced > 0:
        st.success(f"✅ Synchronisation : {_synced} germe(s) mis à jour depuis la base de référence.")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if can_edit:
            if st.button("➕ Ajouter un germe", use_container_width=True):
                st.session_state.show_add = not st.session_state.show_add
                st.session_state.edit_idx = None
    with col_btn2:
        if can_edit:
            if st.button("💾 Sauvegarder", use_container_width=True, key="save_germs_btn"):
                save_germs(st.session_state.germs)
                st.success("✅ Germes sauvegardés !")

    if not can_edit:
        st.info("👁️ Mode lecture seule — connectez-vous pour modifier les germes.")

    # ── Formulaire ajout / modification ────────────────────────────────────────
    def germ_form(existing=None, idx=None):
        is_edit = existing is not None
        with st.container():
            st.markdown(
                f"<div style='background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;"
                f"padding:18px;margin-bottom:12px'>",
                unsafe_allow_html=True)
            st.markdown(f"### {'✏️ Modifier' if is_edit else '➕ Ajouter'} un germe")

            c1, c2, c3 = st.columns(3)

            # ── Col 1 : taxonomie ────────────────────────────────────────────
            with c1:
                st.markdown(
                    "<div style='font-size:.72rem;font-weight:800;color:#1e40af;"
                    "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px'>"
                    "📋 Identification</div>", unsafe_allow_html=True)

                new_name = st.text_input(
                    "Nom du germe *",
                    value=existing["name"] if is_edit else "",
                    placeholder="Ex: Listeria spp.",
                    disabled=not can_edit)

                new_famille = st.selectbox(
                    "Famille *", ["Bactéries", "Champignons"],
                    index=["Bactéries", "Champignons"].index(existing["path"][1])
                          if is_edit else 0,
                    disabled=not can_edit)

                new_origine = st.selectbox(
                    "Origine *", ["Humains ", "Environnemental"],
                    index=0 if (not is_edit or existing["path"][2] in ["Humains", "Humain"]) else 1,
                    disabled=not can_edit)

                if new_famille == "Bactéries":
                    cats = (["Peau / Muqueuse", "Oropharynx / Gouttelettes", "Flore fécale"]
                            if "Humain" in new_origine
                            else ["Humidité", "Sol / Carton / Surface sèche"])
                else:
                    cats = (["Peau / Muqueuse"]
                            if "Humain" in new_origine
                            else ["Humidité", "Sol / Carton / Surface sèche", "Air"])

                cur_cat = existing["path"][3] if is_edit and existing["path"][3] in cats else cats[0]
                new_cat = st.selectbox(
                    "Catégorie *", cats,
                    index=cats.index(cur_cat) if cur_cat in cats else 0,
                    disabled=not can_edit)


            # ── Col 2 : critères de criticité ────────────────────────────────
            with c2:
                st.markdown(
                    "<div style='font-size:.72rem;font-weight:800;color:#1e40af;"
                    "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px'>"
                    "🔬 Critères de criticité</div>", unsafe_allow_html=True)

                # Pathogénicité
                cur_patho = int(existing.get("pathogenicity", 1)) if is_edit else 1
                patho_lbl = st.selectbox(
                    "🧬 Pathogénicité *", PATHO_OPTS,
                    index=min(cur_patho - 1, 2),
                    key="form_patho", disabled=not can_edit)
                patho_num = int(patho_lbl[0])

                # Résistance aux désinfectants
                if is_edit:
                    cur_resist = int(existing.get(
                        "resistance",
                        _infer_resistance(existing.get("surfa"), existing.get("apa"))))
                else:
                    cur_resist = 1
                resist_lbl = st.selectbox(
                    "🧴 Résistance aux désinfectants *", RESIST_OPTS,
                    index=min(cur_resist - 1, 2),
                    key="form_resist", disabled=not can_edit)
                resist_num = int(resist_lbl[0])

                # Mode de dissémination
                cur_dissem = int(existing.get("dissemination", 1)) if is_edit else 1
                dissem_lbl = st.selectbox(
                    "💨 Mode de dissémination *", DISSEM_OPTS,
                    index=min(cur_dissem - 1, 2),
                    key="form_dissem", disabled=not can_edit)
                dissem_num = int(dissem_lbl[0])

                # ── Score calculé ────────────────────────────────────────────              
                risk_num = patho_num * resist_num * dissem_num
                rc = _risk_color(risk_num)
                rl = _risk_label(risk_num)

                if risk_num > 36:
                    status_txt = "🚨 Action probable si lieu ≥ critique"
                    status_bg  = "#fef2f2"
                    status_c   = "#991b1b"
                elif risk_num >= 24:
                    status_txt = "⚠️ Alerte probable si lieu ≥ semi-critique"
                    status_bg  = "#fffbeb"
                    status_c   = "#92400e"
                else:
                    status_txt = "✅ Conforme selon lieu de prélèvement"
                    status_bg  = "#f0fdf4"
                    status_c   = "#166534"

                st.markdown(f"""
                <div style="background:{rc}12;border:2px solid {rc}55;border-radius:12px;
                padding:14px;margin-top:8px;text-align:center">
                  <div style="font-size:.62rem;color:#475569;text-transform:uppercase;
                  letter-spacing:.1em;margin-bottom:6px;font-weight:700">Score de criticité</div>
                  <div style="font-size:2.8rem;font-weight:900;color:{rc};line-height:1">
                    {risk_num}
                  </div>
                  <div style="font-size:.78rem;font-weight:700;color:{rc};margin-top:4px">
                    {rl}
                  </div>
                  <div style="font-size:.62rem;color:#64748b;margin-top:8px;
                  background:#fff;border-radius:6px;padding:5px 8px;display:inline-block">
                    {patho_num} (patho) × {resist_num} (résist.) × {dissem_num} (dissém.) = {risk_num}
                  </div>
                  <div style="font-size:.65rem;font-weight:600;padding:5px 8px;border-radius:6px;
                  margin-top:8px;background:{status_bg};color:{status_c}">
                    {status_txt}
                  </div>
                </div>""", unsafe_allow_html=True)

            # col 3 Notes
                       
            with c3:
                st.markdown(
                    "<div style='font-size:.72rem;font-weight:800;color:#1e40af;"
                    "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px'>"
                    "Information supplémentaire</div>", unsafe_allow_html=True)
                                
                new_notes = st.text_area(
                    "📝 Notes",
                    value=existing.get("notes", "") or "" if is_edit else "",
                    height=70, disabled=not can_edit)

                new_comment = st.text_area(
                    "💬 Commentaire détaillé",
                    value=existing.get("comment", "") or "" if is_edit else "",
                    height=70, disabled=not can_edit)

                                    
                                           
            # ── Boutons ──────────────────────────────────────────────────────
            st.markdown("</div>", unsafe_allow_html=True)
            cb1, cb2 = st.columns(2)
            with cb1:
                if can_edit:
                    if st.button(
                        "✅ " + ("Modifier" if is_edit else "Ajouter"),
                        use_container_width=True, key="form_submit"):
                        if not new_name.strip():
                            st.error("Le nom est obligatoire.")
                            return
                        origine_node = (
                            ("Humains" if new_famille == "Bactéries" else "Humain")
                            if "Humain" in new_origine else "Environnemental")
                        new_germ = dict(
                            name=new_name.strip(),
                            path=["Germes", new_famille, origine_node, new_cat],
                            pathogenicity=patho_num,
                            resistance=resist_num,
                            dissemination=dissem_num,
                            risk=risk_num,
                            notes=new_notes.strip() or None,
                            comment=new_comment.strip() or None,
                        )
                        if is_edit:
                            st.session_state.germs[idx] = new_germ
                            st.session_state.edit_idx   = None
                        else:
                            if any(g["name"].lower() == new_name.strip().lower()
                                   for g in st.session_state.germs):
                                st.error("Ce germe existe déjà.")
                                return
                            st.session_state.germs.append(new_germ)
                            st.session_state.show_add = False
                        save_germs(st.session_state.germs)
                        st.rerun()
            with cb2:
                if can_edit:
                    if st.button("Annuler", use_container_width=True, key="form_cancel"):
                        st.session_state.show_add = False
                        st.session_state.edit_idx = None
                        st.rerun()

    if can_edit and st.session_state.show_add and st.session_state.edit_idx is None:
        germ_form()
    if can_edit and st.session_state.edit_idx is not None:
        germ_form(
            existing=st.session_state.germs[st.session_state.edit_idx],
            idx=st.session_state.edit_idx)

    st.divider()

    # ── Logigramme interactif HTML/D3 ─────────────────────────────────────────
    germs_json         = json.dumps(st.session_state.germs, ensure_ascii=False)
    default_names_json = json.dumps(sorted(DEFAULT_GERM_NAMES), ensure_ascii=False)

    tree_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f8fafc;color:#1e293b;font-family:'Segoe UI',sans-serif;height:95vh;overflow:hidden}}
.app{{display:flex;height:95vh}}
.tree-wrap{{flex:1;overflow:auto;padding:8px;scrollbar-width:thin;scrollbar-color:#cbd5e1 transparent}}
svg{{min-width:900px;width:100%;height:100%}}
.node rect{{fill:#fff;stroke:#e2e8f0;stroke-width:1.5;transition:all .2s;cursor:pointer}}
.node.highlighted rect{{stroke-width:2.5;filter:drop-shadow(0 0 4px rgba(0,0,0,.15))}}
.node text{{font-size:11px;fill:#0f172a;pointer-events:none;font-family:'Courier New',monospace}}
.link{{fill:none;stroke:#e2e8f0;stroke-width:1.5;transition:all .3s}}
.link.highlighted{{stroke-width:2.5}}
.right-panel{{width:490px;border-left:2px solid #e2e8f0;display:flex;flex-direction:column;background:#f1f5f9;flex-shrink:0}}
.sbox{{padding:12px 14px;border-bottom:1px solid #e2e8f0}}
.sbox input{{width:100%;background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;padding:10px 14px;color:#1e293b;font-size:.9rem;outline:none}}
.sbox input:focus{{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.1)}}
.germ-list{{flex:1;overflow-y:auto;padding:6px;scrollbar-width:thin}}
.germ-item{{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;cursor:pointer;transition:background .15s;font-size:.85rem;color:#0f172a;border:1px solid transparent;margin-bottom:3px}}
.germ-item:hover{{background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.germ-item.active{{background:#fff;border-color:#2563eb;box-shadow:0 1px 6px rgba(37,99,235,.2)}}
.risk-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.germ-count{{font-size:.72rem;color:#64748b;padding:6px 14px;text-align:center;border-bottom:1px solid #e2e8f0;background:#f8fafc;font-weight:600}}
.group-header{{font-size:.65rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#475569;padding:8px 12px 3px;background:#e2e8f0;margin:4px -6px 3px;border-radius:3px}}
.info-panel{{border-top:2px solid #e2e8f0;padding:14px;background:#fff;display:none;max-height:600px;overflow-y:auto}}
.info-panel.visible{{display:block}}
.info-name{{font-size:.92rem;font-weight:700;font-style:italic;color:#1e293b;margin-bottom:3px}}
.info-path{{font-size:.6rem;color:#2563eb;opacity:.85;margin-bottom:8px;font-family:monospace}}
.info-badge{{display:inline-flex;align-items:center;gap:5px;font-size:.7rem;padding:3px 10px;border-radius:20px;border:1px solid;margin-bottom:10px;font-weight:600}}
.info-lbl{{font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:#64748b;margin-bottom:2px;margin-top:8px;font-weight:700}}
.info-val{{font-size:.78rem;color:#1e293b;line-height:1.4}}
.score-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-top:6px}}
.score-cell{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:7px 5px;text-align:center}}
.score-cell .lbl{{font-size:.52rem;color:#64748b;text-transform:uppercase;margin-bottom:3px;line-height:1.3}}
.score-cell .val{{font-size:1.2rem;font-weight:900}}
.score-total{{background:#1e293b;border-radius:8px;padding:8px;text-align:center;margin-top:6px}}
.alert-row{{padding:5px 10px;border-radius:6px;font-size:.68rem;font-weight:700;margin-top:5px}}
.sens{{display:flex;align-items:center;gap:7px;padding:5px 9px;border-radius:6px;border:1px solid #e2e8f0;font-size:.72rem;margin-top:3px}}
.ok{{color:#22c55e;font-weight:700}}.warn{{color:#f97316;font-weight:700}}.crit{{color:#ef4444;font-weight:700}}
.notes-box{{margin-top:6px;padding:7px 10px;border-radius:6px;background:rgba(37,99,235,.04);border:1px solid rgba(37,99,235,.18);font-size:.72rem;color:#0f172a;line-height:1.5}}
</style></head><body>
<div class="app">
  <div class="tree-wrap"><svg id="svg"></svg></div>
  <div class="right-panel">
    <div class="sbox"><input type="text" id="sbox" placeholder="🔍 Rechercher un germe..." oninput="filterList()"></div>
    <div class="germ-count" id="germCount">Chargement...</div>
    <div class="germ-list" id="germList"></div>
    <div class="info-panel" id="infoPanel"></div>
  </div>
</div>
<script>
const GERMS={germs_json};
const DEFAULT_NAMES=new Set({default_names_json});
const NODE_W=190,NODE_H=28,H_GAP=28,V_GAP=10;
const LEVEL_COLS=["#38bdf8","#818cf8","#fb923c","#34d399","#a3e635"];
const PATHO_LBL=["","Non pathogène","Pathogène opportuniste","Pathogène opp. MR / Primaire"];
const RESIST_LBL=["","Sensible","Résistant Surfa'Safe","Résistant Surfa'Safe + APA"];
const DISSEM_LBL=["","Environnemental","Manuporté","Aéroporté"];

function riskColor(s){{
  if(s<=4)return"#22c55e";if(s<=8)return"#84cc16";
  if(s<=12)return"#f59e0b";if(s<=18)return"#f97316";return"#ef4444";
}}
function riskLabel(s){{
  if(s<=4)return"Faible";if(s<=8)return"Modéré";
  if(s<=12)return"Important";if(s<=18)return"Majeur";return"Critique";
}}
function germScore(g){{
  if(g.pathogenicity&&g.resistance&&g.dissemination)
    return g.pathogenicity*g.resistance*g.dissemination;
  const m={{1:1,2:2,3:6,4:12,5:18}};return m[g.risk]||g.risk||1;
}}

function buildTree(){{
  const root={{name:"Germes",children:[]}};
  GERMS.forEach(g=>{{
    let cur=root;
    g.path.slice(1).forEach(n=>{{
      let c=cur.children&&cur.children.find(x=>x.name===n);
      if(!c){{c={{name:n,children:[]}};if(!cur.children)cur.children=[];cur.children.push(c);}}
      cur=c;
    }});
  }});
  function clean(n){{if(n.children&&!n.children.length)delete n.children;else if(n.children)n.children.forEach(clean);}}
  clean(root);return root;
}}
function computeLayout(node,depth=0,y=0){{
  node.depth=depth;node.x=depth*(NODE_W+H_GAP);
  if(!node.children||!node.children.length){{node.y=y;return y+NODE_H;}}
  let cy=y;node.children.forEach(c=>{{cy=computeLayout(c,depth+1,cy);cy+=V_GAP;}});
  cy-=V_GAP;node.y=(y+cy)/2;return cy+V_GAP;
}}
function allNodes(n){{return[n,...(n.children||[]).flatMap(allNodes)];}}
function allLinks(n){{return(n.children||[]).flatMap(c=>[{{source:n,target:c}},...allLinks(c)]);}}
function buildPaths(n,p=[]){{n.fullPath=[...p,n.name];(n.children||[]).forEach(c=>buildPaths(c,n.fullPath));}}

function renderTree(){{
  const tree=buildTree();computeLayout(tree);buildPaths(tree);
  const nodes=allNodes(tree),links=allLinks(tree);
  const maxY=Math.max(...nodes.map(n=>n.y))+NODE_H+20;
  const maxX=Math.max(...nodes.map(n=>n.x))+NODE_W+20;
  const svg=document.getElementById('svg');
  svg.innerHTML='';
  svg.setAttribute('viewBox',`0 0 ${{maxX}} ${{maxY}}`);
  svg.setAttribute('height',maxY);svg.setAttribute('width',maxX);
  links.forEach(l=>{{
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    const x1=l.source.x+NODE_W,y1=l.source.y+NODE_H/2,x2=l.target.x,y2=l.target.y+NODE_H/2,mx=(x1+x2)/2;
    p.setAttribute('d',`M${{x1}},${{y1}} C${{mx}},${{y1}} ${{mx}},${{y2}} ${{x2}},${{y2}}`);
    p.setAttribute('class','link');
    p.dataset.sourcefull=l.source.fullPath.join('|||');
    p.dataset.targetfull=l.target.fullPath.join('|||');
    svg.appendChild(p);
  }});
  nodes.forEach(node=>{{
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class','node');
    g.setAttribute('transform',`translate(${{node.x}},${{node.y}})`);
    g.dataset.fullpath=node.fullPath.join('|||');
    const col=LEVEL_COLS[node.depth]||"#0f172a";
    const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
    rect.setAttribute('width',NODE_W);rect.setAttribute('height',NODE_H);
    rect.setAttribute('rx',5);rect.setAttribute('stroke',col);
    const text=document.createElementNS('http://www.w3.org/2000/svg','text');
    text.setAttribute('x',NODE_W/2);text.setAttribute('y',NODE_H/2+4);
    text.setAttribute('text-anchor','middle');
    text.textContent=node.name.length>27?node.name.substring(0,25)+'...':node.name;
    g.appendChild(rect);g.appendChild(text);
    g.addEventListener('mouseenter',()=>highlightPath(node.fullPath));
    g.addEventListener('mouseleave',clearHighlight);
    svg.appendChild(g);
  }});
}}
let selectedPath=null;
function highlightPath(exactPath){{
  const vp=new Set();for(let i=1;i<=exactPath.length;i++)vp.add(exactPath.slice(0,i).join('|||'));
  document.querySelectorAll('.node').forEach(n=>n.classList.toggle('highlighted',vp.has(n.dataset.fullpath||'')));
  document.querySelectorAll('.link').forEach(l=>{{
    const on=vp.has(l.dataset.sourcefull||'')&&vp.has(l.dataset.targetfull||'');
    l.classList.toggle('highlighted',on);
    if(on){{const d=(l.dataset.sourcefull||'').split('|||').length-1;l.style.stroke=LEVEL_COLS[d]||'#38bdf8';}}
    else l.style.stroke='';
  }});
}}
function clearHighlight(){{
  if(selectedPath){{highlightPath(selectedPath);return;}}
  document.querySelectorAll('.node').forEach(n=>n.classList.remove('highlighted'));
  document.querySelectorAll('.link').forEach(l=>{{l.classList.remove('highlighted');l.style.stroke=''}});
}}
function renderList(filter=''){{
  const list=document.getElementById('germList');
  const countEl=document.getElementById('germCount');
  list.innerHTML='';
  const filtered=GERMS.filter(g=>g.name.toLowerCase().includes(filter.toLowerCase()));
  countEl.textContent=filter?`${{filtered.length}} / ${{GERMS.length}} germe(s)`:`${{GERMS.length}} germe(s) — cliquez pour détails`;
  const groups={{}};
  filtered.forEach(g=>{{const cat=(g.path&&g.path[3])||'Autres';if(!groups[cat])groups[cat]=[];groups[cat].push(g);}});
  Object.keys(groups).sort().forEach(cat=>{{
    const header=document.createElement('div');header.className='group-header';header.textContent=cat;list.appendChild(header);
    groups[cat].forEach(g=>{{
      const score=germScore(g);const col=riskColor(score);
      const isCustom=!DEFAULT_NAMES.has(g.name);
      const isAir=(g.dissemination||0)===3;
      const hasResist=(g.resistance||0)>=2;
      let badges='';
      if(isAir)badges+='<span style="font-size:.48rem;background:#eff6ff;color:#1e40af;border-radius:3px;padding:0 4px;margin-left:2px">✈</span>';
      if(hasResist)badges+='<span style="font-size:.48rem;background:#fee2e2;color:#991b1b;border-radius:3px;padding:0 4px;margin-left:2px">⚠</span>';
      if(isCustom)badges+='<span style="font-size:.48rem;background:rgba(56,189,248,.15);color:#2563eb;border-radius:3px;padding:0 4px;margin-left:2px">★</span>';
      const div=document.createElement('div');div.className='germ-item';div.dataset.name=g.name;
      div.innerHTML=`<span class="risk-dot" style="background:${{col}}"></span><span style="flex:1;line-height:1.3">${{g.name}}${{badges}}</span><span style="font-size:.62rem;color:${{col}};font-weight:800;flex-shrink:0">${{score}}</span>`;
      div.addEventListener('click',()=>selectGerm(g));
      list.appendChild(div);
    }});
  }});
}}
function filterList(){{renderList(document.getElementById('sbox').value);}}
function selectGerm(g){{
  selectedPath=g.path;highlightPath(g.path);
  document.querySelectorAll('.germ-item').forEach(el=>el.classList.toggle('active',el.dataset.name===g.name));
  showInfo(g);
}}
function showInfo(g){{
  const panel=document.getElementById('infoPanel');panel.classList.add('visible');
  const score=germScore(g);const col=riskColor(score);
  function sens(v){{if(!v)return['ok','✓'];const l=v.toLowerCase();if(l.includes('modéré'))return['warn','⚠'];if(l.includes('risque'))return['crit','✗'];return['ok','✓'];}}
  
  const alertRow=score>24?`<div class="alert-row" style="background:#fef2f2;color:#991b1b">🚨 Action (score germe seul &gt; 24)</div>`
    :score>=16?`<div class="alert-row" style="background:#fffbeb;color:#92400e">⚠️ Alerte probable selon criticité du lieu</div>`
    :`<div class="alert-row" style="background:#f0fdf4;color:#166534">✅ Conforme à score germe seul</div>`;
  const nh=g.notes?`<div class="info-lbl">📝 Notes</div><div class="notes-box">${{g.notes}}</div>`:'';
  const ch=g.comment?`<div class="info-lbl" style="color:#fb923c">💬 Commentaire</div><div class="notes-box" style="color:#ea580c;background:rgba(251,146,60,.06);border-color:rgba(251,146,60,.3)">${{g.comment}}</div>`:'';
  panel.innerHTML=`
    <div class="info-name">${{g.name}}</div>
    <div class="info-path">${{g.path.join(' › ')}}</div>
    <div class="info-badge" style="color:${{col}};background:${{col}}22;border-color:${{col}}55">
      <span style="width:8px;height:8px;border-radius:50%;background:${{col}};display:inline-block"></span>
      Score ${{score}} — ${{riskLabel(score)}}
    </div>
    <div class="info-lbl">Critères de criticité</div>
    <div class="score-grid">
      <div class="score-cell">
        <div class="lbl">🧬 Pathogénicité</div>
        <div class="val" style="color:${{riskColor(g.pathogenicity||1)}}">${{g.pathogenicity||1}}</div>
        <div style="font-size:.5rem;color:#64748b;margin-top:2px">${{PATHO_LBL[g.pathogenicity||1]||'—'}}</div>
      </div>
      <div class="score-cell">
        <div class="lbl">🧴 Résistance</div>
        <div class="val" style="color:${{riskColor(g.resistance||1)}}">${{g.resistance||1}}</div>
        <div style="font-size:.5rem;color:#64748b;margin-top:2px">${{RESIST_LBL[g.resistance||1]||'—'}}</div>
      </div>
      <div class="score-cell">
        <div class="lbl">💨 Dissémination</div>
        <div class="val" style="color:${{riskColor(g.dissemination||1)}}">${{g.dissemination||1}}</div>
        <div style="font-size:.5rem;color:#64748b;margin-top:2px">${{DISSEM_LBL[g.dissemination||1]||'—'}}</div>
      </div>
    </div>
    <div class="score-total">
      <div style="font-size:.58rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em">Score calculé</div>
      <div style="font-size:1.8rem;font-weight:900;color:${{col}};line-height:1.1">${{score}}</div>
      <div style="font-size:.6rem;color:#94a3b8">${{g.pathogenicity||'?'}} × ${{g.resistance||'?'}} × ${{g.dissemination||'?'}}</div>
    </div>
    ${{alertRow}}
    
    ${{nh}}${{ch}}`;
}}
renderTree();
renderList();
</script></body></html>"""

    st.components.v1.html(tree_html, height=1200, scrolling=False)

    # ── Liste de gestion ───────────────────────────────────────────────────────
    st.markdown("### ✏️ Gérer les germes")
    search_edit = st.text_input(
        "Filtrer", placeholder="Rechercher un germe...", label_visibility="collapsed")
    filtered = ([g for g in st.session_state.germs
                 if search_edit.lower() in g["name"].lower()]
                if search_edit else st.session_state.germs)

    for i, g in enumerate(filtered):
        real_idx = st.session_state.germs.index(g)
        score    = _germ_score(g)
        c        = _risk_color(score)
        rl       = _risk_label(score)

        col_n, col_s, col_rl, col_e, col_d = st.columns([4, 0.6, 1, 0.6, 0.6])
        with col_n:
            st.markdown(
                f'<span style="color:{c};font-size:.75rem">●</span> '
                f'<span style="font-size:.82rem;font-style:italic">{g["name"]}</span>',
                unsafe_allow_html=True)
        with col_s:
            st.markdown(
                f'<span style="font-size:.75rem;color:{c};font-weight:800">{score}</span>',
                unsafe_allow_html=True)
        with col_rl:
            st.markdown(
                f'<span style="font-size:.65rem;color:{c};font-weight:700">{rl}</span>',
                unsafe_allow_html=True)
        with col_e:
            if can_edit:
                if st.button("✏️", key=f"edit_{real_idx}_{i}"):
                    st.session_state.edit_idx = real_idx
                    st.session_state.show_add = False
                    st.rerun()
        with col_d:
            if can_edit:
                if st.button("🗑️", key=f"del_{real_idx}_{i}"):
                    st.session_state.germs.pop(real_idx)
                    save_germs(st.session_state.germs)
                    st.rerun()
# ═══════════════════════════════════════════════════════════════════════════════
# TAB : SURVEILLANCE — 4 SOUS-ONGLETS
# ═══════════════════════════════════════════════════════════════════════════════

if active == "surveillance":
    st.markdown("### 🔍 Identification & Surveillance microbiologique")

    # ── Calcul indicateurs sous-onglets ───────────────────────────────────────
    _active_sids_surv = {p['id'] for p in st.session_state.prelevements if not p.get("archived")}

    _j2_red    = sum(1 for s in st.session_state.schedules
                     if s["when"]=="J2" and s["status"]=="pending"
                     and s.get("sample_id") in _active_sids_surv
                     and datetime.fromisoformat(s["due_date"]).date() <= today)
    _j2_orange = sum(1 for s in st.session_state.schedules
                     if s["when"]=="J2" and s["status"]=="pending"
                     and s.get("sample_id") in _active_sids_surv
                     and datetime.fromisoformat(s["due_date"]).date() > today)
    _j7_red    = sum(1 for s in st.session_state.schedules
                     if s["when"]=="J7" and s["status"]=="pending"
                     and s.get("sample_id") in _active_sids_surv
                     and datetime.fromisoformat(s["due_date"]).date() <= today)
    _j7_orange = sum(1 for s in st.session_state.schedules
                     if s["when"]=="J7" and s["status"]=="pending"
                     and s.get("sample_id") in _active_sids_surv
                     and datetime.fromisoformat(s["due_date"]).date() > today)
    _id_red    = sum(1 for p in st.session_state.pending_identifications
                     if p.get("status") == "pending")

    _dot_j2 = " 🔴" if _j2_red > 0 else (" 🟠" if _j2_orange > 0 else "")
    _dot_j7 = " 🔴" if _j7_red > 0 else (" 🟠" if _j7_orange > 0 else "")
    _dot_id = " 🔴" if _id_red > 0 else ""

    # ── Sous-onglets ──────────────────────────────────────────────────────────
    tab_nouveau, tab_scan, tab_j2, tab_j7, tab_ident = st.tabs([
        "🧪 Nouveau prélèvement",
        "📷 Scan QR",
        f"📖 Lecture J2{_dot_j2}",
        f"📗 Lecture J7{_dot_j7}",
        f"🔴 Identifications en attente{_dot_id}",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — NOUVEAU PRÉLÈVEMENT
    # ══════════════════════════════════════════════════════════════════════════
    with tab_nouveau:
        if not st.session_state.points:
            st.info("Aucun point de prélèvement défini — allez dans **Paramètres → Points de prélèvement**.")
        else:
            p_col1, p_col2 = st.columns([3, 2])
            with p_col1:
                point_labels = [
                    f"{pt['label']} — {pt.get('type','?')} — "
                    f"{'Critique' if pt.get('location_criticality',1)==3 else 'Semi-critique' if pt.get('location_criticality',1)==2 else 'Non critique'}"
                    for pt in st.session_state.points
                ]
                sel_idx = st.selectbox(
                    "Point de prélèvement",
                    list(range(len(point_labels))),
                    format_func=lambda i: point_labels[i],
                    key="new_prelev_point")
                selected_point = st.session_state.points[sel_idx]
                pt_type      = selected_point.get('type', '—')
                pt_loc_crit  = int(selected_point.get('location_criticality', 1))
                pt_gelose    = selected_point.get('gelose', '—')
                pt_room      = selected_point.get('room_class', '—')
                type_icon    = "💨" if pt_type == "Air" else "🧴"
                lc_col       = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(pt_loc_crit),"#94a3b8")
                lc_lbl       = _loc_crit_label(pt_loc_crit)
                st.markdown(f"""
                <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:12px;margin-top:4px">
                  <div style="font-size:.75rem;font-weight:700;color:#0369a1;margin-bottom:8px">{type_icon} Détails du point sélectionné</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                    <div style="background:#fff;border-radius:6px;padding:8px;border:1px solid #e0f2fe">
                      <div style="font-size:.6rem;color:#64748b;text-transform:uppercase">Type</div>
                      <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:2px">{pt_type}</div>
                    </div>
                    <div style="background:#dbeafe;border-radius:6px;padding:8px;border:1px solid #93c5fd">
                      <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Classe ISO / GMP</div>
                      <div style="font-size:.85rem;font-weight:800;color:#1e40af;margin-top:2px">{pt_room if pt_room and pt_room != '—' else '—'}</div>
                    </div>
                    <div style="background:{lc_col}11;border-radius:6px;padding:8px;border:1px solid {lc_col}44">
                      <div style="font-size:.6rem;color:#64748b;text-transform:uppercase">Criticité lieu</div>
                      <div style="font-size:.85rem;font-weight:700;color:{lc_col};margin-top:2px">Nv.{pt_loc_crit} — {lc_lbl}</div>
                    </div>
                    <div style="background:#fff;border-radius:6px;padding:8px;border:1px solid #e0f2fe">
                      <div style="font-size:.6rem;color:#64748b;text-transform:uppercase">Gélose</div>
                      <div style="font-size:.85rem;font-weight:700;color:#1d4ed8;margin-top:2px">🧫 {pt_gelose}</div>
                    </div>
                  </div>
                  <div style="background:#f8fafc;border-radius:6px;padding:7px 10px;margin-top:6px;
                  font-size:.68rem;color:#475569;border:1px solid #e2e8f0">
                    <strong>Grille seuils :</strong>
                    score = criticité lieu ({pt_loc_crit}) × score germe &nbsp;·&nbsp;
                    ⚠️ Alerte 24–36 &nbsp;·&nbsp; 🚨 Action &gt; 36
                  </div>
                </div>""", unsafe_allow_html=True)

            with p_col2:
                oper_list = [
                    o['nom'] + (' — ' + o.get('profession','') if o.get('profession') else '')
                    for o in st.session_state.operators
                ]
                if oper_list:
                    oper_sel = st.selectbox("Opérateur", ["— Sélectionner —"] + oper_list, key="new_prelev_oper_sel")
                    p_oper   = oper_sel if oper_sel != "— Sélectionner —" else ""
                else:
                    st.info("Aucun opérateur — ajoutez-en dans Paramètres")
                    p_oper = st.text_input("Opérateur (manuel)", placeholder="Nom", key="new_prelev_oper_manual")
                p_date = st.date_input("Date prélèvement", value=datetime.today(), key="new_prelev_date")
                j2_date_calc = next_working_day_offset(p_date, 2)
                j7_date_calc = next_working_day_offset(p_date, 5)
                st.markdown(f"""
                <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
                padding:8px;margin-top:6px;font-size:.7rem;color:#166534">
                  📅 J2 (2 jours ouvrés) : <strong>{j2_date_calc.strftime('%d/%m/%Y')}</strong><br>
                  📅 J7 (5 jours ouvrés) : <strong>{j7_date_calc.strftime('%d/%m/%Y')}</strong>
                </div>""", unsafe_allow_html=True)
                p_commentaire = st.text_area("💬 Commentaire", placeholder="Remarque, contexte...", height=70, key="new_prelev_commentaire")

            p_isolateur = ""
            p_poste     = "Poste 1"
            if str(pt_room).strip().upper() == "A":
                st.markdown(
                    "<div style='background:#fef9c3;border:1px solid #fde047;"
                    "border-radius:8px;padding:10px 14px;margin-top:8px'>"
                    "<div style='font-size:.7rem;font-weight:700;color:#854d0e;margin-bottom:8px'>"
                    "🔬 Paramètres Zone Classe A</div>",
                    unsafe_allow_html=True)
                iso_col, poste_col = st.columns(2)
                with iso_col:
                    p_isolateur = st.radio(
                        "Isolateur", ["Iso 16/0724","Iso 14/07169"],
                        horizontal=True, key="new_prelev_isolateur")
                with poste_col:
                    p_poste = st.radio(
                        "Poste", ["Poste 1","Poste 2","Commun"],
                        horizontal=True, key="new_prelev_poste")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            # ── Localisation sur plan ─────────────────────────────────────────
            plans_available = st.session_state.get("plans", [])
            st.markdown(
                "<div style='font-size:.75rem;font-weight:700;color:#475569;margin-bottom:6px'>"
                "🗺️ Localiser sur le plan URC "
                "<span style='font-weight:400;font-style:italic'>(optionnel)</span></div>",
                unsafe_allow_html=True)

            if not plans_available:
                st.markdown(
                    "<div style='background:#f8fafc;border:1.5px dashed #cbd5e1;"
                    "border-radius:10px;padding:16px;text-align:center'>"
                    "<div style='font-size:1.2rem'>🗺️</div>"
                    "<div style='color:#64748b;font-size:.8rem'>Aucun plan — "
                    "ajoutez-en dans <strong>Paramètres → Plans</strong></div></div>",
                    unsafe_allow_html=True)
            else:
                plan_names    = ["— Aucun plan —"] + [p["name"] for p in plans_available]
                sel_plan_name = st.selectbox(
                    "Choisir un plan", plan_names,
                    key="new_prelev_plan_sel",
                    help="Gérez les plans dans Paramètres → Plans")
                sel_plan = None
                if sel_plan_name != "— Aucun plan —":
                    sel_plan = next((p for p in plans_available if p["name"] == sel_plan_name), None)

                if sel_plan and sel_plan.get("image_b64"):
                    _cur_label = selected_point.get("label", "")
                    _cur_pt    = next(
                        (mp for mp in st.session_state.get("map_points", [])
                         if mp.get("label") == _cur_label), None)
                    if _cur_pt and not isinstance(_cur_pt.get("x"), (int, float)):
                        _cur_pt = None

                    if _cur_pt:
                        st.markdown(
                            f"<div style='background:#f0fdf4;border:1.5px solid #86efac;"
                            f"border-radius:8px;padding:8px 14px;font-size:.8rem;"
                            f"color:#166534;font-weight:700;margin-bottom:8px'>"
                            f"📌 Position enregistrée : "
                            f"<b>{float(_cur_pt['x']):.1f}% · {float(_cur_pt['y']):.1f}%</b>"
                            f"</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div style='background:#fffbeb;border:1px solid #fcd34d;"
                            "border-radius:8px;padding:8px 14px;font-size:.78rem;"
                            "color:#92400e;margin-bottom:8px'>"
                            "⬜ Aucune position enregistrée</div>",
                            unsafe_allow_html=True)

                    import base64, io
                    from PIL import Image, ImageDraw
                    from streamlit_image_coordinates import streamlit_image_coordinates

                    _img_b64 = sel_plan["image_b64"]
                    if "," in _img_b64:
                        _img_b64 = _img_b64.split(",", 1)[1]
                    _img_bytes = base64.b64decode(_img_b64)
                    _pil_img   = Image.open(io.BytesIO(_img_bytes)).convert("RGBA")
                    _iw, _ih   = _pil_img.size

                    _click_key = f"map_pending_{_cur_label}"
                    _pending   = st.session_state.get(_click_key)

                    _draw_img  = _pil_img.copy()
                    _draw      = ImageDraw.Draw(_draw_img)
                    _r         = max(12, min(24, _iw // 40))

                    if _pending:
                        _dpx = int(_pending["x"] / 100 * _iw)
                        _dpy = int(_pending["y"] / 100 * _ih)
                        _draw.ellipse([_dpx-_r, _dpy-_r, _dpx+_r, _dpy+_r],
                                      fill=(59,130,246,200), outline=(255,255,255,255), width=3)
                    elif _cur_pt:
                        _dpx = int(float(_cur_pt["x"]) / 100 * _iw)
                        _dpy = int(float(_cur_pt["y"]) / 100 * _ih)
                        _col_map = {"1":(34,197,94),"2":(245,158,11),"3":(239,68,68)}.get(str(pt_loc_crit),(59,130,246))
                        _draw.ellipse([_dpx-_r, _dpy-_r, _dpx+_r, _dpy+_r],
                                      fill=_col_map+(220,), outline=(255,255,255,255), width=3)

                    st.markdown(
                        "<div style='background:#f0f9ff;border:1px solid #bae6fd;"
                        "border-radius:8px;padding:8px 12px;margin-bottom:8px;"
                        "font-size:.73rem;color:#0369a1;line-height:1.7'>"
                        "💡 <b>Comment placer le point :</b> "
                        "cliquez directement sur l'image pour positionner le marqueur, "
                        "puis cliquez <b>📌 Enregistrer</b>."
                        "</div>", unsafe_allow_html=True)

                    _click = streamlit_image_coordinates(
                        _draw_img,
                        key=f"map_click_{_cur_label}",
                        use_column_width=True
                    )

                    if _click is not None:
                        _click_x = max(0.0, min(100.0, round(_click["x"] / _click["width"]  * 100, 1)))
                        _click_y = max(0.0, min(100.0, round(_click["y"] / _click["height"] * 100, 1)))
                        _new_pending = {"x": _click_x, "y": _click_y}
                        if st.session_state.get(_click_key) != _new_pending:
                            st.session_state[_click_key] = _new_pending
                            st.rerun()

                    if _pending:
                        st.markdown(
                            f"<div style='background:#fffbeb;border:1px solid #fcd34d;"
                            f"border-radius:8px;padding:8px 14px;font-size:.8rem;"
                            f"color:#92400e;font-weight:700;margin-bottom:8px'>"
                            f"🖱️ Position sélectionnée : "
                            f"<b>{_pending['x']}% · {_pending['y']}%</b> — cliquez Enregistrer pour confirmer"
                            f"</div>", unsafe_allow_html=True)

                    _bc1, _bc2 = st.columns(2)
                    with _bc1:
                        if st.button("📌 Enregistrer", key=f"map_save_{_cur_label}",
                                     use_container_width=True, type="primary",
                                     disabled=_pending is None):
                            _new_pt = {
                                "label":      _cur_label,
                                "room_class": selected_point.get("room_class", ""),
                                "loc_crit":   pt_loc_crit,
                                "survLabel":  None,
                                "x":          _pending["x"],
                                "y":          _pending["y"],
                            }
                            if "map_points" not in st.session_state:
                                st.session_state.map_points = []
                            _lbls = [p.get("label") for p in st.session_state.map_points]
                            if _cur_label not in _lbls:
                                st.session_state.map_points.append(_new_pt)
                            else:
                                for _mp in st.session_state.map_points:
                                    if _mp.get("label") == _cur_label:
                                        _mp.update(_new_pt)
                            _supa_upsert('map_points', json.dumps(
                                st.session_state.map_points, ensure_ascii=False))
                            st.session_state.pop(_click_key, None)
                            st.success(f"📌 Enregistré : {_pending['x']}% · {_pending['y']}%")
                            st.rerun()
                    with _bc2:
                        if st.button("🗑️ Effacer", key=f"map_clear_{_cur_label}",
                                     use_container_width=True,
                                     disabled=_cur_pt is None):
                            st.session_state.map_points = [
                                p for p in st.session_state.get("map_points", [])
                                if p.get("label") != _cur_label
                            ]
                            _supa_upsert('map_points', json.dumps(
                                st.session_state.map_points, ensure_ascii=False))
                            st.session_state.pop(_click_key, None)
                            st.rerun()

                elif sel_plan and not sel_plan.get("image_b64"):
                    st.markdown(
                        "<div style='background:#fffbeb;border:1px solid #fde047;"
                        "border-radius:8px;padding:12px;text-align:center;"
                        "color:#92400e;font-size:.78rem'>"
                        "⚠️ Ce plan n'a pas d'image. "
                        "Modifiez-le dans <strong>Paramètres → Plans</strong>.</div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        "<div style='background:#f8fafc;border:1px dashed #cbd5e1;"
                        "border-radius:8px;padding:16px;text-align:center;"
                        "color:#94a3b8;font-size:.72rem'>"
                        "Sélectionnez un plan pour afficher la carte</div>",
                        unsafe_allow_html=True)

            # ── Enregistrer le prélèvement ────────────────────────────────────
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("💾 Enregistrer le prélèvement", use_container_width=True,
                         key="save_prelev", type="primary"):
                pid = f"s{len(st.session_state.prelevements)+1}_{int(datetime.now().timestamp())}"
                sample = {
                    "id":                   pid,
                    "label":                selected_point['label'],
                    "type":                 selected_point.get('type'),
                    "gelose":               selected_point.get('gelose','—'),
                    "room_class":           selected_point.get('room_class',''),
                    "location_criticality": pt_loc_crit,
                    "operateur":            p_oper if p_oper else "Non renseigné",
                    "date":                 str(p_date) if p_date else str(today),
                    "archived":             False,
                    "num_isolateur":        p_isolateur if str(pt_room).strip().upper() == "A" else "",
                    "poste":                p_poste     if str(pt_room).strip().upper() == "A" else "",
                    "commentaire":          p_commentaire if p_commentaire else ""
                }
                st.session_state.prelevements.append(sample)
                save_prelevements(st.session_state.prelevements)
                st.session_state.schedules.append({
                    "id": f"sch_{pid}_J2", "sample_id": pid,
                    "label": sample['label'], "due_date": j2_date_calc.isoformat(),
                    "when": "J2", "status": "pending"
                })
                st.session_state.schedules.append({
                    "id": f"sch_{pid}_J7", "sample_id": pid,
                    "label": sample['label'], "due_date": j7_date_calc.isoformat(),
                    "when": "J7", "status": "pending"
                })
                save_schedules(st.session_state.schedules)
                st.success(
                    f"✅ **{sample['label']}** enregistré !\n"
                    f"J2 → {j2_date_calc.strftime('%d/%m/%Y')} | "
                    f"J7 → {j7_date_calc.strftime('%d/%m/%Y')}")

            # ── Liste prélèvements en cours ───────────────────────────────────
            st.divider()
            st.markdown("#### 📋 Prélèvements en cours")
            for idx, samp in enumerate(st.session_state.prelevements):
                if samp.get("archived"):
                    continue
                col_info, col_edit, col_del = st.columns([5, 1, 1])
                with col_info:
                    loc_c    = int(samp.get("location_criticality",1))
                    lc_col_r = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(loc_c),"#94a3b8")
                    room_cl  = samp.get('room_class','') or ''
                    room_badge = (
                        f"<span style='background:#dbeafe;color:#1e40af;border:1px solid #93c5fd;"
                        f"border-radius:4px;padding:1px 6px;font-size:.72rem;font-weight:800;"
                        f"margin-left:4px'>Cl.{room_cl}</span>" if room_cl else "")
                    _comment_html = (
                        f"<div style='font-size:.72rem;color:#6366f1;margin-top:3px'>"
                        f"💬 {samp['commentaire']}</div>" if samp.get('commentaire') else "")
                    st.markdown(
                        f"<div style='background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;"
                        f"padding:10px 16px;margin-bottom:6px'>"
                        f"<span style='font-weight:700'>{samp['label']}</span>{room_badge} "
                        f"<span style='color:#64748b;font-size:.8rem'>— {samp.get('type','—')} "
                        f"· <span style='color:{lc_col_r};font-weight:600'>Nv.{loc_c}</span>"
                        f" · {samp.get('date','—')} · {samp.get('operateur','—')}</span>"
                        f"{_comment_html}</div>",
                        unsafe_allow_html=True)
                with col_edit:
                    if st.button("✏️ Modifier", key=f"edit_prelev_btn_{samp['id']}", use_container_width=True):
                        st.session_state["edit_prelev_id"] = samp["id"]
                        st.rerun()
                with col_del:
                    if st.button("🗑️ Supprimer", key=f"del_prelev_btn_{samp['id']}", use_container_width=True):
                        sid = samp["id"]
                        st.session_state.schedules    = [x for x in st.session_state.schedules    if x.get('sample_id') != sid]
                        st.session_state.prelevements = [x for x in st.session_state.prelevements if x['id'] != sid]
                        st.session_state.pending_identifications = [x for x in st.session_state.pending_identifications if x.get('sample_id') != sid]
                        save_schedules(st.session_state.schedules)
                        save_prelevements(st.session_state.prelevements)
                        save_pending_identifications(st.session_state.pending_identifications)
                        if st.session_state.get("edit_prelev_id") == sid:
                            st.session_state["edit_prelev_id"] = None
                        st.success(f"🗑️ Prélèvement **{samp['label']}** supprimé.")
                        st.rerun()

                if st.session_state.get("edit_prelev_id") == samp["id"]:
                    with st.container():
                        st.markdown(
                            "<div style='background:#eff6ff;border:1.5px solid #93c5fd;"
                            "border-radius:10px;padding:16px;margin-bottom:12px'>",
                            unsafe_allow_html=True)
                        st.markdown(f"**✏️ Modifier — {samp['label']}**")
                        e_col1, e_col2 = st.columns(2)
                        with e_col1:
                            oper_list_e = [
                                o['nom'] + (' — ' + o.get('profession','') if o.get('profession') else '')
                                for o in st.session_state.operators
                            ]
                            current_oper = samp.get("operateur","")
                            if oper_list_e:
                                oper_options = ["— Sélectionner —"] + oper_list_e
                                oper_idx = oper_options.index(current_oper) if current_oper in oper_options else 0
                                new_oper = st.selectbox("Opérateur", oper_options, index=oper_idx, key=f"edit_oper_{samp['id']}")
                                new_oper = new_oper if new_oper != "— Sélectionner —" else ""
                            else:
                                new_oper = st.text_input("Opérateur", value=current_oper, key=f"edit_oper_{samp['id']}")
                            try:
                                current_date = datetime.fromisoformat(samp["date"]).date()
                            except Exception:
                                current_date = datetime.today().date()
                            new_date = st.date_input("Date prélèvement", value=current_date, key=f"edit_date_{samp['id']}")
                        with e_col2:
                            new_gelose      = st.text_input("Gélose", value=samp.get("gelose",""), key=f"edit_gelose_{samp['id']}")
                            new_commentaire = st.text_area("💬 Commentaire", value=samp.get("commentaire",""), height=70, key=f"edit_comment_{samp['id']}")
                            new_isolateur = ""
                            new_poste     = "Poste 1"
                            if str(samp.get("room_class","")).strip().upper() == "A":
                                new_isolateur = st.text_input("Numéro isolateur", value=samp.get("num_isolateur",""), key=f"edit_iso_{samp['id']}")
                                new_poste = st.radio(
                                    "Poste", ["Poste 1","Poste 2","Commun"],
                                    index=["Poste 1","Poste 2","Commun"].index(samp.get("poste","Poste 1"))
                                          if samp.get("poste") in ["Poste 1","Poste 2","Commun"] else 0,
                                    horizontal=True, key=f"edit_poste_{samp['id']}")
                        new_j2 = next_working_day_offset(new_date, 2)
                        new_j7 = next_working_day_offset(new_date, 5)
                        if new_date != current_date:
                            st.markdown(
                                f"<div style='background:#fef9c3;border:1px solid #fde047;border-radius:8px;"
                                f"padding:8px;font-size:.75rem;color:#854d0e;margin-top:4px'>"
                                f"⚠️ Dates recalculées — J2 : <strong>{new_j2.strftime('%d/%m/%Y')}</strong> · "
                                f"J7 : <strong>{new_j7.strftime('%d/%m/%Y')}</strong></div>",
                                unsafe_allow_html=True)
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if st.button("💾 Sauvegarder", key=f"save_edit_{samp['id']}", use_container_width=True, type="primary"):
                                st.session_state.prelevements[idx]["operateur"]   = new_oper
                                st.session_state.prelevements[idx]["date"]        = str(new_date)
                                st.session_state.prelevements[idx]["gelose"]      = new_gelose
                                st.session_state.prelevements[idx]["commentaire"] = new_commentaire
                                if str(samp.get("room_class","")).strip().upper() == "A":
                                    st.session_state.prelevements[idx]["num_isolateur"] = new_isolateur
                                    st.session_state.prelevements[idx]["poste"]         = new_poste
                                if new_date != current_date:
                                    for sch in st.session_state.schedules:
                                        if sch["sample_id"] == samp["id"]:
                                            if sch["when"] == "J2": sch["due_date"] = new_j2.isoformat()
                                            elif sch["when"] == "J7": sch["due_date"] = new_j7.isoformat()
                                    save_schedules(st.session_state.schedules)
                                save_prelevements(st.session_state.prelevements)
                                st.session_state["edit_prelev_id"] = None
                                st.success("✅ Prélèvement mis à jour !")
                                st.rerun()
                        with btn_c2:
                            if st.button("✕ Annuler", key=f"cancel_edit_{samp['id']}", use_container_width=True):
                                st.session_state["edit_prelev_id"] = None
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════
    # ONGLET SCAN QR
    # ══════════════════════════════════════════════════════════════════════════
    with tab_scan:
        st.markdown("### 📷 Création rapide par QR code")

        st.markdown("""
        <div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);border:1.5px solid #93c5fd;
        border-radius:14px;padding:16px 20px;margin-bottom:16px">
          <div style="font-weight:800;color:#1e40af;font-size:.95rem;margin-bottom:8px">
            🔳 Comment utiliser le scan QR
          </div>
          <div style="font-size:.82rem;color:#1e293b;line-height:1.9">
            <strong>1.</strong> Générez les étiquettes PDF depuis <em>Planning → Planning mensuel</em> 🖨️<br>
            <strong>2.</strong> Imprimez-les et collez-les sur vos boîtes de gélose<br>
            <strong>3.</strong> Scannez le QR code avec votre douchette ou utilisez la caméra ci-dessous<br>
            <strong>4.</strong> Le formulaire se pré-remplit — confirmez l'opérateur et enregistrez !
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Panneau scan douchette (input texte) + caméra ──────────────────
        scan_col1, scan_col2 = st.columns([1, 1])

        with scan_col1:
            st.markdown(
                "<div style='background:#fff;border:2px solid #2563eb;border-radius:12px;"
                "padding:16px;text-align:center;margin-bottom:8px'>"
                "<div style='font-size:2rem;margin-bottom:6px'>🔫</div>"
                "<div style='font-weight:800;color:#1e40af;margin-bottom:6px'>Douchette USB</div>"
                "<div style='font-size:.78rem;color:#475569;margin-bottom:10px'>"
                "Cliquez dans le champ ci-dessous, puis scannez l'étiquette.</div>"
                "</div>", unsafe_allow_html=True)

            qr_raw = st.text_input(
                "Zone de scan douchette",
                key="qr_scan_input",
                placeholder='{"app":"URC","label":"..."}  ← scanné automatiquement',
                label_visibility="collapsed",
                help="Le curseur doit être ici quand vous scannez"
            )

        with scan_col2:
            # ── Scan caméra via jsQR ──────────────────────────────────────
            st.markdown(
                "<div style='background:#fff;border:2px solid #7c3aed;border-radius:12px;"
                "padding:16px;text-align:center;margin-bottom:8px'>"
                "<div style='font-size:2rem;margin-bottom:6px'>📷</div>"
                "<div style='font-weight:800;color:#7c3aed;margin-bottom:6px'>Caméra</div>"
                "<div style='font-size:.78rem;color:#475569;margin-bottom:10px'>"
                "Activez la caméra et présentez le QR code.</div>"
                "</div>", unsafe_allow_html=True)

            camera_html = """
<div id="cam-wrap" style="position:relative;background:#0f172a;border-radius:10px;overflow:hidden">
  <video id="video" autoplay muted playsinline
         style="width:100%;max-height:180px;object-fit:cover;display:block"></video>
  <canvas id="canvas" style="display:none"></canvas>
  <div id="overlay" style="position:absolute;inset:0;display:flex;align-items:center;
       justify-content:center;pointer-events:none">
    <div style="width:120px;height:120px;border:3px solid #7c3aed;border-radius:10px;
         box-shadow:0 0 0 2000px rgba(15,23,42,.4)"></div>
  </div>
  <div id="cam-status" style="position:absolute;bottom:6px;left:0;right:0;text-align:center;
       font-size:.65rem;color:#e2e8f0;font-weight:600">En attente d'autorisation…</div>
</div>
<button id="start-btn" onclick="startCam()"
  style="margin-top:8px;width:100%;padding:8px;background:#7c3aed;color:#fff;
         border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.85rem">
  📷 Activer la caméra
</button>
<div id="result-box" style="display:none;margin-top:8px;background:#f0fdf4;
     border:1.5px solid #86efac;border-radius:8px;padding:8px 12px;
     font-size:.75rem;font-weight:700;color:#166534"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jsQR/1.4.0/jsQR.min.js"></script>
<script>
let stream = null;
let scanning = false;
let lastResult = null;

function startCam() {
  document.getElementById('start-btn').style.display = 'none';
  document.getElementById('cam-status').textContent = 'Démarrage…';
  navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}})
    .then(s => {
      stream = s;
      const v = document.getElementById('video');
      v.srcObject = s;
      v.onloadedmetadata = () => { scanning = true; scan(); };
      document.getElementById('cam-status').textContent = '🟢 Scan actif — présentez le QR code';
    })
    .catch(e => {
      document.getElementById('cam-status').textContent = '❌ ' + e.message;
      document.getElementById('start-btn').style.display = 'block';
    });
}

function scan() {
  if (!scanning) return;
  const v = document.getElementById('video');
  const c = document.getElementById('canvas');
  if (v.readyState === v.HAVE_ENOUGH_DATA) {
    c.width = v.videoWidth; c.height = v.videoHeight;
    const ctx = c.getContext('2d');
    ctx.drawImage(v, 0, 0, c.width, c.height);
    const img = ctx.getImageData(0, 0, c.width, c.height);
    const code = jsQR(img.data, img.width, img.height, {inversionAttempts:'dontInvert'});
    if (code && code.data !== lastResult) {
      lastResult = code.data;
      try {
        const d = JSON.parse(code.data);
        if (d.app === 'URC') {
          scanning = false;
          if (stream) stream.getTracks().forEach(t => t.stop());
          const box = document.getElementById('result-box');
          box.style.display = 'block';
          box.innerHTML = '✅ Scanné : <b>' + (d.label || '?') + '</b> — ' + (d.rc || '?');
          document.getElementById('cam-status').textContent = '✅ QR code détecté !';
          // Envoyer vers Streamlit via l'input texte caché
          const ev = new CustomEvent('qr-scanned', {detail: code.data});
          window.parent.document.dispatchEvent(ev);
          // Stratégie : copier dans le clipboard → l'utilisateur peut coller dans la douchette
          if (navigator.clipboard) {
            navigator.clipboard.writeText(code.data).catch(()=>{});
          }
          // Afficher un bouton pour copier manuellement
          box.innerHTML += '<br><button onclick="navigator.clipboard.writeText(' +
            JSON.stringify(JSON.stringify(code.data)) + ').then(()=>alert(' +
            "'Copié ! Collez maintenant dans le champ Douchette.'" + '))" ' +
            'style="margin-top:6px;padding:4px 10px;background:#2563eb;color:#fff;' +
            'border:none;border-radius:6px;cursor:pointer;font-size:.72rem">' +
            '📋 Copier &amp; coller dans Douchette</button>';
        }
      } catch(e) {}
    }
  }
  requestAnimationFrame(scan);
}
</script>"""
            st.components.v1.html(camera_html, height=320, scrolling=False)

        # ── Traitement du scan douchette ───────────────────────────────────
        _scanned_data = None
        if qr_raw and qr_raw.strip().startswith("{"):
            try:
                _scanned_data = json.loads(qr_raw.strip())
            except Exception:
                st.error("❌ QR code non reconnu — format JSON invalide.")

        if _scanned_data and _scanned_data.get("app") == "URC":
            _lbl    = _scanned_data.get("label", "")
            _type   = _scanned_data.get("type", "")
            _rc     = _scanned_data.get("rc", "")
            _lc     = int(_scanned_data.get("lc", 1))
            _gel    = _scanned_data.get("gel", "")
            _pt_ref = next(
                (p for p in st.session_state.points if p.get("label") == _lbl),
                None)
            lc_col_s = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(_lc),"#94a3b8")

            st.markdown(
                f"<div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);"
                f"border:2.5px solid #22c55e;border-radius:14px;padding:18px 22px;margin:12px 0'>"
                f"<div style='font-size:1.1rem;font-weight:900;color:#166534;margin-bottom:10px'>"
                f"✅ QR code reconnu — {_lbl}</div>"
                f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px'>"
                f"<div style='background:#fff;border-radius:8px;padding:8px;text-align:center;border:1px solid #86efac'>"
                f"<div style='font-size:.58rem;color:#64748b;text-transform:uppercase'>Type</div>"
                f"<div style='font-size:.85rem;font-weight:700'>{'💨' if _type=='Air' else '🧴'} {_type}</div></div>"
                f"<div style='background:#dbeafe;border-radius:8px;padding:8px;text-align:center;border:1px solid #93c5fd'>"
                f"<div style='font-size:.58rem;color:#1e40af;text-transform:uppercase'>Classe</div>"
                f"<div style='font-size:.85rem;font-weight:800;color:#1e40af'>{_rc or '—'}</div></div>"
                f"<div style='background:{lc_col_s}11;border-radius:8px;padding:8px;text-align:center;border:1px solid {lc_col_s}44'>"
                f"<div style='font-size:.58rem;color:#64748b;text-transform:uppercase'>Criticité</div>"
                f"<div style='font-size:.85rem;font-weight:700;color:{lc_col_s}'>Nv.{_lc}</div></div>"
                f"<div style='background:#fff;border-radius:8px;padding:8px;text-align:center;border:1px solid #86efac'>"
                f"<div style='font-size:.58rem;color:#64748b;text-transform:uppercase'>Gélose</div>"
                f"<div style='font-size:.85rem;font-weight:700;color:#1d4ed8'>🧫 {_gel[:12]}</div></div>"
                f"</div></div>",
                unsafe_allow_html=True)

            # ── Mini-formulaire de confirmation ────────────────────────────
            st.markdown(
                "<div style='background:#fff;border:1.5px solid #e2e8f0;border-radius:12px;"
                "padding:16px;margin-top:8px'>",
                unsafe_allow_html=True)
            st.markdown("#### ✏️ Confirmer et enregistrer le prélèvement")

            sf1, sf2 = st.columns(2)
            with sf1:
                oper_list_s = [
                    o['nom'] + (' — ' + o.get('profession','') if o.get('profession') else '')
                    for o in st.session_state.operators
                ]
                if oper_list_s:
                    scan_oper = st.selectbox(
                        "👤 Opérateur / Préleveur *",
                        ["— Sélectionner —"] + oper_list_s,
                        key="scan_oper_sel")
                    scan_oper = scan_oper if scan_oper != "— Sélectionner —" else ""
                else:
                    scan_oper = st.text_input(
                        "👤 Opérateur *",
                        placeholder="Nom du préleveur",
                        key="scan_oper_manual")
                scan_date = st.date_input(
                    "📅 Date de prélèvement",
                    value=datetime.today(),
                    key="scan_date")
            with sf2:
                scan_comment = st.text_area(
                    "💬 Commentaire",
                    placeholder="Remarques, contexte…",
                    height=80,
                    key="scan_comment")
                _scan_j2 = next_working_day_offset(scan_date, 2)
                _scan_j7 = next_working_day_offset(scan_date, 5)
                st.markdown(
                    f"<div style='background:#f0fdf4;border:1px solid #86efac;border-radius:8px;"
                    f"padding:8px;font-size:.72rem;color:#166534;margin-top:4px'>"
                    f"📅 J2 → <strong>{_scan_j2.strftime('%d/%m/%Y')}</strong><br>"
                    f"📅 J7 → <strong>{_scan_j7.strftime('%d/%m/%Y')}</strong></div>",
                    unsafe_allow_html=True)

            # ── Localisation sur plan (optionnel) ──────────────────────────
            from streamlit_image_coordinates import streamlit_image_coordinates

            plans_avail_scan = st.session_state.get("plans", [])
            coords = None  # important

            if plans_avail_scan:
                st.markdown(
                    "<div style='font-size:.75rem;font-weight:700;color:#475569;margin:8px 0 4px'>"
                    "🗺️ Localiser sur le plan <span style='font-weight:400;font-style:italic'>(optionnel)</span></div>",
                    unsafe_allow_html=True
                )

                _scan_plan_names = ["— Aucun plan —"] + [p["name"] for p in plans_avail_scan]
                _scan_plan_sel = st.selectbox("Plan", _scan_plan_names, key="scan_plan_sel")

                if _scan_plan_sel != "— Aucun plan —":
                    _scan_plan = next((p for p in plans_avail_scan if p["name"] == _scan_plan_sel), None)

                    if _scan_plan and _scan_plan.get("image_b64"):

                        # 📍 CLIC SUR IMAGE
                        coords = streamlit_image_coordinates(
                            _scan_plan["image_b64"],
                            key="scan_coords"
                        )

                        # 📌 Position existante
                        _cur_pt_scan = next(
                            (mp for mp in st.session_state.get("map_points", [])
                            if mp.get("label") == _lbl),
                            None
                        )

                        if _cur_pt_scan and isinstance(_cur_pt_scan.get("x"), (int, float)):
                            st.markdown(
                                f"<div style='background:#f0fdf4;border:1.5px solid #86efac;"
                                f"border-radius:8px;padding:8px 14px;font-size:.8rem;"
                                f"color:#166534;font-weight:700'>"
                                f"📌 Position existante : {float(_cur_pt_scan['x']):.1f}% · "
                                f"{float(_cur_pt_scan['y']):.1f}%</div>",
                                unsafe_allow_html=True
                            )

                        # 📍 Nouvelle position cliquée
                        if coords:
                            x = coords["x"]
                            y = coords["y"]
                            st.success(f"📍 Nouvelle position : {x:.1f}% · {y:.1f}%")

                    else:
                        st.warning("⚠️ Plan sans image.")

                # ── Bouton d'enregistrement ────────────────────────────────────
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                scan_bc1, scan_bc2 = st.columns([3, 1])
                with scan_bc1:
                    if st.button(
                        f"💾 Créer le prélèvement — {_lbl}",
                        use_container_width=True,
                        type="primary",
                        key="scan_save_btn"
                    ):
                        if not scan_oper:
                            st.error("⚠️ Veuillez sélectionner un opérateur.")
                        else:
                            _pid = f"s{len(st.session_state.prelevements)+1}_{int(datetime.now().timestamp())}"
                            _sample_scan = {
                                "id":                   _pid,
                                "label":                _lbl,
                                "type":                 _type,
                                "gelose":               _gel,
                                "room_class":           _rc,
                                "location_criticality": _lc,
                                "operateur":            scan_oper,
                                "date":                 str(scan_date),
                                "archived":             False,
                                "num_isolateur":        "",
                                "poste":                "Poste 1",
                                "commentaire":          scan_comment or "",
                                "created_via":          "qr_scan",
                            }
                            # ── Sauvegarde position ─────────────────────────────
                            if coords:
                                new_point = {
                                    "label": _lbl,
                                    "x": coords["x"],
                                    "y": coords["y"]
                                }

                                # remplace si déjà existant
                                st.session_state["map_points"] = [
                                    mp for mp in st.session_state.get("map_points", [])
                                    if mp.get("label") != _lbl
                                ] + [new_point]

                                # sauvegarde persistante
                                try:
                                    _supa_upsert("map_points", json.dumps(st.session_state["map_points"], ensure_ascii=False))
                                except Exception:
                                    pass
                            st.session_state.prelevements.append(_sample_scan)
                            save_prelevements(st.session_state.prelevements)
                            st.session_state.schedules.append({
                                "id":        f"sch_{_pid}_J2",
                                "sample_id": _pid,
                                "label":     _lbl,
                                "due_date":  _scan_j2.isoformat(),
                                "when":      "J2",
                                "status":    "pending"
                            })
                            st.session_state.schedules.append({
                                "id":        f"sch_{_pid}_J7",
                                "sample_id": _pid,
                                "label":     _lbl,
                                "due_date":  _scan_j7.isoformat(),
                                "when":      "J7",
                                "status":    "pending"
                            })
                            save_schedules(st.session_state.schedules)
                            # Vider le champ de scan
                            st.session_state["qr_scan_input"] = ""
                            st.success(
                                f"✅ **{_lbl}** créé par scan QR !\n"
                                f"J2 → {_scan_j2.strftime('%d/%m/%Y')} | "
                                f"J7 → {_scan_j7.strftime('%d/%m/%Y')}")
                            st.rerun()
                with scan_bc2:
                    if st.button("✕ Annuler", use_container_width=True, key="scan_cancel_btn"):
                        st.session_state["qr_scan_input"] = ""
                        st.rerun()

            elif qr_raw and qr_raw.strip():
                st.warning("⚠️ Ce QR code ne provient pas de MicroSurveillance URC.")

        # ── Historique des derniers scans ──────────────────────────────────
        _scan_recent = [
            p for p in st.session_state.prelevements
            if p.get("created_via") == "qr_scan" and not p.get("archived")
        ]
        if _scan_recent:
            st.divider()
            st.markdown(
                f"<div style='font-size:.85rem;font-weight:700;color:#1e40af;margin-bottom:8px'>"
                f"🔳 {len(_scan_recent)} prélèvement(s) créé(s) par scan QR (en cours)</div>",
                unsafe_allow_html=True)
            for _sp in reversed(_scan_recent[-5:]):
                lc_s = int(_sp.get("location_criticality", 1))
                lcs_col = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(lc_s),"#94a3b8")
                st.markdown(
                    f"<div style='background:#f8fafc;border-left:3px solid #2563eb;"
                    f"border-radius:8px;padding:8px 14px;margin-bottom:4px;font-size:.78rem'>"
                    f"<span style='font-weight:700'>🔳 {_sp['label']}</span>"
                    f" · Classe {_sp.get('room_class','—')}"
                    f" · <span style='color:{lcs_col}'>Nv.{lc_s}</span>"
                    f" · {_sp.get('date','—')}"
                    f" · {_sp.get('operateur','—')}"
                    f"</div>",
                    unsafe_allow_html=True)
    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS PARTAGÉS
    # ══════════════════════════════════════════════════════════════════════════
    def _render_lecture_card(s, tab_prefix=""):
        sched_date  = datetime.fromisoformat(s["due_date"]).date()
        is_late     = sched_date <= today
        border_col  = "#ef4444" if is_late else "#3b82f6"
        bg_col      = "#fef2f2" if is_late else "#eff6ff"
        badge_col   = "#dc2626" if is_late else "#1d4ed8"
        status_txt  = "EN RETARD" if is_late else f"dans {(sched_date - today).days}j"
        smp         = next((p for p in st.session_state.prelevements if p['id'] == s['sample_id']), None)
        pt_type     = smp.get('type','?')      if smp else '?'
        pt_gelose   = smp.get('gelose','?')    if smp else '?'
        pt_oper     = smp.get('operateur','?') if smp else '?'
        pt_room_cl  = smp.get('room_class','') if smp else ''
        loc_crit    = _get_location_criticality(smp) if smp else 1
        lc_col_s    = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(loc_crit),"#94a3b8")
        lc_lbl_s    = _loc_crit_label(loc_crit)
        room_cl_badge = (
            f"<span style='background:#dbeafe;color:#1e40af;border:1px solid #93c5fd;"
            f"border-radius:4px;padding:1px 6px;font-size:.62rem;font-weight:800;"
            f"margin-left:6px'>Cl.{pt_room_cl}</span>" if pt_room_cl else "")
        extra_info = ""
        if smp and str(smp.get("room_class","")).strip().upper() == "A":
            iso = smp.get("num_isolateur","—") or "—"
            pst = smp.get("poste","—") or "—"
            extra_info = (
                f"<div style='background:#fef9c3;border-radius:6px;padding:6px 8px;"
                f"border:1px solid #fde047;font-size:.7rem;color:#854d0e;"
                f"font-weight:600;margin-top:6px'>"
                f"🔬 Classe A · Isolateur : {iso} · {pst}</div>")
        with st.container():
            st.markdown(f"""
            <div style="background:{bg_col};border:1.5px solid {border_col};border-radius:10px;
            padding:14px 16px;margin-bottom:8px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                <div>
                  <span style="font-weight:700;font-size:.9rem;color:#0f172a">{s['label']}</span>
                  {room_cl_badge}
                  <span style="background:{border_col};color:#fff;font-size:.6rem;font-weight:700;
                  padding:2px 8px;border-radius:10px;margin-left:8px">{s['when']}</span>
                  <span style="color:{badge_col};font-size:.65rem;font-weight:600;margin-left:6px">{status_txt}</span>
                </div>
                <span style="font-size:.75rem;color:#475569">📅 {s['due_date'][:10]}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px">
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Type</div>
                  <div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_type}</div>
                </div>
                <div style="background:#dbeafe;border-radius:6px;padding:6px 8px;border:1px solid #93c5fd">
                  <div style="font-size:.55rem;color:#1e40af;text-transform:uppercase">Classe</div>
                  <div style="font-size:.75rem;font-weight:800;color:#1e40af">{pt_room_cl or '—'}</div>
                </div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Gélose</div>
                  <div style="font-size:.75rem;font-weight:600;color:#1d4ed8">🧫 {pt_gelose}</div>
                </div>
                <div style="background:{lc_col_s}11;border-radius:6px;padding:6px 8px;border:1px solid {lc_col_s}44">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Criticité lieu</div>
                  <div style="font-size:.75rem;font-weight:600;color:{lc_col_s}">Nv.{loc_crit} — {lc_lbl_s}</div>
                </div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Opérateur</div>
                  <div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_oper}</div>
                </div>
              </div>
              {extra_info}
            </div>""", unsafe_allow_html=True)
            bc1, bc2 = st.columns([3, 1])
            with bc1:
                if st.button(f"🔬 Traiter cette lecture ({s['when']})", key=f"{tab_prefix}proc_{s['id']}", use_container_width=True):
                    st.session_state.current_process = s['id']
                    st.rerun()
            with bc2:
                if st.button("🗑️ Supprimer", key=f"{tab_prefix}del_sch_{s['id']}", use_container_width=True):
                    sid = s.get('sample_id')
                    st.session_state.schedules    = [x for x in st.session_state.schedules    if x['sample_id'] != sid]
                    st.session_state.prelevements = [x for x in st.session_state.prelevements if x['id'] != sid]
                    st.session_state.pending_identifications = [x for x in st.session_state.pending_identifications if x.get('sample_id') != sid]
                    save_schedules(st.session_state.schedules)
                    save_prelevements(st.session_state.prelevements)
                    save_pending_identifications(st.session_state.pending_identifications)
                    st.success("Prélèvement, lectures et identifications supprimés.")
                    st.rerun()

    def _render_traitement_lecture(proc_id):
        proc = next((x for x in st.session_state.schedules if x['id'] == proc_id), None)
        if not proc:
            return
        smp       = next((p for p in st.session_state.prelevements if p['id'] == proc['sample_id']), None)
        pt_type   = smp.get('type','?')      if smp else '?'
        pt_gelose = smp.get('gelose','?')    if smp else '?'
        pt_oper   = smp.get('operateur','?') if smp else '?'
        pt_date   = smp.get('date','?')      if smp else '?'
        pt_room_p = smp.get('room_class','') if smp else ''
        loc_crit  = _get_location_criticality(smp) if smp else 1
        lc_col_p  = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(loc_crit),"#94a3b8")
        classea_band = ""
        if smp and str(smp.get("room_class","")).strip().upper() == "A":
            iso = smp.get("num_isolateur","—") or "—"
            pst = smp.get("poste","—") or "—"
            classea_band = (
                f"<div style='background:#fef9c3;border:1px solid #fde047;"
                f"border-radius:8px;padding:8px 12px;margin-top:10px;"
                f"font-size:.75rem;font-weight:700;color:#854d0e'>"
                f"🔬 Classe A · Isolateur : {iso} · {pst}</div>")
        st.markdown("---")
        st.markdown(f"""
        <div style="background:#f8fafc;border:2px solid #2563eb;border-radius:12px;
        padding:16px;margin-bottom:16px">
          <div style="font-size:1rem;font-weight:700;color:#1e40af;margin-bottom:12px">
            🔬 Traitement lecture —
            <span style="font-style:italic">{proc['label']}</span>
            <span style="background:#2563eb;color:#fff;font-size:.65rem;font-weight:700;
            padding:3px 10px;border-radius:10px;margin-left:8px">{proc['when']}</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px">
            <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
              <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Type</div>
              <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">
                {'💨' if pt_type=='Air' else '🧴'} {pt_type}
              </div>
            </div>
            <div style="background:#dbeafe;border-radius:8px;padding:10px;text-align:center;border:1px solid #93c5fd">
              <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Classe</div>
              <div style="font-size:.85rem;font-weight:800;color:#1e40af;margin-top:3px">{pt_room_p or '—'}</div>
            </div>
            <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
              <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Gélose</div>
              <div style="font-size:.85rem;font-weight:700;color:#1d4ed8;margin-top:3px">🧫 {pt_gelose}</div>
            </div>
            <div style="background:{lc_col_p}11;border-radius:8px;padding:10px;text-align:center;border:1px solid {lc_col_p}44">
              <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Criticité lieu</div>
              <div style="font-size:.85rem;font-weight:700;color:{lc_col_p};margin-top:3px">Nv.{loc_crit}</div>
            </div>
            <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
              <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Opérateur</div>
              <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_oper}</div>
            </div>
            <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
              <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Date prélèv.</div>
              <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_date}</div>
            </div>
          </div>
          {classea_band}
        </div>""", unsafe_allow_html=True)
        lc1, lc2 = st.columns([2, 2])
        with lc1:
            res = st.radio(
                "Résultat",
                ["✅ Négatif (0 colonie)", "🔴 Positif (colonies détectées)"],
                index=0, key=f"res_{proc_id}")
        with lc2:
            ncol = (st.number_input("Nombre de colonies (UFC)", min_value=1, value=1, key=f"ncol_{proc_id}")
                    if "Positif" in res else 0)
        vc1, vc2 = st.columns(2)
        with vc1:
            if st.button("✅ Valider la lecture", use_container_width=True, key=f"submit_proc_{proc_id}"):
                proc['status'] = 'done'
                save_schedules(st.session_state.schedules)
                if "Négatif" in res:
                    j7_sch = next((x for x in st.session_state.schedules
                        if x['sample_id'] == proc['sample_id'] and x['when'] == 'J7' and x['status'] == 'pending'), None)
                    if proc['when'] == 'J7' or (proc['when'] == 'J2' and not j7_sch):
                        if smp:
                            smp['archived'] = True
                            st.session_state.archived_samples.append(smp)
                            save_archived_samples(st.session_state.archived_samples)
                            save_prelevements(st.session_state.prelevements)
                        st.success("✅ Lecture négative — prélèvement archivé.")
                    else:
                        st.success(f"✅ J2 négative — en attente J7 ({j7_sch['due_date'][:10] if j7_sch else '?'}).")
                    st.session_state.surveillance.append({
                        "date": str(today), "prelevement": proc['label'],
                        "sample_id": proc.get('sample_id',''),
                        "germ_saisi": "", "germ_match": "Négatif", "match_score": "—",
                        "ufc": 0, "germ_score": 0, "location_criticality": loc_crit,
                        "total_score": 0, "risk": 0,
                        "room_class": smp.get('room_class','') if smp else '',
                        "alert_threshold": "Score ≥ 24", "action_threshold": "Score > 36",
                        "triggered_by": None, "status": "ok",
                        "operateur": pt_oper,
                        "remarque": f"Lecture {proc['when']} négative"
                    })
                    save_surveillance(st.session_state.surveillance)
                else:
                    st.session_state.pending_identifications.append({
                        "sample_id": proc['sample_id'], "label": proc['label'],
                        "when": proc['when'], "colonies": int(ncol),
                        "date": str(today), "status": "pending"
                    })
                    save_pending_identifications(st.session_state.pending_identifications)
                    if proc['when'] == 'J2':
                        j7_sch = next((x for x in st.session_state.schedules
                            if x['sample_id'] == proc['sample_id'] and x['when'] == 'J7'), None)
                        if j7_sch:
                            j7_sch['status'] = 'skipped'
                            save_schedules(st.session_state.schedules)
                        st.success(f"🔴 J2 positive ({ncol} UFC) — identification requise.")
                    else:
                        st.success(f"🔴 J7 positive ({ncol} UFC) — identification requise.")
                st.session_state.current_process = None
                st.rerun()
        with vc2:
            if st.button("↩️ Annuler / Retour", use_container_width=True, key=f"cancel_proc_{proc_id}"):
                st.session_state.current_process = None
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — LECTURE J2
    # ══════════════════════════════════════════════════════════════════════════
    with tab_j2:
        st.markdown("#### 📖 Lectures J2 en attente")
        _active_sids = {p['id'] for p in st.session_state.prelevements if not p.get("archived")}
        pending_j2  = [s for s in st.session_state.schedules
                       if s["when"] == "J2" and s["status"] == "pending"
                       and s.get("sample_id") in _active_sids]
        overdue_j2  = [s for s in pending_j2 if datetime.fromisoformat(s["due_date"]).date() <= today]
        upcoming_j2 = [s for s in pending_j2 if datetime.fromisoformat(s["due_date"]).date() > today]

        if not pending_j2:
            st.success("✅ Aucune lecture J2 en attente — tout est à jour !")
        else:
            if overdue_j2:
                st.markdown(
                    f'<div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;'
                    f'padding:12px 16px;margin-bottom:12px"><span style="color:#dc2626;font-weight:700">'
                    f'🔔 {len(overdue_j2)} lecture(s) J2 en retard — à traiter dès que possible</span></div>',
                    unsafe_allow_html=True)
            if upcoming_j2:
                st.markdown(
                    f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;'
                    f'padding:10px 16px;margin-bottom:12px"><span style="color:#16a34a;font-size:.8rem">'
                    f'📆 {len(upcoming_j2)} lecture(s) J2 à venir</span></div>',
                    unsafe_allow_html=True)
            for s in overdue_j2 + upcoming_j2:
                _render_lecture_card(s)

        if st.session_state.current_process:
            proc_check = next((x for x in st.session_state.schedules
                               if x['id'] == st.session_state.current_process
                               and x['when'] == 'J2'), None)
            if proc_check:
                _render_traitement_lecture(st.session_state.current_process)

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 3 — LECTURE J7
    # ══════════════════════════════════════════════════════════════════════════
    with tab_j7:
        st.markdown("#### 📗 Lectures J7 en attente")
        _active_sids_j7 = {p['id'] for p in st.session_state.prelevements if not p.get("archived")}

        def _j2_done_for(sample_id):
            j2 = next((x for x in st.session_state.schedules
                        if x['sample_id'] == sample_id and x['when'] == 'J2'), None)
            return j2 is None or j2['status'] == 'done'

        pending_j7  = [s for s in st.session_state.schedules
                       if s["when"] == "J7" and s["status"] == "pending"
                       and s.get("sample_id") in _active_sids_j7
                       and _j2_done_for(s["sample_id"])]
        overdue_j7  = [s for s in pending_j7 if datetime.fromisoformat(s["due_date"]).date() <= today]
        upcoming_j7 = [s for s in pending_j7 if datetime.fromisoformat(s["due_date"]).date() > today]

        if not pending_j7:
            st.success("✅ Aucune lecture J7 en attente — tout est à jour !")
        else:
            if overdue_j7:
                st.markdown(
                    f'<div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;'
                    f'padding:12px 16px;margin-bottom:12px"><span style="color:#dc2626;font-weight:700">'
                    f'🔔 {len(overdue_j7)} lecture(s) J7 en retard — à traiter dès que possible</span></div>',
                    unsafe_allow_html=True)
            if upcoming_j7:
                st.markdown(
                    f'<div style="background:#eff6ff;border:1px solid #93c5fd;border-radius:10px;'
                    f'padding:10px 16px;margin-bottom:12px"><span style="color:#1d4ed8;font-size:.8rem">'
                    f'📆 {len(upcoming_j7)} lecture(s) J7 à venir</span></div>',
                    unsafe_allow_html=True)
            for s in overdue_j7 + upcoming_j7:
                _render_lecture_card(s)

        if st.session_state.current_process:
            proc_check = next((x for x in st.session_state.schedules
                               if x['id'] == st.session_state.current_process
                               and x['when'] == 'J7'), None)
            if proc_check:
                _render_traitement_lecture(st.session_state.current_process)

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 4 — IDENTIFICATIONS EN ATTENTE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_ident:
        def _render_alerte_mesures(pop_data, key_suffix):
            _is_action   = pop_data["status"] == "action"
            _border      = "#ef4444" if _is_action else "#f59e0b"
            _bg_head     = "#fef2f2" if _is_action else "#fffbeb"
            _hd_col      = "#991b1b" if _is_action else "#92400e"
            _ic          = "🚨" if _is_action else "⚠️"
            _txt         = "ACTION REQUISE" if _is_action else "ALERTE"
            _germ_sc     = pop_data.get("germ_score","—")
            _loc_c       = pop_data.get("loc_criticality","—")
            _total       = pop_data.get("total_score","—")
            type_colors  = {"action":"#ef4444","alert":"#f59e0b","both":"#818cf8"}
            type_labels  = {"action":"🚨 Action","alert":"⚠️ Alerte","both":"⚠️🚨 Les deux"}

            def _match(m):
                if pop_data["status"]=="alert"  and m.get("type") not in ("alert","both"):  return False
                if pop_data["status"]=="action" and m.get("type") not in ("action","both"): return False
                mr = m.get("risk","all")
                if mr != "all":
                    gr = pop_data.get("risk",1)
                    if isinstance(mr, list): return gr in mr
                    return mr == gr
                return True

            mesures = [m for m in st.session_state.origin_measures if _match(m)]

            st.markdown(f"""
            <div style="border:2.5px solid {_border};border-radius:14px;overflow:hidden;
                        margin-top:16px;margin-bottom:4px;box-shadow:0 4px 20px {_border}33">
              <div style="background:{_bg_head};padding:16px 20px;border-bottom:1.5px solid {_border}44">
                <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
                  <span style="font-size:2rem;line-height:1">{_ic}</span>
                  <div style="flex:1">
                    <div style="font-size:1.05rem;font-weight:900;color:{_hd_col}">
                      {_txt} — {pop_data['label']}
                    </div>
                    <div style="font-size:.78rem;color:#475569;margin-top:4px;line-height:1.8">
                      <strong>{pop_data['ufc']} UFC</strong>
                      &nbsp;·&nbsp; Germe : <em>{pop_data['germ']}</em>
                      &nbsp;·&nbsp; Lieu Nv.{_loc_c} ({_loc_crit_label(int(_loc_c)) if str(_loc_c).isdigit() else _loc_c})
                    </div>
                  </div>
                  <div style="background:#fff;border:2px solid {_border}55;border-radius:12px;
                  padding:12px 18px;text-align:center;min-width:130px">
                    <div style="font-size:.58rem;color:#475569;text-transform:uppercase;font-weight:700">Score total</div>
                    <div style="font-size:2.2rem;font-weight:900;color:{_border};line-height:1.1">{_total}</div>
                    <div style="font-size:.6rem;color:#64748b;margin-top:2px">Lieu {_loc_c} × Germe {_germ_sc}</div>
                    <div style="font-size:.62rem;font-weight:700;color:{_hd_col};margin-top:4px">
                      {'Seuil action (> 36)' if _is_action else 'Seuil alerte (24–36)'}
                    </div>
                  </div>
                </div>
              </div>
              <div style="background:#fff;padding:14px 20px 6px 20px">
                <div style="font-size:.82rem;font-weight:800;color:{_hd_col};margin-bottom:10px">
                  📋 Mesures correctives applicables
                </div>""", unsafe_allow_html=True)

            if mesures:
                for _m in mesures:
                    _tc = type_colors.get(_m["type"],"#94a3b8")
                    _tl = type_labels.get(_m["type"],_m["type"])
                    st.markdown(
                        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                        f"border-left:4px solid {_tc};border-radius:0 8px 8px 0;"
                        f"padding:10px 14px;margin-bottom:7px;display:flex;"
                        f"align-items:center;justify-content:space-between;gap:12px'>"
                        f"<div style='font-size:.83rem;color:#0f172a;line-height:1.5;flex:1'>"
                        f"<span style='color:{_tc};font-weight:700;margin-right:6px'>▸</span>{_m['text']}</div>"
                        f"<span style='background:{_tc}18;color:{_tc};border:1.5px solid {_tc}66;"
                        f"border-radius:6px;padding:3px 9px;font-size:.65rem;font-weight:800;"
                        f"white-space:nowrap;flex-shrink:0'>{_tl}</span></div>",
                        unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div style='font-size:.8rem;color:#94a3b8;font-style:italic;padding:6px 0 10px'>"
                    "Aucune mesure corrective configurée — ajoutez-en dans "
                    "<strong>Paramètres → Mesures correctives</strong>.</div>",
                    unsafe_allow_html=True)

            st.markdown("<div style='height:4px'></div></div></div>", unsafe_allow_html=True)

            _b1, _b2, _b3 = st.columns([3, 2, 1])
            with _b1:
                if st.button("✅ Compris — Mesures prises en charge",
                             use_container_width=True, type="primary",
                             key=f"alert_ok_{key_suffix}"):
                    st.session_state["_last_mesures_popup"] = pop_data
                    st.session_state["_show_mesures_popup"] = None
                    st.rerun()
            with _b2:
                if st.button("🖨️ Imprimer / noter", use_container_width=True, key=f"alert_print_{key_suffix}"):
                    st.session_state["_last_mesures_popup"] = pop_data
                    st.session_state["_show_mesures_popup"] = None
                    st.rerun()
            with _b3:
                if st.button("✕ Ignorer", use_container_width=True, key=f"alert_dismiss_{key_suffix}"):
                    st.session_state["_show_mesures_popup"] = None
                    st.rerun()

        if st.session_state.get("_show_mesures_popup"):
            _render_alerte_mesures(st.session_state["_show_mesures_popup"], "main")

        if not st.session_state.get("_show_mesures_popup") and st.session_state.get("_last_mesures_popup"):
            _last      = st.session_state["_last_mesures_popup"]
            _is_action = _last["status"] == "action"
            _sc  = "#ef4444" if _is_action else "#f59e0b"
            _ic  = "🚨" if _is_action else "⚠️"
            _txt = "ACTION REQUISE" if _is_action else "ALERTE"
            with st.expander(
                f"{_ic} Récapitulatif — {_txt} · {_last['label']} · Score {_last.get('total_score','—')}",
                expanded=False):
                def _match_last(m):
                    if _last["status"]=="alert"  and m.get("type") not in ("alert","both"):  return False
                    if _last["status"]=="action" and m.get("type") not in ("action","both"): return False
                    mr = m.get("risk","all")
                    if mr != "all":
                        gr = _last.get("risk",1)
                        if isinstance(mr, list): return gr in mr
                        return mr == gr
                    return True
                _mes_last     = [m for m in st.session_state.origin_measures if _match_last(m)]
                type_colors_l = {"action":"#ef4444","alert":"#f59e0b","both":"#818cf8"}
                type_labels_l = {"action":"🚨 Action","alert":"⚠️ Alerte","both":"⚠️🚨 Les deux"}
                st.markdown(
                    f"<div style='font-size:.8rem;color:{_sc};font-weight:700;margin-bottom:8px'>"
                    f"📋 {_last.get('germ','—')} · Lieu Nv.{_last.get('loc_criticality','—')} "
                    f"× Germe {_last.get('germ_score','—')} = Score {_last.get('total_score','—')}</div>",
                    unsafe_allow_html=True)
                if _mes_last:
                    for _m in _mes_last:
                        _tc = type_colors_l.get(_m["type"],"#94a3b8")
                        _tl = type_labels_l.get(_m["type"],_m["type"])
                        st.markdown(
                            f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                            f"border-left:4px solid {_tc};border-radius:0 8px 8px 0;"
                            f"padding:8px 12px;margin-bottom:6px;display:flex;"
                            f"align-items:center;justify-content:space-between;gap:10px'>"
                            f"<div style='font-size:.8rem;color:#0f172a;flex:1'>"
                            f"<span style='color:{_tc};font-weight:700;margin-right:6px'>▸</span>{_m['text']}</div>"
                            f"<span style='background:{_tc}18;color:{_tc};border:1.5px solid {_tc}66;"
                            f"border-radius:6px;padding:2px 8px;font-size:.63rem;font-weight:800;"
                            f"white-space:nowrap'>{_tl}</span></div>",
                            unsafe_allow_html=True)
                else:
                    st.caption("Aucune mesure corrective configurée.")
                if st.button("✕ Effacer ce récapitulatif", key="dismiss_last_mesures"):
                    st.session_state["_last_mesures_popup"] = None
                    st.rerun()

        st.markdown("#### 🔴 Identifications en attente")

        def _j7_done_or_absent(sample_id):
            j7 = next((x for x in st.session_state.schedules
                        if x['sample_id'] == sample_id and x['when'] == 'J7'), None)
            return j7 is None or j7['status'] in ('done','skipped')

        _all_pending = [
            p for p in st.session_state.pending_identifications
            if p.get('status') == 'pending' and _j7_done_or_absent(p['sample_id'])
        ]
        _seen_sids = {}
        for _p in _all_pending:
            _sid = _p['sample_id']
            if _sid not in _seen_sids:
                _seen_sids[_sid] = {
                    "sample_id": _sid, "label": _p['label'],
                    "date": _p['date'], "entries": [], "when_list": [], "colonies": 0,
                }
            _seen_sids[_sid]["entries"].append(_p)
            _seen_sids[_sid]["when_list"].append(_p['when'])
            if _p['when'] == 'J7' or _seen_sids[_sid]["colonies"] == 0:
                _seen_sids[_sid]["colonies"] = _p['colonies']
        pending_ids_grouped = list(_seen_sids.values())

        if not pending_ids_grouped:
            st.success("✅ Aucune identification en attente.")
        else:
            germ_names = sorted([g['name'] for g in st.session_state.germs])

            for pg in pending_ids_grouped:
                _sid      = pg["sample_id"]
                _entries  = pg["entries"]
                _when_str = " + ".join(sorted(set(pg["when_list"])))
                _ufc      = pg["colonies"]
                _label    = pg["label"]
                _date     = pg["date"]
                smp       = next((p for p in st.session_state.prelevements if p['id'] == _sid), None)
                pt_oper   = smp.get('operateur','?') if smp else '?'
                loc_crit  = _get_location_criticality(smp) if smp else 1
                lc_col_id = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(loc_crit),"#94a3b8")
                pt_class  = smp.get('room_class','') if smp else ''

                real_indices = [
                    st.session_state.pending_identifications.index(e)
                    for e in _entries
                    if e in st.session_state.pending_identifications
                ]
                _key = _sid.replace("-","_")

                germs_list_key = f"germs_list_{_key}"
                if germs_list_key not in st.session_state:
                    st.session_state[germs_list_key] = [{"germ": "— Sélectionner un germe —", "ufc": 0}]

                with st.expander(
                    f"🔴 {_label} — {_when_str} — {_ufc} UFC — {_date}",
                    expanded=True):

                    st.markdown(f"""
                    <div style="background:{lc_col_id}11;border:1px solid {lc_col_id}44;
                    border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:.75rem;
                    font-weight:700;color:{lc_col_id}">
                      🏷️ Criticité du lieu : Niveau {loc_crit} — {_loc_crit_label(loc_crit)}
                      &nbsp;·&nbsp; Score final = {loc_crit} × score germe le plus critique
                    </div>""", unsafe_allow_html=True)

                    if len(_entries) > 1:
                        _ufc_detail = "  ·  ".join(f"{e['when']} : {e['colonies']} UFC" for e in _entries)
                        st.markdown(
                            f"<div style='background:#fef9c3;border:1px solid #fde047;"
                            f"border-radius:8px;padding:8px 12px;margin-bottom:8px;"
                            f"font-size:.75rem;color:#854d0e;font-weight:600'>"
                            f"⚠️ Lectures J2 <em>et</em> J7 positives — une seule identification "
                            f"requise · {_ufc_detail}</div>",
                            unsafe_allow_html=True)

                    st.markdown(
                        "<div style='font-size:.8rem;font-weight:700;color:#475569;"
                        "margin-bottom:6px'>🧫 Germes identifiés</div>",
                        unsafe_allow_html=True)

                    germs_to_remove = []
                    current_germs   = st.session_state[germs_list_key]

                    for gi, germ_entry in enumerate(current_germs):
                        cols = st.columns([3, 1, 0.4])
                        with cols[0]:
                            selected = st.selectbox(
                                f"Germe {gi+1} *" if gi == 0 else f"Germe {gi+1}",
                                ["— Sélectionner un germe —"] + germ_names,
                                index=(["— Sélectionner un germe —"] + germ_names).index(germ_entry["germ"])
                                      if germ_entry["germ"] in germ_names else 0,
                                key=f"germ_sel_{_key}_{gi}")
                            current_germs[gi]["germ"] = selected
                        with cols[1]:
                            ufc_val = st.number_input(
                                "UFC", min_value=0,
                                value=int(germ_entry["ufc"]) if germ_entry["ufc"] else 0,
                                step=1, key=f"germ_ufc_{_key}_{gi}")
                            current_germs[gi]["ufc"] = ufc_val
                        with cols[2]:
                            st.markdown("<div style='margin-top:22px'>", unsafe_allow_html=True)
                            if gi > 0:
                                if st.button("🗑️", key=f"del_germ_{_key}_{gi}", help="Supprimer ce germe"):
                                    germs_to_remove.append(gi)
                            st.markdown("</div>", unsafe_allow_html=True)

                    for idx_r in sorted(germs_to_remove, reverse=True):
                        st.session_state[germs_list_key].pop(idx_r)
                        st.rerun()

                    if st.button("➕ Ajouter un germe", key=f"add_germ_{_key}", use_container_width=False):
                        st.session_state[germs_list_key].append({"germ": "— Sélectionner un germe —", "ufc": 0})
                        st.rerun()

                    valid_germs = [
                        g for g in current_germs
                        if g["germ"] and g["germ"] != "— Sélectionner un germe —"
                    ]
                    if valid_germs:
                        scored_germs = []
                        for vg in valid_germs:
                            gobj = next((g for g in st.session_state.germs if g['name'] == vg["germ"]), None)
                            if gobj:
                                gs = (int(gobj.get('pathogenicity',1)) *
                                      int(gobj.get('resistance',1)) *
                                      int(gobj.get('dissemination',1)))
                                scored_germs.append({"name": vg["germ"], "score": gs, "ufc": vg["ufc"], "obj": gobj})

                        if scored_germs:
                            worst       = max(scored_germs, key=lambda x: x["score"])
                            ts_prev     = loc_crit * worst["score"]
                            st_prev, _, sc_prev = _evaluate_score(ts_prev)
                            ufc_total_prev = sum(s["ufc"] for s in scored_germs)
                            preview_rows = "".join(
                                f"<tr><td style='padding:2px 8px;color:#475569'>{s['name']}</td>"
                                f"<td style='padding:2px 8px;text-align:center;color:#475569'>{s['ufc']} UFC</td>"
                                f"<td style='padding:2px 8px;text-align:center;"
                                f"font-weight:700;color:{'#ef4444' if s['name']==worst['name'] else '#64748b'}'>"
                                f"{s['score']}{'  👑' if s['name']==worst['name'] else ''}</td></tr>"
                                for s in scored_germs)
                            st.markdown(f"""
                                <div style="background:{sc_prev}11;border:1.5px solid {sc_prev}44;
                                border-radius:8px;padding:10px 14px;margin-top:8px">
                                <div style="font-size:.6rem;color:#475569;text-transform:uppercase;
                                font-weight:700;margin-bottom:6px">Aperçu score — germe le plus critique 👑</div>
                                <table style="width:100%;border-collapse:collapse;font-size:.72rem;margin-bottom:8px">
                                    <tr style="border-bottom:1px solid #e2e8f0">
                                        <th style="padding:2px 8px;text-align:left;color:#94a3b8">Germe</th>
                                        <th style="padding:2px 8px;text-align:center;color:#94a3b8">UFC</th>
                                        <th style="padding:2px 8px;text-align:center;color:#94a3b8">Score germe</th>
                                    </tr>
                                    {preview_rows}
                                    <tr style="border-top:2px solid #e2e8f0;background:#f0fdf4">
                                        <td style="padding:4px 8px;font-weight:800;color:#166534">Σ UFC TOTAL</td>
                                        <td style="padding:4px 8px;text-align:center;font-weight:900;
                                        color:#166534;font-size:.85rem">{ufc_total_prev}</td>
                                        <td style="padding:4px 8px;text-align:center;font-size:.65rem;
                                        color:#64748b">somme des germes</td>
                                    </tr>
                                </table>
                                <div style="display:flex;align-items:center;gap:12px">
                                    <div style="font-size:1.6rem;font-weight:900;color:{sc_prev}">{ts_prev}</div>
                                    <div style="font-size:.72rem;color:#475569">
                                        Lieu {loc_crit} × Germe le + critique {worst['score']}<br>
                                        <span style="font-weight:700;color:{sc_prev}">
                                            {'🚨 ACTION' if st_prev=='action' else '⚠️ ALERTE' if st_prev=='alert' else '✅ Conforme'}
                                        </span>
                                    </div>
                                </div>
                                </div>""", unsafe_allow_html=True)

                        ic1, ic2 = st.columns([3, 1])
                        with ic1:
                            remarque = st.text_area("Remarque", height=68, key=f"rem_id_{_key}")
                        with ic2:
                            date_id = st.date_input("Date identification", value=datetime.today(), key=f"date_id_{_key}")

                    idc1, idc2, idc3 = st.columns([2, 2, 1])
                    with idc1:
                        if st.button("🔍 Analyser & Enregistrer", use_container_width=True, key=f"submit_id_{_key}"):
                            valid_entries = [
                                g for g in st.session_state[germs_list_key]
                                if g["germ"] and g["germ"] != "— Sélectionner un germe —"
                            ]
                            if not valid_entries:
                                st.error("Veuillez sélectionner au moins un germe.")
                            else:
                                scored_entries = []
                                for ve in valid_entries:
                                    match, score_fuzzy = find_germ_match(ve["germ"], st.session_state.germs)
                                    if match and score_fuzzy > 0.4:
                                        gs = _get_germ_score(match)
                                        scored_entries.append({
                                            "germ_saisi":  ve["germ"],
                                            "germ_match":  match["name"],
                                            "match_score": f"{int(score_fuzzy*100)}%",
                                            "ufc":         ve["ufc"],
                                            "germ_score":  gs,
                                            "match_obj":   match,
                                        })
                                if not scored_entries:
                                    st.warning("⚠️ Aucune correspondance trouvée pour les germes saisis.")
                                else:
                                    worst_entry = max(scored_entries, key=lambda x: x["germ_score"])
                                    total_sc    = loc_crit * worst_entry["germ_score"]
                                    status, status_lbl, status_col = _evaluate_score(total_sc)
                                    ufc_total = sum(e["ufc"] for e in scored_entries)
                                    triggered_by = None
                                    if status in ("alert","action"):
                                        triggered_by = (
                                            f"lieu {loc_crit} × germe {worst_entry['germ_score']} "
                                            f"({worst_entry['germ_match']})"
                                            if loc_crit > 1
                                            else f"germe {worst_entry['germ_match']} (score {worst_entry['germ_score']})")
                                    germs_detail = [
                                        {
                                            "name":        e["germ_match"],
                                            "germ_saisi":  e["germ_saisi"],
                                            "match_score": e["match_score"],
                                            "ufc":         e["ufc"],
                                            "germ_score":  e["germ_score"],
                                            "is_worst":    e["germ_match"] == worst_entry["germ_match"],
                                        }
                                        for e in scored_entries
                                    ]
                                    st.session_state.surveillance.append({
                                        "date":               str(date_id),
                                        "prelevement":        _label,
                                        "sample_id":          _sid,
                                        "germ_saisi":         worst_entry["germ_saisi"],
                                        "germ_match":         worst_entry["germ_match"],
                                        "match_score":        worst_entry["match_score"],
                                        "ufc":                worst_entry["ufc"],
                                        "ufc_total":          ufc_total,
                                        "germ_score":         worst_entry["germ_score"],
                                        "germs_detail":       germs_detail,
                                        "multi_germ":         len(scored_entries) > 1,
                                        "location_criticality": loc_crit,
                                        "total_score":        total_sc,
                                        "risk":               worst_entry["match_obj"].get("risk", worst_entry["germ_score"]),
                                        "room_class":         pt_class,
                                        "alert_threshold":    "Score ≥ 24",
                                        "action_threshold":   "Score > 36",
                                        "triggered_by":       triggered_by,
                                        "status":             status,
                                        "operateur":          pt_oper,
                                        "remarque":           remarque,
                                        "readings":           _when_str,
                                    })
                                    save_surveillance(st.session_state.surveillance)
                                    for _ri in real_indices:
                                        st.session_state.pending_identifications[_ri]['status'] = 'done'
                                    if smp and not smp.get('archived'):
                                        smp['archived'] = True
                                        st.session_state.archived_samples.append(smp)
                                        save_archived_samples(st.session_state.archived_samples)
                                        save_prelevements(st.session_state.prelevements)
                                    del st.session_state[germs_list_key]
                                    if status in ("alert","action"):
                                        st.session_state["_show_mesures_popup"] = {
                                            "status":          status,
                                            "germ":            worst_entry["germ_match"],
                                            "ufc":             worst_entry["ufc"],
                                            "risk":            worst_entry["match_obj"].get("risk", worst_entry["germ_score"]),
                                            "label":           _label,
                                            "room_class":      pt_class,
                                            "triggered_by":    triggered_by,
                                            "germ_score":      worst_entry["germ_score"],
                                            "loc_criticality": loc_crit,
                                            "total_score":     total_sc,
                                            "th_germe":        {"alert":"Score ≥ 24","action":"Score > 36"},
                                            "germs_detail":    germs_detail,
                                        }
                                    else:
                                        germs_summary = ", ".join(
                                            f"{e['name']} ({e['ufc']} UFC)" for e in germs_detail)
                                        st.success(
                                            f"✅ {germs_summary} — **Conforme** "
                                            f"(score {total_sc} = lieu {loc_crit} × germe le + critique {worst_entry['germ_score']}) "
                                            f"| UFC total : **{ufc_total}**")
                                    st.rerun()
                    with idc2:
                        if st.button("↩️ Corriger la lecture", use_container_width=True, key=f"cancel_id_{_key}"):
                            for _e in _entries:
                                sch = next((x for x in st.session_state.schedules
                                    if x['sample_id'] == _sid and x['when'] == _e['when'] and x['status'] == 'done'), None)
                                if sch: sch['status'] = 'pending'
                            save_schedules(st.session_state.schedules)
                            for _ri in sorted(real_indices, reverse=True):
                                st.session_state.pending_identifications.pop(_ri)
                            save_pending_identifications(st.session_state.pending_identifications)
                            if germs_list_key in st.session_state:
                                del st.session_state[germs_list_key]
                            st.rerun()
                    with idc3:
                        if st.button("🗑️", use_container_width=True, key=f"del_id_{_key}"):
                            for _ri in sorted(real_indices, reverse=True):
                                st.session_state.pending_identifications.pop(_ri)
                            save_pending_identifications(st.session_state.pending_identifications)
                            if germs_list_key in st.session_state:
                                del st.session_state[germs_list_key]
                            st.rerun()

        if st.session_state.surveillance:
            st.divider()
            st.markdown("### 📋 Derniers résultats")
            for r in reversed(st.session_state.surveillance[-10:]):
                sc  = "#ef4444" if r["status"]=="action" else "#f59e0b" if r["status"]=="alert" else "#22c55e"
                ic  = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
                ufc_display = f"{r['ufc']} UFC" if r.get('ufc') else "—"
                total_score = r.get("total_score")
                germ_score  = r.get("germ_score")
                loc_crit_r  = r.get("location_criticality")
                score_badge = ""
                if total_score is not None:
                    score_badge = (
                        f"<span style='background:{sc}22;color:{sc};border:1px solid {sc}55;"
                        f"border-radius:4px;padding:1px 7px;font-size:.62rem;font-weight:700;"
                        f"margin-left:6px'>Score {total_score} "
                        f"(Nv.{loc_crit_r}×{germ_score})</span>")
                trig = r.get("triggered_by")
                trig_badge = (
                    f"<span style='background:#e0e7ff;color:#3730a3;border:1px solid #c7d2fe;"
                    f"border-radius:4px;padding:1px 6px;font-size:.6rem;font-weight:600;"
                    f"margin-left:4px'>⚡ {trig}</span>"
                    if trig else "")
                st.markdown(f"""
                <div style="background:#f8fafc;border-left:3px solid {sc};border-radius:8px;
                    padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;gap:12px">
                  <span style="font-size:1.1rem">{ic}</span>
                  <div style="flex:1">
                    <div style="font-size:.78rem;color:#1e293b;font-weight:600">
                      {r['prelevement']} — <span style="font-style:italic">{r['germ_match']}</span>
                      {score_badge}{trig_badge}
                    </div>
                    <div style="font-size:.68rem;color:#475569;margin-top:2px">
                      {r['date']} · {ufc_display}
                      · Lieu Nv.{r.get('location_criticality','—')}
                      · {r.get('operateur') or 'N/A'}
                    </div>
                  </div>
                  <div style="text-align:right">
                    <span style="font-size:.75rem;color:{sc};font-weight:800">{ufc_display}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB : PLANNING — Charge hebdo & Planning mensuel | Export Excel | Étiquettes
# Calendrier supprimé.
# Algorithme : max prélèvements/classe/semaine → répartition mensuelle
#              jamais 2× le même point le même jour (sauf freq > 1/jour)
# ═══════════════════════════════════════════════════════════════════════════════

if active == "planning":
    st.markdown("### 📅 Planning des prélèvements & lectures")

    _today_dt      = datetime.today().date()
    MOIS_FR        = ["","Janvier","Février","Mars","Avril","Mai","Juin",
                      "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    JOURS_FR_LONG  = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]

    # ── Persistance overrides manuels ─────────────────────────────────────────
    def _load_planning_overrides():
        for k, v in st.session_state.get("planning_overrides", {}).items():
            if k not in st.session_state:
                try: st.session_state[k] = int(v)
                except: pass

    def _persist_overrides():
        overrides = {k: int(v) for k, v in st.session_state.items()
                     if isinstance(k, str) and k.startswith("ch_prevu_")}
        st.session_state["planning_overrides"] = overrides
        _supa_upsert('planning_overrides', json.dumps(overrides, ensure_ascii=False))

    if "planning_overrides_loaded" not in st.session_state:
        _load_planning_overrides()
        st.session_state["planning_overrides_loaded"] = True

    # ── Helpers fréquence ─────────────────────────────────────────────────────
    def _frc_default(rc):
        rc = (rc or '').strip().upper()
        if 'A' in rc: return 20
        if 'D' in rc: return 10
        return 2

    def _freq_en_semaine(pt, nb_jours_ouvres=5):
        """Fréquence hebdomadaire d'un point (float)."""
        fr = pt.get('frequency'); u = pt.get('frequency_unit','/ semaine')
        try: fr = float(fr)
        except: fr = 0.0
        if fr <= 0:
            return float(_frc_default((pt.get('room_class') or '').strip()))
        if '/ jour' in u:  return fr * nb_jours_ouvres
        if '/ mois' in u:  return fr / 4.33
        return fr

    def _freq_par_jour(pt):
        """Fréquence journalière brute si unité = /jour, sinon 0."""
        u = pt.get('frequency_unit','/ semaine')
        if '/ jour' in u:
            try: return float(pt.get('frequency') or 0)
            except: return 0.0
        return 0.0

    def _semaines_du_mois(year, month):
        import calendar as _c
        _, n_days = _c.monthrange(year, month)
        first = date_type(year, month, 1)
        last  = date_type(year, month, n_days)
        cur   = first - timedelta(days=first.weekday())
        ms    = []
        while cur <= last:
            ms.append(cur); cur += timedelta(weeks=1)
        return ms

    def _doit_prelever_cette_semaine_mensuel(freq_mois, week_monday):
        vendredi = week_monday + timedelta(days=4)
        month    = vendredi.month; year = vendredi.year
        semaines = _semaines_du_mois(year, month)
        nb_sem   = len(semaines)
        try: idx = semaines.index(week_monday)
        except: return False, 0
        freq_mois = max(1, min(int(freq_mois), nb_sem))
        if freq_mois >= nb_sem: return True, 1
        step    = nb_sem / freq_mois
        actives = {int(i * step) for i in range(freq_mois)}
        return idx in actives, 1

    def _get_prevu_semaine(pt, week_monday, nb_wd, class_override_alloc=None):
        pt_id     = pt.get('id','')
        rc        = (pt.get('room_class') or '').strip()
        sess_key  = f"ch_prevu_{pt_id}_{week_monday.isoformat()}"
        freq_raw  = pt.get('frequency'); freq_unit = pt.get('frequency_unit','/ semaine')
        if class_override_alloc is not None:
            default_nb = int(class_override_alloc); freq_label = f"{default_nb}/sem. (réparti classe)"
        elif freq_raw is not None:
            try: freq_int = int(freq_raw)
            except: freq_int = 0
            if freq_int > 0:
                if freq_unit == '/ jour':
                    default_nb = freq_int * nb_wd; freq_label = f"{freq_int}/j → {default_nb}/sem."
                elif freq_unit == '/ semaine':
                    default_nb = freq_int; freq_label = f"{freq_int} / semaine"
                elif freq_unit == '/ mois':
                    actif, nb  = _doit_prelever_cette_semaine_mensuel(freq_int, week_monday)
                    default_nb = nb if actif else 0; freq_label = f"{freq_int} / mois"
                else:
                    default_nb = freq_int; freq_label = f"{freq_int} {freq_unit}"
            else:
                default_nb = _frc_default(rc); freq_label = f"{default_nb}/sem. (défaut)"
        else:
            default_nb = _frc_default(rc); freq_label = f"{default_nb}/sem. (défaut)"
        if sess_key not in st.session_state:
            st.session_state[sess_key] = default_nb
        return int(st.session_state[sess_key]), freq_label, sess_key

    def get_week_start(d):
        return d - timedelta(days=d.weekday())

    def fmt_week(ws):
        we = ws + timedelta(days=6)
        return ws.strftime('%d/%m') + ' – ' + we.strftime('%d/%m/%Y')
        # ── QR Code helpers ────────────────────────────────────────────────────────────
    def _make_qr_bytes(data_dict: dict) -> bytes:
        """Génère un QR code PNG en bytes à partir d'un dict."""
        payload = json.dumps(data_dict, ensure_ascii=False, separators=(',', ':'))
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _qr_payload(pt: dict) -> dict:
        """Construit le payload JSON minimal d'un point pour le QR code."""
        return {
            "app":   "URC",
            "id":    pt.get("id", ""),
            "label": pt.get("label", ""),
            "type":  pt.get("type", ""),
            "rc":    pt.get("room_class", ""),
            "lc":    int(pt.get("location_criticality", 1)),
            "gel":   pt.get("gelose", ""),
        }
    def _compute_monthly_planning(year, month, class_max_dict, holidays_set):
        """"
        Planning mensuel  fréquences intrinsèques respectées :
        - class_max = 0  → fréquence individuelle du point utilisée directement
        - class_max > 0  → plafonne à class_max réparti proportionnellement
        - mensuel        → 1 passage par mois (semaine désignée uniquement)
        - hebdomadaire   → au plus freq×/semaine, JAMAIS 2× le même jour
        - journalier     → freq×/jour (max_per_day = freq)
        """
        import calendar as _cm
        import random as _rnd
    
        _, n_days = _cm.monthrange(year, month)
        first = date_type(year, month, 1)
        last  = date_type(year, month, n_days)
        cur   = first - timedelta(days=first.weekday())
        mondays = []
        while cur <= last:
            mondays.append(cur)
            cur += timedelta(weeks=1)
    
        planning = {}
    
        def _active_week_for_monthly(freq_mois_val, week_monday):
            semaines = []
            c2 = first - timedelta(days=first.weekday())
            while c2 <= last:
                semaines.append(c2)
                c2 += timedelta(weeks=1)
            nb_sem = len(semaines)
            try:
                idx = semaines.index(week_monday)
            except ValueError:
                return False
            n = max(1, min(int(freq_mois_val), nb_sem))
            if n >= nb_sem:
                return True
            step = nb_sem / n
            actives = {int(i * step) for i in range(n)}
            return idx in actives
    
        for week_idx, week_monday in enumerate(mondays):
            wd_week = [
                week_monday + timedelta(days=i)
                for i in range(5)
                if (week_monday + timedelta(days=i)) not in holidays_set
            ]
            if not wd_week:
                continue
            nb_wd = len(wd_week)
            for d in wd_week:
                if d not in planning:
                    planning[d] = []
    
            day_counts = {d: 0  for d in wd_week}
            day_labels = {d: {} for d in wd_week}
    
            tasks = []
            for pt in st.session_state.points:
                rc        = (pt.get('room_class') or '').strip()
                max_cls   = int(class_max_dict.get(rc, 0))
                freq_raw  = pt.get('frequency')
                freq_unit = pt.get('frequency_unit', '/ semaine')
    
                try:
                    freq_val = float(freq_raw) if freq_raw else 0.0
                except (TypeError, ValueError):
                    freq_val = 0.0
    
                # ── Calcul alloc intrinsèque ──────────────────────────────────
                if freq_val <= 0:
                    default_by_class = {'A': 20, 'B': 10, 'C': 4, 'D': 2}
                    alloc       = default_by_class.get(rc[:1] if rc else '', 2)
                    max_per_day = 1
                elif '/ jour' in freq_unit:
                    alloc       = int(freq_val) * nb_wd
                    max_per_day = int(freq_val)
                elif '/ semaine' in freq_unit:
                    alloc       = int(freq_val)
                    max_per_day = 1          # jamais 2× le même jour
                elif '/ mois' in freq_unit:
                    alloc       = 1 if _active_week_for_monthly(freq_val, week_monday) else 0
                    max_per_day = 1
                else:
                    alloc       = int(freq_val)
                    max_per_day = 1
    
                # ── Plafond classe (si activé) ────────────────────────────────
                if max_cls > 0:
                    pts_cls   = [p for p in st.session_state.points
                                if (p.get('room_class') or '').strip() == rc]
                    freqs_cls = [max(0.01, _freq_en_semaine(p, nb_wd)) for p in pts_cls]
                    tot_cls   = sum(freqs_cls) or 1
                    my_f      = max(0.01, _freq_en_semaine(pt, nb_wd))
                    alloc_cls = round(my_f / tot_cls * max_cls)
                    alloc     = min(alloc, alloc_cls)
                # class_max = 0 → pas de plafond, fréquence intrinsèque conservée
    
                tasks.append({
                    'label':       pt['label'],
                    'type':        pt.get('type', '—'),
                    'risk':        int(pt.get('risk_level', 1)),
                    'room_class':  rc,
                    'alloc':       max(0, alloc),
                    'max_per_day': max(1, max_per_day),
                })
    
            tasks.sort(key=lambda x: (-x['risk'], x['label']))
            rng = _rnd.Random(year * 10000 + month * 100 + week_idx)
    
            for task in tasks:
                remaining    = task['alloc']
                mpd          = task['max_per_day']
                max_attempts = max(remaining * nb_wd * 4, 50)
                attempts     = 0
                while remaining > 0 and attempts < max_attempts:
                    attempts += 1
                    candidates = [
                        d for d in wd_week
                        if day_labels[d].get(task['label'], 0) < mpd
                    ]
                    if not candidates:
                        break
                    best = min(candidates, key=lambda d: (day_counts[d], rng.random()))
                    planning[best].append({
                        'label':      task['label'],
                        'type':       task['type'],
                        'risk':       task['risk'],
                        'room_class': task['room_class'],
                    })
                    day_counts[best] += 1
                    day_labels[best][task['label']] = day_labels[best].get(task['label'], 0) + 1
                    remaining -= 1
    
        return planning

# ═════════════════════════════════════════════════════════════════════════
    # ONGLETS Planning
    # ═════════════════════════════════════════════════════════════════════════
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        _openpyxl_ok = True
    except ImportError:
        _openpyxl_ok = False

    plan_tab_charge, plan_tab_export = st.tabs([
        "📊 Charge hebdo & Planning mensuel",
        "📥 Export Excel",
    ])

    # ═════════════════════════════════════════════════════════════════════════
# ONGLET : CHARGE HEBDO & PLANNING MENSUEL
# ═════════════════════════════════════════════════════════════════════════
    with plan_tab_charge:
        st.markdown("### 📊 Charge hebdomadaire")

    # Navigation mois
    nav_c1, nav_c2, nav_c3, nav_c4, nav_c5 = st.columns([1, 1, 3, 1, 1])
    with nav_c1:
        if st.button("◀◀", use_container_width=True, key="ch_prev_year"):
            st.session_state.cal_year -= 1
            st.rerun()
    with nav_c2:
        if st.button("◀", use_container_width=True, key="ch_prev_month"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()
    with nav_c3:
        _ch_year  = st.session_state.get("cal_year",  _today_dt.year)
        _ch_month = st.session_state.get("cal_month", _today_dt.month)
        st.markdown(
            f"<div style='text-align:center;background:linear-gradient(135deg,#1e40af,#2563eb);"
            f"border-radius:10px;padding:10px;color:#fff;font-weight:800;font-size:1.1rem'>"
            f"📅 {MOIS_FR[_ch_month]} {_ch_year}</div>",
            unsafe_allow_html=True)
    with nav_c4:
        if st.button("▶", use_container_width=True, key="ch_next_month"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()
    with nav_c5:
        if st.button("▶▶", use_container_width=True, key="ch_next_year"):
            st.session_state.cal_year += 1
            st.rerun()
    if st.button("📍 Mois courant", key="ch_today_btn"):
        st.session_state.cal_year  = _today_dt.year
        st.session_state.cal_month = _today_dt.month
        st.rerun()

    _ch_year     = st.session_state.get("cal_year",  _today_dt.year)
    _ch_month    = st.session_state.get("cal_month", _today_dt.month)
    _ch_holidays = get_holidays_cached(_ch_year)

    st.divider()

    # ── Contraintes max / classe / semaine ────────────────────────────────
    st.markdown("#### 🏷️ Contraintes max prélèvements / classe / semaine")
    st.caption(
        "**0 = aucun prélèvement** pour cette classe (tous les points sont désactivés). "
        "**> 0** = le total hebdomadaire de la classe est plafonné à cette valeur, "
        "puis réparti proportionnellement aux fréquences individuelles (utilisées comme poids). "
        "**Un même point ne peut pas apparaître 2× le même jour**, "
        "sauf si sa fréquence est définie en > 1/jour.")

    all_classes = sorted({
        (pt.get('room_class') or '').strip()
        for pt in st.session_state.points
        if (pt.get('room_class') or '').strip()
    })
    if "class_constraints_loaded" not in st.session_state:
        _raw_cc = _supa_get('class_constraints')
        if _raw_cc:
            try:
                for _cls_k, _cls_v in json.loads(_raw_cc).items():
                    st.session_state[f"class_max_{_cls_k}"] = int(_cls_v)
            except Exception:
                pass
        st.session_state["class_constraints_loaded"] = True

    for _cls in all_classes:
        _key = f"class_max_{_cls}"
        if _key not in st.session_state:
            st.session_state[_key] = 0
    class_max_dict = {}

    if all_classes:
        rc_colors = {
            "A": "#22c55e", "B": "#84cc16", "C": "#f59e0b",
            "D": "#f97316", "E": "#ef4444",
        }
        cls_cols = st.columns(min(len(all_classes), 6))
        for ci, cls in enumerate(all_classes):
            rc_col  = rc_colors.get(cls.replace(' ', '').upper()[:1], "#6366f1")
            pts_cls = [pt for pt in st.session_state.points
                       if (pt.get('room_class') or '').strip() == cls]
            with cls_cols[ci % len(cls_cols)]:
                st.markdown(
                    f"<div style='background:{rc_col}15;border:1.5px solid {rc_col}55;"
                    f"border-radius:8px;padding:8px;text-align:center;margin-bottom:4px'>"
                    f"<div style='font-size:.9rem;font-weight:900;color:{rc_col}'>Classe {cls}</div>"
                    f"<div style='font-size:.65rem;color:#64748b'>{len(pts_cls)} point(s)</div>"
                    f"</div>",
                    unsafe_allow_html=True)
                st.number_input(
                    f"Max/sem Cl.{cls}", min_value=0, max_value=500,
                    step=1, key=f"class_max_{cls}",
                    label_visibility="collapsed",
                    help=f"0 = aucun prélèvement · >0 = plafond hebdomadaire classe {cls}")
                new_max = int(st.session_state.get(f"class_max_{cls}", 0))
                class_max_dict[cls] = new_max

                if new_max > 0:
                    freqs_p  = [max(0.01, _freq_en_semaine(pt, 5)) for pt in pts_cls]
                    tot_p    = sum(freqs_p) or 1
                    allocs   = []
                    assigned = 0
                    for ii, (pt, f) in enumerate(zip(pts_cls, freqs_p)):
                        if ii < len(pts_cls) - 1:
                            a = round(f / tot_p * new_max)
                        else:
                            a = max(0, new_max - assigned)
                        assigned += a
                        allocs.append(a)
                    preview = "".join(
                        f"<div style='font-size:.6rem;color:#1e40af'>"
                        f"{pt['label'][:20]}: <b>{a}×/sem</b></div>"
                        for pt, a in zip(pts_cls, allocs))
                    st.markdown(
                        f"<div style='background:#eff6ff;border:1px solid #93c5fd;"
                        f"border-radius:6px;padding:6px 8px;margin-top:2px'>{preview}</div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div style='background:#fef2f2;border:1px solid #fca5a5;"
                        f"border-radius:6px;padding:6px 8px;margin-top:2px;"
                        f"text-align:center'>"
                        f"<div style='font-size:.62rem;font-weight:700;color:#991b1b'>"
                        f"🚫 Aucun prélèvement planifié</div>"
                        f"<div style='font-size:.58rem;color:#b91c1c;margin-top:1px'>"
                        f"Définissez une valeur &gt; 0 pour activer</div>"
                        f"</div>",
                        unsafe_allow_html=True)
    else:
        st.info("Aucune classe de salle définie sur les points de prélèvement.")
        class_max_dict = {}

    if all_classes:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        sv_col, _ = st.columns([1, 3])
        with sv_col:
            if st.button("💾 Sauvegarder les contraintes",
                         key="save_class_constraints",
                         use_container_width=True, type="primary"):
                payload = {
                    cls: int(st.session_state.get(f"class_max_{cls}", 0))
                    for cls in all_classes
                }
                if _supa_upsert('class_constraints',
                                json.dumps(payload, ensure_ascii=False)):
                    st.success("✅ Contraintes sauvegardées dans Supabase !")
                else:
                    st.warning("⚠️ Supabase non connecté — contraintes non sauvegardées.")
    st.divider()

    # ── Sélecteur semaine ─────────────────────────────────────────────────
    ch_ws_set = {get_week_start(_today_dt)}
    for _p in st.session_state.prelevements:
        try:
            ch_ws_set.add(get_week_start(datetime.fromisoformat(_p["date"]).date()))
        except Exception:
            pass
    for _i in range(1, 9):
        ch_ws_set.add(get_week_start(_today_dt) + timedelta(weeks=_i))
    ch_week_starts = sorted(ch_ws_set)
    ch_week_labels = [fmt_week(ws) for ws in ch_week_starts]
    ch_cur_idx = 0
    for _i, _ws in enumerate(ch_week_starts):
        if _ws <= _today_dt < _ws + timedelta(days=7):
            ch_cur_idx = _i
            break

    ch_sel_label = st.selectbox(
        "Semaine à détailler", ch_week_labels, index=ch_cur_idx, key="ch_week_sel")
    ch_sel_ws       = ch_week_starts[ch_week_labels.index(ch_sel_label)]
    ch_sel_we       = ch_sel_ws + timedelta(days=6)
    ch_holidays     = get_holidays_cached(ch_sel_ws.year)
    ch_working_days = [
        ch_sel_ws + timedelta(days=i)
        for i in range(5)
        if (ch_sel_ws + timedelta(days=i)) not in ch_holidays
    ]
    nb_jours = len(ch_working_days)

    ch_j0 = [
        p for p in st.session_state.prelevements
        if p.get('date')
        and ch_sel_ws <= datetime.fromisoformat(p['date']).date() <= ch_sel_we
        and not p.get('archived', False)
    ]
    ch_j2 = [
        s for s in st.session_state.schedules
        if s['when'] == 'J2'
        and ch_sel_ws <= datetime.fromisoformat(s['due_date']).date() <= ch_sel_we
    ]
    ch_j7 = [
        s for s in st.session_state.schedules
        if s['when'] == 'J7'
        and ch_sel_ws <= datetime.fromisoformat(s['due_date']).date() <= ch_sel_we
    ]
    total_actes    = len(ch_j0) + len(ch_j2) + len(ch_j7)
    actes_par_jour = total_actes / nb_jours if nb_jours > 0 else 0

    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#1e40af,#2563eb);border-radius:14px;
        padding:16px 22px;margin:10px 0 18px 0;display:flex;align-items:center;
        justify-content:space-between;flex-wrap:wrap;gap:10px">
        <div style="color:#fff">
          <div style="font-size:1.05rem;font-weight:800">📅 {ch_sel_label}</div>
          <div style="font-size:.82rem;color:#bfdbfe;margin-top:3px">
            {nb_jours} jour(s) ouvré(s)
          </div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <div style="background:rgba(255,255,255,.15);border-radius:10px;padding:10px 18px;text-align:center">
            <div style="font-size:.72rem;color:#bfdbfe;font-weight:700;text-transform:uppercase">Actes total</div>
            <div style="font-size:2rem;font-weight:900;color:#fff">{total_actes}</div>
          </div>
          <div style="background:rgba(255,255,255,.15);border-radius:10px;padding:10px 18px;text-align:center">
            <div style="font-size:.72rem;color:#bfdbfe;font-weight:700;text-transform:uppercase">/ jour</div>
            <div style="font-size:2rem;font-weight:900;color:#fff">{actes_par_jour:.1f}</div>
          </div>
        </div></div>""",
        unsafe_allow_html=True)

    m2, m3, m4, m5 = st.columns(4)
    m2.metric("📍 Points actifs", len(st.session_state.points))
    m3.metric("🧪 Prélèv. J0",   len(ch_j0))
    m4.metric("📖 Lectures J2",  len(ch_j2))
    m5.metric("📗 Lectures J7",  len(ch_j7))

    st.divider()

    st.divider()
 
    # ── Avancement au cours de la semaine (expander) ──────────────────
    _av_prevu_total   = 0
    _av_realise_total = 0
    _av_rows          = []
 
    for pt_av in st.session_state.points:
        rc_av  = (pt_av.get('room_class') or '').strip()
        max_av = int(class_max_dict.get(rc_av, 0))
 
        pts_cls_av  = [p for p in st.session_state.points
                       if (p.get('room_class') or '').strip() == rc_av]
        freqs_av    = [max(0.01, _freq_en_semaine(p, nb_jours)) for p in pts_cls_av]
        tot_av      = sum(freqs_av) or 1
        my_f_av     = max(0.01, _freq_en_semaine(pt_av, nb_jours))
        alloc_av    = round(my_f_av / tot_av * max_av) if max_av > 0 else 0
 
        nb_prevu_av, _, _ = _get_prevu_semaine(pt_av, ch_sel_ws, nb_jours, alloc_av)
        realise_av = sum(1 for p in ch_j0 if p.get('label') == pt_av['label'])
        _av_prevu_total   += nb_prevu_av
        _av_realise_total += realise_av
        _av_rows.append((pt_av, nb_prevu_av, realise_av))
 
    taux_av  = int(_av_realise_total / _av_prevu_total * 100) if _av_prevu_total > 0 else 0
    taux_ic  = "✅" if taux_av >= 100 else "⏳" if taux_av >= 50 else "🔴"
    taux_col = "#22c55e" if taux_av >= 100 else "#f59e0b" if taux_av >= 50 else "#ef4444"
 
    with st.expander(
        f"📊 Avancement au cours de la semaine "
        f"— {_av_realise_total}/{_av_prevu_total} réalisé(s) {taux_ic} {taux_av}%",
        expanded=False,
    ):
        st.markdown(
            "<div style='display:grid;grid-template-columns:3fr 0.8fr 1.4fr;"
            "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff'>Point</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Réalisé</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Statut</div>"
            "</div>",
            unsafe_allow_html=True)
 
        for pt_av, nb_prevu_av, realise_av in _av_rows:
            type_icon_av = "💨" if pt_av.get('type') == 'Air' else "🧴"
            if nb_prevu_av == 0:
                st_bg_av="#f8fafc"; st_brd_av="#e2e8f0"; st_col_av="#94a3b8"; st_lbl_av="⏸️ Non planifié"
            elif realise_av >= nb_prevu_av:
                st_bg_av="#f0fdf4"; st_brd_av="#86efac"; st_col_av="#166534"; st_lbl_av="✅ Complet"
            elif realise_av > 0:
                pct_av=int(realise_av/nb_prevu_av*100)
                st_bg_av="#fffbeb"; st_brd_av="#fcd34d"; st_col_av="#92400e"; st_lbl_av=f"⏳ {pct_av}%"
            else:
                st_bg_av="#fef2f2"; st_brd_av="#fca5a5"; st_col_av="#991b1b"; st_lbl_av=f"🔴 0/{nb_prevu_av}"
 
            st.markdown(
                "<div style='display:grid;grid-template-columns:3fr 0.8fr 1.4fr;"
                "gap:4px;background:#fff;border:1px solid #e2e8f0;border-top:none;"
                "padding:8px 14px;align-items:center'>"
                f"<div style='font-size:.85rem;font-weight:600;color:#0f172a'>"
                f"{type_icon_av} {pt_av['label']}</div>"
                f"<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>"
                f"{realise_av}</div>"
                f"<div style='text-align:center'>"
                f"<span style='background:{st_bg_av};border:1px solid {st_brd_av};"
                f"border-radius:8px;padding:3px 10px;font-size:.72rem;"
                f"font-weight:700;color:{st_col_av}'>{st_lbl_av}</span>"
                f"</div></div>",
                unsafe_allow_html=True)
 
        st.markdown(
            "<div style='background:#1e293b;border-radius:0 0 10px 10px;"
            "padding:8px 14px;display:flex;justify-content:space-between;align-items:center'>"
            f"<div style='font-size:.78rem;font-weight:700;color:#94a3b8'>TOTAL SEMAINE</div>"
            f"<div style='display:flex;gap:16px;align-items:center'>"
            f"<span style='font-size:.78rem;color:#93c5fd'>Prévu : {_av_prevu_total}</span>"
            f"<span style='font-size:.78rem;color:#86efac'>Réalisé : {_av_realise_total}</span>"
            f"<span style='font-size:.88rem;font-weight:800;color:{taux_col}'>"
            f"{taux_av}% réalisé</span></div></div>",
            unsafe_allow_html=True)

    # ── Planning mensuel automatique ──────────────────────────────────────
    st.markdown("#### 📅 Planning mensuel automatique")
    st.caption(
        "Répartition basée sur les contraintes max/classe/semaine définies ci-dessus. "
        "**0 = aucun prélèvement** pour la classe concernée. "
        "Un point n'apparaît jamais 2× le même jour sauf si sa fréquence est > 1/jour.")

    class_max_dict = {
        cls: int(st.session_state.get(f"class_max_{cls}", 0))
        for cls in all_classes
    }

    monthly_plan = _compute_monthly_planning(
        _ch_year, _ch_month,
        class_max_dict,
        _ch_holidays)

    import calendar as _cal_pm
    _, _pm_ndays = _cal_pm.monthrange(_ch_year, _ch_month)
    _pm_start    = date_type(_ch_year, _ch_month, 1)
    _pm_end      = date_type(_ch_year, _ch_month, _pm_ndays)
    cur_pm       = _pm_start - timedelta(days=_pm_start.weekday())
    pm_mondays   = []
    while cur_pm <= _pm_end:
        pm_mondays.append(cur_pm)
        cur_pm += timedelta(weeks=1)

    if "pm_selected_day" not in st.session_state:
        st.session_state["pm_selected_day"] = None

    rcp_pm = {
        "1": "#22c55e", "2": "#84cc16", "3": "#f59e0b",
        "4": "#f97316", "5": "#ef4444",
    }

    def _generate_pdf_etiquettes(tasks, date_obj_or_list):
        """
        Génère le PDF d'étiquettes.
        - date_obj_or_list peut être une date unique (un jour)
          ou une liste de tuples [(date, [tasks]), ...] pour l'impression semaine.
        Retourne les bytes du PDF.
        """
        import io as _io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units     import cm as rl_cm
        from reportlab.lib           import colors as rlc
        from reportlab.platypus      import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, HRFlowable, Spacer)
        from reportlab.lib.styles    import ParagraphStyle
        from reportlab.lib.enums     import TA_RIGHT

        _RISK_COLORS_ETQ = {
            "1": "#22c55e", "2": "#84cc16",
            "3": "#f59e0b", "4": "#f97316", "5": "#ef4444",
        }
        W_ETQ  = 4.5  * rl_cm
        H_ETQ  = 3.2  * rl_cm
        N_COLS = 4
        GAP    = 0.25 * rl_cm
        MARGIN = 0.7  * rl_cm

        buf     = _io.BytesIO()
        RISK_RL = {k: rlc.HexColor(v) for k, v in _RISK_COLORS_ETQ.items()}

        s_titre   = ParagraphStyle("et_t", fontName="Helvetica-Bold",
                                   fontSize=7.5, leading=9, spaceAfter=2,
                                   textColor=rlc.HexColor("#0f172a"))
        s_lbl     = ParagraphStyle("et_l", fontName="Helvetica",
                                   fontSize=5.5, leading=7,
                                   textColor=rlc.HexColor("#64748b"))
        s_date    = ParagraphStyle("et_d", fontName="Helvetica-Bold",
                                   fontSize=9, leading=10,
                                   textColor=rlc.HexColor("#1e40af"))
        s_logo    = ParagraphStyle("et_lo", fontName="Helvetica",
                                   fontSize=5, leading=6,
                                   textColor=rlc.HexColor("#94a3b8"),
                                   alignment=TA_RIGHT)
        s_classea = ParagraphStyle("et_ca", fontName="Helvetica-Bold",
                                   fontSize=6, leading=7,
                                   textColor=rlc.HexColor("#854d0e"),
                                   backColor=rlc.HexColor("#fef9c3"),
                                   spaceAfter=2)
        s_val     = ParagraphStyle("et_v", fontName="Helvetica-Bold",
                                   fontSize=7.5, leading=9,
                                   textColor=rlc.HexColor("#0f172a"))
        s_phdr    = ParagraphStyle("et_h", fontName="Helvetica-Bold",
                                   fontSize=8,
                                   textColor=rlc.HexColor("#1e40af"),
                                   spaceAfter=5)
        s_day_sep = ParagraphStyle("et_ds", fontName="Helvetica-Bold",
                                   fontSize=10, leading=12,
                                   textColor=rlc.HexColor("#ffffff"),
                                   backColor=rlc.HexColor("#1e40af"),
                                   spaceBefore=8, spaceAfter=6)

        # Détermine si on est en mode "semaine" (liste de tuples) ou "jour" (date + tasks)
        if isinstance(date_obj_or_list, list):
            # Mode semaine : [(date, [tasks]), ...]
            days_data = date_obj_or_list
            is_week   = True
            total_n   = sum(len(t) for _, t in days_data)
            doc_title = f"Étiquettes semaine — {days_data[0][0].strftime('%d/%m')} → {days_data[-1][0].strftime('%d/%m/%Y')}"
        else:
            days_data = [(date_obj_or_list, tasks)]
            is_week   = False
            day_lbl   = f"{JOURS_FR_LONG[date_obj_or_list.weekday()]} {date_obj_or_list.strftime('%d/%m/%Y')}"
            total_n   = len(tasks)
            doc_title = f"Étiquettes {date_obj_or_list.strftime('%d/%m/%Y')}"

        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN,  bottomMargin=MARGIN,
            title=doc_title)

        def _build_cell(task, d_obj):
            rv      = str(task.get("risk", ""))
            rc_etiq = RISK_RL.get(rv, rlc.HexColor("#6366f1"))
            lv      = task.get("label", "—")
            dv      = d_obj.strftime("%d/%m/%Y")
            W_INNER = W_ETQ - 0.55 * rl_cm
            _pt_data = next(
                (p for p in st.session_state.points
                 if p.get("label") == lv), None)

            qr_flowable = ""
            if _pt_data:
                try:
                    from reportlab.platypus import Image as RLImage
                    _qr_bytes = _make_qr_bytes(_qr_payload(_pt_data))
                    _qr_buf   = BytesIO(_qr_bytes)
                    _qr_img   = RLImage(_qr_buf, width=1.1*rl_cm, height=1.1*rl_cm)
                    qr_flowable = _qr_img
                except Exception:
                    qr_flowable = ""

            classea_rows = []
            if task.get("room_class") == "A" and _pt_data:
                iso = _pt_data.get("num_isolateur", "—") or "—"
                pst = _pt_data.get("poste", "—") or "—"
                classea_rows = [[Paragraph(f"ISO {iso} · {pst}", s_classea)]]

            W_TEXT = W_INNER - 1.2 * rl_cm
            W_QR   = 1.2 * rl_cm
            left_tbl = Table([
                [Paragraph(lv, s_titre)],
                [HRFlowable(width=W_TEXT, thickness=0.6, color=rc_etiq, spaceAfter=2)],
                *classea_rows,
                [Paragraph("📅 Date", s_lbl)],
                [Paragraph(dv, s_date)],
                [Paragraph("👤 Préleveur :", s_lbl)],
                [Paragraph("", s_val)],
                [Paragraph("URC — MicroSurveillance", s_logo)],
            ], colWidths=[W_TEXT])
            left_tbl.setStyle(TableStyle([
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                ("TOPPADDING",    (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING",    (0, -1), (0, -1), 4),
            ]))

            if qr_flowable:
                inner = Table([[left_tbl, qr_flowable]], colWidths=[W_TEXT, W_QR])
                inner.setStyle(TableStyle([
                    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                    ("TOPPADDING",    (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("ALIGN",         (1, 0), (1, 0),   "CENTER"),
                ]))
            else:
                inner = left_tbl

            outer = Table([[inner]], colWidths=[W_ETQ], rowHeights=[H_ETQ])
            outer.setStyle(TableStyle([
                ("BOX",            (0, 0), (0, 0), 1.2, rc_etiq),
                ("ROUNDEDCORNERS", (0, 0), (0, 0), [5]),
                ("LINEAFTER",      (0, 0), (0, 0), 5.5, rc_etiq),
                ("LEFTPADDING",    (0, 0), (0, 0), 5),
                ("RIGHTPADDING",   (0, 0), (0, 0), 4),
                ("TOPPADDING",     (0, 0), (0, 0), 5),
                ("BOTTOMPADDING",  (0, 0), (0, 0), 4),
                ("VALIGN",         (0, 0), (0, 0), "TOP"),
                ("BACKGROUND",     (0, 0), (0, 0), rlc.white),
            ]))
            return outer

        # ── Construction du document ──────────────────────────────────────
        story = []

        if is_week:
            story.append(Paragraph(
                f"Étiquettes semaine — "
                f"{days_data[0][0].strftime('%d/%m')} → {days_data[-1][0].strftime('%d/%m/%Y')} — "
                f"{total_n} étiquette{'s' if total_n > 1 else ''} — 45×32 mm · 4 col.",
                s_phdr))
        else:
            story.append(Paragraph(
                f"Étiquettes — {day_lbl} — "
                f"{total_n} étiquette{'s' if total_n > 1 else ''} — 45×32 mm · 4 col.",
                s_phdr))

        for day_date, day_tasks in days_data:
            if not day_tasks:
                continue

            if is_week:
                # Séparateur jour en couleur
                day_label_str = f"  {JOURS_FR_LONG[day_date.weekday()]} {day_date.strftime('%d/%m/%Y')}  — {len(day_tasks)} prélèvement{'s' if len(day_tasks) > 1 else ''}"
                story.append(Paragraph(day_label_str, s_day_sep))

            # Grille d'étiquettes pour ce jour
            rows_etiq, row_buf = [], []
            for _task in day_tasks:
                row_buf.append(_build_cell(_task, day_date))
                if len(row_buf) == N_COLS:
                    rows_etiq.append(row_buf)
                    row_buf = []
            if row_buf:
                while len(row_buf) < N_COLS:
                    row_buf.append("")
                rows_etiq.append(row_buf)

            if rows_etiq:
                main_tbl = Table(
                    rows_etiq,
                    colWidths=[W_ETQ] * N_COLS,
                    rowHeights=[H_ETQ] * len(rows_etiq))
                main_tbl.setStyle(TableStyle([
                    ("LEFTPADDING",   (0, 0), (-1, -1), GAP / 2),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), GAP / 2),
                    ("TOPPADDING",    (0, 0), (-1, -1), GAP / 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), GAP / 2),
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(main_tbl)

            # Saut de ligne entre les jours (sauf dernier)
            if is_week:
                story.append(Spacer(1, 0.4 * rl_cm))

        doc.build(story)
        buf.seek(0)
        return buf.getvalue()

    # ── Rendu du calendrier semaine par semaine ───────────────────────────
    for week_idx, week_monday in enumerate(pm_mondays):
        wd_week = [
            week_monday + timedelta(days=i)
            for i in range(5)
            if (week_monday + timedelta(days=i)) not in _ch_holidays
        ]
        if not wd_week:
            continue

        _we_end    = week_monday + timedelta(days=6)
        _total_sem = sum(len(monthly_plan.get(wd, [])) for wd in wd_week)

        # ── En-tête de semaine + bouton impression semaine ────────────────
        _pdf_week_key   = f"pdf_week_{week_monday.isoformat()}"
        _pdf_week_ready = st.session_state.get(_pdf_week_key)

        hdr_c1, hdr_c2, hdr_c3 = st.columns([4, 2, 1])
        with hdr_c1:
            st.markdown(
                f"<div style='background:#1e293b;border-radius:10px;padding:8px 16px;"
                f"display:flex;justify-content:space-between;align-items:center;"
                f"margin-top:14px;margin-bottom:6px'>"
                f"<span style='color:#fff;font-weight:800;font-size:.88rem'>"
                f"Semaine {week_monday.isocalendar()[1]} — "
                f"{week_monday.strftime('%d/%m')} → {_we_end.strftime('%d/%m')}</span>"
                f"<span style='background:rgba(255,255,255,.15);color:#93c5fd;"
                f"border-radius:8px;padding:3px 12px;font-size:.8rem;font-weight:700'>"
                f"📋 {_total_sem} prélèv. planifiés</span>"
                f"</div>",
                unsafe_allow_html=True)
        with hdr_c2:
            st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
            # Bouton impression semaine entière
            if _pdf_week_ready:
                st.download_button(
                    label="⬇️ Étiquettes semaine",
                    data=_pdf_week_ready["data"],
                    file_name=_pdf_week_ready["fname"],
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"wk_dl_{week_monday.isoformat()}",
                    help="Télécharger les étiquettes de toute la semaine")
            else:
                if st.button(
                    "🖨️ Imprimer la semaine",
                    key=f"wk_print_{week_monday.isoformat()}",
                    use_container_width=True,
                    disabled=(_total_sem == 0),
                    help="Générer les étiquettes de toute la semaine (regroupées par jour)"
                ):
                    try:
                        # Construire la liste [(date, [tasks])] pour chaque jour ouvré
                        week_days_data = [
                            (wd, monthly_plan.get(wd, []))
                            for wd in wd_week
                            if monthly_plan.get(wd)
                        ]
                        if week_days_data:
                            _pdf_bytes = _generate_pdf_etiquettes(week_days_data, week_days_data)
                            _fname_wk  = f"etiquettes_sem{week_monday.isocalendar()[1]}_{week_monday.strftime('%Y%m%d')}.pdf"
                            st.session_state[_pdf_week_key] = {
                                "data":  _pdf_bytes,
                                "fname": _fname_wk,
                            }
                            st.rerun()
                        else:
                            st.warning("Aucun prélèvement planifié cette semaine.")
                    except ImportError:
                        st.error("❌ **ReportLab** non installé. Ajoutez `reportlab` dans requirements.txt.")
                    except Exception as _e:
                        st.error(f"Erreur PDF semaine : {_e}")
        with hdr_c3:
            # Bouton réinitialiser le PDF semaine
            if _pdf_week_ready:
                st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
                if st.button("🔄", key=f"wk_reset_{week_monday.isoformat()}",
                             use_container_width=True, help="Regénérer le PDF"):
                    del st.session_state[_pdf_week_key]
                    st.rerun()

        _day_cols = st.columns(len(wd_week))
        for di, wd in enumerate(wd_week):
            taches_j   = monthly_plan.get(wd, [])
            prevu_j    = len(taches_j)
            is_today_d = (wd == _today_dt)
            is_past_d  = (wd < _today_dt)
            is_other_m = (wd.month != _ch_month)
            realise_j  = sum(
                1 for p in st.session_state.prelevements
                if p.get("date") and not p.get("archived", False)
                and datetime.fromisoformat(p["date"]).date() == wd)
            j2_j = [
                s for s in st.session_state.schedules
                if s["when"] == "J2"
                and datetime.fromisoformat(s["due_date"]).date() == wd
            ]
            j7_j = [
                s for s in st.session_state.schedules
                if s["when"] == "J7"
                and datetime.fromisoformat(s["due_date"]).date() == wd
            ]

            bg_d     = "#dbeafe" if is_today_d else ("#f1f5f9" if is_other_m else ("#f8fafc" if is_past_d else "#ffffff"))
            border_d = "2px solid #2563eb" if is_today_d else ("1px dashed #cbd5e1" if is_other_m else "1.5px solid #e2e8f0")
            jour_col = "#1e40af" if is_today_d else ("#94a3b8" if is_other_m or is_past_d else "#475569")
            op_d     = "0.6" if is_other_m else ("0.75" if is_past_d and not is_today_d else "1")

            if realise_j >= prevu_j and prevu_j > 0:
                stat_bg = "#f0fdf4"; stat_col = "#166534"; stat_lbl = "✅"
            elif realise_j > 0:
                stat_bg = "#fffbeb"; stat_col = "#92400e"
                stat_lbl = f"⏳{realise_j}/{prevu_j}"
            elif prevu_j > 0:
                stat_bg = "#fef2f2"; stat_col = "#991b1b"
                stat_lbl = f"🔴{prevu_j}"
            else:
                stat_bg = "#f8fafc"; stat_col = "#94a3b8"; stat_lbl = "—"

            pts_html = ""
            for t in taches_j[:5]:
                _c  = rcp_pm.get(str(t["risk"]), "#94a3b8")
                _ic = "💨" if t["type"] == "Air" else "🧴"
                _lb = t["label"][:18] + ("…" if len(t["label"]) > 18 else "")
                pts_html += (
                    f"<div style='border-left:2px solid {_c};padding:1px 5px;"
                    f"font-size:.58rem;color:#0f172a;margin-bottom:1px'>{_ic} {_lb}</div>")
            if len(taches_j) > 5:
                pts_html += f"<div style='font-size:.55rem;color:#94a3b8'>+{len(taches_j)-5}</div>"

            lect_html = ""
            if j2_j:
                lect_html += f"<div style='font-size:.58rem;color:#d97706;margin-top:2px'>📖×{len(j2_j)}</div>"
            if j7_j:
                lect_html += f"<div style='font-size:.58rem;color:#0369a1'>📗×{len(j7_j)}</div>"

            autre_mois_badge = (
                f"<div style='font-size:.5rem;color:#94a3b8;font-style:italic'>"
                f"{wd.strftime('%b')}</div>"
                if is_other_m else "")

            is_selected = (st.session_state.get("pm_selected_day") == wd)
            card_html = (
                f"<div style='background:{'#faf5ff' if is_selected else bg_d};"
                f"border:{'2.5px solid #7c3aed' if is_selected else border_d};"
                f"border-radius:10px;padding:8px 6px;opacity:{op_d};min-height:100px'>"
                f"<div style='font-size:.75rem;font-weight:800;color:{jour_col};text-align:center'>"
                f"{JOURS_FR_LONG[wd.weekday()][:3]}</div>"
                f"<div style='font-size:.7rem;color:#94a3b8;text-align:center;margin-bottom:2px'>"
                f"{wd.strftime('%d/%m')}</div>"
                f"{autre_mois_badge}"
                f"<div style='background:{stat_bg};border-radius:6px;padding:2px 4px;"
                f"text-align:center;font-size:.68rem;font-weight:800;color:{stat_col};"
                f"margin-bottom:4px'>{stat_lbl}</div>"
                f"{pts_html}{lect_html}</div>")

            _pdf_key   = f"pdf_quick_{wd.isoformat()}"
            _pdf_ready = st.session_state.get(_pdf_key)

            with _day_cols[di]:
                st.markdown(card_html, unsafe_allow_html=True)

                # ── Bouton Détail uniquement (impression remontée au niveau semaine) ──
                btn_lbl = "🔍 Détail" if not is_selected else "✖ Fermer"
                if st.button(
                    btn_lbl,
                    key=f"pm_btn_{wd.isoformat()}",
                    use_container_width=True
                ):
                    st.session_state["pm_selected_day"] = (
                        None if is_selected else wd)
                    st.rerun()

    # ── Panel fixe bas de page : détail du jour sélectionné ──────────────
    _sel = st.session_state.get("pm_selected_day")
    if _sel:
        taches_sel = monthly_plan.get(_sel, [])
        j0r_sel = [
            p for p in st.session_state.prelevements
            if p.get("date") and not p.get("archived", False)
            and datetime.fromisoformat(p["date"]).date() == _sel
        ]
        j2r_sel = [
            s for s in st.session_state.schedules
            if s["when"] == "J2"
            and datetime.fromisoformat(s["due_date"]).date() == _sel
        ]
        j7r_sel = [
            s for s in st.session_state.schedules
            if s["when"] == "J7"
            and datetime.fromisoformat(s["due_date"]).date() == _sel
        ]
        _day_lbl = f"{JOURS_FR_LONG[_sel.weekday()]} {_sel.strftime('%d/%m/%Y')}"
        rcp_fix  = {
            "1": "#22c55e", "2": "#84cc16", "3": "#f59e0b",
            "4": "#f97316", "5": "#ef4444",
        }

        _cards = ""
        for t in taches_sel:
            _c  = rcp_fix.get(str(t["risk"]), "#94a3b8")
            _ic = "💨" if t["type"] == "Air" else "🧴"
            _dn = any(p.get("label") == t["label"] for p in j0r_sel)
            _bg = "#f0fdf4" if _dn else "#fff"
            _bd = "#86efac" if _dn else _c + "44"
            _cards += (
                f"<div style='background:{_bg};border:1px solid {_bd};"
                f"border-left:3px solid {_c};border-radius:7px;"
                f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px'>"
                f"<div style='font-size:.77rem;font-weight:700;color:#0f172a'>"
                f"{_ic} {'✅ ' if _dn else ''}{t['label']}</div>"
                f"<div style='font-size:.63rem;color:#64748b'>"
                f"Cl.{t['room_class'] or '—'} · Nv.{t['risk']}</div></div>")
        for s in j2r_sel:
            _dn = s["status"] == "done"
            _lt = not _dn and _sel < _today_dt
            _c  = "#22c55e" if _dn else ("#ef4444" if _lt else "#d97706")
            _bg = "#f0fdf4" if _dn else ("#fef2f2" if _lt else "#fffbeb")
            _st = "✅" if _dn else ("⚠️" if _lt else "⏳")
            _cards += (
                f"<div style='background:{_bg};border:1px solid {_c}44;"
                f"border-left:3px solid {_c};border-radius:7px;"
                f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px'>"
                f"<div style='font-size:.77rem;font-weight:700;color:#0f172a'>"
                f"📖 J2 — {s['label'][:22]}</div>"
                f"<div style='font-size:.63rem;color:{_c};font-weight:700'>"
                f"{_st} {'Fait' if _dn else ('Retard' if _lt else 'À faire')}</div></div>")
        for s in j7r_sel:
            _dn = s["status"] == "done"
            _lt = not _dn and _sel < _today_dt
            _c  = "#22c55e" if _dn else ("#ef4444" if _lt else "#0369a1")
            _bg = "#f0fdf4" if _dn else ("#fef2f2" if _lt else "#eff6ff")
            _st = "✅" if _dn else ("⚠️" if _lt else "⏳")
            _cards += (
                f"<div style='background:{_bg};border:1px solid {_c}44;"
                f"border-left:3px solid {_c};border-radius:7px;"
                f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px'>"
                f"<div style='font-size:.77rem;font-weight:700;color:#0f172a'>"
                f"📗 J7 — {s['label'][:22]}</div>"
                f"<div style='font-size:.63rem;color:{_c};font-weight:700'>"
                f"{_st} {'Fait' if _dn else ('Retard' if _lt else 'À faire')}</div></div>")
        for p in j0r_sel:
            _cards += (
                f"<div style='background:#faf5ff;border:1px solid #e9d5ff;"
                f"border-left:3px solid #7c3aed;border-radius:7px;"
                f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px'>"
                f"<div style='font-size:.77rem;font-weight:700;color:#0f172a'>"
                f"🧪 {p['label'][:22]}</div>"
                f"<div style='font-size:.63rem;color:#64748b'>"
                f"{p.get('gelose', '—')} · {p.get('operateur', '—') or '—'}</div></div>")
        if not _cards:
            _cards = (
                "<div style='color:#94a3b8;font-size:.82rem;"
                "padding:8px 0;align-self:center'>Aucune activité ce jour.</div>")

        _nb_t  = len(taches_sel)
        _nb_j0 = len(j0r_sel)
        _nb_j2 = len(j2r_sel)
        _nb_j7 = len(j7r_sel)
        _rbadge = f" · 🧪 {_nb_j0} réalisé" if _nb_j0 else ""
        st.markdown(
            "<div style='position:fixed;bottom:0;left:0;right:0;z-index:9999;"
            "background:linear-gradient(135deg,#0f172a,#1e293b);"
            "border-top:3px solid #2563eb;padding:10px 20px 14px 20px;"
            "box-shadow:0 -6px 32px rgba(0,0,0,.4)'>"
            "<div style='display:flex;align-items:center;justify-content:space-between;"
            "margin-bottom:8px'>"
            f"<div style='color:#fff;font-weight:800;font-size:.95rem'>📋 {_day_lbl}"
            f"<span style='margin-left:10px;font-size:.75rem;font-weight:400;color:#93c5fd'>"
            f"{_nb_t} prélèv. · {_nb_j2} J2 · {_nb_j7} J7{_rbadge}</span></div>"
            "<span style='font-size:.7rem;color:#475569;font-style:italic'>"
            "Cliquez à nouveau sur le jour pour fermer</span>"
            "</div>"
            f"<div style='display:flex;gap:8px;overflow-x:auto;padding-bottom:2px'>"
            f"{_cards}</div>"
            "</div>"
            "<div style='height:170px'></div>",
            unsafe_allow_html=True)

        st.divider()
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#0f172a,#1e293b);"
            f"border-radius:12px;padding:12px 20px;margin-bottom:12px'>"
            f"<div style='color:#fff;font-weight:800;font-size:1rem'>📋 {_day_lbl}</div>"
            f"<div style='color:#93c5fd;font-size:.78rem;margin-top:2px'>"
            f"{_nb_t} prélèv. planifiés · {_nb_j2} J2 · {_nb_j7} J7"
            f"{'  · 🧪 ' + str(_nb_j0) + ' réalisé(s)' if j0r_sel else ''}"
            f"</div></div>",
            unsafe_allow_html=True)

        # ── Activités du jour ─────────────────────────────────────────────
        if j2r_sel or j7r_sel or j0r_sel:
            with st.expander("📖 Lectures & réalisés du jour", expanded=False):
                act_cols = st.columns(3)
                ci = 0
                for s in j2r_sel:
                    _dn = s["status"] == "done"
                    _lt = not _dn and _sel < _today_dt
                    _c  = "#22c55e" if _dn else ("#ef4444" if _lt else "#d97706")
                    _st = "✅ Fait" if _dn else ("⚠️ Retard" if _lt else "⏳ À faire")
                    with act_cols[ci % 3]:
                        st.markdown(
                            f"<div style='background:#fffbeb;border:1px solid {_c}44;"
                            f"border-left:3px solid {_c};border-radius:7px;"
                            f"padding:7px 10px;margin-bottom:6px'>"
                            f"<div style='font-size:.78rem;font-weight:700'>📖 J2 — {s['label'][:24]}</div>"
                            f"<div style='font-size:.65rem;color:{_c};font-weight:700'>{_st}</div></div>",
                            unsafe_allow_html=True)
                    ci += 1
                for s in j7r_sel:
                    _dn = s["status"] == "done"
                    _lt = not _dn and _sel < _today_dt
                    _c  = "#22c55e" if _dn else ("#ef4444" if _lt else "#0369a1")
                    _st = "✅ Fait" if _dn else ("⚠️ Retard" if _lt else "⏳ À faire")
                    with act_cols[ci % 3]:
                        st.markdown(
                            f"<div style='background:#eff6ff;border:1px solid {_c}44;"
                            f"border-left:3px solid {_c};border-radius:7px;"
                            f"padding:7px 10px;margin-bottom:6px'>"
                            f"<div style='font-size:.78rem;font-weight:700'>📗 J7 — {s['label'][:24]}</div>"
                            f"<div style='font-size:.65rem;color:{_c};font-weight:700'>{_st}</div></div>",
                            unsafe_allow_html=True)
                    ci += 1
                for p in j0r_sel:
                    with act_cols[ci % 3]:
                        st.markdown(
                            f"<div style='background:#faf5ff;border:1px solid #e9d5ff;"
                            f"border-left:3px solid #7c3aed;border-radius:7px;"
                            f"padding:7px 10px;margin-bottom:6px'>"
                            f"<div style='font-size:.78rem;font-weight:700'>🧪 {p['label'][:24]}</div>"
                            f"<div style='font-size:.65rem;color:#64748b'>"
                            f"{p.get('gelose','—')} · {p.get('operateur','—') or '—'}</div></div>",
                            unsafe_allow_html=True)
                    ci += 1

        # ── Sélection & génération étiquettes (jour sélectionné) ────────────────
        if taches_sel:
            st.markdown(
                "<div style='background:#eff6ff;border:1px solid #bfdbfe;"
                "border-radius:8px;padding:8px 14px;margin-bottom:8px'>"
                "<span style='font-size:.88rem;font-weight:800;color:#1e40af'>"
                "🏷️ Générer les étiquettes pour ce jour</span></div>",
                unsafe_allow_html=True)

            col_sa, col_sn, _ = st.columns([1, 1, 4])
            with col_sa:
                if st.button("☑️ Tout sélectionner",
                             key=f"etiq_all_{_sel.isoformat()}",
                             use_container_width=True):
                    for _t in taches_sel:
                        st.session_state[f"etiq_chk_{_sel.isoformat()}_{_t['label']}"] = True
                    st.rerun()
            with col_sn:
                if st.button("⬜ Tout désélectionner",
                             key=f"etiq_none_{_sel.isoformat()}",
                             use_container_width=True):
                    for _t in taches_sel:
                        st.session_state[f"etiq_chk_{_sel.isoformat()}_{_t['label']}"] = False
                    st.rerun()

            _chk_cols = st.columns(3)
            _selected_tasks = []
            for _ti, _t in enumerate(taches_sel):
                _chk_key = f"etiq_chk_{_sel.isoformat()}_{_t['label']}"
                if _chk_key not in st.session_state:
                    st.session_state[_chk_key] = True
                _rc = rcp_fix.get(str(_t["risk"]), "#94a3b8")
                _ic = "💨" if _t["type"] == "Air" else "🧴"
                _dn = any(p.get("label") == _t["label"] for p in j0r_sel)
                with _chk_cols[_ti % 3]:
                    st.markdown(
                        f"<div style='background:{'#f0fdf4' if _dn else '#fff'};"
                        f"border:1px solid {_rc}44;border-left:3px solid {_rc};"
                        f"border-radius:7px;padding:4px 8px;margin-bottom:4px'>"
                        f"<span style='font-size:.72rem;font-weight:700;color:#0f172a'>"
                        f"{_ic} {'✅ ' if _dn else ''}{_t['label'][:28]}</span><br>"
                        f"<span style='font-size:.6rem;color:#64748b'>"
                        f"Cl.{_t['room_class'] or '—'} · Nv.{_t['risk']}</span></div>",
                        unsafe_allow_html=True)
                    if st.checkbox("Inclure", value=st.session_state[_chk_key],
                                   key=_chk_key, label_visibility="collapsed"):
                        _selected_tasks.append(_t)

            _n_sel_etiq = len(_selected_tasks)
            st.markdown(
                f"<div style='font-size:.8rem;color:#475569;margin:6px 0'>"
                f"{_n_sel_etiq} / {len(taches_sel)} point(s) sélectionné(s)</div>",
                unsafe_allow_html=True)

            if _n_sel_etiq > 0:
                if st.button(
                    f"📄 Générer {_n_sel_etiq} "
                    f"étiquette{'s' if _n_sel_etiq > 1 else ''} — {_day_lbl}",
                    use_container_width=True,
                    key=f"etiq_gen_{_sel.isoformat()}",
                    type="primary"
                ):
                    try:
                        _pdf_bytes = _generate_pdf_etiquettes(_selected_tasks, _sel)
                        _pdf_key_sel = f"pdf_quick_{_sel.isoformat()}"
                        st.session_state[_pdf_key_sel] = {
                            "data":  _pdf_bytes,
                            "fname": f"etiquettes_{_sel.strftime('%Y%m%d')}.pdf",
                        }
                        fname_etiq = f"etiquettes_{_sel.strftime('%Y%m%d')}.pdf"
                        st.download_button(
                            label=f"⬇️ Télécharger {fname_etiq}",
                            data=_pdf_bytes,
                            file_name=fname_etiq,
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"etiq_dl_{_sel.isoformat()}")
                        st.success(
                            f"✅ {_n_sel_etiq} étiquette{'s' if _n_sel_etiq > 1 else ''} "
                            f"générée{'s' if _n_sel_etiq > 1 else ''} pour le {_day_lbl}")
                    except ImportError:
                        st.error("❌ **ReportLab** non installé.\n\n"
                                 "Ajoutez `reportlab` dans **requirements.txt**.")
                    except Exception as _e:
                        st.error(f"Erreur génération PDF : {_e}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.info("Aucun prélèvement planifié ce jour.")



    # ═════════════════════════════════════════════════════════════════════════
    # ONGLET : EXPORT EXCEL
    # ═════════════════════════════════════════════════════════════════════════
    with plan_tab_export:
        st.markdown("#### 📥 Exporter le planning en Excel")

        if not _openpyxl_ok:
            st.error(
                "❌ **openpyxl** n'est pas installé.\n\n"
                "Ajoutez `openpyxl` dans votre fichier **requirements.txt** "
                "puis redémarrez l'application.")
            st.stop()

        exp_scope = st.selectbox(
            "Période",
            ["Semaine en cours", "Semaine choisie", "Mois en cours", "4 semaines à venir", "Tout le planning"],
            key="exp_scope")

        # ── Sélecteur de semaine si "Semaine choisie" ─────────────────────
        if exp_scope == "Semaine choisie":
            _today_ref     = _today_dt
            _cur_monday    = _today_ref - timedelta(days=_today_ref.weekday())
            _week_opts     = [_cur_monday + timedelta(weeks=i) for i in range(-4, 13)]
            _week_labels   = []
            for _wm in _week_opts:
                _we = _wm + timedelta(days=4)
                _marker = " ← semaine en cours" if _wm == _cur_monday else ""
                _week_labels.append(
                    f"Sem. {_wm.isocalendar()[1]} — {_wm.strftime('%d/%m/%Y')} → {_we.strftime('%d/%m/%Y')}{_marker}")
            _sel_week_idx = st.selectbox(
                "Choisir la semaine",
                range(len(_week_labels)),
                format_func=lambda i: _week_labels[i],
                index=4,
                key="exp_chosen_week")
            _chosen_monday = _week_opts[_sel_week_idx]
        else:
            _chosen_monday = None

        exp_oper_filter = st.selectbox(
            "Filtrer par opérateur",
            ["Tous"] + [o['nom'] for o in st.session_state.operators],
            key="exp_oper")
        only_working = st.checkbox(
            "Inclure uniquement les jours ouvrés", value=True)

        if st.button("📊 Générer Excel", use_container_width=True, key="gen_xlsx"):
            import io as _io
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()

            # ── Palette couleurs ──────────────────────────────────────────
            C_BLUE     = "1E40AF"; C_BLUE2  = "2563EB"; C_BLUE_L   = "DBEAFE"
            C_WHITE    = "FFFFFF"; C_TEXT   = "0F172A"; C_GREY_L   = "F1F5F9"
            C_GREY_HDR = "334155"; C_GREEN  = "16A34A"; C_RED      = "DC2626"
            C_AMBER    = "D97706"

            thin   = Side(style="thin",   color="CBD5E1")
            medium = Side(style="medium", color="94A3B8")

            def fill(h):
                return PatternFill("solid", fgColor=h)

            def font(size=9, bold=False, color=C_TEXT):
                return Font(name="Arial", size=size, bold=bold, color=color)

            def al_c(wrap=False):
                return Alignment(horizontal="center", vertical="center", wrap_text=wrap)

            def al_l(wrap=False):
                return Alignment(horizontal="left", vertical="center", wrap_text=wrap)

            def border_all():
                return Border(left=thin, right=thin, top=thin, bottom=thin)

            def border_medium():
                return Border(left=medium, right=medium, top=medium, bottom=medium)

            # ── Plage de dates ────────────────────────────────────────────
            exp_today = _today_dt

            if exp_scope == "Semaine en cours":
                _monday   = exp_today - timedelta(days=exp_today.weekday())
                exp_dates = [_monday + timedelta(days=i) for i in range(7)]

            elif exp_scope == "Semaine choisie":
                exp_dates = [_chosen_monday + timedelta(days=i) for i in range(7)]

            elif exp_scope == "Mois en cours":
                import calendar as cal_module
                first = exp_today.replace(day=1)
                last  = exp_today.replace(
                    day=cal_module.monthrange(exp_today.year, exp_today.month)[1])
                exp_dates = [
                    first + timedelta(days=i)
                    for i in range((last - first).days + 1)
                ]
            elif exp_scope == "4 semaines à venir":
                ws_e = exp_today - timedelta(days=exp_today.weekday())
                exp_dates = [ws_e + timedelta(days=i) for i in range(28)]
            else:
                all_d = []
                for p in st.session_state.prelevements:
                    try:
                        all_d.append(datetime.fromisoformat(p["date"]).date())
                    except Exception:
                        pass
                for s in st.session_state.schedules:
                    try:
                        all_d.append(datetime.fromisoformat(s["due_date"]).date())
                    except Exception:
                        pass
                exp_dates = (
                    [min(all_d) + timedelta(days=i)
                     for i in range((max(all_d) - min(all_d)).days + 1)]
                    if all_d
                    else [exp_today + timedelta(days=i) for i in range(7)])

            if only_working:
                exp_dates = [d for d in exp_dates if is_working_day(d)]

            # ══════════════════════════════════════════════════════════════
            # FEUILLE 1 — VUE MATRICIELLE : Points × Jours de semaine
            # Lignes = points de prélèvement
            # Colonnes = jours de la semaine (Lun→Ven) avec date
            # Cellule = "X" si prévu ce jour-là, fond coloré si réalisé
            # ══════════════════════════════════════════════════════════════
            ws_matrix = wb.active
            ws_matrix.title = "Planning Semaine"
            ws_matrix.sheet_view.showGridLines = False

            # Regrouper les dates par semaine (lundi)
            from collections import OrderedDict
            weeks_map = OrderedDict()
            for d in exp_dates:
                ws_key = d - timedelta(days=d.weekday())  # lundi de la semaine
                if ws_key not in weeks_map:
                    weeks_map[ws_key] = []
                weeks_map[ws_key].append(d)

            JOURS_XL = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            pts_all = st.session_state.points

            n_weeks = len(weeks_map)
            FIXED_COLS = 3  # Label | Classe | Type
            DAYS_PER_WEEK = 5
            total_cols = FIXED_COLS + DAYS_PER_WEEK * n_weeks

            ws_matrix.merge_cells(start_row=1, start_column=1,
                                  end_row=1, end_column=total_cols)
            ws_matrix.cell(1, 1).value     = "PLANNING MICROBIOLOGIQUE — MicroSurveillance URC"
            ws_matrix.cell(1, 1).font      = Font(name="Arial", size=13, bold=True, color=C_WHITE)
            ws_matrix.cell(1, 1).fill      = fill(C_BLUE)
            ws_matrix.cell(1, 1).alignment = al_c()
            ws_matrix.row_dimensions[1].height = 28

            ws_matrix.merge_cells(start_row=2, start_column=1,
                                  end_row=2, end_column=total_cols)
            ws_matrix.cell(2, 1).value     = (
                f"Généré le {exp_today.strftime('%d/%m/%Y')} — "
                f"{'Jours ouvrés uniquement' if only_working else 'Tous les jours'} — "
                f"X = prélèvement prévu · X 1/X 2 = poste spécifique · ✓ = réalisé")
            ws_matrix.cell(2, 1).font      = Font(name="Arial", size=8, color="475569")
            ws_matrix.cell(2, 1).fill      = fill(C_BLUE_L)
            ws_matrix.cell(2, 1).alignment = al_c()
            ws_matrix.row_dimensions[2].height = 16

            # ── Ligne 3 : en-têtes semaines (fusionné sur 5 jours) ────────
            ws_matrix.row_dimensions[3].height = 20
            for wi, (ws_key, ws_days) in enumerate(weeks_map.items()):
                col_start = FIXED_COLS + 1 + wi * DAYS_PER_WEEK
                col_end   = col_start + DAYS_PER_WEEK - 1
                ws_matrix.merge_cells(start_row=3, start_column=col_start,
                                      end_row=3,   end_column=col_end)
                we_key = ws_key + timedelta(days=4)
                c = ws_matrix.cell(3, col_start)
                c.value     = f"Sem. {ws_key.isocalendar()[1]}  {ws_key.strftime('%d/%m')} → {we_key.strftime('%d/%m/%Y')}"
                c.font      = Font(name="Arial", size=9, bold=True, color=C_WHITE)
                c.fill      = fill(C_GREY_HDR)
                c.alignment = al_c()
                c.border    = border_medium()

            # ── Ligne 4 : en-têtes colonnes fixes ─────────────────────────
            ws_matrix.row_dimensions[4].height = 34
            fixed_headers = ["Point de prélèvement", "Classe", "Type"]
            fixed_widths  = [32, 9, 10]
            for ci, (h, w) in enumerate(zip(fixed_headers, fixed_widths), start=1):
                c = ws_matrix.cell(4, ci)
                c.value     = h
                c.font      = Font(name="Arial", size=9, bold=True, color=C_WHITE)
                c.fill      = fill(C_BLUE2)
                c.alignment = al_c(wrap=True)
                c.border    = border_all()
                ws_matrix.column_dimensions[get_column_letter(ci)].width = w

            # ── Ligne 4 : en-têtes jours (Lun, Mar… + date) ──────────────
            for wi, (ws_key, ws_days) in enumerate(weeks_map.items()):
                day_date_map = {}
                for d in ws_days:
                    day_date_map[d.weekday()] = d  # weekday: 0=Lun … 4=Ven

                for di in range(DAYS_PER_WEEK):
                    col = FIXED_COLS + 1 + wi * DAYS_PER_WEEK + di
                    d_for_col = day_date_map.get(di)
                    if d_for_col:
                        label = f"{JOURS_XL[di][:3]}\n{d_for_col.strftime('%d/%m')}"
                        is_today_col = (d_for_col == exp_today)
                        bg_col = "DBEAFE" if is_today_col else "EFF6FF"
                        fc_col = "1E40AF"
                    else:
                        label  = f"{JOURS_XL[di][:3]}\n—"
                        bg_col = "F1F5F9"
                        fc_col = "94A3B8"
                    c = ws_matrix.cell(4, col)
                    c.value     = label
                    c.font      = Font(name="Arial", size=8, bold=True, color=fc_col)
                    c.fill      = fill(bg_col)
                    c.alignment = al_c(wrap=True)
                    c.border    = border_all()
                    ws_matrix.column_dimensions[get_column_letter(col)].width = 8

            ws_matrix.freeze_panes = "D5"

            # ── Lignes données : un point par ligne ───────────────────────
            RISK_BG = {
                "1": "DCFCE7", "2": "D9F99D",
                "3": "FEF9C3", "4": "FFEDD5", "5": "FEE2E2",
            }
            RISK_FC = {
                "1": "166534", "2": "365314",
                "3": "713F12", "4": "7C2D12", "5": "7F1D1D",
            }

            data_row = 5
            for pt_idx, pt in enumerate(pts_all):
                rc         = (pt.get('room_class') or '').strip()
                rv         = str(pt.get('risk_level', ''))
                type_lbl   = pt.get('type', '—')
                poste_type = pt.get('poste_type', 'non_applicable')
                is_class_a = rc.strip().upper() == "A"
                row_bg     = "FFFFFF" if pt_idx % 2 == 0 else "F8FAFC"

                ws_matrix.row_dimensions[data_row].height = 18

                # Col 1 : label point
                c = ws_matrix.cell(data_row, 1)
                c.value     = ("💨 " if type_lbl == "Air" else "🧴 ") + pt['label']
                c.font      = Font(name="Arial", size=9, bold=True, color=C_TEXT)
                c.fill      = fill(RISK_BG.get(rv, row_bg))
                c.alignment = al_l()
                c.border    = border_all()

                # Col 2 : classe
                c = ws_matrix.cell(data_row, 2)
                c.value     = rc or "—"
                c.font      = Font(name="Arial", size=9, bold=True,
                                   color=RISK_FC.get(rv, C_TEXT))
                c.fill      = fill(RISK_BG.get(rv, row_bg))
                c.alignment = al_c()
                c.border    = border_all()

                # Col 3 : type
                c = ws_matrix.cell(data_row, 3)
                c.value     = type_lbl
                c.font      = font(9, color=C_TEXT)
                c.fill      = fill(row_bg)
                c.alignment = al_c()
                c.border    = border_all()

                # Compteur alternance poste spécifique : P1 un jour, P2 le suivant
                poste_counter = 0

                # Colonnes jours : X (+ numéro poste si classe A spécifique) ou ✓ si réalisé
                for wi, (ws_key, ws_days) in enumerate(weeks_map.items()):
                    day_date_map = {d.weekday(): d for d in ws_days}
                    for di in range(DAYS_PER_WEEK):
                        col       = FIXED_COLS + 1 + wi * DAYS_PER_WEEK + di
                        d_for_col = day_date_map.get(di)
                        c = ws_matrix.cell(data_row, col)

                        if d_for_col is None:
                            c.value  = ""
                            c.fill   = fill("E2E8F0")
                            c.border = border_all()
                            continue

                        # Vérifier si ce point est planifié ce jour
                        tasks_day  = monthly_plan.get(d_for_col, [])
                        is_planned = any(t.get("label") == pt["label"] for t in tasks_day)

                        # Vérifier si réalisé
                        is_done = any(
                            p.get("label") == pt["label"] and not p.get("archived", False)
                            and p.get("date")
                            and datetime.fromisoformat(p["date"]).date() == d_for_col
                            for p in st.session_state.prelevements)

                        # ── Suffixe numéro de poste pour classe A spécifique ──
                        if (is_planned or is_done) and is_class_a and poste_type == "specifique":
                            poste_num    = (poste_counter % 2) + 1   # alterne 1 / 2
                            poste_suffix = f" {poste_num}"
                            poste_counter += 1
                        else:
                            poste_suffix = ""
                            if is_planned or is_done:
                                poste_counter += 1  # on incrémente quand même pour cohérence

                        if is_done:
                            c.value     = f"✓{poste_suffix}"
                            c.font      = Font(name="Arial", size=11, bold=True, color=C_GREEN)
                            c.fill      = fill("DCFCE7")
                        elif is_planned:
                            c.value     = f"X{poste_suffix}"
                            c.font      = Font(name="Arial", size=10, bold=True, color=C_BLUE2)
                            c.fill      = fill("DBEAFE")
                        else:
                            c.value = ""
                            c.fill  = fill("FFFFFF" if pt_idx % 2 == 0 else "F8FAFC")

                        c.alignment = al_c()
                        c.border    = border_all()

                data_row += 1

            # ── Ligne totaux par jour ─────────────────────────────────────
            ws_matrix.row_dimensions[data_row].height = 20
            c = ws_matrix.cell(data_row, 1)
            c.value     = "TOTAL prélèvements planifiés"
            c.font      = Font(name="Arial", size=9, bold=True, color=C_WHITE)
            c.fill      = fill(C_GREY_HDR)
            c.alignment = al_c()
            c.border    = border_all()
            ws_matrix.merge_cells(start_row=data_row, start_column=1,
                                  end_row=data_row, end_column=FIXED_COLS)
            for wi, (ws_key, ws_days) in enumerate(weeks_map.items()):
                day_date_map = {d.weekday(): d for d in ws_days}
                for di in range(DAYS_PER_WEEK):
                    col       = FIXED_COLS + 1 + wi * DAYS_PER_WEEK + di
                    d_for_col = day_date_map.get(di)
                    c = ws_matrix.cell(data_row, col)
                    if d_for_col:
                        total_day = len(monthly_plan.get(d_for_col, []))
                        c.value   = total_day if total_day > 0 else "—"
                        c.font    = Font(name="Arial", size=9, bold=True,
                                        color=C_WHITE if total_day > 0 else "94A3B8")
                        c.fill    = fill(C_BLUE2 if total_day > 0 else C_GREY_HDR)
                    else:
                        c.value = ""
                        c.fill  = fill("334155")
                    c.alignment = al_c()
                    c.border    = border_all()

            buf = _io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            fname = f"planning_URC_{exp_today.strftime('%Y%m%d')}.xlsx"
            st.download_button(
                "⬇️ Télécharger le planning Excel",
                data=buf.getvalue(), file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
            st.success(
                f"✅ Fichier **{fname}** généré avec succès — "
                f"2 onglets : **Planning Semaine** (matriciel) ·")
            
# ═══════════════════════════════════════════════════════════════════════════════
# TAB : HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════
if active == "historique":
    st.markdown("### 📋 Historique de surveillance")
    surv  = st.session_state.surveillance
    total = len(surv)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _get_criticite(germ_name):
        for g in st.session_state.get("germs", []):
            if g.get("name", "") == germ_name:
                return int(g.get("criticite", 0) or 0)
        return 0

    def _crit_label(c):
        return {5:"Critique",4:"Majeur",3:"Important",2:"Modéré",1:"Limité"}.get(c,"—")

    def _crit_color(c):
        return {5:"#7c3aed",4:"#ef4444",3:"#f97316",2:"#f59e0b",1:"#22c55e"}.get(c,"#94a3b8")

    def _parse_date(d_str):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(d_str), fmt).date()
            except Exception:
                pass
        return None

    if surv:
        # ── Export / Vider ────────────────────────────────────────────────────
        c_dl, c_cl = st.columns(2)
        with c_dl:
            csv_str  = io.StringIO()
            all_keys = list(dict.fromkeys(k for r in surv for k in r.keys()))
            writer   = csv.DictWriter(csv_str, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(surv)
            st.download_button(
                "⬇️ Télécharger CSV", csv_str.getvalue(),
                "surveillance.csv", "text/csv",
                use_container_width=True)
        with c_cl:
            if st.button("🗑️ Vider l'historique", use_container_width=True):
                st.session_state.surveillance = []
                save_surveillance([])
                try:
                    supa = get_supabase_client()
                    if supa:
                        supa.table("app_data").upsert({
                            "key": "surveillance",
                            "value": json.dumps([], ensure_ascii=False)
                        }).execute()
                except Exception:
                    pass
                if os.path.exists(CSV_FILE):
                    os.remove(CSV_FILE)
                st.rerun()

        # ── Filtre par période ────────────────────────────────────────────────
        from datetime import date as dt_date

        all_dates_ok = [d for d in (_parse_date(r.get("date","")) for r in surv) if d]
        d_min = min(all_dates_ok) if all_dates_ok else dt_date.today()
        d_max = max(all_dates_ok) if all_dates_ok else dt_date.today()

        if "hist_date_debut_val" not in st.session_state:
            st.session_state["hist_date_debut_val"] = d_min
        if "hist_date_fin_val" not in st.session_state:
            st.session_state["hist_date_fin_val"] = d_max
        if d_max > st.session_state["hist_date_fin_val"]:
            st.session_state["hist_date_fin_val"] = d_max
        if d_min < st.session_state["hist_date_debut_val"]:
            st.session_state["hist_date_debut_val"] = d_min

        st.markdown(
            "<div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;"
            "padding:12px 16px;margin:10px 0 6px 0'>"
            "<div style='font-size:.8rem;font-weight:700;color:#0369a1;margin-bottom:8px'>"
            "🗓️ Filtrer par période</div>",
            unsafe_allow_html=True)
        cf1, cf2, cf3 = st.columns([2, 2, 1])
        with cf1:
            date_debut = st.date_input(
                "Du", value=st.session_state["hist_date_debut_val"],
                min_value=d_min, max_value=d_max, key="hist_date_debut_input")
            st.session_state["hist_date_debut_val"] = date_debut
        with cf2:
            date_fin = st.date_input(
                "Au", value=st.session_state["hist_date_fin_val"],
                min_value=d_min, max_value=d_max, key="hist_date_fin_input")
            st.session_state["hist_date_fin_val"] = date_fin
        with cf3:
            st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
            if st.button("↺ Reset", use_container_width=True):
                st.session_state["hist_date_debut_val"] = d_min
                st.session_state["hist_date_fin_val"]   = d_max
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        surv_f = [r for r in surv
                  if _parse_date(r.get("date","")) is not None
                  and date_debut <= _parse_date(r.get("date","")) <= date_fin]
        total_f = len(surv_f)
        if total_f < total:
            st.caption(f"🔍 {total_f} résultat(s) sur {total} — "
                       f"{date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y')}")

        # ── Métriques globales ────────────────────────────────────────────────
        alerts  = sum(1 for r in surv_f if r.get("status") == "alert")
        actions = sum(1 for r in surv_f if r.get("status") == "action")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total",        total_f)
        c2.metric("✅ Conformes", total_f - alerts - actions)
        c3.metric("⚠️ Alertes",  alerts)
        c4.metric("🚨 Actions",   actions)
        st.divider()

        hist_tab_plan, hist_tab_pts, hist_tab_germs, hist_tab_prev, hist_tab_liste = st.tabs([
            "🗺️ Plan interactif",
            "📍 Stats par point",
            "🦠 Stats par germe",
            "👤 Répartition par préleveur",
            "📋 Liste des entrées",
        ])

        # ══════════════════════════════════════════════════════════════════════
        # ONGLET 0 : PLAN INTERACTIF
        # ══════════════════════════════════════════════════════════════════════
        with hist_tab_plan:
            import json as _json_plan

            # ── Chargement map_points robuste ─────────────────────────────────
            map_points_raw = list(st.session_state.get("map_points", []))
            if not map_points_raw:
                try:
                    _raw_mp = _supa_get('map_points')
                    if _raw_mp:
                        _loaded = json.loads(_raw_mp) if isinstance(_raw_mp, str) else _raw_mp
                        if isinstance(_loaded, list) and _loaded:
                            st.session_state["map_points"] = _loaded
                            map_points_raw = _loaded
                except Exception:
                    pass

            # Coordonnées avec float garanti
            pt_coords = {}
            for mp in map_points_raw:
                _lbl = mp.get("label", "")
                if not _lbl:
                    continue
                try:
                    pt_coords[_lbl] = {
                        "x": float(mp.get("x", "")),
                        "y": float(mp.get("y", "")),
                    }
                except (TypeError, ValueError):
                    continue

            STATUS_COL = {"action":"#ef4444","alert":"#f59e0b","ok":"#22c55e","none":"#94a3b8"}
            STATUS_IC  = {"action":"🚨","alert":"⚠️","ok":"✅","none":"⬜"}
            STATUS_LBL = {"action":"ACTION","alert":"ALERTE","ok":"Conforme","none":"Aucune donnée"}

            plans_dispo = st.session_state.get("plans", [])
            if not plans_dispo:
                st.markdown(
                    "<div style='background:#f8fafc;border:1.5px dashed #cbd5e1;"
                    "border-radius:12px;padding:40px;text-align:center'>"
                    "<div style='font-size:2.5rem;margin-bottom:8px'>🗺️</div>"
                    "<div style='font-weight:700;color:#475569;margin-bottom:4px'>"
                    "Aucun plan disponible</div>"
                    "<div style='font-size:.8rem;color:#94a3b8'>"
                    "Créez des plans dans <strong>Paramètres → Plans</strong>.</div></div>",
                    unsafe_allow_html=True)
            else:
                plan_sel_name = st.selectbox(
                    "Plan à afficher",
                    [p["name"] for p in plans_dispo],
                    key="hist_tab_plan_sel")
                plan_sel = next((p for p in plans_dispo if p["name"] == plan_sel_name), None)

                # ── Filtres ───────────────────────────────────────────────────
                st.markdown(
                    "<div style='background:#f0f9ff;border:1px solid #bae6fd;"
                    "border-radius:10px;padding:12px 16px;margin:8px 0 12px 0'>"
                    "<div style='font-size:.8rem;font-weight:700;color:#0369a1;"
                    "margin-bottom:8px'>🔍 Filtres</div>",
                    unsafe_allow_html=True)
                fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 2, 2])
                all_dates_plan = [_parse_date(r.get("date","")) for r in surv_f
                                  if _parse_date(r.get("date",""))]
                d_min_plan = min(all_dates_plan) if all_dates_plan else dt_date.today()
                d_max_plan = max(all_dates_plan) if all_dates_plan else dt_date.today()
                with fc1:
                    filt_date_debut = st.date_input("Du", value=d_min_plan,
                        min_value=d_min_plan, max_value=d_max_plan,
                        key="hist_tab_plan_date_debut")
                with fc2:
                    filt_date_fin = st.date_input("Au", value=d_max_plan,
                        min_value=d_min_plan, max_value=d_max_plan,
                        key="hist_tab_plan_date_fin")
                with fc3:
                    filt_points = st.multiselect("Points",
                        sorted({r.get("prelevement","") for r in surv_f
                                if r.get("prelevement")}),
                        placeholder="Tous les points",
                        key="hist_tab_plan_filt_pts")
                with fc4:
                    filt_germs = st.multiselect("Germes",
                        sorted({r.get("germ_match","") for r in surv_f
                                if r.get("germ_match") and
                                r.get("germ_match") not in ("Négatif","—","")}),
                        placeholder="Tous les germes",
                        key="hist_tab_plan_filt_germs")
                st.markdown("</div>", unsafe_allow_html=True)

                _surv_plan_all = [
                    r for r in surv_f
                    if (_parse_date(r.get("date","")) is not None
                        and filt_date_debut <= _parse_date(r.get("date","")) <= filt_date_fin)
                    and (not filt_points or r.get("prelevement","") in filt_points)
                    and (not filt_germs  or r.get("germ_match","")  in filt_germs)
                ]
                
                # Dédupliquer par sample_id : garder le pire résultat (action > alert > ok)
                # Si pas de sample_id (ancienne entrée), on garde toutes
                prio = {"ok": 0, "alert": 1, "action": 2}   # ← AJOUTER CETTE LIGNE
                _seen_sample_ids = {}
                surv_plan = []
                for r in _surv_plan_all:
                    sid = r.get("sample_id", "")
                    if not sid:
                        surv_plan.append(r)
                        continue
                    if sid not in _seen_sample_ids:
                        _seen_sample_ids[sid] = r
                    else:
                        existing = _seen_sample_ids[sid]
                        if prio.get(r.get("status","ok"),0) > prio.get(existing.get("status","ok"),0):
                            _seen_sample_ids[sid] = r

                surv_plan = [r for r in _surv_plan_all if not r.get("sample_id","")]
                surv_plan += list(_seen_sample_ids.values())
                surv_plan.sort(key=lambda x: _parse_date(x.get("date","")) or dt_date.min)

                # ── Métriques ─────────────────────────────────────────────────
                nb_action = sum(1 for r in surv_plan if r.get("status")=="action")
                nb_alert  = sum(1 for r in surv_plan if r.get("status")=="alert")
                nb_ok     = sum(1 for r in surv_plan if r.get("status")=="ok")
                nb_pts_pos = len({r.get("prelevement") for r in surv_plan
                                  if pt_coords.get(r.get("prelevement",""))})
                m1,m2,m3,m4,m5 = st.columns(5)
                m1.metric("📋 Prélèvements", len(surv_plan))
                m2.metric("✅ Conformes", nb_ok)
                m3.metric("⚠️ Alertes",   nb_alert)
                m4.metric("🚨 Actions",    nb_action)
                m5.metric("📍 Points",     nb_pts_pos)

                pts_no_coords = {r.get("prelevement","") for r in surv_plan} - set(pt_coords.keys())
                pts_no_coords.discard("")
                if pts_no_coords:
                    st.info(
                        f"💡 **{len(pts_no_coords)} point(s)** sans position sur ce plan : "
                        f"**{', '.join(sorted(pts_no_coords))}**. "
                        f"Positionnez-les via **Surveillance → Nouveau prélèvement**.")

                # ── Construction pts_on_plan ──────────────────────────────────
                # Grouper par coordonnées exactes → une pastille par groupe
                # Si N prélèvements au même endroit : pastille avec chiffre N
                # Si 1 prélèvement : pastille avec UFC ou ✓
                from collections import defaultdict as _dd
                prio = {"action":2,"alert":1,"ok":0,"none":-1}
                
                # Grouper par LABEL (pas par coordonnées) → chaque point garde sa position unique
                label_groups = _dd(list)
                for r in surv_plan:
                    pt_label = r.get("prelevement","")
                    if not pt_label:
                        continue
                    coords = pt_coords.get(pt_label)
                    if not coords:
                        continue
                    label_groups[pt_label].append({
                        "label":  pt_label,
                        "x":      coords["x"],
                        "y":      coords["y"],
                        "status": r.get("status","ok"),
                        "ufc":    int(r.get("ufc",0) or 0),
                        "germ":   r.get("germ_match","—") or "—",
                        "date":   r.get("date","—"),
                        "oper":   r.get("operateur","—") or "—",
                    })
                
                pts_on_plan = []
                for pt_label, items in label_groups.items():
                    n      = len(items)
                    worst  = max(items, key=lambda x: prio.get(x["status"],0))
                    w_st   = worst["status"]
                    w_col  = STATUS_COL.get(w_st,"#94a3b8")
                    # Coordonnées exactes du point (toutes les entrées ont les mêmes coords pour ce label)
                    cx = items[0]["x"]
                    cy = items[0]["y"]
                    # Trier les détails par date décroissante
                    details = sorted(items, key=lambda x: x["date"], reverse=True)
                
                    if n == 1:
                        it = items[0]
                        txt = str(it["ufc"]) if it["ufc"] > 0 else "✓"
                    else:
                        txt = str(n)  # Chiffre = nombre de prélèvements pour ce point
                
                    pts_on_plan.append({
                        "label":   pt_label,
                        "x":       cx,
                        "y":       cy,
                        "status":  w_st,
                        "color":   w_col,
                        "text":    txt,
                        "count":   n,
                        "grouped": n > 1,
                        "details": details,
                    })

                pts_json = _json_plan.dumps(pts_on_plan, ensure_ascii=False)

                if plan_sel and plan_sel.get("image_b64"):
                    img_b64 = plan_sel["image_b64"]
                    if not img_b64.startswith("data:"):
                        img_b64 = "data:image/png;base64," + img_b64

                    plan_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f172a;font-family:'Segoe UI',sans-serif;height:100vh;
     display:flex;flex-direction:column;overflow:hidden;color:#f8fafc}}
.header{{padding:8px 14px;background:#1e293b;border-bottom:1px solid #334155;
         display:flex;align-items:center;gap:10px;flex-shrink:0;flex-wrap:wrap}}
.title{{font-size:.82rem;font-weight:800;color:#e2e8f0}}
.legend{{display:flex;gap:10px;margin-left:auto;flex-wrap:wrap}}
.leg-item{{display:flex;align-items:center;gap:5px;font-size:.65rem;color:#94a3b8}}
.leg-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.leg-dot.dashed{{border:2px dashed #94a3b8;background:transparent}}
.main{{flex:1;overflow:auto;background:#1e293b;display:flex;
       align-items:flex-start;justify-content:center;padding:10px}}
.mi{{position:relative;display:inline-block;
     box-shadow:0 6px 32px rgba(0,0,0,.6);border-radius:6px}}
#img{{display:block;max-width:100%;border-radius:6px;user-select:none}}
.pt{{position:absolute;min-width:32px;height:32px;border-radius:16px;
     padding:0 7px;border:3px solid rgba(255,255,255,0.9);cursor:pointer;
     transform:translate(-50%,-50%);
     display:flex;align-items:center;justify-content:center;
     font-size:12px;font-weight:900;color:#fff;
     box-shadow:0 3px 14px rgba(0,0,0,.6);
     z-index:20;transition:transform .15s,box-shadow .15s;white-space:nowrap}}
.pt.grouped{{border-style:dashed;border-width:3px}}
.pt:hover{{transform:translate(-50%,-50%) scale(1.28);
           box-shadow:0 6px 20px rgba(0,0,0,.8)}}
.pt.pulse{{animation:pulse 2s infinite}}
@keyframes pulse{{
  0%,100%{{box-shadow:0 3px 14px rgba(0,0,0,.6)}}
  50%{{box-shadow:0 0 0 8px rgba(239,68,68,.25),0 3px 14px rgba(0,0,0,.6)}}
}}
.tooltip{{position:fixed;background:#0f172a;border:1.5px solid #334155;
          border-radius:10px;padding:10px 14px;font-size:.72rem;
          color:#e2e8f0;z-index:9999;pointer-events:none;
          max-width:270px;box-shadow:0 8px 32px rgba(0,0,0,.7);
          display:none;line-height:1.6}}
.tooltip.show{{display:block}}
.tt-name{{font-weight:800;font-size:.84rem;margin-bottom:4px}}
.tt-badge{{display:inline-block;border-radius:4px;padding:1px 8px;
           font-size:.62rem;font-weight:700;margin-bottom:6px}}
.tt-sep{{border:none;border-top:1px solid #1e3a5f;margin:5px 0}}
.tt-row{{color:#94a3b8;font-size:.65rem;padding:1px 0}}
.tt-row b{{color:#e2e8f0}}
.empty{{position:absolute;top:50%;left:50%;
        transform:translate(-50%,-50%);
        color:#475569;font-size:.85rem;text-align:center;
        padding:40px;width:80%}}
</style></head><body>
<div class="header">
  <div class="title">🗺️ {plan_sel_name}</div>
  <div class="legend">
    <div class="leg-item"><div class="leg-dot" style="background:#22c55e"></div>Conforme</div>
    <div class="leg-item"><div class="leg-dot" style="background:#f59e0b"></div>Alerte</div>
    <div class="leg-item"><div class="leg-dot" style="background:#ef4444"></div>Action</div>
    <div class="leg-item">
      <div class="leg-dot dashed"></div>
      Groupé (N prélèvements)
    </div>
  </div>
</div>
<div class="main"><div class="mi" id="mi">
  <img id="img" src="{img_b64}" draggable="false">
</div></div>
<div class="tooltip" id="tt"></div>
<script>
const PTS = {pts_json};
const STATUS_LABELS = {{
  action:"🚨 ACTION", alert:"⚠️ ALERTE",
  ok:"✅ Conforme", none:"⬜ Sans données"
}};
const STATUS_BG = {{
  action:"rgba(239,68,68,.2)", alert:"rgba(245,158,11,.2)",
  ok:"rgba(34,197,94,.2)",     none:"rgba(148,163,184,.2)"
}};
const STATUS_COL = {{
  action:"#ef4444", alert:"#f59e0b",
  ok:"#22c55e",     none:"#94a3b8"
}};
const ST_IC = {{action:"🚨", alert:"⚠️", ok:"✅", none:"⬜"}};
const tt = document.getElementById('tt');
const mi = document.getElementById('mi');

function render() {{
  document.querySelectorAll('.pt,.empty').forEach(p => p.remove());
  if (!PTS.length) {{
    const em = document.createElement('div');
    em.className = 'empty';
    em.innerHTML =
      '<div><div style="font-size:2rem;margin-bottom:8px">📍</div>'
      + '<div>Aucun prélèvement positionné sur ce plan.</div>'
      + '<div style="font-size:.72rem;color:#64748b;margin-top:4px">'
      + 'Placez des points via Surveillance → Nouveau prélèvement</div></div>';
    mi.appendChild(em);
    return;
  }}
  PTS.forEach(pt => {{
    const el = document.createElement('div');
    el.className = 'pt'
      + (pt.status === 'action' ? ' pulse' : '')
      + (pt.grouped ? ' grouped' : '');
    el.style.left    = pt.x + '%';
    el.style.top     = pt.y + '%';
    el.style.background = pt.color;
    el.textContent   = pt.text;
    el.addEventListener('mouseenter', e => showTT(e, pt));
    el.addEventListener('mouseleave', hideTT);
    el.addEventListener('mousemove',  moveTT);
    mi.appendChild(el);
  }});
}}

function showTT(e, pt) {{
  const lbl = STATUS_LABELS[pt.status] || pt.status;
  const bg  = STATUS_BG[pt.status]  || 'rgba(148,163,184,.2)';
  const col = STATUS_COL[pt.status] || '#94a3b8';

  let body = '';

  if (pt.grouped) {{
    // Pastille groupée → liste tous les prélèvements
    body += `<div style="font-size:.62rem;color:#64748b;margin-bottom:3px">
               ${{pt.count}} prélèvement(s) à cette position
             </div>`;
    pt.details.slice(0, 6).forEach(d => {{
      const dc = STATUS_COL[d.status] || '#94a3b8';
      const di = ST_IC[d.status] || '⬜';
      body += `<hr class="tt-sep">
        <div class="tt-row">${{di}} <b>${{d.date}}</b> — ${{d.label}}</div>
        <div class="tt-row">🦠 ${{d.germ}}</div>
        <div class="tt-row">🔬 <b>${{d.ufc}} UFC</b> &nbsp;·&nbsp; 👤 ${{d.oper}}</div>`;
    }});
    if (pt.details.length > 6) {{
      body += `<div style="font-size:.6rem;color:#64748b;margin-top:4px">
                 + ${{pt.details.length - 6}} autre(s) prélèvement(s)
               </div>`;
    }}
  }} else {{
    // Pastille simple → détail unique
    const d = pt.details[0];
    body = `
      <div class="tt-row">📅 <b>${{d.date}}</b></div>
      <div class="tt-row">🦠 ${{d.germ}}</div>
      <div class="tt-row">🔬 <b>${{d.ufc}} UFC</b></div>
      <div class="tt-row">👤 ${{d.oper}}</div>`;
  }}

  tt.innerHTML = `
    <div class="tt-name">${{pt.label}}</div>
    <div class="tt-badge"
         style="background:${{bg}};color:${{col}};border:1px solid ${{col}}44">
      ${{lbl}}
    </div>
    ${{body}}
  `;
  tt.classList.add('show');
  moveTT(e);
}}

function moveTT(e) {{
  let x = e.clientX + 14, y = e.clientY - 10;
  if (x + 280 > window.innerWidth)  x = e.clientX - 280;
  if (y + 220 > window.innerHeight) y = e.clientY - 220;
  tt.style.left = x + 'px';
  tt.style.top  = y + 'px';
}}
function hideTT() {{ tt.classList.remove('show'); }}

const img = document.getElementById('img');
if (img.complete && img.naturalWidth > 0) render();
else img.addEventListener('load', render);
img.addEventListener('error', render);
</script></body></html>"""
                    st.components.v1.html(plan_html, height=520, scrolling=False)

                elif plan_sel and not plan_sel.get("image_b64"):
                    st.markdown(
                        "<div style='background:#fffbeb;border:1px solid #fde047;"
                        "border-radius:10px;padding:20px;text-align:center;color:#92400e'>"
                        "⚠️ Ce plan n'a pas d'image. "
                        "Modifiez-le dans <strong>Paramètres → Plans</strong>.</div>",
                        unsafe_allow_html=True)

                st.divider()

                # ── Tableau récapitulatif par point ───────────────────────────
                st.markdown(
                    "<div style='font-size:.88rem;font-weight:700;color:#1e40af;margin-bottom:10px'>"
                    "📋 Récapitulatif par point</div>",
                    unsafe_allow_html=True)

                pt_stats_plan = {}
                for r in surv_plan:
                    pt = r.get("prelevement","—")
                    if pt not in pt_stats_plan:
                        pt_stats_plan[pt] = {
                            "total":0,"ok":0,"alert":0,"action":0,
                            "germes":[],"last_status":"ok",
                            "last_date":"","worst_status":"ok",
                        }
                    s    = pt_stats_plan[pt]
                    s["total"] += 1
                    st_r = r.get("status","ok")
                    s[st_r] = s.get(st_r,0) + 1
                    germ = r.get("germ_match","")
                    if germ and germ not in ("Négatif","—",""):
                        s["germes"].append(germ)
                    d_r = r.get("date","")
                    if d_r >= s["last_date"]:
                        s["last_date"]   = d_r
                        s["last_status"] = st_r
                    if prio.get(st_r,0) > prio.get(s["worst_status"],0):
                        s["worst_status"] = st_r

                if not pt_stats_plan:
                    st.info("Aucun résultat pour les filtres sélectionnés.")
                else:
                    st.markdown(
                        "<div style='display:grid;"
                        "grid-template-columns:2.2fr 0.6fr 0.6fr 0.6fr 0.7fr 0.9fr 1.8fr 1.2fr;"
                        "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff'>Point</div>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Total</div>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>✅</div>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>⚠️</div>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🚨</div>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Pire</div>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff'>Germes</div>"
                        "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Dernier</div>"
                        "</div>",
                        unsafe_allow_html=True)
                    for ri,(pt_label,s) in enumerate(sorted(
                            pt_stats_plan.items(),
                            key=lambda x:({"action":0,"alert":1,"ok":2}.get(x[1]["worst_status"],3),x[0]))):
                        ws   = s["worst_status"]
                        wsc  = STATUS_COL.get(ws,"#94a3b8")
                        wsl  = STATUS_LBL.get(ws,"—")
                        wsi  = STATUS_IC.get(ws,"⬜")
                        has_pos   = pt_label in pt_coords
                        pos_badge = (
                            " <span style='background:#dbeafe;color:#1e40af;"
                            "border-radius:3px;padding:0 4px;font-size:.55rem'>📍</span>"
                            if has_pos else
                            " <span style='background:#fef2f2;color:#991b1b;"
                            "border-radius:3px;padding:0 4px;font-size:.55rem'>?</span>")
                        germes_str = ", ".join(sorted(set(s["germes"]))[:3]) or "—"
                        _ls  = s["last_status"]
                        _lsc = STATUS_COL.get(_ls,"#94a3b8")
                        _lsi = STATUS_IC.get(_ls,"⬜")
                        _ld  = s["last_date"][:10] if s["last_date"] else "—"
                        row_bg = "#f8fafc" if ri%2==0 else "#ffffff"
                        st.markdown(
                            "<div style='display:grid;"
                            "grid-template-columns:2.2fr 0.6fr 0.6fr 0.6fr 0.7fr 0.9fr 1.8fr 1.2fr;"
                            f"gap:4px;background:{row_bg};border:1px solid #e2e8f0;border-top:none;"
                            "padding:9px 14px;align-items:center'>"
                            f"<div style='font-size:.85rem;font-weight:700;color:#0f172a'>📍 {pt_label}{pos_badge}</div>"
                            f"<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>{s['total']}</div>"
                            f"<div style='font-size:.9rem;font-weight:700;color:#22c55e;text-align:center'>{s.get('ok',0)}</div>"
                            f"<div style='font-size:.9rem;font-weight:700;color:#f59e0b;text-align:center'>{s.get('alert',0)}</div>"
                            f"<div style='font-size:.9rem;font-weight:700;color:#ef4444;text-align:center'>{s.get('action',0)}</div>"
                            f"<div style='text-align:center'>"
                            f"<span style='background:{wsc}22;color:{wsc};border:1px solid {wsc}55;"
                            f"border-radius:6px;padding:2px 8px;font-size:.68rem;font-weight:700'>"
                            f"{wsi} {wsl}</span></div>"
                            f"<div style='font-size:.72rem;color:#475569;font-style:italic'>{germes_str}</div>"
                            f"<div style='font-size:.72rem;font-weight:600;color:#475569;text-align:center'>"
                            f"{_ld}<br><span style='color:{_lsc};font-size:.62rem'>{_lsi}</span></div>"
                            "</div>",
                            unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                        f"<div style='font-size:.78rem;color:#94a3b8'>"
                        f"{len(pt_stats_plan)} point(s) · {len(surv_plan)} prélèvement(s) "
                        f"· <span style='color:#86efac'>📍 positionné</span> "
                        f"· <span style='color:#fca5a5'>? non positionné</span>"
                        f"</div></div>",
                        unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # ONGLET 1 : STATS PAR POINT
        # ══════════════════════════════════════════════════════════════════════
        with hist_tab_pts:
            from collections import defaultdict
            import json as _json_pts

            pts_stats = defaultdict(lambda: {
                "total":0,"positives":0,"negatives":0,
                "alertes":0,"actions":0,
                "germes":defaultdict(int),
                "ufc_j2_list":[],"ufc_j7_list":[],
            })
            for r in surv_f:
                pt     = r.get("prelevement","—")
                ufc    = int(r.get("ufc",0) or 0)
                germ   = r.get("germ_match","") or ""
                st_r   = r.get("status","ok")
                ufc_j2 = int(r.get("ufc_48h", r.get("ufc",0)) or 0)
                ufc_j7 = int(r.get("ufc_5j",  r.get("ufc",0)) or 0)
                pts_stats[pt]["total"] += 1
                if ufc > 0 and germ not in ("Négatif","—",""):
                    pts_stats[pt]["positives"] += 1
                    pts_stats[pt]["germes"][germ] += 1
                else:
                    pts_stats[pt]["negatives"] += 1
                if st_r == "alert":    pts_stats[pt]["alertes"]  += 1
                elif st_r == "action": pts_stats[pt]["actions"]  += 1
                if ufc_j2 > 0: pts_stats[pt]["ufc_j2_list"].append(ufc_j2)
                if ufc_j7 > 0: pts_stats[pt]["ufc_j7_list"].append(ufc_j7)

            sorted_pts   = sorted(pts_stats.items(), key=lambda x: -x[1]["positives"])
            chart_labels = [p[:22]+"…" if len(p)>22 else p for p,_ in sorted_pts]
            chart_data   = {
                "labels": chart_labels,
                "neg": [d["negatives"] for _,d in sorted_pts],
                "pos": [d["positives"] for _,d in sorted_pts],
            }
            chart_html = f"""
            <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                        padding:16px;margin-bottom:18px">
              <div style="font-size:.8rem;font-weight:700;color:#1e40af;margin-bottom:10px">
                📊 Résultats par point de prélèvement
              </div>
              <div style="width:100%;height:180px"><canvas id="ptChart"></canvas></div>
            </div>
            <script>
            (function(){{
              const d = {_json_pts.dumps(chart_data)};
              new Chart(document.getElementById('ptChart'), {{
                type:'bar',
                data:{{
                  labels:d.labels,
                  datasets:[
                    {{label:'✅ Négatifs',data:d.neg,backgroundColor:'#22c55e88',borderColor:'#22c55e',borderWidth:1}},
                    {{label:'🦠 Positifs',data:d.pos,backgroundColor:'#ef444488',borderColor:'#ef4444',borderWidth:1}}
                  ]
                }},
                options:{{
                  responsive:true,maintainAspectRatio:false,
                  plugins:{{legend:{{position:'top',labels:{{font:{{size:11}}}}}}}},
                  scales:{{
                    x:{{stacked:true,ticks:{{font:{{size:10}}}}}},
                    y:{{stacked:true,beginAtZero:true,ticks:{{stepSize:1,font:{{size:10}}}}}}
                  }}
                }}
              }});
            }})();
            </script>"""
            st.components.v1.html(chart_html, height=240)

            st.markdown(
                "<div style='display:grid;"
                "grid-template-columns:2fr 0.55fr 0.55fr 0.55fr 0.7fr 0.7fr 0.7fr 1.8fr;"
                "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff'>Point</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Total</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>✅</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🦠</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Taux+</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#7dd3fc;text-align:center'>Moy J2</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#c4b5fd;text-align:center'>Moy J7</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff'>Germes détectés</div>"
                "</div>",
                unsafe_allow_html=True)
            for ri,(pt_name,pt_data) in enumerate(sorted_pts):
                t     = pt_data["total"]
                pos   = pt_data["positives"]
                taux  = pos/t*100 if t>0 else 0
                tc    = "#ef4444" if taux>=50 else "#f59e0b" if taux>0 else "#22c55e"
                germes_str = ", ".join(
                    g+"("+str(n)+"x)"
                    for g,n in sorted(pt_data["germes"].items(),key=lambda x:-x[1])[:3]
                ) or "—"
                j2_list = pt_data["ufc_j2_list"]
                j7_list = pt_data["ufc_j7_list"]
                moy_j2  = str(round(sum(j2_list)/len(j2_list))) if j2_list else "—"
                moy_j7  = str(round(sum(j7_list)/len(j7_list))) if j7_list else "—"
                row_bg  = "#f8fafc" if ri%2==0 else "#ffffff"
                st.markdown(
                    "<div style='display:grid;"
                    "grid-template-columns:2fr 0.55fr 0.55fr 0.55fr 0.7fr 0.7fr 0.7fr 1.8fr;"
                    "gap:4px;background:"+row_bg+";border:1px solid #e2e8f0;border-top:none;"
                    "padding:9px 14px;align-items:center'>"
                    "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>📍 "+pt_name+"</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>"+str(t)+"</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#22c55e;text-align:center'>"+str(pt_data["negatives"])+"</div>"
                    "<div style='text-align:center'><span style='background:"+tc+"22;color:"+tc+";"
                    "border:1px solid "+tc+"55;border-radius:6px;padding:2px 7px;"
                    "font-size:.8rem;font-weight:700'>"+str(pos)+"</span></div>"
                    "<div style='font-size:.85rem;font-weight:700;color:"+tc+";text-align:center'>"+str(round(taux))+"%</div>"
                    "<div style='font-size:.82rem;font-weight:700;color:#0369a1;text-align:center'>"+moy_j2+"</div>"
                    "<div style='font-size:.82rem;font-weight:700;color:#7c3aed;text-align:center'>"+moy_j7+"</div>"
                    "<div style='font-size:.72rem;color:#475569;font-style:italic'>"+germes_str+"</div>"
                    "</div>",
                    unsafe_allow_html=True)
            st.markdown(
                "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                "<div style='font-size:.78rem;color:#94a3b8'>"
                +str(len(pts_stats))+" point(s) — "+str(total_f)+" résultats"
                +" &nbsp;|&nbsp; <span style='color:#7dd3fc'>J2 = 48h</span>"
                +" &nbsp;|&nbsp; <span style='color:#c4b5fd'>J7 = 5 jours</span>"
                "</div></div>",
                unsafe_allow_html=True)

            st.divider()
            st.markdown(
                "<div style='font-size:.85rem;font-weight:700;color:#1e40af;margin-bottom:8px'>"
                "📈 Évolution UFC dans le temps</div>",
                unsafe_allow_html=True)
            pt_choices = [p for p,_ in sorted_pts]
            if pt_choices:
                selected_pt = st.selectbox("Point", options=pt_choices,
                    key="hist_pt_evol", label_visibility="collapsed")
                pt_records = sorted(
                    [r for r in surv_f if r.get("prelevement")==selected_pt],
                    key=lambda x: _parse_date(x.get("date","")) or dt_date.min)
                evol_dates=[]; evol_j2=[]; evol_j7=[]
                seuil_alerte=None; seuil_action=None
                for r in pt_records:
                    d = _parse_date(r.get("date",""))
                    if not d: continue
                    evol_dates.append(d.strftime("%d/%m/%y"))
                    evol_j2.append(int(r.get("ufc_48h",r.get("ufc",0)) or 0))
                    evol_j7.append(int(r.get("ufc_5j", r.get("ufc",0)) or 0))
                    if seuil_alerte is None:
                        try: seuil_alerte=int(float(r.get("alert_threshold",50) or 50))
                        except: seuil_alerte=50
                        try: seuil_action=int(float(r.get("action_threshold",100) or 100))
                        except: seuil_action=100
                if evol_dates:
                    evol_data={"dates":evol_dates,"j2":evol_j2,"j7":evol_j7,
                               "alerte":seuil_alerte,"action":seuil_action}
                    evol_html = f"""
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
                    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                                padding:16px;margin-bottom:8px">
                      <div style="font-size:.78rem;font-weight:700;color:#334155;margin-bottom:10px">
                        📍 {selected_pt} — UFC/m³ au fil du temps
                      </div>
                      <div style="width:100%;height:220px"><canvas id="evolChart"></canvas></div>
                    </div>
                    <script>
                    (function(){{
                      const d={_json_pts.dumps(evol_data)};
                      const thr={{id:'thr',afterDraw(chart){{
                        const {{ctx,chartArea:{{left,right}},scales:{{y}}}}=chart;
                        if(!y)return;
                        function dl(val,color,lbl){{
                          const yp=y.getPixelForValue(val);
                          ctx.save();ctx.beginPath();ctx.setLineDash([6,4]);
                          ctx.strokeStyle=color;ctx.lineWidth=1.5;
                          ctx.moveTo(left,yp);ctx.lineTo(right,yp);ctx.stroke();
                          ctx.setLineDash([]);ctx.fillStyle=color;
                          ctx.font='bold 10px sans-serif';
                          ctx.fillText(lbl,right-56,yp-4);ctx.restore();
                        }}
                        dl(d.alerte,'#f59e0b','⚠ Alerte');
                        dl(d.action,'#ef4444','🚨 Action');
                      }}}};
                      new Chart(document.getElementById('evolChart'),{{
                        type:'line',plugins:[thr],
                        data:{{labels:d.dates,datasets:[
                          {{label:'🔵 J2',data:d.j2,borderColor:'#0ea5e9',
                            backgroundColor:'#0ea5e922',borderWidth:2,pointRadius:4,tension:0.3,fill:false}},
                          {{label:'🟣 J7',data:d.j7,borderColor:'#8b5cf6',
                            backgroundColor:'#8b5cf622',borderWidth:2,pointRadius:4,tension:0.3,fill:false}}
                        ]}},
                        options:{{responsive:true,maintainAspectRatio:false,
                          interaction:{{mode:'index',intersect:false}},
                          plugins:{{legend:{{position:'top',labels:{{font:{{size:11}},boxWidth:14}}}},
                            tooltip:{{callbacks:{{footer:items=>{{
                              const v=items[0]?.parsed?.y??0;
                              return v>=d.action?'🚨 ACTION':v>=d.alerte?'⚠️ ALERTE':'✅ Conforme';
                            }}}}}}}},
                          scales:{{
                            x:{{ticks:{{font:{{size:10}},maxRotation:45}}}},
                            y:{{beginAtZero:true,
                              title:{{display:true,text:'UFC/m³',font:{{size:10}}}},
                              ticks:{{font:{{size:10}}}}}}
                          }}
                        }}
                      }});
                    }})();
                    </script>"""
                    st.components.v1.html(evol_html, height=290)
                    st.caption(f"⚠️ Alerte ≥ {seuil_alerte} · 🚨 Action ≥ {seuil_action} · {len(evol_dates)} mesure(s)")
                else:
                    st.info("Aucune donnée datée pour ce point.")

            st.divider()
            st.markdown(
                "<div style='font-size:.85rem;font-weight:700;color:#1e40af;margin-bottom:4px'>"
                "🚨 Alertes pondérées</div>"
                "<div style='font-size:.72rem;color:#64748b;margin-bottom:10px'>"
                "Score = criticité germe (1→5) + dépassement (Alerte +1 / Action +3)</div>",
                unsafe_allow_html=True)
            alertes_list=[]
            for r in surv_f:
                germ=r.get("germ_match","") or ""
                st_r=r.get("status","ok")
                ufc=int(r.get("ufc",0) or 0)
                if germ in ("Négatif","—","") or ufc==0: continue
                crit=_get_criticite(germ)
                if st_r=="ok" and crit<4: continue
                score=crit
                if st_r=="action":   score+=3; niveau="ACTION"
                elif st_r=="alert":  score+=1; niveau="ALERTE"
                else:                niveau="—"
                if score>=7:   gravite,g_bg,g_brd="🔴 CRITIQUE","#fef2f2","#fca5a5"
                elif score>=5: gravite,g_bg,g_brd="🟠 MAJEUR","#fff7ed","#fed7aa"
                elif score>=3: gravite,g_bg,g_brd="🟡 MODÉRÉ","#fefce8","#fde68a"
                else:          gravite,g_bg,g_brd="🟢 LIMITÉ","#f0fdf4","#bbf7d0"
                alertes_list.append({
                    "date":r.get("date","—"),"point":r.get("prelevement","—"),
                    "germ":germ,"ufc":ufc,"crit":crit,"crit_lbl":_crit_label(crit),
                    "niveau":niveau,"score":score,"gravite":gravite,"g_bg":g_bg,"g_brd":g_brd,
                })
            alertes_list.sort(key=lambda x:-x["score"])
            if not alertes_list:
                st.success("✅ Aucune alerte pondérée sur la période.")
            else:
                st.markdown(
                    "<div style='display:grid;"
                    "grid-template-columns:0.8fr 1.5fr 1.8fr 0.6fr 0.7fr 0.6fr 0.5fr 1fr;"
                    "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff'>Date</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff'>Point</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff'>Germe</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>UFC</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Criticité</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Niveau</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Score</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Gravité</div>"
                    "</div>",
                    unsafe_allow_html=True)
                for ai,a in enumerate(alertes_list[:30]):
                    row_bg=a["g_bg"] if ai%2==0 else "#ffffff"
                    niv_c="#ef4444" if a["niveau"]=="ACTION" else "#f59e0b" if a["niveau"]=="ALERTE" else "#94a3b8"
                    cc=_crit_color(a["crit"])
                    st.markdown(
                        "<div style='display:grid;"
                        "grid-template-columns:0.8fr 1.5fr 1.8fr 0.6fr 0.7fr 0.6fr 0.5fr 1fr;"
                        "gap:4px;background:"+row_bg+";border:1px solid "+a["g_brd"]+";border-top:none;"
                        "padding:8px 14px;align-items:center'>"
                        "<div style='font-size:.75rem;color:#475569'>"+a["date"]+"</div>"
                        "<div style='font-size:.8rem;font-weight:600;color:#0f172a'>"+a["point"][:20]+"</div>"
                        "<div style='font-size:.8rem;font-weight:700;color:#1e293b'>🦠 "+a["germ"][:22]+"</div>"
                        "<div style='font-size:.85rem;font-weight:800;color:#1e40af;text-align:center'>"+str(a["ufc"])+"</div>"
                        "<div style='text-align:center'><span style='background:"+cc+"22;color:"+cc+";"
                        "border:1px solid "+cc+"55;border-radius:5px;padding:1px 6px;"
                        "font-size:.72rem;font-weight:700'>"+a["crit_lbl"]+"</span></div>"
                        "<div style='font-size:.78rem;font-weight:700;text-align:center;color:"+niv_c+"'>"+a["niveau"]+"</div>"
                        "<div style='font-size:1.1rem;font-weight:900;text-align:center;color:#1e40af'>"+str(a["score"])+"</div>"
                        "<div style='font-size:.85rem;font-weight:700;text-align:center'>"+a["gravite"]+"</div>"
                        "</div>",
                        unsafe_allow_html=True)
                st.markdown(
                    "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                    "<div style='font-size:.78rem;color:#94a3b8'>"
                    +str(len(alertes_list))+" alerte(s)"
                    +(" — 30 premières affichées" if len(alertes_list)>30 else "")
                    +"</div></div>",
                    unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # ONGLET 2 : STATS PAR GERME
        # ══════════════════════════════════════════════════════════════════════
        with hist_tab_germs:
            from collections import defaultdict
            import json as _json_germs

            germs_stats=defaultdict(lambda:{"count":0,"ufc_sum":0,"points":set(),"criticite":0})
            total_pos=0
            for r in surv_f:
                germ=r.get("germ_match","") or ""
                if germ in ("Négatif","—","") or int(r.get("ufc",0) or 0)==0: continue
                total_pos+=1
                germs_stats[germ]["count"]+=1
                germs_stats[germ]["ufc_sum"]+=int(r.get("ufc",0) or 0)
                germs_stats[germ]["points"].add(r.get("prelevement","—"))
                if germs_stats[germ]["criticite"]==0:
                    germs_stats[germ]["criticite"]=_get_criticite(germ)
            if not germs_stats:
                st.info("Aucun germe positif dans l'historique.")
            else:
                sorted_germs=sorted(germs_stats.items(),key=lambda x:-x[1]["count"])
                palette=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e",
                         "#06b6d4","#6366f1","#a855f7","#ec4899","#14b8a6"]
                g_labels=[g[:28] for g,_ in sorted_germs]
                g_counts=[d["count"] for _,d in sorted_germs]
                g_colors=[palette[i%len(palette)] for i in range(len(g_labels))]
                gchart_html=f"""
                <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                            padding:16px;margin-bottom:18px">
                  <div style="font-size:.8rem;font-weight:700;color:#1e40af;margin-bottom:10px">
                    📊 Distribution des germes positifs
                  </div>
                  <div style="width:100%;max-width:400px;height:280px;margin:0 auto">
                    <canvas id="germDoughnut"></canvas>
                  </div>
                </div>
                <script>
                (function(){{
                  const d={_json_germs.dumps({"labels":g_labels,"counts":g_counts,"colors":g_colors})};
                  new Chart(document.getElementById('germDoughnut'),{{
                    type:'doughnut',
                    data:{{labels:d.labels,datasets:[{{data:d.counts,backgroundColor:d.colors,borderWidth:2}}]}},
                    options:{{responsive:true,maintainAspectRatio:false,
                      plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},boxWidth:14,padding:10}}}}}}}}
                  }});
                }})();
                </script>"""
                st.components.v1.html(gchart_html, height=360)
                st.markdown(
                    "<div style='display:grid;"
                    "grid-template-columns:2fr 0.6fr 1fr 0.9fr 0.9fr 1.5fr;"
                    "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff'>Germe</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Cas</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>% positifs</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Moy. UFC</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Criticité</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff'>Points touchés</div>"
                    "</div>",
                    unsafe_allow_html=True)
                for gi,(gname,gdata) in enumerate(sorted_germs):
                    pct=gdata["count"]/total_pos*100 if total_pos>0 else 0
                    avg_ufc=gdata["ufc_sum"]/gdata["count"] if gdata["count"]>0 else 0
                    pts_str=", ".join(list(gdata["points"])[:3])
                    crit=gdata["criticite"]; cc=_crit_color(crit)
                    row_bg="#f8fafc" if gi%2==0 else "#ffffff"
                    crit_cell=(
                        "<span style='background:"+cc+"22;color:"+cc+";border:1px solid "+cc+"55;"
                        "border-radius:5px;padding:1px 7px;font-size:.72rem;font-weight:700'>"
                        +str(crit)+" – "+_crit_label(crit)+"</span>"
                        if crit>0 else "<span style='color:#94a3b8'>—</span>")
                    st.markdown(
                        "<div style='display:grid;"
                        "grid-template-columns:2fr 0.6fr 1fr 0.9fr 0.9fr 1.5fr;"
                        "gap:4px;background:"+row_bg+";border:1px solid #e2e8f0;border-top:none;"
                        "padding:9px 14px;align-items:center'>"
                        "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>🦠 "+gname+"</div>"
                        "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>"+str(gdata["count"])+"</div>"
                        "<div style='text-align:center'>"
                        "<div style='background:#e2e8f0;border-radius:4px;height:8px;margin-bottom:2px'>"
                        "<div style='background:#ef4444;border-radius:4px;height:8px;width:"+str(int(pct))+"%'></div></div>"
                        "<span style='font-size:.75rem;font-weight:700;color:#ef4444'>"+str(round(pct,1))+"%</span></div>"
                        "<div style='font-size:.85rem;font-weight:700;color:#475569;text-align:center'>"+str(round(avg_ufc))+"</div>"
                        "<div style='text-align:center'>"+crit_cell+"</div>"
                        "<div style='font-size:.72rem;color:#475569;font-style:italic'>"+pts_str+"</div>"
                        "</div>",
                        unsafe_allow_html=True)
                st.markdown(
                    "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                    "<div style='font-size:.78rem;color:#94a3b8'>"
                    +str(len(germs_stats))+" germe(s) — "+str(total_pos)+" positifs"
                    "</div></div>",
                    unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # ONGLET 3 : RÉPARTITION PAR PRÉLEVEUR
        # ══════════════════════════════════════════════════════════════════════
        with hist_tab_prev:
            from collections import defaultdict

            prev_stats=defaultdict(lambda:{
                "total":0,"positives":0,"negatives":0,
                "alertes":0,"actions":0,"germes":defaultdict(int)
            })
            for r in surv_f:
                op=(r.get("operateur","") or "Non renseigné").strip() or "Non renseigné"
                ufc=int(r.get("ufc",0) or 0)
                germ=r.get("germ_match","") or ""
                st_r=r.get("status","ok")
                prev_stats[op]["total"]+=1
                if ufc>0 and germ not in ("Négatif","—",""):
                    prev_stats[op]["positives"]+=1
                    prev_stats[op]["germes"][germ]+=1
                else:
                    prev_stats[op]["negatives"]+=1
                if st_r=="alert":    prev_stats[op]["alertes"]+=1
                elif st_r=="action": prev_stats[op]["actions"]+=1

            op_list=sorted(prev_stats.items(),key=lambda x:-x[1]["total"])
            card_cols=st.columns(min(len(op_list),4))
            for ci,(op_name,op_data) in enumerate(op_list):
                t=op_data["total"]; pos=op_data["positives"]
                taux_pos=pos/t*100 if t>0 else 0
                tc="#ef4444" if taux_pos>=30 else "#f59e0b" if taux_pos>0 else "#22c55e"
                ini=op_name[0].upper() if op_name!="Non renseigné" else "?"
                with card_cols[ci%len(card_cols)]:
                    st.markdown(
                        "<div style='background:#fff;border:1.5px solid #e2e8f0;border-radius:14px;"
                        "padding:18px 14px;text-align:center;margin-bottom:12px'>"
                        "<div style='background:#2563eb;color:#fff;border-radius:50%;width:48px;height:48px;"
                        "display:flex;align-items:center;justify-content:center;font-weight:800;"
                        "font-size:1.2rem;margin:0 auto 10px auto'>"+ini+"</div>"
                        "<div style='font-size:.92rem;font-weight:700;color:#0f172a;margin-bottom:6px'>"+op_name+"</div>"
                        "<div style='font-size:2rem;font-weight:900;color:#1e40af'>"+str(t)+"</div>"
                        "<div style='font-size:.68rem;color:#64748b;margin-bottom:10px'>résultat(s)</div>"
                        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px'>"
                        "<div style='background:#f0fdf4;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#22c55e'>"+str(op_data["negatives"])+"</div>"
                        "<div style='font-size:.6rem;color:#166534'>✅ Nég.</div></div>"
                        "<div style='background:#fef2f2;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#ef4444'>"+str(pos)+"</div>"
                        "<div style='font-size:.6rem;color:#991b1b'>🦠 Pos.</div></div>"
                        "<div style='background:#fffbeb;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#f59e0b'>"+str(op_data["alertes"])+"</div>"
                        "<div style='font-size:.6rem;color:#92400e'>⚠️ Alerte</div></div>"
                        "<div style='background:#fef2f2;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#dc2626'>"+str(op_data["actions"])+"</div>"
                        "<div style='font-size:.6rem;color:#991b1b'>🚨 Action</div></div></div>"
                        "<div style='margin-top:10px;background:"+tc+"22;border:1px solid "+tc+"55;"
                        "border-radius:8px;padding:5px'>"
                        "<div style='font-size:.8rem;font-weight:800;color:"+tc+"'>"
                        +str(round(taux_pos))+"% positifs</div></div></div>",
                        unsafe_allow_html=True)
            st.divider()
            st.markdown(
                "<div style='display:grid;grid-template-columns:2fr 0.7fr 0.7fr 0.7fr 0.7fr 0.7fr 2fr;"
                "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff'>Préleveur</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Total</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>✅</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🦠</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>⚠️</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🚨</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff'>Germes fréquents</div>"
                "</div>",
                unsafe_allow_html=True)
            for ri,(op_name,op_data) in enumerate(op_list):
                t=op_data["total"]; pos=op_data["positives"]
                taux_pos=pos/t*100 if t>0 else 0
                tc="#ef4444" if taux_pos>=30 else "#f59e0b" if taux_pos>0 else "#22c55e"
                top_g=", ".join(
                    g+"("+str(n)+"x)"
                    for g,n in sorted(op_data["germes"].items(),key=lambda x:-x[1])[:3]
                ) or "—"
                row_bg="#f8fafc" if ri%2==0 else "#ffffff"
                st.markdown(
                    "<div style='display:grid;grid-template-columns:2fr 0.7fr 0.7fr 0.7fr 0.7fr 0.7fr 2fr;"
                    "gap:4px;background:"+row_bg+";border:1px solid #e2e8f0;border-top:none;"
                    "padding:9px 14px;align-items:center'>"
                    "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>👤 "+op_name+"</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>"+str(t)+"</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#22c55e;text-align:center'>"+str(op_data["negatives"])+"</div>"
                    "<div style='text-align:center'><span style='background:"+tc+"22;color:"+tc+";"
                    "border-radius:6px;padding:2px 8px;font-size:.8rem;font-weight:700'>"+str(pos)+"</span></div>"
                    "<div style='font-size:1rem;font-weight:800;color:#f59e0b;text-align:center'>"+str(op_data["alertes"])+"</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#ef4444;text-align:center'>"+str(op_data["actions"])+"</div>"
                    "<div style='font-size:.72rem;color:#475569;font-style:italic'>"+top_g+"</div>"
                    "</div>",
                    unsafe_allow_html=True)
            st.markdown(
                "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                "<div style='font-size:.78rem;color:#94a3b8'>"
                +str(len(op_list))+" préleveur(s)</div></div>",
                unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # ONGLET 4 : LISTE DES ENTRÉES
        # ══════════════════════════════════════════════════════════════════════
        with hist_tab_liste:
            surv_f_indexed = []
            for r in surv_f:
                try:
                    real_i = surv.index(r)
                    surv_f_indexed.append((real_i, r))
                except ValueError:
                    continue

            for real_i, r in reversed(surv_f_indexed):
                ic = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
                with st.expander(
                    ic+" "+r.get("date","—")+" — "+r.get("prelevement","—")
                    +" — "+r.get("germ_match","—")+" — "+str(r.get("ufc","—"))+" UFC/m³"):
                    if st.session_state.get("edit_surv_idx") == real_i:
                        st.markdown("**✏️ Modifier cette entrée**")
                        e1,e2 = st.columns(2)
                        with e1:
                            new_germ      = st.text_input("Germe",    value=r.get("germ_match",""), key=f"es_germ_{real_i}")
                            new_ufc       = st.number_input("UFC",    value=int(r.get("ufc",0) or 0), min_value=0, key=f"es_ufc_{real_i}")
                            new_operateur = st.text_input("Opérateur",value=r.get("operateur",""),  key=f"es_oper_{real_i}")
                        with e2:
                            new_remarque    = st.text_area("Remarque",   value=r.get("remarque",""),   height=70, key=f"es_rem_{real_i}")
                            new_commentaire = st.text_area("Commentaire",value=r.get("commentaire",""),height=70, key=f"es_com_{real_i}")
                        sb1,sb2 = st.columns(2)
                        with sb1:
                            if st.button("💾 Sauvegarder", key=f"es_save_{real_i}",
                                         use_container_width=True, type="primary"):
                                st.session_state.surveillance[real_i].update({
                                    "germ_match":  new_germ,
                                    "germ_saisi":  new_germ,
                                    "ufc":         new_ufc,
                                    "operateur":   new_operateur,
                                    "remarque":    new_remarque,
                                    "commentaire": new_commentaire,
                                })
                                save_surveillance(st.session_state.surveillance)
                                st.session_state["edit_surv_idx"] = None
                                st.rerun()
                        with sb2:
                            if st.button("✕ Annuler", key=f"es_cancel_{real_i}", use_container_width=True):
                                st.session_state["edit_surv_idx"] = None
                                st.rerun()
                    else:
                        c1,c2,c3,c4 = st.columns([3,3,3,1])
                        crit_r = _get_criticite(r.get("germ_match",""))
                        c1.markdown(
                            "**Germe saisi :** "+str(r.get("germ_saisi","—"))
                            +"\n\n**Correspondance :** "+str(r.get("germ_match","—"))
                            +" ("+str(r.get("match_score","—"))+")"
                            +("\n\n**Criticité :** "+str(crit_r)+" – "+_crit_label(crit_r) if crit_r>0 else ""))
                        c2.markdown(
                            "**UFC/m³ :** "+str(r.get("ufc","—"))
                            +"\n\n**Seuil alerte :** "+str(r.get("alert_threshold","—"))
                            +" | **Seuil action :** "+str(r.get("action_threshold","—")))
                        c3.markdown(
                            "**Opérateur :** "+str(r.get("operateur","N/A"))
                            +"\n\n**Remarque :** "+str(r.get("remarque","—")))
                        if r.get("commentaire"):
                            c3.markdown(
                                f"<div style='background:#f5f3ff;border:1px solid #c4b5fd;"
                                f"border-radius:6px;padding:6px 10px;margin-top:6px;"
                                f"font-size:.78rem;color:#5b21b6'>"
                                f"💬 <b>Commentaire :</b> {r['commentaire']}</div>",
                                unsafe_allow_html=True)
                        with c4:
                            if st.button("✏️", key=f"edit_surv_{real_i}", use_container_width=True):
                                st.session_state["edit_surv_idx"] = real_i
                                st.rerun()
                            if st.button("🗑️", key=f"del_surv_{real_i}", use_container_width=True):
                                st.session_state.surveillance.pop(real_i)
                                save_surveillance(st.session_state.surveillance)
                                st.rerun()
    else:
        st.info("Aucun prélèvement enregistré.")
# ═══════════════════════════════════════════════════════════════════════════════
# TAB : PARAMÈTRES — COMPLET
# ═══════════════════════════════════════════════════════════════════════════════

elif active == "parametres":
    can_edit = check_access_protege("Paramètres & Seuils")
    if not can_edit:
        st.info("👁️ Mode lecture seule — connectez-vous pour modifier les paramètres.")
    st.markdown("### ⚙️ Paramètres")

    (subtab_mesures, subtab_points, subtab_plans, subtab_seuils,
     subtab_operateurs, subtab_backup, subtab_supabase, subtab_faq) = st.tabs([
        "📋 Mesures correctives", "📍 Points de prélèvement", "🗺️ Plans",
        "⚖️ Seuils d'alerte", "👤 Opérateurs", "💾 Sauvegarde", "☁️ Base de données", "❓ FAQ"
    ])

    # ── Constantes Points ──────────────────────────────────────────────────────
    LOC_CRIT_OPTS = [
        "1 — Limité",
        "2 — Modéré",
        "3 — Important",
        "4 — Critique",
    ]
    LOC_CRIT_COLORS = {"1": "#22c55e", "2": "#0babf5", "3": "#ee811a", "4": "#f50b0b"}
    LOC_CRIT_LABELS = {"1": "Non critique", "2": "Semi-critique", "3": "Critique", "4": "Critique"}
    PT_FREQ_UNIT_OPTS = ["/ jour", "/ semaine", "/ mois"]

    # ══════════════════════════════════════════════════════════════════════════
    # MESURES CORRECTIVES
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_mesures:
        om = st.session_state.origin_measures
        scope_labels = {
            "all": "🌐 Toutes", "Air": "💨 Air", "Humidité": "💧 Humidité",
            "Flore fécale": "🦠 Flore fécale",
            "Oropharynx / Gouttelettes": "😷 Oropharynx",
            "Peau / Muqueuse": "🖐️ Peau / Muqueuse",
            "Sol / Carton / Surface sèche": "📦 Sol / Surface sèche"
        }
        type_labels  = {"alert": "⚠️ Alerte", "action": "🚨 Action", "both": "⚠️🚨 Alerte & Action"}
        type_colors  = {"alert": "#f59e0b", "action": "#ef4444", "both": "#818cf8"}
        scope_r_map  = {v: k for k, v in scope_labels.items()}
        risk_opts_map = {
            "all": "🌐 Toutes", "1": "🟢 1", "2": "🟢 2", "3": "🟡 3",
            "4": "🟠 4", "5": "🔴 5", "[3,4,5]": "3-4-5",
            "[4,5]": "4-5", "[1,2,3]": "1-2-3"
        }
        risk_opts_rev = {v: k for k, v in risk_opts_map.items()}

        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1])
        with col_f1:
            filter_scope = st.selectbox("Origine",
                ["Tout afficher"] + list(scope_labels.values()),
                label_visibility="collapsed", key="filter_scope")
        with col_f2:
            filter_risk_lbl = st.selectbox("Criticité",
                ["🌐 Tout", "🟢 1", "🟢 2", "🟡 3", "🟠 4", "🔴 5"],
                label_visibility="collapsed", key="filter_risk")
        with col_f3:
            filter_type = st.selectbox("Type",
                ["Tout", "⚠️ Alerte", "🚨 Action"],
                label_visibility="collapsed", key="filter_type")
        with col_f4:
            if can_edit:
                if st.button("➕ Nouvelle", use_container_width=True):
                    st.session_state.show_new_measure = True
                    st.session_state["_edit_mesure_idx"] = None
                    st.rerun()

        active_scope = scope_r_map.get(filter_scope) if filter_scope != "Tout afficher" else None
        active_risk  = filter_risk_lbl.split()[-1] if filter_risk_lbl != "🌐 Tout" else None
        active_type  = ("alert" if "Alerte" in filter_type else "action") if filter_type != "Tout" else None

        if can_edit and st.session_state.get("show_new_measure", False):
            with st.container():
                st.markdown(
                    "<div style='background:#f0fdf4;border:1.5px solid #86efac;"
                    "border-radius:10px;padding:16px;margin-bottom:12px'>",
                    unsafe_allow_html=True)
                st.markdown("#### ➕ Nouvelle mesure")
                nmc1, nmc2, nmc3, nmc4 = st.columns([3, 2, 1.5, 1.5])
                with nmc1:
                    nm_text = st.text_input("Texte *", key="nm_text")
                with nmc2:
                    nm_scope_label = st.selectbox("Origine", list(scope_labels.values()), key="nm_scope")
                    nm_scope = scope_r_map.get(nm_scope_label, "all")
                with nmc3:
                    nm_risk_lbl = st.selectbox("Criticité", list(risk_opts_map.values()), key="nm_risk")
                    nm_risk_key = risk_opts_rev.get(nm_risk_lbl, "all")
                    nm_risk = ("all" if nm_risk_key == "all"
                               else json.loads(nm_risk_key) if nm_risk_key.startswith("[")
                               else int(nm_risk_key))
                with nmc4:
                    nm_type_label = st.selectbox("Type", list(type_labels.values()), key="nm_type")
                    nm_type = {v: k for k, v in type_labels.items()}.get(nm_type_label, "alert")
                nb1, nb2 = st.columns(2)
                with nb1:
                    if st.button("✅ Ajouter", use_container_width=True, key="nm_submit"):
                        if nm_text.strip():
                            om.append({
                                "id":    f"m{len(om)+1:03d}_custom",
                                "text":  nm_text.strip(),
                                "scope": nm_scope,
                                "risk":  nm_risk,
                                "type":  nm_type
                            })
                            save_origin_measures(om, supa=False)
                            st.session_state.origin_measures  = om
                            st.session_state.show_new_measure = False
                            st.rerun()
                with nb2:
                    if st.button("Annuler", use_container_width=True, key="nm_cancel"):
                        st.session_state.show_new_measure = False
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        def _passes_filter(m):
            if active_scope and m["scope"] != active_scope:
                return False
            if active_type and m["type"] != active_type and m["type"] != "both":
                return False
            if active_risk:
                mr = m.get("risk", "all")
                if mr != "all":
                    if isinstance(mr, list):
                        if int(active_risk) not in mr: return False
                    else:
                        if str(mr) != active_risk: return False
            return True

        if st.session_state.get("_mesures_modifiees"):
            st.markdown(
                "<div style='background:#fffbeb;border:1.5px solid #fcd34d;border-radius:8px;"
                "padding:8px 14px;margin-bottom:10px;font-size:.78rem;color:#92400e'>"
                "⚠️ Modifications non sauvegardées — cliquez sur <strong>💾 Sauvegarder</strong>."
                "</div>", unsafe_allow_html=True)

        for m in [m for m in om if _passes_filter(m)]:
            real_idx = om.index(m)
            tcol = type_colors.get(m["type"], "#0f172a")
            tlbl = type_labels.get(m["type"], m["type"])

            if st.session_state.get("_edit_mesure_idx") == real_idx:
                with st.container():
                    st.markdown(
                        "<div style='background:#eff6ff;border:1.5px solid #93c5fd;"
                        "border-radius:10px;padding:14px;margin-bottom:8px'>",
                        unsafe_allow_html=True)
                    st.markdown("**✏️ Modifier la mesure**")
                    ec1, ec2, ec3, ec4 = st.columns([3, 2, 1.5, 1.5])
                    with ec1:
                        new_text = st.text_input("Texte *", value=m.get("text", ""), key=f"em_text_{real_idx}")
                    with ec2:
                        cur_scope_lbl = scope_labels.get(m.get("scope", "all"), "🌐 Toutes")
                        scope_opts    = list(scope_labels.values())
                        scope_idx     = scope_opts.index(cur_scope_lbl) if cur_scope_lbl in scope_opts else 0
                        new_scope_lbl = st.selectbox("Origine", scope_opts, index=scope_idx, key=f"em_scope_{real_idx}")
                        new_scope = scope_r_map.get(new_scope_lbl, "all")
                    with ec3:
                        cur_risk     = m.get("risk", "all")
                        cur_risk_key = (str(cur_risk) if not isinstance(cur_risk, list)
                                        else json.dumps(cur_risk).replace(" ", ""))
                        cur_risk_lbl = risk_opts_map.get(cur_risk_key, "🌐 Toutes")
                        risk_opts_list = list(risk_opts_map.values())
                        risk_idx = risk_opts_list.index(cur_risk_lbl) if cur_risk_lbl in risk_opts_list else 0
                        new_risk_lbl = st.selectbox("Criticité", risk_opts_list, index=risk_idx, key=f"em_risk_{real_idx}")
                        new_risk_key = risk_opts_rev.get(new_risk_lbl, "all")
                        new_risk = ("all" if new_risk_key == "all"
                                    else json.loads(new_risk_key) if new_risk_key.startswith("[")
                                    else int(new_risk_key))
                    with ec4:
                        cur_type_lbl = type_labels.get(m.get("type", "alert"), "⚠️ Alerte")
                        type_opts    = list(type_labels.values())
                        type_idx     = type_opts.index(cur_type_lbl) if cur_type_lbl in type_opts else 0
                        new_type_lbl = st.selectbox("Type", type_opts, index=type_idx, key=f"em_type_{real_idx}")
                        new_type = {v: k for k, v in type_labels.items()}.get(new_type_lbl, "alert")
                    sb1, sb2 = st.columns(2)
                    with sb1:
                        if st.button("✔️ Valider", key=f"em_save_{real_idx}", use_container_width=True, type="primary"):
                            if new_text.strip():
                                om[real_idx]["text"]  = new_text.strip()
                                om[real_idx]["scope"] = new_scope
                                om[real_idx]["risk"]  = new_risk
                                om[real_idx]["type"]  = new_type
                                save_origin_measures(om, supa=False)
                                st.session_state.origin_measures        = om
                                st.session_state["_edit_mesure_idx"]    = None
                                st.session_state["_mesures_modifiees"]  = True
                                st.rerun()
                            else:
                                st.error("Le texte est obligatoire.")
                    with sb2:
                        if st.button("✕ Annuler", key=f"em_cancel_{real_idx}", use_container_width=True):
                            st.session_state["_edit_mesure_idx"] = None
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                rc1, rc2, rc3, rc4, rc5 = st.columns([4.5, 1.2, 1.5, 0.8, 0.8])
                with rc1:
                    st.markdown(
                        f'<div style="padding:6px 0;font-size:.8rem;color:#1e293b">• {m["text"]}</div>',
                        unsafe_allow_html=True)
                with rc3:
                    st.markdown(
                        f'<div style="padding:6px 0;font-size:.65rem;color:{tcol};"'
                        f'font-weight:600;text-align:center">{tlbl}</div>',
                        unsafe_allow_html=True)
                with rc4:
                    if can_edit:
                        if st.button("✏️", key=f"edit_btn_{real_idx}"):
                            st.session_state["_edit_mesure_idx"] = real_idx
                            st.session_state["show_new_measure"] = False
                            st.rerun()
                with rc5:
                    if can_edit:
                        if st.button("🗑️", key=f"del_m_{real_idx}"):
                            om.pop(real_idx)
                            save_origin_measures(om, supa=False)
                            st.session_state.origin_measures       = om
                            st.session_state["_mesures_modifiees"] = True
                            st.rerun()

        col_sr, col_def = st.columns(2)
        with col_sr:
            if can_edit:
                if st.button("💾 Sauvegarder", use_container_width=True, key="save_mesures"):
                    save_origin_measures(om, supa=True)
                    st.session_state["_mesures_modifiees"] = False
                    st.success("✅ Mesures sauvegardées et synchronisées !")
        with col_def:
            if can_edit:
                if st.button("↩️ Réinitialiser", use_container_width=True, key="reinit_mesures"):
                    st.session_state.origin_measures = [dict(m) for m in DEFAULT_ORIGIN_MEASURES]
                    save_origin_measures(st.session_state.origin_measures, supa=True)
                    st.session_state["_mesures_modifiees"] = False
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # POINTS DE PRÉLÈVEMENT
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_points:
        st.markdown("""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
        padding:12px 16px;margin-bottom:16px;font-size:.82rem;color:#1e40af">
        ℹ️ Le <strong>niveau de criticité du lieu</strong> (1–3) est automatiquement repris
        lors de l'identification microbiologique.<br>
        Score total = criticité lieu × score germe · ⚠️ Alerte : 16–24 · 🚨 Action : &gt; 24
        </div>""", unsafe_allow_html=True)

        if not st.session_state.points:
            st.info("Aucun point défini.")
        else:
            st.markdown("""
            <div style="display:grid;
            grid-template-columns:2.2fr 0.7fr 0.7fr 1.3fr 0.9fr 1.1fr 0.5fr 0.5fr;
            gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px">
              <div style="font-size:.72rem;font-weight:800;color:#fff">Point</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Type</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Classe</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Criticité lieu</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Gélose</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Fréquence</div>
              <div></div><div></div>
            </div>""", unsafe_allow_html=True)

            for i, pt in enumerate(list(st.session_state.points)):
                pt_type    = pt.get('type', '—')
                type_icon  = "💨" if pt_type == "Air" else "🧴"
                loc_crit   = str(pt.get('location_criticality', 1))
                lc_color   = LOC_CRIT_COLORS.get(loc_crit, "#94a3b8")
                lc_label   = LOC_CRIT_LABELS.get(loc_crit, "—")
                room_cl    = pt.get('room_class', '—') or '—'
                freq       = pt.get('frequency', 1)
                freq_unit  = pt.get('frequency_unit', '/ semaine')
                freq_short = (str(freq) + "x/" +
                              ("j" if "jour" in freq_unit else
                               "sem" if "sem" in freq_unit else "mois"))
                row_bg = "#f8fafc" if i % 2 == 0 else "#ffffff"

                c1, c2 = st.columns([8, 1])
                with c1:
                    st.markdown(
                        f"<div style='display:grid;"
                        f"grid-template-columns:2.2fr 0.7fr 0.7fr 1.3fr 0.9fr 1.1fr;"
                        f"gap:4px;background:{row_bg};border:1px solid #e2e8f0;"
                        f"border-top:none;padding:9px 14px;align-items:center'>"
                        f"<div style='font-size:.88rem;font-weight:700;color:#0f172a'>"
                        f"{type_icon} {pt['label']}</div>"
                        f"<div style='font-size:.75rem;color:#475569;text-align:center'>{pt_type}</div>"
                        f"<div style='text-align:center'>"
                        f"<span style='background:#dbeafe;color:#1e40af;"
                        f"border:1px solid #93c5fd;border-radius:6px;"
                        f"padding:2px 8px;font-size:.78rem;font-weight:800'>{room_cl}</span></div>"
                        f"<div style='text-align:center'>"
                        f"<span style='background:{lc_color}22;color:{lc_color};"
                        f"border:1px solid {lc_color}55;border-radius:6px;"
                        f"padding:3px 8px;font-size:.68rem;font-weight:700'>"
                        f"Nv.{loc_crit} — {lc_label}</span></div>"
                        f"<div style='font-size:.72rem;color:#1d4ed8;text-align:center'>"
                        f"🧫 {pt.get('gelose', '—')[:12]}</div>"
                        f"<div style='text-align:center'>"
                        f"<span style='background:#eff6ff;color:#1e40af;"
                        f"border:1px solid #bfdbfe;border-radius:6px;"
                        f"padding:2px 8px;font-size:.75rem;font-weight:700'>"
                        f"🔁 {freq_short}</span></div>"
                        f"</div>", unsafe_allow_html=True)
                with c2:
                    be, bd = st.columns(2)
                    with be:
                        if can_edit:
                            if st.button("✏️", key=f"edit_pt_{i}"):
                                st.session_state._edit_point = i
                                st.rerun()
                    with bd:
                        if can_edit:
                            if st.button("🗑️", key=f"del_pt_{i}"):
                                st.session_state.points.pop(i)
                                save_points(st.session_state.points, supa=True)
                                st.rerun()

            st.markdown(
                f"<div style='background:#1e293b;border-radius:0 0 10px 10px;"
                f"padding:8px 14px;margin-bottom:16px'>"
                f"<div style='font-size:.78rem;font-weight:700;color:#94a3b8'>"
                f"{len(st.session_state.points)} point(s)</div></div>",
                unsafe_allow_html=True)

        st.divider()

        # ── Formulaire édition ────────────────────────────────────────────────
        if st.session_state.get('_edit_point') is not None:
            idx = st.session_state._edit_point
            pt  = st.session_state.points[idx]
            st.markdown(f"### ✏️ Modifier — {pt['label']}")

            er1, er2, er3, er_room = st.columns([3, 1.5, 1.5, 1.5])
            with er1:
                new_label = st.text_input("Nom", value=pt['label'], key="pt_edit_label")
            with er2:
                new_type = st.selectbox(
                    "Type", ["Air", "Surface"],
                    index=["Air", "Surface"].index(pt.get('type', 'Air'))
                          if pt.get('type', 'Air') in ["Air", "Surface"] else 0,
                    key="pt_edit_type")
            with er3:
                # ── CORRECTION : selectbox criticité lieu (édition) ──
                cur_lc_val = str(pt.get('location_criticality', 1))
                lc_edit_idx = next(
                    (i for i, o in enumerate(LOC_CRIT_OPTS) if o.startswith(cur_lc_val)), 0)
                new_lc_label = st.selectbox(
                    "Criticité lieu",
                    LOC_CRIT_OPTS,
                    index=lc_edit_idx,
                    key="pt_edit_loc_crit")
                new_lc = int(new_lc_label[0])          # extrait "1", "2" ou "3"
            with er_room:
                new_room = st.text_input(
                    "Classe ISO / GMP",
                    value=pt.get('room_class', ''),
                    placeholder="Ex: A, B, C, D…",
                    key="pt_edit_room")

            # ── Poste type si Classe A (édition) ─────────────────────────────
            if new_room and new_room.strip().upper() == "A":
                st.markdown(
                    "<div style='background:#fef9c3;border:1px solid #fde047;"
                    "border-radius:8px;padding:10px 14px;margin:6px 0'>"
                    "<div style='font-size:.7rem;font-weight:700;color:#854d0e;margin-bottom:6px'>"
                    "🔬 Configuration poste — Classe A</div>",
                    unsafe_allow_html=True)
                _cur_ptype = pt.get("poste_type", "commun")
                _cur_index = 0 if _cur_ptype == "commun" else 1
                new_poste_type = st.radio(
                    "Type de poste *",
                    ["commun", "specifique"],
                    format_func=lambda x: (
                        "🔵 Poste commun"
                        if x == "commun"
                        else "🔀 Poste spécifique (alternance Poste 1 / Poste 2)"
                    ),
                    index=_cur_index,
                    key="pt_edit_poste_type")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                new_poste_type = "non_applicable"

            er4, er5, er6 = st.columns([2, 1, 2])
            with er4:
                g_opts = (["Gélose de sédimentation", "Gélose TSA", "Gélose Columbia", "Autre"]
                          if new_type == "Air"
                          else ["Gélose contact TSA", "Ecouvillonnage", "Autre"])
                cur_g  = pt.get('gelose', g_opts[0])
                g_idx  = g_opts.index(cur_g) if cur_g in g_opts else 0
                new_gel = st.selectbox("Gélose", g_opts, index=g_idx, key="pt_edit_gelose")
            with er5:
                new_freq = st.number_input(
                    "🔁 Fréquence", min_value=1, max_value=31,
                    value=int(pt.get('frequency', 1)), step=1, key="pt_edit_freq")
            with er6:
                cur_unit = pt.get('frequency_unit', '/ semaine')
                unit_idx = PT_FREQ_UNIT_OPTS.index(cur_unit) if cur_unit in PT_FREQ_UNIT_OPTS else 1
                new_fu   = st.selectbox("Unité", PT_FREQ_UNIT_OPTS, index=unit_idx, key="pt_edit_freq_unit")

            # Aperçu grille seuils (utilise new_lc défini ci-dessus)
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
            padding:10px 14px;margin-top:6px">
              <div style="font-size:.65rem;color:#475569;text-transform:uppercase;
              font-weight:700;margin-bottom:8px">
                Grille d'alerte — criticité lieu {new_lc} (score = lieu × germe)
              </div>
              <div style="display:flex;gap:8px">
                <div style="flex:1;background:#f0fdf4;border-radius:6px;padding:8px;
                text-align:center;border:1px solid #86efac">
                  <div style="font-size:.6rem;color:#166534;font-weight:700">✅ Conforme</div>
                  <div style="font-size:.78rem;color:#166534;font-weight:800;margin-top:2px">Score &lt; 16</div>
                  <div style="font-size:.58rem;color:#94a3b8;margin-top:2px">
                    Germe ≤ {int(15/new_lc)}</div>
                </div>
                <div style="flex:1;background:#fffbeb;border-radius:6px;padding:8px;
                text-align:center;border:1px solid #fcd34d">
                  <div style="font-size:.6rem;color:#92400e;font-weight:700">⚠️ Alerte</div>
                  <div style="font-size:.78rem;color:#92400e;font-weight:800;margin-top:2px">Score 16–24</div>
                  <div style="font-size:.58rem;color:#94a3b8;margin-top:2px">
                    Germe {round(16/new_lc,1)}–{round(24/new_lc,1)}</div>
                </div>
                <div style="flex:1;background:#fef2f2;border-radius:6px;padding:8px;
                text-align:center;border:1px solid #fca5a5">
                  <div style="font-size:.6rem;color:#991b1b;font-weight:700">🚨 Action</div>
                  <div style="font-size:.78rem;color:#dc2626;font-weight:800;margin-top:2px">Score &gt; 24</div>
                  <div style="font-size:.58rem;color:#94a3b8;margin-top:2px">
                    Germe &gt; {round(24/new_lc,1)}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            eb1, eb2 = st.columns(2)
            with eb1:
                if st.button("✅ Enregistrer", key="pt_save_edit"):
                    _edit_pt_poste = (
                        new_poste_type
                        if new_room and new_room.strip().upper() == "A"
                        else "non_applicable"
                    )
                    st.session_state.points[idx] = {
                        "id":                   pt.get('id', f"p{idx+1}"),
                        "label":                new_label,
                        "type":                 new_type,
                        "gelose":               new_gel,
                        "location_criticality": new_lc,
                        "frequency":            new_freq,
                        "frequency_unit":       new_fu,
                        "room_class":           new_room.strip(),
                        "poste_type":           _edit_pt_poste,
                    }
                    save_points(st.session_state.points, supa=True)
                    st.session_state._edit_point = None
                    st.success("✅ Point mis à jour")
                    st.rerun()
            with eb2:
                if st.button("Annuler", key="pt_cancel_edit"):
                    st.session_state._edit_point = None
                    st.rerun()

        # ── Formulaire ajout ──────────────────────────────────────────────────
        elif can_edit:
            st.markdown("### ➕ Ajouter un point de prélèvement")

            np1, np2, np3, np_room_col = st.columns([3, 1.5, 1.5, 1.5])
            with np1:
                np_label = st.text_input(
                    "Nom *", placeholder="Ex: Salle 3 — Poste A", key="np_label")
            with np2:
                np_type = st.selectbox("Type", ["Air", "Surface"], key="np_type")
            with np3:
                # ── CORRECTION : selectbox criticité lieu (ajout) ──
                np_lc_label = st.selectbox(
                    "Criticité lieu",
                    LOC_CRIT_OPTS,
                    index=0,
                    key="np_loc_crit")
                np_lc = int(np_lc_label[0])             # extrait "1", "2" ou "3"
            with np_room_col:
                np_room = st.text_input(
                    "Classe ISO / GMP", placeholder="Ex: A, B, C, D…", key="np_room")

            # ── Poste type si Classe A ────────────────────────────────────────
            if np_room and np_room.strip().upper() == "A":
                st.markdown(
                    "<div style='background:#fef9c3;border:1px solid #fde047;"
                    "border-radius:8px;padding:10px 14px;margin:6px 0'>"
                    "<div style='font-size:.7rem;font-weight:700;color:#854d0e;margin-bottom:6px'>"
                    "🔬 Configuration poste — Classe A</div>",
                    unsafe_allow_html=True)
                np_poste_type = st.radio(
                    "Type de poste *",
                    ["commun", "specifique"],
                    format_func=lambda x: (
                        "🔵 Poste commun (un seul poste, identique chaque jour)"
                        if x == "commun"
                        else "🔀 Poste spécifique (alternance Poste 1 / Poste 2 chaque jour)"
                    ),
                    key="np_poste_type")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                np_poste_type = "non_applicable"

            np4, np5, np6 = st.columns([2, 1, 2])
            with np4:
                g_opts_new = (["Gélose de sédimentation", "Gélose TSA", "Gélose Columbia", "Autre"]
                              if np_type == "Air"
                              else ["Gélose contact TSA", "Ecouvillonnage", "Autre"])
                np_gel = st.selectbox("Gélose", g_opts_new, key="np_gelose")
            with np5:
                np_freq = st.number_input(
                    "🔁 Fréquence", min_value=1, max_value=31, value=1, step=1, key="np_freq")
            with np6:
                np_fu = st.selectbox("Unité", PT_FREQ_UNIT_OPTS, index=0, key="np_freq_unit")

            # Aperçu grille (utilise np_lc défini ci-dessus)
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
            padding:10px 14px;margin-top:4px;margin-bottom:10px">
              <div style="font-size:.65rem;color:#475569;text-transform:uppercase;
              font-weight:700;margin-bottom:8px">
                Aperçu grille (criticité lieu {np_lc} × score germe)
              </div>
              <div style="display:flex;gap:8px">
                <div style="flex:1;background:#f0fdf4;border-radius:6px;padding:7px;
                text-align:center;border:1px solid #86efac">
                  <div style="font-size:.6rem;color:#166534;font-weight:700">✅ Conforme</div>
                  <div style="font-size:.72rem;color:#166534;font-weight:800">Score &lt; 16</div>
                </div>
                <div style="flex:1;background:#fffbeb;border-radius:6px;padding:7px;
                text-align:center;border:1px solid #fcd34d">
                  <div style="font-size:.6rem;color:#92400e;font-weight:700">⚠️ Alerte</div>
                  <div style="font-size:.72rem;color:#92400e;font-weight:800">Score 16–24</div>
                </div>
                <div style="flex:1;background:#fef2f2;border-radius:6px;padding:7px;
                text-align:center;border:1px solid #fca5a5">
                  <div style="font-size:.6rem;color:#991b1b;font-weight:700">🚨 Action</div>
                  <div style="font-size:.72rem;color:#dc2626;font-weight:800">Score &gt; 24</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            if st.button("➕ Ajouter", key="np_add"):
                if not np_label.strip():
                    st.error("Le nom est requis")
                else:
                    nid = f"p{len(st.session_state.points)+1}_{int(datetime.now().timestamp())}"
                    _save_pt = (
                        np_poste_type
                        if np_room and np_room.strip().upper() == "A"
                        else "non_applicable"
                    )
                    st.session_state.points.append({
                        "id":                   nid,
                        "label":                np_label.strip(),
                        "type":                 np_type,
                        "gelose":               np_gel,
                        "location_criticality": np_lc,
                        "frequency":            np_freq,
                        "frequency_unit":       np_fu,
                        "room_class":           np_room.strip(),
                        "poste_type":           _save_pt,
                    })
                    save_points(st.session_state.points, supa=True)
                    st.success(f"✅ Point **{np_label}** ajouté")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PLANS DE LOCALISATION
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_plans:
        st.markdown("### 🗺️ Gestion des plans de localisation")
        st.markdown("""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
        padding:12px 16px;margin-bottom:16px;font-size:.82rem;color:#1e40af">
        ℹ️ Les plans permettent de localiser visuellement les points de prélèvement.<br>
        Dans <strong>Surveillance → Nouveau prélèvement</strong>, choisissez un plan
        dans le menu déroulant pour afficher la carte et positionner le point.
        </div>""", unsafe_allow_html=True)

        if not st.session_state.plans:
            st.markdown(
                "<div style='background:#f8fafc;border:1.5px dashed #cbd5e1;"
                "border-radius:12px;padding:32px;text-align:center'>"
                "<div style='font-size:2.5rem;margin-bottom:8px'>🗺️</div>"
                "<div style='font-weight:700;color:#475569;margin-bottom:4px'>Aucun plan défini</div>"
                "<div style='font-size:.8rem;color:#94a3b8'>Ajoutez un plan ci-dessous</div></div>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;"
                f"padding:12px 16px;margin-bottom:16px'>"
                f"<span style='font-size:.75rem;color:#0369a1;font-weight:700'>"
                f"🗺️ {len(st.session_state.plans)} plan(s)</span></div>",
                unsafe_allow_html=True)
            for pi, plan in enumerate(list(st.session_state.plans)):
                has_img = bool(plan.get("image_b64"))
                pc1, pc2, pc3 = st.columns([5, 1, 1])
                with pc1:
                    img_badge = (
                        " <span style='background:#f0fdf4;color:#166534;border:1px solid #86efac;"
                        "border-radius:4px;padding:1px 7px;font-size:.62rem;font-weight:700'>"
                        "🖼️ Image</span>"
                        if has_img else
                        " <span style='background:#f8fafc;color:#94a3b8;border:1px solid #e2e8f0;"
                        "border-radius:4px;padding:1px 7px;font-size:.62rem'>Pas d'image</span>")
                    st.markdown(
                        f"<div style='background:#f8fafc;border:1.5px solid #e2e8f0;"
                        f"border-radius:10px;padding:10px 16px;display:flex;align-items:center;gap:10px'>"
                        f"<span style='font-size:1.3rem'>🗺️</span><div>"
                        f"<div style='font-weight:700;color:#0f172a'>{plan['name']}</div>"
                        f"<div style='font-size:.7rem;color:#64748b;margin-top:2px'>"
                        f"ID: {plan['id']}{img_badge}</div></div></div>",
                        unsafe_allow_html=True)
                with pc2:
                    if can_edit:
                        if st.button("✏️", key=f"edit_plan_{pi}"):
                            st.session_state["_edit_plan_idx"] = pi
                            st.session_state.pop("_ep_image_b64", None)
                            st.rerun()
                with pc3:
                    if can_edit:
                        if st.button("🗑️", key=f"del_plan_{pi}"):
                            st.session_state.plans.pop(pi)
                            save_plans(st.session_state.plans)
                            st.success("Plan supprimé.")
                            st.rerun()

        st.divider()

        edit_plan_idx = st.session_state.get("_edit_plan_idx")
        if edit_plan_idx is not None and edit_plan_idx < len(st.session_state.plans):
            plan_e = st.session_state.plans[edit_plan_idx]
            st.markdown(f"### ✏️ Modifier — {plan_e['name']}")
            ep1, ep2 = st.columns([3, 2])
            with ep1:
                ep_name = st.text_input("Nom du plan *", value=plan_e.get("name", ""), key="ep_name")
            with ep2:
                ep_upload = st.file_uploader(
                    "Remplacer l'image (PNG/JPG/PDF)",
                    type=["png", "jpg", "jpeg", "pdf"], key="ep_upload")
            if ep_upload:
                import base64 as _b64ep
                if ep_upload.type == "application/pdf":
                    try:
                        import fitz
                        doc = fitz.open(stream=ep_upload.read(), filetype="pdf")
                        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                        st.session_state["_ep_image_b64"] = (
                            f"data:image/png;base64,{_b64ep.b64encode(pix.tobytes('png')).decode()}")
                        st.success("PDF converti.")
                    except Exception as e:
                        st.error(f"Erreur PDF : {e}")
                else:
                    raw_ep = ep_upload.read()
                    st.session_state["_ep_image_b64"] = (
                        f"data:{ep_upload.type};base64,{_b64ep.b64encode(raw_ep).decode()}")
            cur_img = st.session_state.get("_ep_image_b64", plan_e.get("image_b64", ""))
            if cur_img:
                st.image(cur_img, caption="Aperçu du plan", use_column_width=True)
            eb1, eb2 = st.columns(2)
            with eb1:
                if st.button("✅ Enregistrer", key="ep_save", use_container_width=True, type="primary"):
                    if ep_name.strip():
                        st.session_state.plans[edit_plan_idx]["name"] = ep_name.strip()
                        if st.session_state.get("_ep_image_b64"):
                            st.session_state.plans[edit_plan_idx]["image_b64"] = st.session_state["_ep_image_b64"]
                        save_plans(st.session_state.plans)
                        st.session_state["_edit_plan_idx"] = None
                        st.session_state.pop("_ep_image_b64", None)
                        st.success("✅ Plan mis à jour")
                        st.rerun()
                    else:
                        st.error("Le nom est obligatoire.")
            with eb2:
                if st.button("Annuler", key="ep_cancel", use_container_width=True):
                    st.session_state["_edit_plan_idx"] = None
                    st.session_state.pop("_ep_image_b64", None)
                    st.rerun()
        elif can_edit:
            st.markdown("### ➕ Ajouter un plan")
            np1, np2 = st.columns([3, 2])
            with np1:
                np_plan_name = st.text_input(
                    "Nom du plan *",
                    placeholder="Ex: ZAC — Isolateur ISO 16, Salle de préparation B...",
                    key="np_plan_name")
            with np2:
                np_plan_upload = st.file_uploader(
                    "Image du plan (PNG / JPG / PDF)",
                    type=["png", "jpg", "jpeg", "pdf"], key="np_plan_upload")
            np_plan_b64 = ""
            if np_plan_upload:
                import base64 as _b64np2
                if np_plan_upload.type == "application/pdf":
                    try:
                        import fitz
                        doc = fitz.open(stream=np_plan_upload.read(), filetype="pdf")
                        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                        np_plan_b64 = (
                            f"data:image/png;base64,{_b64np2.b64encode(pix.tobytes('png')).decode()}")
                        st.success("✅ PDF converti — première page utilisée comme plan")
                    except ImportError:
                        st.error("❌ PyMuPDF non installé — ajoutez pymupdf dans requirements.txt")
                    except Exception as e:
                        st.error(f"Erreur PDF : {e}")
                else:
                    np_plan_b64 = (
                        f"data:{np_plan_upload.type};base64,"
                        f"{_b64np2.b64encode(np_plan_upload.read()).decode()}")
            if np_plan_b64:
                st.image(np_plan_b64, caption="Aperçu du plan", use_column_width=True)
            if st.button("➕ Ajouter ce plan", key="np_plan_add",
                         use_container_width=True, type="primary"):
                if not np_plan_name.strip():
                    st.error("Le nom du plan est obligatoire.")
                else:
                    import time as _time_plans
                    plan_id = f"plan_{len(st.session_state.plans)+1}_{int(_time_plans.time())}"
                    st.session_state.plans.append({
                        "id":        plan_id,
                        "name":      np_plan_name.strip(),
                        "image_b64": np_plan_b64,
                    })
                    save_plans(st.session_state.plans)
                    st.success(f"✅ Plan **{np_plan_name}** ajouté avec succès !")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # SEUILS D'ALERTE ET D'ACTION
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_seuils:
        st.markdown("### ⚖️ Seuils d'alerte et d'action")

        st.markdown("""
        <div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);border:1.5px solid #93c5fd;
        border-radius:14px;padding:20px 24px;margin-bottom:20px">
          <div style="font-size:1rem;font-weight:800;color:#1e40af;margin-bottom:14px">
            🧮 Comment est calculé le score de criticité ?
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
            <div style="background:#fff;border-radius:10px;padding:14px;border:1px solid #bfdbfe;text-align:center">
              <div style="font-size:1.4rem;margin-bottom:4px">🧬</div>
              <div style="font-weight:800;color:#1e40af;font-size:.88rem">Pathogénicité</div>
              <div style="font-size:.72rem;color:#475569;margin-top:6px;line-height:1.6">
                <b>1</b> — Non pathogène<br>
                <b>2</b> — Pathogène opportuniste<br>
                <b>3</b> — Pathogène MR / primaire
              </div>
            </div>
            <div style="background:#fff;border-radius:10px;padding:14px;border:1px solid #bfdbfe;text-align:center">
              <div style="font-size:1.4rem;margin-bottom:4px">🧴</div>
              <div style="font-weight:800;color:#1e40af;font-size:.88rem">Résistance désinfectants</div>
              <div style="font-size:.72rem;color:#475569;margin-top:6px;line-height:1.6">
                <b>1</b> — Sensible<br>
                <b>2</b> — Résistant Surfa'Safe<br>
                <b>3</b> — Résistant Surfa'Safe + APA
              </div>
            </div>
            <div style="background:#fff;border-radius:10px;padding:14px;border:1px solid #bfdbfe;text-align:center">
              <div style="font-size:1.4rem;margin-bottom:4px">💨</div>
              <div style="font-weight:800;color:#1e40af;font-size:.88rem">Dissémination</div>
              <div style="font-size:.72rem;color:#475569;margin-top:6px;line-height:1.6">
                <b>1</b> — Environnemental<br>
                <b>2</b> — Manuporté<br>
                <b>3</b> — Aéroporté
              </div>
            </div>
          </div>
          <div style="background:#1e293b;border-radius:10px;padding:14px;text-align:center;margin-bottom:14px">
            <div style="font-size:.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">
              Formule du score total
            </div>
            <div style="font-size:1rem;color:#e2e8f0;font-weight:700">
              Score total = <span style="color:#60a5fa">Criticité lieu (1–3)</span>
              × <span style="color:#34d399">Pathogénicité (1–3)</span>
              × <span style="color:#fbbf24">Résistance (1–3)</span>
              × <span style="color:#f87171">Dissémination (1–3)</span>
            </div>
            <div style="font-size:.72rem;color:#64748b;margin-top:8px">
              Score minimum : 1×1×1×1 = <b style="color:#94a3b8">1</b>
              &nbsp;·&nbsp;
              Score maximum : 3×3×3×3 = <b style="color:#f87171">81</b>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
            <div style="background:#f0fdf4;border:1.5px solid #86efac;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:1.1rem">✅</div>
              <div style="font-weight:800;color:#166534;font-size:.85rem;margin-top:4px">CONFORME</div>
              <div style="font-size:.78rem;color:#166534;margin-top:4px">Score &lt; seuil alerte</div>
            </div>
            <div style="background:#fffbeb;border:1.5px solid #fcd34d;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:1.1rem">⚠️</div>
              <div style="font-weight:800;color:#92400e;font-size:.85rem;margin-top:4px">ALERTE</div>
              <div style="font-size:.78rem;color:#92400e;margin-top:4px">Seuil alerte ≤ Score ≤ seuil action</div>
            </div>
            <div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:1.1rem">🚨</div>
              <div style="font-weight:800;color:#991b1b;font-size:.85rem;margin-top:4px">ACTION</div>
              <div style="font-size:.78rem;color:#991b1b;margin-top:4px">Score &gt; seuil action</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        _seuil_alerte = st.session_state.get("_seuil_alerte", 24)
        _seuil_action = st.session_state.get("_seuil_action", 36)

        st.markdown("#### ⚙️ Modifier les seuils")
        if not can_edit:
            st.info("👁️ Mode lecture seule — connectez-vous pour modifier les seuils.")

        sc1, sc2, sc3 = st.columns([2, 2, 3])
        with sc1:
            new_seuil_alerte = st.number_input(
                "⚠️ Seuil ALERTE",
                min_value=1, max_value=80, value=int(_seuil_alerte), step=1,
                disabled=not can_edit,
                help="En dessous : conforme. À partir de ce score : alerte.",
                key="input_seuil_alerte")
        with sc2:
            new_seuil_action = st.number_input(
                "🚨 Seuil ACTION",
                min_value=1, max_value=81, value=int(_seuil_action), step=1,
                disabled=not can_edit,
                help="Au-dessus de ce score : action immédiate requise.",
                key="input_seuil_action")
        with sc3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if can_edit:
                if st.button("💾 Sauvegarder les seuils", use_container_width=True,
                             key="save_seuils", type="primary"):
                    if new_seuil_alerte >= new_seuil_action:
                        st.error("❌ Le seuil d'alerte doit être strictement inférieur au seuil d'action.")
                    else:
                        st.session_state["_seuil_alerte"] = new_seuil_alerte
                        st.session_state["_seuil_action"] = new_seuil_action
                        _supa_upsert('seuils', json.dumps({
                            "alerte": new_seuil_alerte,
                            "action": new_seuil_action
                        }, ensure_ascii=False))
                        st.success(
                            f"✅ Seuils sauvegardés — Alerte : {new_seuil_alerte} · Action : {new_seuil_action}")
                        st.rerun()

        if new_seuil_alerte >= new_seuil_action:
            st.error("❌ Le seuil d'alerte doit être strictement inférieur au seuil d'action.")
        else:
            st.markdown(f"""
            <div style="background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:10px;
            padding:14px 18px;margin-top:8px">
              <div style="font-size:.78rem;font-weight:700;color:#475569;margin-bottom:10px">
                Aperçu de la grille avec ces seuils
              </div>
              <div style="display:flex;gap:0;border-radius:8px;overflow:hidden;border:1px solid #e2e8f0">
                <div style="flex:1;background:#f0fdf4;padding:10px;text-align:center;border-right:1px solid #e2e8f0">
                  <div style="font-size:.65rem;color:#166534;font-weight:700;text-transform:uppercase">✅ Conforme</div>
                  <div style="font-size:1.1rem;font-weight:900;color:#166534;margin-top:2px">
                    Score &lt; {new_seuil_alerte}
                  </div>
                </div>
                <div style="flex:1;background:#fffbeb;padding:10px;text-align:center;border-right:1px solid #e2e8f0">
                  <div style="font-size:.65rem;color:#92400e;font-weight:700;text-transform:uppercase">⚠️ Alerte</div>
                  <div style="font-size:1.1rem;font-weight:900;color:#92400e;margin-top:2px">
                    {new_seuil_alerte} – {new_seuil_action}
                  </div>
                </div>
                <div style="flex:1;background:#fef2f2;padding:10px;text-align:center">
                  <div style="font-size:.65rem;color:#991b1b;font-weight:700;text-transform:uppercase">🚨 Action</div>
                  <div style="font-size:1.1rem;font-weight:900;color:#dc2626;margin-top:2px">
                    Score &gt; {new_seuil_action}
                  </div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.divider()

        st.markdown("#### 📊 Tableau de référence — scores limites par criticité de lieu")
        st.caption(
            "Montre à quel score germe (pathogénicité × résistance × dissémination) "
            "les seuils sont déclenchés selon la criticité du lieu.")

        _sa     = new_seuil_alerte
        _sc_val = new_seuil_action

        st.markdown(
            "<div style='display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr 2fr;"
            "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff'>Criticité lieu</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Score lieu</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Germe → ⚠️ Alerte</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Germe → 🚨 Action</div>"
            "<div style='font-size:.72rem;font-weight:800;color:#fff'>Exemples de lieux</div>"
            "</div>",
            unsafe_allow_html=True)

        lc_examples = {
            1: "Couloirs, locaux techniques, zones administratives",
            2: "Préparations non stériles, zones annexes ZAC, vestiaires",
            3: "ZAC, salles blanches ISO A/B, isolateurs",
        }
        lc_colors_ref = {1: "#22c55e", 2: "#f59e0b", 3: "#ef4444"}

        for lci, loc_crit_val in enumerate([1, 2, 3]):
            lc_lbl       = f"Nv.{loc_crit_val} — {LOC_CRIT_LABELS[str(loc_crit_val)]}"
            germe_alerte = _sa / loc_crit_val
            germe_action = _sc_val / loc_crit_val
            lc_col = lc_colors_ref[loc_crit_val]
            row_bg = "#f8fafc" if lci % 2 == 0 else "#ffffff"
            st.markdown(
                "<div style='display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr 2fr;"
                f"gap:4px;background:{row_bg};border:1px solid #e2e8f0;border-top:none;"
                "padding:10px 14px;align-items:center'>"
                f"<div style='font-size:.85rem;font-weight:700'>"
                f"<span style='color:{lc_col}'>●</span> {lc_lbl}</div>"
                f"<div style='text-align:center'>"
                f"<span style='background:{lc_col}22;color:{lc_col};"
                f"border:1px solid {lc_col}55;border-radius:6px;"
                f"padding:2px 10px;font-size:.82rem;font-weight:800'>× {loc_crit_val}</span></div>"
                f"<div style='text-align:center;font-size:.82rem;font-weight:700;color:#92400e'>"
                f"Score germe ≥ {germe_alerte:.1f}</div>"
                f"<div style='text-align:center;font-size:.82rem;font-weight:700;color:#dc2626'>"
                f"Score germe &gt; {germe_action:.1f}</div>"
                f"<div style='font-size:.7rem;color:#64748b;font-style:italic'>"
                f"{lc_examples[loc_crit_val]}</div>"
                "</div>",
                unsafe_allow_html=True)

        st.markdown(
            "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
            f"<div style='font-size:.75rem;color:#94a3b8'>"
            f"Score germe = Pathogénicité × Résistance × Dissémination (min 1 · max 27) "
            f"· Seuil alerte : <b style='color:#fbbf24'>{_sa}</b> "
            f"· Seuil action : <b style='color:#f87171'>{_sc_val}</b>"
            f"</div></div>",
            unsafe_allow_html=True)

        st.divider()

        st.markdown("#### ↩️ Réinitialiser aux valeurs par défaut")
        st.markdown(
            "<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;"
            "padding:10px 14px;font-size:.78rem;color:#475569;margin-bottom:8px'>"
            "Les valeurs par défaut sont <b>Alerte : 24</b> et <b>Action : 36</b>.<br>"
            "Ces seuils correspondent à :<br>"
            "• Alerte dès qu'un germe de score 8 est trouvé en zone critique (3×8=24)<br>"
            "• Action dès qu'un germe de score 12 est trouvé en zone critique (3×12=36)"
            "</div>",
            unsafe_allow_html=True)
        if can_edit:
            if st.button("↩️ Remettre Alerte=24 / Action=36", key="reset_seuils"):
                st.session_state["_seuil_alerte"] = 24
                st.session_state["_seuil_action"] = 36
                _supa_upsert('seuils', json.dumps({"alerte": 24, "action": 36}, ensure_ascii=False))
                st.success("✅ Seuils réinitialisés — Alerte : 24 · Action : 36")
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # OPÉRATEURS
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_operateurs:
        ops = st.session_state.operators
        if not ops:
            st.info("Aucun opérateur enregistré.")
        else:
            st.markdown(
                f'<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;'
                f'padding:12px 16px;margin-bottom:16px">'
                f'<span style="font-size:.75rem;color:#0369a1;font-weight:700">'
                f'👥 {len(ops)} opérateur(s)</span></div>',
                unsafe_allow_html=True)
            for i, op in enumerate(ops):
                nom        = op.get('nom', '—')
                profession = op.get('profession', '—')
                oc1, oc2, oc3 = st.columns([5, 1, 1])
                with oc1:
                    st.markdown(f"""
                    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                    padding:10px 14px;display:flex;gap:16px;align-items:center">
                      <div style="background:#2563eb;color:#fff;border-radius:50%;
                      width:36px;height:36px;display:flex;align-items:center;justify-content:center;
                      font-weight:700;font-size:.9rem;flex-shrink:0">
                        {nom[0].upper() if nom else '?'}
                      </div>
                      <div>
                        <div style="font-weight:700;font-size:.9rem;color:#0f172a">{nom}</div>
                        <div style="font-size:.72rem;color:#475569;margin-top:2px">👔 {profession}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                with oc2:
                    if can_edit:
                        if st.button("✏️", key=f"edit_op_{i}"):
                            st.session_state._edit_operator = i
                            st.rerun()
                with oc3:
                    if can_edit:
                        if st.button("🗑️", key=f"del_op_{i}"):
                            ops.pop(i)
                            save_operators(ops, supa=True)
                            st.session_state.operators = ops
                            st.rerun()

        st.divider()
        p_opts = ["Préparateur en pharmacie hospitalière", "Pharmacien", "Interne de pharmacie"]

        if st.session_state.get('_edit_operator') is not None:
            idx = st.session_state._edit_operator
            op  = st.session_state.operators[idx]
            st.markdown(f"### ✏️ Modifier — {op.get('nom', '')}")
            ec1, ec2 = st.columns(2)
            with ec1:
                edit_nom = st.text_input("Nom *", value=op.get('nom', ''), key="op_edit_nom")
            with ec2:
                cur_p    = op.get('profession', '')
                p_idx    = p_opts.index(cur_p) if cur_p in p_opts else 0
                edit_pro = st.selectbox("Profession *", p_opts, index=p_idx, key="op_edit_prof")
            eb1, eb2 = st.columns(2)
            with eb1:
                if st.button("✅ Enregistrer", use_container_width=True, key="op_save_edit"):
                    if edit_nom.strip():
                        st.session_state.operators[idx] = {
                            "nom": edit_nom.strip(), "profession": edit_pro}
                        save_operators(st.session_state.operators, supa=True)
                        st.session_state._edit_operator = None
                        st.success("✅ Mis à jour")
                        st.rerun()
                    else:
                        st.error("Le nom est obligatoire.")
            with eb2:
                if st.button("Annuler", use_container_width=True, key="op_cancel_edit"):
                    st.session_state._edit_operator = None
                    st.rerun()
        elif can_edit:
            st.markdown("### ➕ Ajouter un opérateur")
            nc1, nc2 = st.columns(2)
            with nc1:
                new_nom = st.text_input("Nom *", placeholder="Ex: Marie Dupont", key="op_new_nom")
            with nc2:
                new_pro = st.selectbox("Profession *", p_opts, key="op_new_prof")
            if st.button("➕ Ajouter", key="op_add"):
                if not new_nom.strip():
                    st.error("Le nom est obligatoire.")
                elif any(o['nom'].lower() == new_nom.strip().lower() for o in st.session_state.operators):
                    st.error("Cet opérateur existe déjà.")
                else:
                    st.session_state.operators.append({"nom": new_nom.strip(), "profession": new_pro})
                    save_operators(st.session_state.operators, supa=True)
                    st.success(f"✅ **{new_nom}** ajouté")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # SAUVEGARDE
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_backup:
        st.markdown("### 💾 Sauvegarde & Restauration")
        supa_connected = get_supabase_client() is not None
        if supa_connected:
            st.success("✅ **Supabase actif** — données persistantes dans le cloud.")
        else:
            st.warning("⚠️ **Supabase non configuré** — données perdues au redémarrage.")

        st.markdown("""
        <div style="background:#fffbeb;border:1.5px solid #fcd34d;border-radius:12px;
        padding:16px 20px;margin:12px 0">
          <div style="font-weight:800;color:#92400e;font-size:.95rem;margin-bottom:8px">
            📋 Pourquoi sauvegarder ?
          </div>
          <div style="font-size:.82rem;color:#78350f;line-height:1.8">
            Chaque modification du code provoque un redémarrage. Sans Supabase, toutes
            les données locales sont <strong>effacées</strong>.<br>
            ✅ <strong>Solution 1</strong> : configurer Supabase (onglet ☁️).<br>
            ✅ <strong>Solution 2</strong> : exporter avant chaque update, réimporter après.
          </div>
        </div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown("#### ⬇️ Exporter toutes les données")
        backup_data     = export_all_data()
        backup_json     = json.dumps(backup_data, ensure_ascii=False, indent=2)
        backup_filename = f"backup_URC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("🦠 Germes",          len(backup_data.get("germs", [])))
        b2.metric("🧪 Prélèvements",    len(backup_data.get("prelevements", [])))
        b3.metric("📅 Lectures planif.", len(backup_data.get("schedules", [])))
        b4.metric("📋 Historique",       len(backup_data.get("surveillance", [])))
        st.download_button(
            label=f"⬇️ Télécharger ({len(backup_json)//1024 + 1} Ko)",
            data=backup_json, file_name=backup_filename,
            mime="application/json",
            use_container_width=True, key="main_export_btn")

        st.divider()
        st.markdown("#### ⬆️ Restaurer depuis une sauvegarde")
        st.markdown("""
        <div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;
        padding:12px 16px;margin-bottom:12px">
          <span style="color:#dc2626;font-weight:700;font-size:.82rem">
            ⚠️ La restauration remplace TOUTES les données sans possibilité d'annulation.
          </span>
        </div>""", unsafe_allow_html=True)

        uploaded_backup = st.file_uploader(
            "Fichier de sauvegarde (.json)", type=["json"], key="backup_uploader")
        if uploaded_backup is not None:
            try:
                backup_content = json.loads(uploaded_backup.read().decode("utf-8"))
                meta = backup_content.get("_meta", {})
                st.markdown(f"""
                <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                padding:14px 18px;margin-bottom:12px">
                  <div style="font-weight:700;color:#166534;font-size:.85rem;margin-bottom:8px">
                    📁 Contenu détecté
                  </div>
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;
                  font-size:.75rem;color:#0f172a">
                    <div>🦠 Germes : <strong>{len(backup_content.get("germs",[]))}</strong></div>
                    <div>🧪 Prélèvements : <strong>{len(backup_content.get("prelevements",[]))}</strong></div>
                    <div>📅 Lectures : <strong>{len(backup_content.get("schedules",[]))}</strong></div>
                    <div>👤 Opérateurs : <strong>{len(backup_content.get("operators",[]))}</strong></div>
                    <div>📍 Points : <strong>{len(backup_content.get("points",[]))}</strong></div>
                    <div>📋 Historique : <strong>{len(backup_content.get("surveillance",[]))}</strong></div>
                  </div>
                  <div style="font-size:.68rem;color:#475569;margin-top:8px">
                    Exporté le : {meta.get("exported_at","—")[:19].replace("T"," ")}
                    | Version : {meta.get("version","?")}
                  </div>
                </div>""", unsafe_allow_html=True)

                if st.session_state.get("confirm_restore", False):
                    st.error("🚨 Dernière confirmation — toutes les données seront remplacées.")
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        if st.button("✅ OUI — Restaurer maintenant",
                                     use_container_width=True, key="confirm_restore_yes"):
                            ok, msg = import_all_data(backup_content)
                            st.session_state.confirm_restore = False
                            if ok: st.success(f"✅ {msg}"); st.rerun()
                            else:  st.error(msg)
                    with rc2:
                        if st.button("❌ Annuler", use_container_width=True, key="confirm_restore_no"):
                            st.session_state.confirm_restore = False
                            st.rerun()
                else:
                    if can_edit:
                        if st.button("⬆️ Restaurer ces données",
                                     use_container_width=True, key="restore_btn"):
                            st.session_state.confirm_restore = True
                            st.rerun()
            except json.JSONDecodeError:
                st.error("❌ Fichier JSON invalide.")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # SUPABASE
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_supabase:
        st.markdown("### ☁️ Configuration Supabase")
        supa_ok = get_supabase_client() is not None
        if supa_ok:
            st.success("✅ **Supabase connecté** — modifications synchronisées en temps réel.")
        else:
            st.error("🔴 **Supabase non connecté** — sauvegarde locale uniquement.")

        st.markdown("""
        <div style="background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;
        padding:20px;margin-top:16px">
          <div style="font-size:.95rem;font-weight:700;color:#0f172a;margin-bottom:12px">
            📋 Comment configurer Supabase
          </div>
          <div style="font-size:.82rem;color:#1e293b;line-height:1.8">
            <strong>1.</strong> Créez un compte sur <strong>supabase.com</strong><br>
            <strong>2.</strong> Créez un nouveau projet<br>
            <strong>3.</strong> Dans l'éditeur SQL, exécutez le code ci-dessous
          </div>
        </div>""", unsafe_allow_html=True)

        st.code("""CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE app_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_all" ON app_state FOR ALL USING (true) WITH CHECK (true);""",
                language="sql")

        st.markdown("""
        <div style="background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;
        padding:20px;margin-top:12px">
          <div style="font-size:.82rem;color:#1e293b;line-height:1.8">
            <strong>4.</strong> Dans <em>Project Settings → API</em>, copiez :<br>
            &nbsp;&nbsp;• <strong>Project URL</strong> → <code>SUPABASE_URL</code><br>
            &nbsp;&nbsp;• <strong>anon/public key</strong> → <code>SUPABASE_KEY</code>
          </div>
        </div>""", unsafe_allow_html=True)

        st.code("""SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGci..."  # votre clé anon""", language="toml")

        if supa_ok:
            st.divider()
            st.markdown("### 🔄 Actions Supabase")
            syn1, syn2 = st.columns(2)
            with syn1:
                if can_edit:
                    if st.button("🔄 Forcer la synchronisation", use_container_width=True):
                        save_germs(st.session_state.germs)
                        save_prelevements(st.session_state.prelevements, supa=True)
                        save_schedules(st.session_state.schedules, supa=True)
                        save_surveillance(st.session_state.surveillance)
                        save_points(st.session_state.points, supa=True)
                        save_operators(st.session_state.operators, supa=True)
                        save_pending_identifications(st.session_state.pending_identifications, supa=True)
                        save_origin_measures(st.session_state.origin_measures, supa=True)
                        save_faq(st.session_state.faq_items, supa=True)
                        st.session_state["_mesures_modifiees"] = False
                        st.success("✅ Toutes les données synchronisées !")
            with syn2:
                if can_edit:
                    if st.button("🔃 Recharger depuis Supabase", use_container_width=True):
                        st.session_state.germs                   = load_germs()[0]
                        st.session_state.prelevements            = load_prelevements()
                        st.session_state.schedules               = load_schedules()
                        st.session_state.surveillance            = load_surveillance()
                        st.session_state.points                  = load_points()
                        st.session_state.operators               = load_operators()
                        st.session_state.pending_identifications = load_pending_identifications()
                        st.session_state.origin_measures         = load_origin_measures()
                        st.session_state.faq_items               = load_faq()
                        st.success("✅ Données rechargées depuis Supabase !")
                        st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # FAQ
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_faq:
        faq_items = st.session_state.get("faq_items", [])

        cats_count = {}
        for f in faq_items:
            c = f.get("category", "Général")
            cats_count[c] = cats_count.get(c, 0) + 1

        cols_stat = st.columns(min(len(cats_count) + 1, 5))
        with cols_stat[0]:
            st.metric("Total Q&R", len(faq_items))
        for i, (cat, cnt) in enumerate(list(cats_count.items())[:4], 1):
            with cols_stat[i]:
                st.metric(cat[:14], cnt)

        st.divider()

        edit_idx = st.session_state.get("_faq_edit_idx")

        if can_edit and st.session_state.get("_faq_show_form", False):
            is_edit  = edit_idx is not None
            existing = faq_items[edit_idx] if is_edit else {}
            form_bg  = "#eff6ff" if is_edit else "#f0fdf4"
            form_bdr = "#93c5fd" if is_edit else "#86efac"
            form_ttl = "✏️ Modifier la question" if is_edit else "➕ Nouvelle question"

            st.markdown(
                f"<div style='background:{form_bg};border:1.5px solid {form_bdr};"
                f"border-radius:12px;padding:18px;margin-bottom:16px'>",
                unsafe_allow_html=True)
            st.markdown(f"#### {form_ttl}")

            fc1, fc2 = st.columns([3, 1])
            with fc1:
                faq_q = st.text_input(
                    "Question *", value=existing.get("question", ""),
                    placeholder="Ex: Comment ajouter un point de prélèvement ?",
                    key="faq_form_question")
            with fc2:
                cur_cat = existing.get("category", "Général")
                faq_c = st.selectbox(
                    "Catégorie", FAQ_CATEGORIES,
                    index=FAQ_CATEGORIES.index(cur_cat) if cur_cat in FAQ_CATEGORIES else 0,
                    key="faq_form_category")

            faq_a = st.text_area(
                "Réponse * (Markdown supporté)", value=existing.get("answer", ""),
                height=150,
                placeholder="Décrivez la réponse. **Gras**, *italique*, listes…",
                key="faq_form_answer")
            if faq_a.strip():
                with st.expander("👁️ Aperçu", expanded=False):
                    st.markdown(faq_a)

            fb1, fb2 = st.columns(2)
            with fb1:
                if st.button(
                    "✔️ Mettre à jour" if is_edit else "✅ Ajouter",
                    use_container_width=True, type="primary", key="faq_form_submit"):
                    if not faq_q.strip():
                        st.error("La question est obligatoire.")
                    elif not faq_a.strip():
                        st.error("La réponse est obligatoire.")
                    else:
                        if is_edit:
                            faq_items[edit_idx].update(
                                question=faq_q.strip(), answer=faq_a.strip(), category=faq_c)
                        else:
                            faq_items.append({
                                "id":       f"faq_{int(datetime.now().timestamp())}",
                                "category": faq_c,
                                "question": faq_q.strip(),
                                "answer":   faq_a.strip(),
                                "order":    len(faq_items),
                            })
                        save_faq(faq_items, supa=True)
                        st.session_state["faq_items"]      = faq_items
                        st.session_state["_faq_show_form"] = False
                        st.session_state["_faq_edit_idx"]  = None
                        st.success("✅ FAQ mise à jour !")
                        st.rerun()
            with fb2:
                if st.button("✕ Annuler", use_container_width=True, key="faq_form_cancel"):
                    st.session_state["_faq_show_form"] = False
                    st.session_state["_faq_edit_idx"]  = None
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif can_edit and not st.session_state.get("_faq_show_form", False):
            if st.button("➕ Ajouter une question", key="faq_add_btn", use_container_width=True):
                st.session_state["_faq_show_form"] = True
                st.session_state["_faq_edit_idx"]  = None
                st.rerun()

        if not faq_items:
            st.markdown(
                "<div style='background:#f8fafc;border:1.5px dashed #cbd5e1;"
                "border-radius:12px;padding:32px;text-align:center;margin-top:12px'>"
                "<div style='font-size:2.5rem;margin-bottom:8px'>❓</div>"
                "<div style='font-weight:700;color:#475569'>Aucune question définie</div>"
                "<div style='font-size:.8rem;color:#94a3b8;margin-top:4px'>"
                "Cliquez sur ➕ Ajouter une question ci-dessus</div></div>",
                unsafe_allow_html=True)
        else:
            all_cats_tab = ["Toutes"] + sorted(set(f.get("category", "Général") for f in faq_items))
            faq_filter_cat = st.selectbox(
                "Filtrer", all_cats_tab, key="faq_tab_cat_filter", label_visibility="collapsed")

            st.markdown(
                "<div style='display:grid;grid-template-columns:2fr 1fr;"
                "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;"
                "padding:10px 14px;margin-top:8px'>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff'>Question</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Catégorie</div>"
                "</div>",
                unsafe_allow_html=True)

            CAT_COL = {
                "Général":             "#2563eb",
                "Score & Seuils":      "#7c3aed",
                "Prélèvements":        "#0891b2",
                "Paramètres":          "#059669",
                "Données":             "#d97706",
                "Mesures correctives": "#dc2626",
            }

            displayed = [
                (i, f) for i, f in enumerate(faq_items)
                if faq_filter_cat == "Toutes" or f.get("category") == faq_filter_cat
            ]

            if not displayed:
                st.markdown(
                    "<div style='background:#f8fafc;border:1px solid #e2e8f0;border-top:none;"
                    "border-radius:0 0 10px 10px;padding:20px;text-align:center;"
                    "color:#94a3b8;font-size:.82rem'>Aucune question dans cette catégorie</div>",
                    unsafe_allow_html=True)
            else:
                for dp, (ri, item) in enumerate(displayed):
                    cc     = CAT_COL.get(item.get("category", "Général"), "#475569")
                    row_bg = "#f8fafc" if dp % 2 == 0 else "#ffffff"

                    rc1, rc2 = st.columns([6, 1])
                    with rc1:
                        st.markdown(
                            f"<div style='display:grid;grid-template-columns:2fr 1fr;"
                            f"gap:4px;background:{row_bg};border:1px solid #e2e8f0;"
                            f"border-top:none;padding:10px 14px;align-items:center'>"
                            f"<div style='font-size:.82rem;font-weight:600;color:#0f172a'>"
                            f"{item['question']}</div>"
                            f"<div style='text-align:center'>"
                            f"<span style='background:{cc}18;color:{cc};"
                            f"border:1px solid {cc}44;border-radius:12px;"
                            f"padding:2px 10px;font-size:.65rem;font-weight:700'>"
                            f"{item.get('category','Général')}</span></div></div>",
                            unsafe_allow_html=True)
                    with rc2:
                        a1, a2, a3, a4 = st.columns(4)
                        with a1:
                            if can_edit and ri > 0:
                                if st.button("↑", key=f"faq_up_{ri}", help="Monter"):
                                    faq_items[ri], faq_items[ri-1] = faq_items[ri-1], faq_items[ri]
                                    for k, f in enumerate(faq_items): f["order"] = k
                                    save_faq(faq_items, supa=True)
                                    st.session_state["faq_items"] = faq_items
                                    st.rerun()
                        with a2:
                            if can_edit and ri < len(faq_items) - 1:
                                if st.button("↓", key=f"faq_dn_{ri}", help="Descendre"):
                                    faq_items[ri], faq_items[ri+1] = faq_items[ri+1], faq_items[ri]
                                    for k, f in enumerate(faq_items): f["order"] = k
                                    save_faq(faq_items, supa=True)
                                    st.session_state["faq_items"] = faq_items
                                    st.rerun()
                        with a3:
                            if can_edit:
                                if st.button("✏️", key=f"faq_edit_{ri}"):
                                    st.session_state["_faq_edit_idx"]  = ri
                                    st.session_state["_faq_show_form"] = True
                                    st.rerun()
                        with a4:
                            if can_edit:
                                if st.button("🗑️", key=f"faq_del_{ri}"):
                                    faq_items.pop(ri)
                                    for k, f in enumerate(faq_items): f["order"] = k
                                    save_faq(faq_items, supa=True)
                                    st.session_state["faq_items"] = faq_items
                                    st.rerun()

                st.markdown(
                    f"<div style='background:#1e293b;border-radius:0 0 10px 10px;"
                    f"padding:8px 14px'><div style='font-size:.75rem;color:#94a3b8'>"
                    f"{len(faq_items)} question(s) · {len(displayed)} affichée(s)"
                    f"</div></div>",
                    unsafe_allow_html=True)

        st.divider()

        if can_edit:
            st.markdown("#### ↩️ Réinitialiser la FAQ")
            st.caption("Recharge les questions prédéfinies (efface les modifications personnalisées).")
            if st.button("↩️ Remettre les questions par défaut", key="faq_reset"):
                st.session_state["faq_items"] = [dict(f) for f in DEFAULT_FAQ]
                save_faq(st.session_state["faq_items"], supa=True)
                st.success("✅ FAQ réinitialisée.")
                st.rerun()