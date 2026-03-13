import streamlit as st
import json
import csv
import io
import os
import base64
import calendar as cal_module
from datetime import datetime, timedelta, date as date_type
import difflib

# ── Gestion accès protégé ──────────────────────────────────────────────
if "access_mode" not in st.session_state:
    st.session_state["access_mode"] = None  # None = pas encore choisi

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
</style>""", unsafe_allow_html=True)

RISK_COLORS = {1:"#22c55e",2:"#84cc16",3:"#f59e0b",4:"#f97316",5:"#ef4444"}
RISK_LABELS = {1:"Limité",2:"Modéré",3:"Important",4:"Majeur",5:"Critique"}
CSV_FILE = "surveillance_data.csv"
GERMS_FILE = "germs_data.json"
THRESHOLDS_FILE = "thresholds_config.json"

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

MEASURES_FILE = "measures_config.json"
POINTS_FILE = "points.json"
PRELEVEMENTS_FILE = "prelevements.json"
SCHEDULES_FILE = "schedules.json"
PENDING_FILE = "pending_identifications.json"
ARCHIVED_FILE = "archived_samples.json"
OPERATORS_FILE = "operators.json"

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
    dict(name="Burkholderia cepacia",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
    dict(name="Burkholderia cepacia",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Massilia spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],notes=None,comment=None),
    dict(name="Massilia spp.",path=["Germes","Bactéries","Environnemental","Humidité"],notes=None,comment=None),
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
            {'key': key, 'value': value_json},
            on_conflict='key'
        ).execute()
        return True
    except Exception as e:
        print(f"[SUPA ERROR] key={key} : {e}")  # visible dans les logs Streamlit Cloud
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
    # On sauvegarde aussi les noms connus pour différencier
    # "supprimé intentionnellement" vs "nouveau dans le code"
    known_default_names = sorted(DEFAULT_GERM_NAMES)
    payload = {
        "germs": germs,
        "known_defaults": known_default_names
    }
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
    known_defaults = set()  # noms connus lors de la dernière sauvegarde

    raw_json = _supa_get('germs')
    if raw_json:
        try:
            raw = json.loads(raw_json)
            # Nouveau format : dict avec "germs" et "known_defaults"
            if isinstance(raw, dict):
                saved_germs = raw.get("germs", [])
                known_defaults = set(raw.get("known_defaults", []))
            # Ancien format : liste simple (rétrocompatibilité)
            elif isinstance(raw, list):
                saved_germs = raw
                known_defaults = set()  # inconnu → comportement sécurisé
        except Exception:
            saved_germs = []

    if not saved_germs and os.path.exists(GERMS_FILE):
        try:
            with open(GERMS_FILE) as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                saved_germs = raw.get("germs", [])
                known_defaults = set(raw.get("known_defaults", []))
            elif isinstance(raw, list):
                saved_germs = raw
        except Exception:
            saved_germs = []

    # Rien en base → on retourne les défauts tels quels
    if not saved_germs:
        return [dict(d) for d in DEFAULT_GERMS], len(DEFAULT_GERMS)

    saved_by_name = {g.get("name", ""): g for g in saved_germs}
    merged = []
    new_defaults_added = 0

    for dflt in DEFAULT_GERMS:
        name = dflt["name"]
        if name in saved_by_name:
            # Germe existant : on garde la version sauvegardée
            merged.append(dict(saved_by_name[name]))
        elif name not in known_defaults:
            # Genuinement nouveau dans le code (absent de l'ancienne base)
            merged.append(dict(dflt))
            new_defaults_added += 1
        # else : était connu mais absent de saved → intentionnellement supprimé, on skip

    # Germes personnalisés (hors DEFAULT_GERMS)
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
    # Aucune donnée sauvegardée → on charge les défauts une seule fois
    return [dict(m) for m in DEFAULT_ORIGIN_MEASURES]

def save_origin_measures(measures, supa=True):
    if supa:
        try:
            result = _supa_upsert('measures', json.dumps(measures, ensure_ascii=False))
            if not result:
                import streamlit as st
                st.warning("⚠️ Supabase non connecté — sauvegarde locale uniquement.")
        except Exception as e:
            import streamlit as st
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

def load_points(): return _load_json_key('points', POINTS_FILE)
def save_points(d, supa=True):
    _save_json_key('points', d, POINTS_FILE)
    if supa: _supa_upsert('points', json.dumps(d, ensure_ascii=False))

def load_prelevements(): return _load_json_key('prelevements', PRELEVEMENTS_FILE)
def save_prelevements(d, supa=True):
    _save_json_key('prelevements', d, PRELEVEMENTS_FILE)
    if supa: _supa_upsert('prelevements', json.dumps(d, ensure_ascii=False))

def load_schedules(): return _load_json_key('schedules', SCHEDULES_FILE)
def save_schedules(d, supa=True):
    _save_json_key('schedules', d, SCHEDULES_FILE)
    if supa: _supa_upsert('schedules', json.dumps(d, ensure_ascii=False))

def load_pending_identifications(): return _load_json_key('pending_identifications', PENDING_FILE)
def save_pending_identifications(d, supa=True):
    _save_json_key('pending_identifications', d, PENDING_FILE)
    if supa: _supa_upsert('pending_identifications', json.dumps(d, ensure_ascii=False))

def load_archived_samples(): return _load_json_key('archived_samples', ARCHIVED_FILE)
def save_archived_samples(d, supa=True):
    _save_json_key('archived_samples', d, ARCHIVED_FILE)
    if supa: _supa_upsert('archived_samples', json.dumps(d, ensure_ascii=False))

def load_operators(): return _load_json_key('operators', OPERATORS_FILE)
def save_operators(d, supa=True):
    _save_json_key('operators', d, OPERATORS_FILE)
    if supa: _supa_upsert('operators', json.dumps(d, ensure_ascii=False))

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
    # Supprimer le CSV si liste vide, sinon écrire
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
        "germs":                    st.session_state.germs,
        "thresholds":               {str(k): v for k, v in st.session_state.thresholds.items()},
        "measures":                 {str(k): v for k, v in st.session_state.measures.items()},
        "origin_measures":          st.session_state.origin_measures,
        "points":                   st.session_state.points,
        "operators":                st.session_state.operators,
        "prelevements":             st.session_state.prelevements,
        "schedules":                st.session_state.schedules,
        "pending_identifications":  st.session_state.pending_identifications,
        "archived_samples":         st.session_state.archived_samples,
        "surveillance":             st.session_state.surveillance,
        "planning_overrides": st.session_state.get("planning_overrides", {}),
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
    query_low = query.lower().strip()
    query_genus = query_low.split()[0] if query_low else ""
    best_score = 0
    best_match = None
    for g in germs:
        name_low = g["name"].lower()
        genus = name_low.split()[0]
        if query_genus and query_genus == genus:
            score = 0.9
        else:
            score = difflib.SequenceMatcher(None, query_low, name_low).ratio()
            genus_score = difflib.SequenceMatcher(None, query_genus, genus).ratio()
            score = max(score, genus_score * 0.85)
        if score > best_score:
            best_score = score
            best_match = g
    return best_match, best_score


# ── CONTRÔLE D'ACCÈS PROTÉGÉ ───────────────────────────────────────────────────
def check_access_protege(onglet_nom: str) -> bool:
    """
    Affiche un écran de connexion pour les onglets protégés.
    Retourne True si l'utilisateur est en mode admin (modifications autorisées).
    Retourne False si lecture seule (le contenu de l'onglet est bloqué via st.stop()).
    """
    key_mode = f"access_mode_{onglet_nom}"
    key_pwd  = f"pwd_input_{onglet_nom}"
    key_err  = f"pwd_error_{onglet_nom}"

    # ── Déjà authentifié en admin ──────────────────────────────────────────
    if st.session_state.get(key_mode) == "admin":
        col_info, col_lock = st.columns([5, 1])
        with col_info:
            st.success("🔓 Mode administrateur — modifications autorisées")
        with col_lock:
            if st.button("🔒 Verrouiller", key=f"lock_{onglet_nom}", use_container_width=True):
                st.session_state[key_mode] = None
                st.rerun()
        return True

    # ── Déjà en lecture seule ──────────────────────────────────────────────
    if st.session_state.get(key_mode) == "lecture":
        col_info, col_conn = st.columns([5, 1])
        with col_info:
            st.info("👁️ Mode lecture seule — aucune modification possible")
        with col_conn:
            if st.button("🔑 Se connecter", key=f"connect_{onglet_nom}", use_container_width=True):
                st.session_state[key_mode] = None
                st.rerun()
        return False

    # ── Pas encore choisi → afficher le formulaire ─────────────────────────
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
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔑 Accès administrateur**")
        pwd = st.text_input(
            "Mot de passe",
            type="password",
            key=key_pwd,
            placeholder="Entrez le mot de passe",
            label_visibility="collapsed"
        )
        if st.button("✅ Connexion", key=f"btn_admin_{onglet_nom}", use_container_width=True, type="primary"):
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
            unsafe_allow_html=True
        )
        if st.button("👁️ Continuer en lecture", key=f"btn_lecture_{onglet_nom}", use_container_width=True):
            st.session_state[key_mode] = "lecture"
            st.rerun()

    st.stop()  # bloque le rendu du reste de l'onglet tant qu'aucun choix n'est fait
    return False


# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "germs" not in st.session_state:
    _germs, _new = load_germs()
    st.session_state.germs = _germs
    st.session_state.germs_synced_count = _new
    # Sauvegarde SEULEMENT si de nouveaux germes par défaut ont été ajoutés
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

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-size:.85rem;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;margin-bottom:12px;font-weight:700">NAVIGATION</p>', unsafe_allow_html=True)
    tabs_cfg = [
        ("logigramme",   "📊", "Logigramme"),
        ("surveillance", "🔍", "Identification & Surveillance"),
        ("planning",     "📅", "Planning"),
        ("plan",         "🗺️", "Plan URC"),
        ("historique",   "📋", "Historique"),
        ("parametres",   "⚙️", "Paramètres & Seuils"),
    ]
    for key, icon, label in tabs_cfg:
        t = "primary" if st.session_state.active_tab == key else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.active_tab = key
            st.rerun()
    st.divider()
    supa_ok = get_supabase_client() is not None
    supa_icon = "🟢" if supa_ok else "🔴"
    supa_txt = "Supabase connecté" if supa_ok else "Mode local (fichiers)"
    st.markdown(f'<p style="font-size:.7rem;color:#94a3b8;text-align:center">{supa_icon} {supa_txt}</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:.75rem;color:#94a3b8;text-align:center">MicroSurveillance URC v5.0</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<p style="font-size:.7rem;color:#f59e0b;font-weight:700;text-align:center;text-transform:uppercase;letter-spacing:.08em">💾 Sauvegarde données</p>', unsafe_allow_html=True)
    _backup_data = json.dumps(export_all_data(), ensure_ascii=False, indent=2)
    _backup_name = f"backup_URC_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    st.download_button(
        label="⬇️ Exporter toutes les données",
        data=_backup_data,
        file_name=_backup_name,
        mime="application/json",
        use_container_width=True,
        key="sidebar_export",
        help="Téléchargez ce fichier avant toute modification du code pour ne jamais perdre vos données"
    )
    if not supa_ok:
        st.markdown('<p style="font-size:.6rem;color:#f59e0b;text-align:center;margin-top:4px">⚠️ Sans Supabase, exportez régulièrement vos données !</p>', unsafe_allow_html=True)

active = st.session_state.active_tab
today = datetime.today().date()

# ═══════════════════════════════════════════════════════════════════════════════
# POPUP MODALE — lectures en attente (remplace le st.warning basique)
# ═══════════════════════════════════════════════════════════════════════════════
due_global = [s for s in st.session_state.schedules if s["status"] == "pending" and datetime.fromisoformat(s["due_date"]).date() <= today]

if due_global and not st.session_state.due_alert_shown:
    _nb = len(due_global)
    _items_html = ""
    for _s in due_global[:6]:
        _d = datetime.fromisoformat(_s["due_date"]).date()
        _late = _d < today
        _bc = "#ef4444" if _late else "#f59e0b"
        _ic = "🚨" if _late else "⏳"
        _diff_txt = f"{(today - _d).days}j de retard" if _late else "aujourd'hui"
        _items_html += f"""<div style='background:#fff;border-left:3px solid {_bc};border-radius:0 6px 6px 0;
            padding:7px 12px;margin-bottom:5px;font-size:.8rem;color:#0f172a;
            display:flex;align-items:center;justify-content:space-between'>
            <span>{_ic} <strong>{_s['label']}</strong></span>
            <span style='background:{_bc}22;color:{_bc};border-radius:4px;padding:2px 8px;
                font-size:.68rem;font-weight:700'>{_s['when']} — {_diff_txt}</span>
        </div>"""
    if _nb > 6:
        _items_html += f"<div style='font-size:.7rem;color:#94a3b8;font-style:italic;padding:4px 10px'>+ {_nb - 6} autre(s)…</div>"

    _popup = f"""
    <div id="dueModal" style="position:fixed;inset:0;background:rgba(15,23,42,.6);z-index:99999;
        display:flex;align-items:center;justify-content:center;animation:fadeIn .2s ease">
      <div style="background:#fff;border-radius:16px;width:min(480px,92vw);
          box-shadow:0 24px 60px rgba(0,0,0,.35);overflow:hidden;animation:slideUp .25s ease">
        <div style="background:linear-gradient(135deg,#dc2626,#ef4444);padding:20px 24px;
            display:flex;align-items:center;justify-content:space-between">
          <div style="display:flex;align-items:center;gap:14px">
            <span style="font-size:2rem">🔔</span>
            <div>
              <div style="color:#fff;font-weight:800;font-size:1.1rem">
                {_nb} lecture{'s' if _nb > 1 else ''} à faire aujourd'hui
              </div>
              <div style="color:#fecaca;font-size:.75rem;margin-top:3px">
                Allez dans Identification &amp; Surveillance pour les traiter
              </div>
            </div>
          </div>
          <button onclick="document.getElementById('dueModal').style.display='none'"
            style="background:rgba(255,255,255,.2);border:none;border-radius:50%;width:32px;height:32px;
            cursor:pointer;font-size:1.1rem;color:#fff;line-height:32px;text-align:center">✕</button>
        </div>
        <div style="background:#fef2f2;padding:20px;text-align:center;border-bottom:1px solid #fee2e2">
          <div style="font-size:3.5rem;font-weight:900;color:#dc2626;line-height:1">{_nb}</div>
          <div style="font-size:.8rem;color:#991b1b;font-weight:700;text-transform:uppercase;
              letter-spacing:.08em;margin-top:4px">
            lecture{'s' if _nb > 1 else ''} en attente
          </div>
        </div>
        <div style="padding:14px 16px;max-height:200px;overflow-y:auto;background:#f8fafc">
          {_items_html}
        </div>
        <div style="padding:14px 16px;background:#fff;border-top:1px solid #f1f5f9">
          <button onclick="document.getElementById('dueModal').style.display='none'"
            style="width:100%;background:#2563eb;color:#fff;border:none;border-radius:10px;
            padding:12px;font-size:.95rem;font-weight:700;cursor:pointer">
            Compris — Je vais les traiter 👍
          </button>
        </div>
      </div>
    </div>
    <style>
      @keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
      @keyframes slideUp{{from{{transform:translateY(24px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
    </style>
    """
    st.components.v1.html(_popup, height=0, scrolling=False)
    st.session_state.due_alert_shown = True

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown('<h1 style="font-size:1.3rem;letter-spacing:.1em;text-transform:uppercase;color:#1e40af!important;margin-bottom:0">🦠 MicroSurveillance URC</h1>', unsafe_allow_html=True)
st.caption("Surveillance microbiologique — Unité de Reconstitution des Chimiothérapies")

# ─────────────────────────────────────────────────────────────────────────────
# UTILISATION dans vos onglets (à coller en tête de chaque onglet protégé) :
#
#   if active == "parametres":
#       can_edit = check_access_protege("Paramètres & Seuils")
#       # si lecture seule → st.stop() est appelé dans la fonction,
#       # donc la suite ne s'exécute que si can_edit == True
#       ... reste du code paramètres ...
#
#   if active == "logigramme":
#       can_edit = check_access_protege("Logigramme")
#       ... reste du code logigramme ...
# ─────────────────────────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════════════════
# TAB : LOGIGRAMME — COMPLET
# Criticité germe = Pathogénicité × Résistance × Dissémination (score 1–27)
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
# TAB : SURVEILLANCE — COMPLET
# score_total = location_criticality (1–3) × germ_score (1–27)
# ⚠️ Alerte : 24 ≤ score ≤ 36  |  🚨 Action : score > 36
# ═══════════════════════════════════════════════════════════════════════════════

if active == "surveillance":
    st.markdown("### 🔍 Identification & Surveillance microbiologique")

    # ── Helpers scoring ────────────────────────────────────────────────────────
    def _get_location_criticality(sample):
        """
        Récupère la criticité du lieu depuis le sample.
        Fallback : retrouve le point dans session_state.points,
        puis migration room_class (A=3, B/C=2, D=1), sinon 1.
        """
        if "location_criticality" in sample:
            try: return int(sample["location_criticality"])
            except: pass
        # Cherche dans la liste des points par label
        pt = next((p for p in st.session_state.points
                   if p.get("label") == sample.get("label")), None)
        if pt and "location_criticality" in pt:
            try: return int(pt["location_criticality"])
            except: pass
        # Migration room_class
        rc = str(sample.get("room_class", "")).strip().upper()
        return {"A": 3, "B": 2, "C": 2, "D": 1}.get(rc, 1)

    def _get_germ_score(germ):
        """Score du germe : p × r × d, ou migration ancien modèle."""
        if all(k in germ for k in ("pathogenicity", "resistance", "dissemination")):
            return int(germ["pathogenicity"]) * int(germ["resistance"]) * int(germ["dissemination"])
        old = germ.get("risk", 1)
        return {1: 1, 2: 2, 3: 6, 4: 12, 5: 18}.get(old, old)

    def _evaluate_score(total):
        if total > 36:  return "action", "🚨 ACTION",  "#ef4444"
        if total >= 24: return "alert",  "⚠️ ALERTE",  "#f59e0b"
        return "ok", "✅ Conforme", "#22c55e"

    def _loc_crit_label(n):
        return {1: "Non critique", 2: "Semi-critique", 3: "Critique"}.get(n, str(n))

    tab_surv, tab_etiq = st.tabs(["🔬 Surveillance", "🏷️ Étiquettes"])

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET SURVEILLANCE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_surv:

        # ── Nouveau prélèvement ───────────────────────────────────────────────
        with st.expander("🧪 Nouveau prélèvement", expanded=False):
            if not st.session_state.points:
                st.info("Aucun point de prélèvement défini — allez dans **Paramètres → Points de prélèvement**.")
            else:
                p_col1, p_col2, p_col3 = st.columns([3, 2, 1])
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
                          <div style="font-size:.85rem;font-weight:700;color:{lc_col};margin-top:2px">
                            Nv.{pt_loc_crit} — {lc_lbl}
                          </div>
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
                        ⚠️ Alerte 16–24 &nbsp;·&nbsp; 🚨 Action &gt; 24
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
                    p_poste = "Poste 1"
                    if selected_point.get('room_class') == "A" or pt_loc_crit == 3:
                        st.markdown(
                            "<div style='background:#fef9c3;border:1px solid #fde047;"
                            "border-radius:8px;padding:10px;margin-top:8px'>"
                            "<div style='font-size:.7rem;font-weight:700;color:#854d0e;margin-bottom:8px'>"
                            "🔬 Paramètres Zone Critique (Nv.3)</div>",
                            unsafe_allow_html=True)
                        p_isolateur = st.radio(
                            "Quel isolateur ?", ["Iso 16/0724","Iso 14/07169"],
                            horizontal=True, key="new_prelev_isolateur")
                        p_poste = st.radio(
                            "Quel poste ?", ["Poste 1","Poste 2","Commun"],
                            horizontal=True, key="new_prelev_poste")
                        st.markdown("</div>", unsafe_allow_html=True)

                with p_col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Enregistrer\nprélèvement", use_container_width=True, key="save_prelev"):
                        pid = f"s{len(st.session_state.prelevements)+1}_{int(datetime.now().timestamp())}"
                        sample = {
                            "id":                   pid,
                            "label":                selected_point['label'],
                            "type":                 selected_point.get('type'),
                            "gelose":               selected_point.get('gelose', '—'),
                            "room_class":           selected_point.get('room_class', ''),
                            "location_criticality": pt_loc_crit,
                            "operateur":            p_oper,
                            "date":                 str(p_date),
                            "archived":             False,
                            "num_isolateur":        p_isolateur if pt_loc_crit == 3 else "",
                            "poste":                p_poste if pt_loc_crit == 3 else "",
                            "commentaire":          p_commentaire
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
                        st.rerun()

        st.divider()

        # ── Prélèvements actifs ───────────────────────────────────────────────
        for idx, samp in enumerate(st.session_state.prelevements):
            if samp.get("archived"):
                continue
            col_info, col_edit, col_del = st.columns([5, 1, 1])
            with col_info:
                loc_c    = int(samp.get("location_criticality", 1))
                lc_col   = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(loc_c),"#94a3b8")
                room_cl  = samp.get('room_class','') or ''
                room_badge = (
                    f"<span style='background:#dbeafe;color:#1e40af;border:1px solid #93c5fd;"
                    f"border-radius:4px;padding:1px 6px;font-size:.72rem;font-weight:800;"
                    f"margin-left:4px'>Cl.{room_cl}</span>"
                    if room_cl else "")
                _comment_html = (
                    f"<div style='font-size:.72rem;color:#6366f1;margin-top:3px'>"
                    f"💬 {samp['commentaire']}</div>"
                    if samp.get('commentaire') else "")
                st.markdown(
                    f"<div style='background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;"
                    f"padding:10px 16px;margin-bottom:6px'>"
                    f"<span style='font-weight:700'>{samp['label']}</span>{room_badge} "
                    f"<span style='color:#64748b;font-size:.8rem'>— {samp.get('type','—')} "
                    f"· <span style='color:{lc_col};font-weight:600'>Nv.{loc_c}</span>"
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
                        new_poste = "Poste 1"
                        if int(samp.get("location_criticality", 1)) == 3:
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
                            if int(samp.get("location_criticality",1)) == 3:
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

        # ── Lectures en attente ───────────────────────────────────────────────
        st.markdown("#### 📅 Lectures en attente")
        pending_schedules = [s for s in st.session_state.schedules if s["status"] == "pending"]
        overdue  = [s for s in pending_schedules if datetime.fromisoformat(s["due_date"]).date() <= today]
        upcoming = [s for s in pending_schedules if datetime.fromisoformat(s["due_date"]).date() > today]

        if overdue:
            st.markdown(
                f'<div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;'
                f'padding:12px 16px;margin-bottom:12px"><span style="color:#dc2626;font-weight:700">'
                f'🔔 {len(overdue)} lecture(s) en retard — à traiter dès que possible</span></div>',
                unsafe_allow_html=True)
        if upcoming:
            st.markdown(
                f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;'
                f'padding:10px 16px;margin-bottom:12px"><span style="color:#16a34a;font-size:.8rem">'
                f'📆 {len(upcoming)} lecture(s) à venir</span></div>',
                unsafe_allow_html=True)
        if not pending_schedules:
            st.info("Aucune lecture planifiée — tous les prélèvements sont à jour.")

        def _should_show(s, all_schedules):
            if s['when'] == 'J2': return True
            j2 = next((x for x in all_schedules if x['sample_id'] == s['sample_id'] and x['when'] == 'J2'), None)
            return j2 is None or j2['status'] == 'done'

        for s in [s for s in (overdue + upcoming) if _should_show(s, st.session_state.schedules)]:
            sched_date  = datetime.fromisoformat(s["due_date"]).date()
            is_late     = sched_date <= today
            border_col  = "#ef4444" if is_late else "#3b82f6"
            bg_col      = "#fef2f2" if is_late else "#eff6ff"
            badge_col   = "#dc2626" if is_late else "#1d4ed8"
            status_txt  = "EN RETARD" if is_late else f"dans {(sched_date - today).days}j"
            smp         = next((p for p in st.session_state.prelevements if p['id'] == s['sample_id']), None)
            pt_type     = smp.get('type', '?')       if smp else '?'
            pt_gelose   = smp.get('gelose', '?')     if smp else '?'
            pt_oper     = smp.get('operateur', '?')  if smp else '?'
            pt_room_cl  = smp.get('room_class', '')  if smp else ''
            loc_crit    = _get_location_criticality(smp) if smp else 1
            lc_col_s    = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(loc_crit),"#94a3b8")
            lc_lbl_s    = _loc_crit_label(loc_crit)
            room_cl_badge = (
                f"<span style='background:#dbeafe;color:#1e40af;border:1px solid #93c5fd;"
                f"border-radius:4px;padding:1px 6px;font-size:.62rem;font-weight:800;"
                f"margin-left:6px'>Cl.{pt_room_cl}</span>"
                if pt_room_cl else "")

            extra_info = ""
            if smp and loc_crit == 3:
                iso = smp.get("num_isolateur","—") or "—"
                pst = smp.get("poste","—") or "—"
                extra_info = (
                    f"<div style='background:#fef9c3;border-radius:6px;padding:6px 8px;"
                    f"border:1px solid #fde047;font-size:.7rem;color:#854d0e;"
                    f"font-weight:600;margin-top:6px'>"
                    f"🔬 Zone Critique · Isolateur : {iso} · {pst}</div>")

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
                    if st.button(f"🔬 Traiter cette lecture ({s['when']})", key=f"proc_{s['id']}", use_container_width=True):
                        st.session_state.current_process = s['id']
                        st.rerun()
                with bc2:
                    if st.button("🗑️ Supprimer", key=f"del_sch_{s['id']}", use_container_width=True):
                        sid = s.get('sample_id')
                        st.session_state.schedules    = [x for x in st.session_state.schedules    if x['sample_id'] != sid]
                        st.session_state.prelevements = [x for x in st.session_state.prelevements if x['id'] != sid]
                        st.session_state.pending_identifications = [x for x in st.session_state.pending_identifications if x.get('sample_id') != sid]
                        save_schedules(st.session_state.schedules)
                        save_prelevements(st.session_state.prelevements)
                        save_pending_identifications(st.session_state.pending_identifications)
                        st.success("Prélèvement, lectures et identifications supprimés.")
                        st.rerun()

        # ── Traitement d'une lecture ──────────────────────────────────────────
        if st.session_state.current_process:
            proc_id = st.session_state.current_process
            proc    = next((x for x in st.session_state.schedules if x['id'] == proc_id), None)
            if proc:
                smp       = next((p for p in st.session_state.prelevements if p['id'] == proc['sample_id']), None)
                pt_type   = smp.get('type', '?')       if smp else '?'
                pt_gelose = smp.get('gelose', '?')     if smp else '?'
                pt_oper   = smp.get('operateur', '?')  if smp else '?'
                pt_date   = smp.get('date', '?')       if smp else '?'
                pt_room_p = smp.get('room_class', '')  if smp else ''
                loc_crit  = _get_location_criticality(smp) if smp else 1
                lc_col_p  = {"1":"#22c55e","2":"#f59e0b","3":"#ef4444"}.get(str(loc_crit),"#94a3b8")

                classea_band = ""
                if smp and loc_crit == 3:
                    iso = smp.get("num_isolateur","—") or "—"
                    pst = smp.get("poste","—") or "—"
                    classea_band = (
                        f"<div style='background:#fef9c3;border:1px solid #fde047;"
                        f"border-radius:8px;padding:8px 12px;margin-top:10px;"
                        f"font-size:.75rem;font-weight:700;color:#854d0e'>"
                        f"🔬 Zone Critique · Isolateur : {iso} · {pst}</div>")

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
                    <div style="background:#dbeafe;border-radius:8px;padding:10px;text-align:center;
                    border:1px solid #93c5fd">
                      <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Classe</div>
                      <div style="font-size:.85rem;font-weight:800;color:#1e40af;margin-top:3px">{pt_room_p or '—'}</div>
                    </div>
                    <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
                      <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Gélose</div>
                      <div style="font-size:.85rem;font-weight:700;color:#1d4ed8;margin-top:3px">🧫 {pt_gelose}</div>
                    </div>
                    <div style="background:{lc_col_p}11;border-radius:8px;padding:10px;text-align:center;
                    border:1px solid {lc_col_p}44">
                      <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Criticité lieu</div>
                      <div style="font-size:.85rem;font-weight:700;color:{lc_col_p};margin-top:3px">
                        Nv.{loc_crit}
                      </div>
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

        # ── Carte d'alerte mesures correctives ────────────────────────────────
        def _render_alerte_mesures(pop_data, key_suffix):
            _is_action   = pop_data["status"] == "action"
            _border      = "#ef4444" if _is_action else "#f59e0b"
            _bg_head     = "#fef2f2" if _is_action else "#fffbeb"
            _hd_col      = "#991b1b" if _is_action else "#92400e"
            _ic          = "🚨" if _is_action else "⚠️"
            _txt         = "ACTION REQUISE" if _is_action else "ALERTE"
            _germ_sc     = pop_data.get("germ_score", "—")
            _loc_c       = pop_data.get("loc_criticality", "—")
            _total       = pop_data.get("total_score", "—")

            type_colors = {"action":"#ef4444","alert":"#f59e0b","both":"#818cf8"}
            type_labels = {"action":"🚨 Action","alert":"⚠️ Alerte","both":"⚠️🚨 Les deux"}

            def _match(m):
                if pop_data["status"]=="alert"  and m.get("type") not in ("alert","both"):  return False
                if pop_data["status"]=="action" and m.get("type") not in ("action","both"): return False
                mr = m.get("risk","all")
                if mr != "all":
                    gr = pop_data.get("risk", 1)
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
                    <div style="font-size:.6rem;color:#64748b;margin-top:2px">
                      Lieu {_loc_c} × Germe {_germ_sc}
                    </div>
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
                    _tc = type_colors.get(_m["type"], "#94a3b8")
                    _tl = type_labels.get(_m["type"], _m["type"])
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

        # ── Récapitulatif dernière alerte ─────────────────────────────────────
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

        # ── Identifications en attente ────────────────────────────────────────
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

        if pending_ids_grouped:
            st.markdown("---")
            st.markdown("#### 🔴 Identifications en attente")
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

                # ── Init liste germes en session state ──────────────────
                germs_list_key = f"germs_list_{_key}"
                if germs_list_key not in st.session_state:
                    st.session_state[germs_list_key] = [{"germ": "— Sélectionner un germe —", "ufc": 0}]

                with st.expander(
                    f"🔴 {_label} — {_when_str} — {_ufc} UFC — {_date}",
                    expanded=True):

                    # Bandeau criticité lieu
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

                    # ── Liste dynamique des germes ───────────────────────
                    st.markdown(
                        "<div style='font-size:.8rem;font-weight:700;color:#475569;"
                        "margin-bottom:6px'>🧫 Germes identifiés</div>",
                        unsafe_allow_html=True)

                    germs_to_remove = []
                    current_germs = st.session_state[germs_list_key]

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
                                "UFC",
                                min_value=0,
                                value=int(germ_entry["ufc"]) if germ_entry["ufc"] else 0,
                                step=1,
                                key=f"germ_ufc_{_key}_{gi}")
                            current_germs[gi]["ufc"] = ufc_val
                        with cols[2]:
                            st.markdown("<div style='margin-top:22px'>", unsafe_allow_html=True)
                            if gi > 0:
                                if st.button("🗑️", key=f"del_germ_{_key}_{gi}", help="Supprimer ce germe"):
                                    germs_to_remove.append(gi)
                            st.markdown("</div>", unsafe_allow_html=True)

                    # Appliquer suppressions
                    for idx in sorted(germs_to_remove, reverse=True):
                        st.session_state[germs_list_key].pop(idx)
                        st.rerun()

                    if st.button("➕ Ajouter un germe", key=f"add_germ_{_key}", use_container_width=False):
                        st.session_state[germs_list_key].append({"germ": "— Sélectionner un germe —", "ufc": 0})
                        st.rerun()

                    # ── Aperçu score multi-germes ────────────────────────
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
                            worst = max(scored_germs, key=lambda x: x["score"])
                            ts_prev = loc_crit * worst["score"]
                            st_prev, _, sc_prev = _evaluate_score(ts_prev)

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
                        remarque = st.text_area("Remarque", height=60, key=f"rem_id_{_key}")
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
                                # Calcul scores pour chaque germe
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
                                    # Germe avec score le plus élevé → détermine le statut
                                    worst_entry = max(scored_entries, key=lambda x: x["germ_score"])
                                    total_sc    = loc_crit * worst_entry["germ_score"]
                                    status, status_lbl, status_col = _evaluate_score(total_sc)

                                    triggered_by = None
                                    if status in ("alert", "action"):
                                        triggered_by = (
                                            f"lieu {loc_crit} × germe {worst_entry['germ_score']} "
                                            f"({worst_entry['germ_match']})"
                                            if loc_crit > 1
                                            else f"germe {worst_entry['germ_match']} (score {worst_entry['germ_score']})")

                                    # Sérialisation liste germes pour stockage
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
                                        # Compatibilité champs mono-germe (germe le + critique)
                                        "germ_saisi":         worst_entry["germ_saisi"],
                                        "germ_match":         worst_entry["germ_match"],
                                        "match_score":        worst_entry["match_score"],
                                        "ufc":                worst_entry["ufc"],
                                        "germ_score":         worst_entry["germ_score"],
                                        # Multi-germes
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

                                    # Nettoyage liste germes temporaire
                                    del st.session_state[germs_list_key]

                                    if status in ("alert", "action"):
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
                                            f"(score {total_sc} = lieu {loc_crit} × germe le + critique {worst_entry['germ_score']})")
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

        # ── Derniers résultats ────────────────────────────────────────────────
        if st.session_state.surveillance:
            st.markdown("---")
            st.markdown("### 📋 Derniers résultats")
            for r in reversed(st.session_state.surveillance[-10:]):
                sc  = "#ef4444" if r["status"]=="action" else "#f59e0b" if r["status"]=="alert" else "#22c55e"
                ic  = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
                ufc_display  = f"{r['ufc']} UFC" if r.get('ufc') else "—"
                total_score  = r.get("total_score")
                germ_score   = r.get("germ_score")
                loc_crit_r   = r.get("location_criticality")

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
    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET ÉTIQUETTES — tout le contenu est DANS with tab_etiq
    # ══════════════════════════════════════════════════════════════════════════
    with tab_etiq:
        import io as _io

        st.markdown("### 🏷️ Étiquettes de prélèvement")

        _today_etiq = datetime.today().date()
        _RISK_COLORS_ETQ = {
            "1": "#22c55e", "2": "#84cc16",
            "3": "#f59e0b", "4": "#f97316", "5": "#ef4444",
        }

        all_prevs = [p for p in st.session_state.prelevements if not p.get("archived", False)]

        if not all_prevs:
            st.info("Aucun prélèvement enregistré. Créez-en d'abord dans **Nouveau prélèvement**.")
        else:
            with st.expander("🔍 Filtres", expanded=True):
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    dates_dispo = sorted(
                        {datetime.fromisoformat(p["date"]).date() for p in all_prevs if p.get("date")},
                        reverse=True)
                    sel_dates = st.multiselect(
                        "Date(s)", dates_dispo,
                        default=[dates_dispo[0]] if dates_dispo else [],
                        format_func=lambda d: d.strftime("%d/%m/%Y"),
                        key="etiq_dates")
                with fc2:
                    sel_points = st.multiselect(
                        "Point(s) de prélèvement",
                        sorted({p.get("label", "") for p in all_prevs if p.get("label")}),
                        key="etiq_points")
                with fc3:
                    sel_opers = st.multiselect(
                        "Opérateur(s)",
                        sorted({p.get("operateur", "") for p in all_prevs if p.get("operateur")}),
                        key="etiq_opers")

            filtered = all_prevs
            if sel_dates:
                filtered = [p for p in filtered if p.get("date") and datetime.fromisoformat(p["date"]).date() in sel_dates]
            if sel_points:
                filtered = [p for p in filtered if p.get("label") in sel_points]
            if sel_opers:
                filtered = [p for p in filtered if p.get("operateur") in sel_opers]

            n_sel = len(filtered)

            if n_sel == 0:
                st.warning("Aucun prélèvement ne correspond aux filtres.")
            else:
                st.markdown(
                    f"<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;"
                    f"padding:8px 16px;font-size:.9rem;color:#1e40af;font-weight:700;margin-bottom:8px'>"
                    f"🏷️ {n_sel} étiquette{'s' if n_sel > 1 else ''} à générer</div>",
                    unsafe_allow_html=True)

                st.markdown("#### 👁️ Prévisualisation")

                def _preview_card(p: dict) -> str:
                    risk   = str(p.get("risk_level", ""))
                    rcol   = _RISK_COLORS_ETQ.get(risk, "#6366f1")
                    label  = p.get("label", "—")
                    date_s = ""
                    if p.get("date"):
                        try:    date_s = datetime.fromisoformat(p["date"]).strftime("%d/%m/%Y")
                        except: date_s = str(p["date"])
                    classe_a_html = ""
                    if p.get("room_class") == "A":
                        iso = p.get("num_isolateur", "—") or "—"
                        pst = p.get("poste", "—") or "—"
                        classe_a_html = (
                            f"<div style='font-size:7pt;color:#854d0e;font-weight:700;"
                            f"background:#fef9c3;border-radius:3px;padding:2px 5px;"
                            f"margin-bottom:4px;white-space:nowrap;overflow:hidden;"
                            f"text-overflow:ellipsis'>"
                            f"🔬 ISO {iso} · {pst}</div>")
                    risk_band = (
                        f"<div style='position:absolute;top:0;right:0;bottom:0;width:7px;"
                        f"background:{rcol};border-radius:0 6px 6px 0'>"
                        f"<div style='writing-mode:vertical-rl;font-size:5.5pt;font-weight:900;"
                        f"color:#fff;padding:4px 0;text-align:center;height:100%'>"
                        f"{'Nv.' + risk if risk else ''}</div></div>")
                    return (
                        f"<div style='position:relative;width:6cm;height:4.5cm;"
                        f"border:1.5px solid {rcol};border-radius:8px;"
                        f"padding:8px 14px 6px 8px;box-sizing:border-box;"
                        f"background:#fff;font-family:Arial,Helvetica,sans-serif;"
                        f"display:flex;flex-direction:column;overflow:hidden;"
                        f"box-shadow:0 2px 8px rgba(0,0,0,.08)'>"
                        f"{risk_band}"
                        f"<div style='font-size:11pt;font-weight:900;color:#0f172a;"
                        f"border-bottom:1.5px solid {rcol}33;padding-bottom:4px;margin-bottom:4px;"
                        f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
                        f"max-width:calc(6cm - 24px)'>{label}</div>"
                        f"{classe_a_html}"
                        f"<div style='display:flex;align-items:center;gap:5px;margin-bottom:4px'>"
                        f"<span style='font-size:8pt;color:#64748b;font-weight:600;min-width:44px'>📅 Date</span>"
                        f"<span style='font-size:10pt;font-weight:800;color:#1e40af'>{date_s or '—'}</span></div>"
                        f"<div style='display:flex;align-items:center;gap:5px'>"
                        f"<span style='font-size:8pt;color:#64748b;font-weight:600'>👤 Préleveur :</span></div>"
                        f"<div style='margin-top:auto;font-size:6.5pt;color:#94a3b8;"
                        f"text-align:right;padding-top:4px'>URC — MicroSurveillance</div>"
                        f"</div>")

                preview_max = min(n_sel, 6)
                p_cols = st.columns(3)
                for idx, p in enumerate(filtered[:preview_max]):
                    with p_cols[idx % 3]:
                        st.markdown(_preview_card(p), unsafe_allow_html=True)
                        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
                if n_sel > preview_max:
                    st.caption(f"Prévisualisation limitée aux {preview_max} premières — toutes les {n_sel} figureront dans le PDF.")

                st.markdown("---")
                if st.button(
                    f"📄 Générer le PDF — {n_sel} étiquette{'s' if n_sel > 1 else ''}",
                    use_container_width=True, key="etiq_gen_pdf", type="primary"):
                    try:
                        from reportlab.lib.pagesizes import A4
                        from reportlab.lib.units     import cm as rl_cm
                        from reportlab.lib           import colors as rlc
                        from reportlab.platypus      import (SimpleDocTemplate, Table,
                                                              TableStyle, Paragraph, HRFlowable)
                        from reportlab.lib.styles    import ParagraphStyle
                        from reportlab.lib.enums     import TA_RIGHT

                        W_ETQ  = 6    * rl_cm
                        H_ETQ  = 4.5  * rl_cm
                        N_COLS = 3
                        GAP    = 0.4  * rl_cm
                        MARGIN = 0.8  * rl_cm

                        buf = _io.BytesIO()
                        doc = SimpleDocTemplate(
                            buf, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN,
                            title=f"Étiquettes {_today_etiq.strftime('%d/%m/%Y')}")

                        RISK_RL   = {k: rlc.HexColor(v) for k, v in _RISK_COLORS_ETQ.items()}
                        s_titre   = ParagraphStyle("etiq_titre",  fontName="Helvetica-Bold", fontSize=11, leading=14, spaceAfter=4)
                        s_lbl     = ParagraphStyle("etiq_lbl",    fontName="Helvetica",      fontSize=8,  leading=9,  textColor=rlc.HexColor("#64748b"))
                        s_val     = ParagraphStyle("etiq_val",    fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=rlc.HexColor("#0f172a"))
                        s_date    = ParagraphStyle("etiq_date",   fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=rlc.HexColor("#1e40af"))
                        s_logo    = ParagraphStyle("etiq_logo",   fontName="Helvetica",      fontSize=6.5,leading=8,  textColor=rlc.HexColor("#94a3b8"), alignment=TA_RIGHT)
                        s_classea = ParagraphStyle("etiq_classea",fontName="Helvetica-Bold", fontSize=7.5,leading=9,  textColor=rlc.HexColor("#854d0e"),  backColor=rlc.HexColor("#fef9c3"), spaceAfter=3)
                        s_phdr    = ParagraphStyle("page_hdr",    fontName="Helvetica-Bold", fontSize=9,  textColor=rlc.HexColor("#1e40af"), spaceAfter=6)

                        def _build_cell(pd):
                            rv = str(pd.get("risk_level", ""))
                            rc = RISK_RL.get(rv, rlc.HexColor("#6366f1"))
                            lv = pd.get("label", "—")
                            dv = ""
                            if pd.get("date"):
                                try:    dv = datetime.fromisoformat(pd["date"]).strftime("%d/%m/%Y")
                                except: dv = str(pd["date"])
                            classea_rows = []
                            if pd.get("room_class") == "A":
                                iso = pd.get("num_isolateur", "—") or "—"
                                pst = pd.get("poste", "—") or "—"
                                classea_rows = [[Paragraph(f"🔬 Isolateur {iso}  ·  {pst}", s_classea)]]
                            inner = Table([
                                [Paragraph(lv, s_titre)],
                                [HRFlowable(width=W_ETQ - 1.0*rl_cm, thickness=0.8, color=rc, spaceAfter=3)],
                                *classea_rows,
                                [Paragraph("📅 Date prélèvement", s_lbl)],
                                [Paragraph(dv or "—", s_date)],
                                [Paragraph("👤 Préleveur :", s_lbl)],
                                [Paragraph("", s_val)],
                                [Paragraph("URC — MicroSurveillance", s_logo)],
                            ], colWidths=[W_ETQ - 1.0*rl_cm])
                            inner.setStyle(TableStyle([
                                ("LEFTPADDING",   (0,0),(-1,-1), 0),
                                ("RIGHTPADDING",  (0,0),(-1,-1), 0),
                                ("TOPPADDING",    (0,0),(-1,-1), 0),
                                ("BOTTOMPADDING", (0,0),(-1,-1), 2),
                                ("TOPPADDING",    (0,-1),(0,-1), 6),
                            ]))
                            outer = Table([[inner]], colWidths=[W_ETQ], rowHeights=[H_ETQ])
                            outer.setStyle(TableStyle([
                                ("BOX",            (0,0),(0,0), 1.5, rc),
                                ("ROUNDEDCORNERS", (0,0),(0,0), [6]),
                                ("LINEAFTER",      (0,0),(0,0), 7,  rc),
                                ("LEFTPADDING",    (0,0),(0,0), 7),
                                ("RIGHTPADDING",   (0,0),(0,0), 14),
                                ("TOPPADDING",     (0,0),(0,0), 7),
                                ("BOTTOMPADDING",  (0,0),(0,0), 5),
                                ("VALIGN",         (0,0),(0,0), "TOP"),
                                ("BACKGROUND",     (0,0),(0,0), rlc.white),
                            ]))
                            return outer

                        rows, row_buf = [], []
                        for p_item in filtered:
                            row_buf.append(_build_cell(p_item))
                            if len(row_buf) == N_COLS:
                                rows.append(row_buf); row_buf = []
                        if row_buf:
                            while len(row_buf) < N_COLS: row_buf.append("")
                            rows.append(row_buf)

                        main_tbl = Table(rows, colWidths=[W_ETQ]*N_COLS, rowHeights=[H_ETQ]*len(rows))
                        main_tbl.setStyle(TableStyle([
                            ("LEFTPADDING",   (0,0),(-1,-1), GAP/2),
                            ("RIGHTPADDING",  (0,0),(-1,-1), GAP/2),
                            ("TOPPADDING",    (0,0),(-1,-1), GAP/2),
                            ("BOTTOMPADDING", (0,0),(-1,-1), GAP/2),
                            ("VALIGN",        (0,0),(-1,-1), "TOP"),
                        ]))

                        doc.build([
                            Paragraph(
                                f"Étiquettes prélèvements — Imprimé le {_today_etiq.strftime('%d/%m/%Y')} — "
                                f"{n_sel} étiquette{'s' if n_sel > 1 else ''}",
                                s_phdr),
                            main_tbl
                        ])
                        buf.seek(0)

                        fname = f"etiquettes_{_today_etiq.strftime('%Y%m%d')}.pdf"
                        st.download_button(
                            label=f"⬇️ Télécharger {fname}",
                            data=buf.getvalue(), file_name=fname,
                            mime="application/pdf",
                            use_container_width=True, key="etiq_dl_btn")
                        st.markdown(
                            f"<div style='background:#f0fdf4;border:1px solid #86efac;border-radius:8px;"
                            f"padding:10px 14px;margin-top:6px'>"
                            f"<div style='font-size:.88rem;font-weight:800;color:#166534'>✅ PDF généré avec succès</div>"
                            f"<div style='font-size:.78rem;color:#475569;margin-top:3px'>"
                            f"{n_sel} étiquette{'s' if n_sel > 1 else ''} · {N_COLS} colonnes · Format A4 · 6×4.5 cm</div></div>",
                            unsafe_allow_html=True)

                    except ImportError:
                        st.error("❌ **ReportLab** non installé.\n\nAjoutez `reportlab` dans **requirements.txt**.")
                    except Exception as _e:
                        st.error(f"Erreur génération PDF : {_e}")
                        import traceback; st.code(traceback.format_exc())
                        
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 : PLANNING
# ═══════════════════════════════════════════════════════════════════════════════
if active == "planning":
    st.markdown("### 📅 Planning des prélèvements & lectures")

    _today_dt      = datetime.today().date()
    MOIS_FR        = ["","Janvier","Février","Mars","Avril","Mai","Juin",
                      "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    JOURS_FR_COURT = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]
    JOURS_FR_LONG  = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]

    # ═════════════════════════════════════════════════════════════════════════
    # PERSISTANCE
    # ═════════════════════════════════════════════════════════════════════════
    def _load_planning_overrides():
        for k, v in st.session_state.get("planning_overrides", {}).items():
            if k not in st.session_state:
                try:
                    st.session_state[k] = int(v)
                except Exception:
                    pass

    def _persist_overrides():
        overrides = {
            k: int(v)
            for k, v in st.session_state.items()
            if isinstance(k, str) and k.startswith("ch_prevu_")
        }
        st.session_state["planning_overrides"] = overrides
        _supa_upsert('planning_overrides', json.dumps(overrides, ensure_ascii=False))

    if "planning_overrides_loaded" not in st.session_state:
        _load_planning_overrides()
        st.session_state["planning_overrides_loaded"] = True

    # ═════════════════════════════════════════════════════════════════════════
    # HELPERS FRÉQUENCE
    # ═════════════════════════════════════════════════════════════════════════
    def _frc_default(rc):
        rc = (rc or '').strip().upper()
        if 'A' in rc: return 20
        if 'D' in rc: return 10
        return 2

    def _semaines_du_mois(year, month):
        import calendar as _c
        _, n_days = _c.monthrange(year, month)
        first = date_type(year, month, 1)
        last  = date_type(year, month, n_days)
        mondays = []
        cur = first - timedelta(days=first.weekday())
        while cur <= last:
            mondays.append(cur)
            cur += timedelta(weeks=1)
        return mondays

    def _doit_prelever_cette_semaine_mensuel(freq_mois, week_monday):
        """
        Pour freq_mois prélèvements/mois, détermine si cette semaine
        est une semaine active. Répartit sur les premières semaines du mois.
        Retourne (actif: bool, nb: int).
        """
        # Identifier le mois de la semaine (vendredi comme référence)
        vendredi = week_monday + timedelta(days=4)
        month = vendredi.month
        year  = vendredi.year

        semaines = _semaines_du_mois(year, month)
        nb_sem   = len(semaines)
        try:
            idx = semaines.index(week_monday)
        except ValueError:
            return False, 0

        freq_mois = max(1, min(int(freq_mois), nb_sem))
        if freq_mois >= nb_sem:
            return True, 1
        step = nb_sem / freq_mois
        semaines_actives = {int(i * step) for i in range(freq_mois)}
        if idx in semaines_actives:
            return True, 1
        return False, 0

    def _get_prevu_semaine(pt, week_monday, nb_wd, class_override=None):
        """
        Retourne (nb_prevu_cette_semaine, freq_label_display, sess_key).
        Priorité :
          1. Override manuel (ch_prevu_<id>_<lundi ISO>)
          2. Override de classe (class_override)
          3. Fréquence propre au point
          4. Fallback par classe
        """
        pt_id     = pt.get('id', '')
        rc        = (pt.get('room_class') or '').strip()
        sess_key  = f"ch_prevu_{pt_id}_{week_monday.isoformat()}"
        freq_raw  = pt.get('frequency')
        freq_unit = pt.get('frequency_unit', '/ semaine')

        # Calcul valeur par défaut
        if class_override is not None:
            default_nb  = int(class_override)
            freq_label  = f"{default_nb} / sem. (classe)"
        elif freq_raw is not None:
            try:
                freq_int = int(freq_raw)
            except (ValueError, TypeError):
                freq_int = 0
            if freq_int > 0:
                if freq_unit == '/ jour':
                    default_nb = freq_int * nb_wd
                    freq_label = f"{freq_int}/j → {default_nb}/sem."
                elif freq_unit == '/ semaine':
                    default_nb = freq_int
                    freq_label = f"{freq_int} / semaine"
                elif freq_unit == '/ mois':
                    actif, nb  = _doit_prelever_cette_semaine_mensuel(freq_int, week_monday)
                    default_nb = nb if actif else 0
                    freq_label = f"{freq_int} / mois"
                else:
                    default_nb = freq_int
                    freq_label = f"{freq_int} {freq_unit}"
            else:
                default_nb = _frc_default(rc)
                freq_label = f"{default_nb}/sem. (défaut)"
        else:
            default_nb = _frc_default(rc)
            freq_label = f"{default_nb}/sem. (défaut)"

        if sess_key not in st.session_state:
            st.session_state[sess_key] = default_nb

        return int(st.session_state[sess_key]), freq_label, sess_key

    # ═════════════════════════════════════════════════════════════════════════
    # ONGLETS
    # ═════════════════════════════════════════════════════════════════════════
    plan_tab_view, plan_tab_charge, plan_tab_export = st.tabs([
        "📅 Calendrier", "📊 Charge hebdo", "📥 Export Excel"
    ])

# ═════════════════════════════════════════════════════════════════════════
    # ONGLET CALENDRIER
    # ═════════════════════════════════════════════════════════════════════════
    with plan_tab_view:

        # ── Navigation mois ───────────────────────────────────────────────────
        nav_c1, nav_c2, nav_c3, nav_c4, nav_c5 = st.columns([1, 1, 3, 1, 1])
        with nav_c1:
            if st.button("◀◀", use_container_width=True, key="cal_prev_year"):
                st.session_state.cal_year -= 1; st.rerun()
        with nav_c2:
            if st.button("◀", use_container_width=True, key="cal_prev_month"):
                if st.session_state.cal_month == 1:
                    st.session_state.cal_month = 12; st.session_state.cal_year -= 1
                else:
                    st.session_state.cal_month -= 1
                st.rerun()
        with nav_c3:
            st.markdown(
                f"<div style='text-align:center;background:linear-gradient(135deg,#1e40af,#2563eb);"
                f"border-radius:10px;padding:10px;color:#fff;font-weight:800;font-size:1.1rem'>"
                f"📅 {MOIS_FR[st.session_state.cal_month]} {st.session_state.cal_year}</div>",
                unsafe_allow_html=True)
        with nav_c4:
            if st.button("▶", use_container_width=True, key="cal_next_month"):
                if st.session_state.cal_month == 12:
                    st.session_state.cal_month = 1; st.session_state.cal_year += 1
                else:
                    st.session_state.cal_month += 1
                st.rerun()
        with nav_c5:
            if st.button("▶▶", use_container_width=True, key="cal_next_year"):
                st.session_state.cal_year += 1; st.rerun()

        if st.button("📍 Aujourd'hui", key="cal_today"):
            st.session_state.cal_year  = _today_dt.year
            st.session_state.cal_month = _today_dt.month
            st.rerun()

        cal_year  = st.session_state.cal_year
        cal_month = st.session_state.cal_month
        holidays_this_month = get_holidays_cached(cal_year)

        import calendar as _cal3
        _, n_days_m = _cal3.monthrange(cal_year, cal_month)
        cal_weeks   = _cal3.monthcalendar(cal_year, cal_month)

       # ── Snapshot session_state pour le rendu ──────────────────────────────
        _prevs       = [p for p in st.session_state.prelevements if not p.get("archived", False)]
        _active_sids = {p['id'] for p in _prevs}  # IDs des prélèvements actifs uniquement

        def _get_day_cal(d):
            # On filtre strictement : seuls les schedules dont le sample existe encore et n'est pas archivé
            j0r = [p for p in _prevs
                   if p.get('date') and datetime.fromisoformat(p['date']).date() == d]
            j2r = [s for s in st.session_state.schedules
                   if s['when'] == 'J2'
                   and s.get('sample_id') in _active_sids
                   and datetime.fromisoformat(s['due_date']).date() == d]
            j7r = [s for s in st.session_state.schedules
                   if s['when'] == 'J7'
                   and s.get('sample_id') in _active_sids
                   and datetime.fromisoformat(s['due_date']).date() == d]
            return j0r, j2r, j7r

        # ── Légende ───────────────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;gap:12px;margin:12px 0;flex-wrap:wrap;
                    background:#f8fafc;border-radius:10px;padding:10px 14px;
                    border:1px solid #e2e8f0">
          <div style="display:flex;align-items:center;gap:5px">
            <div style="width:12px;height:12px;border-radius:3px;background:#7c3aed"></div>
            <span style="font-size:.72rem;color:#1e293b;font-weight:600">Prélèv. réel (J0)</span>
          </div>
          <div style="display:flex;align-items:center;gap:5px">
            <div style="width:12px;height:12px;border-radius:3px;background:#d97706"></div>
            <span style="font-size:.72rem;color:#1e293b;font-weight:600">Lecture J2 à faire</span>
          </div>
          <div style="display:flex;align-items:center;gap:5px">
            <div style="width:12px;height:12px;border-radius:3px;background:#0369a1"></div>
            <span style="font-size:.72rem;color:#1e293b;font-weight:600">Lecture J7 à faire</span>
          </div>
          <div style="display:flex;align-items:center;gap:5px">
            <div style="width:12px;height:12px;border-radius:3px;background:#ef4444"></div>
            <span style="font-size:.72rem;color:#1e293b;font-weight:600">En retard</span>
          </div>
          <div style="display:flex;align-items:center;gap:5px">
            <div style="width:12px;height:12px;border-radius:3px;background:#22c55e"></div>
            <span style="font-size:.72rem;color:#1e293b;font-weight:600">Faite ✅</span>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── En-tête colonnes jours ────────────────────────────────────────────
        hdr = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:4px">'
        for i, jour in enumerate(JOURS_FR_COURT):
            cc = "#ef4444" if i >= 5 else "#1e40af"
            hdr += (f'<div style="text-align:center;padding:8px 4px;font-weight:800;'
                    f'font-size:.78rem;color:{cc};border-radius:6px;background:#eff6ff">{jour}</div>')
        hdr += '</div>'

        # ── Grille des jours ─────────────────────────────────────────────────
        day_has_content = {}
        grid = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px">'

        for week in cal_weeks:
            for day_idx, day_num in enumerate(week):
                is_weekend = day_idx >= 5
                if day_num == 0:
                    grid += '<div style="background:#f8fafc;border-radius:8px;min-height:95px"></div>'
                    continue

                d = date_type(cal_year, cal_month, day_num)
                is_today       = d == _today_dt
                is_holiday     = d in holidays_this_month
                is_non_working = is_weekend or is_holiday
                is_past        = d < _today_dt
                j0r, j2r, j7r  = _get_day_cal(d)

                # Couleurs de fond
                if is_today:
                    bg  = "#dbeafe"
                    bdr = "2px solid #2563eb"
                elif is_non_working:
                    bg  = "#f1f5f9"
                    bdr = "1px solid #e2e8f0"
                else:
                    bg  = "#ffffff"
                    bdr = "1px solid #e2e8f0"

                dnc = "#2563eb" if is_today else ("#94a3b8" if is_non_working else "#0f172a")
                op  = "0.6" if is_past and not is_today and not j0r and not j2r and not j7r else "1"

                badges = ""

                # J0 — prélèvements réels
                if j0r:
                    badges += (
                        f'<div style="background:#7c3aed;color:#fff;border-radius:4px;'
                        f'padding:2px 6px;font-size:.6rem;font-weight:700;margin-top:3px;'
                        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                        f'🧪 {len(j0r)} J0</div>')

                # J2 — lectures
                for s in j2r:
                    done = s['status'] == 'done'
                    late = not done and d <= _today_dt
                    sc   = "#22c55e" if done else ("#ef4444" if late else "#d97706")
                    si   = "✅" if done else ("🔔" if late else "📖")
                    lbl  = "✅ J2 faite" if done else ("⚠️ J2 retard" if late else "📖 J2")
                    badges += (
                        f'<div style="background:{sc};color:#fff;border-radius:4px;'
                        f'padding:2px 6px;font-size:.6rem;font-weight:700;margin-top:3px;'
                        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                        f'{lbl}</div>')

                # J7 — lectures
                for s in j7r:
                    done = s['status'] == 'done'
                    late = not done and d <= _today_dt
                    sc   = "#22c55e" if done else ("#ef4444" if late else "#0369a1")
                    lbl  = "✅ J7 faite" if done else ("⚠️ J7 retard" if late else "📗 J7")
                    badges += (
                        f'<div style="background:{sc};color:#fff;border-radius:4px;'
                        f'padding:2px 6px;font-size:.6rem;font-weight:700;margin-top:3px;'
                        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                        f'{lbl}</div>')

                # Label week-end / férié
                hlbl = ""
                if is_holiday and not is_weekend:
                    hlbl = '<div style="font-size:.5rem;color:#ef4444;font-weight:600;margin-top:2px">🔴 Férié</div>'
                elif is_weekend:
                    hlbl = '<div style="font-size:.5rem;color:#94a3b8;margin-top:2px">Repos</div>'

                day_has_content[d] = {"j0r": j0r, "j2r": j2r, "j7r": j7r}

                grid += (
                    f'<div style="background:{bg};border:{bdr};border-radius:8px;padding:6px 5px;'
                    f'min-height:95px;opacity:{op};display:flex;flex-direction:column">'
                    f'<div style="font-weight:800;font-size:.88rem;color:{dnc}">{day_num}</div>'
                    f'{hlbl}{badges}</div>')

        grid += '</div>'
        st.markdown(hdr + grid, unsafe_allow_html=True)

        # ── Stats du mois ─────────────────────────────────────────────────────
        total_j0  = sum(len(v["j0r"]) for v in day_has_content.values())
        total_j2  = sum(len(v["j2r"]) for v in day_has_content.values())
        total_j7  = sum(len(v["j7r"]) for v in day_has_content.values())
        done_j2   = sum(1 for v in day_has_content.values() for s in v["j2r"] if s["status"] == "done")
        done_j7   = sum(1 for v in day_has_content.values() for s in v["j7r"] if s["status"] == "done")
        late_all  = sum(
            1 for v in day_has_content.values()
            for s in v["j2r"] + v["j7r"]
            if s["status"] != "done" and datetime.fromisoformat(s["due_date"]).date() <= _today_dt
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("🧪 Prélèv. J0", total_j0)
        mc2.metric("📖 Lectures J2", total_j2, f"✅ {done_j2} faites")
        mc3.metric("📗 Lectures J7", total_j7, f"✅ {done_j7} faites")
        mc4.metric("✅ Taux J2", f"{int(done_j2/total_j2*100)}%" if total_j2 else "—")
        mc5.metric("🔔 En retard", late_all, delta_color="inverse")


# ═════════════════════════════════════════════════════════════════════════
    # ONGLET CHARGE HEBDO
    # ═════════════════════════════════════════════════════════════════════════
    def get_week_start(d):
        return d - timedelta(days=d.weekday())

    def fmt_week(ws):
        we = ws + timedelta(days=6)
        return ws.strftime('%d/%m') + ' – ' + we.strftime('%d/%m/%Y')

    with plan_tab_charge:
        st.markdown("### 📊 Charge hebdomadaire")

        ch_ws_set = set()
        ch_ws_set.add(get_week_start(_today_dt))
        for _p in st.session_state.prelevements:
            try:
                ch_ws_set.add(get_week_start(datetime.fromisoformat(_p["date"]).date()))
            except:
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

        csel_col1, csel_col2 = st.columns([4, 1])
        with csel_col1:
            ch_sel_label = st.selectbox(
                "Semaine", ch_week_labels, index=ch_cur_idx,
                label_visibility="collapsed", key="ch_week_sel")
        with csel_col2:
            nb_preleveurs = st.number_input(
                "Nb préleveurs", min_value=1, max_value=20,
                value=max(1, len(st.session_state.operators)), step=1,
                key="ch_nb_prev")

        ch_sel_ws       = ch_week_starts[ch_week_labels.index(ch_sel_label)]
        ch_sel_we       = ch_sel_ws + timedelta(days=6)
        ch_holidays     = get_holidays_cached(ch_sel_ws.year)
        ch_working_days = [ch_sel_ws + timedelta(days=i) for i in range(5)
                           if (ch_sel_ws + timedelta(days=i)) not in ch_holidays]
        nb_jours        = len(ch_working_days)

        ch_j0 = [p for p in st.session_state.prelevements
                 if p.get('date')
                 and ch_sel_ws <= datetime.fromisoformat(p['date']).date() <= ch_sel_we
                 and not p.get('archived', False)]
        ch_j2 = [s for s in st.session_state.schedules
                 if s['when'] == 'J2'
                 and ch_sel_ws <= datetime.fromisoformat(s['due_date']).date() <= ch_sel_we]
        ch_j7 = [s for s in st.session_state.schedules
                 if s['when'] == 'J7'
                 and ch_sel_ws <= datetime.fromisoformat(s['due_date']).date() <= ch_sel_we]

        total_actes    = len(ch_j0) + len(ch_j2) + len(ch_j7)
        actes_par_jour = total_actes / nb_jours      if nb_jours      > 0 else 0
        actes_par_prev = total_actes / nb_preleveurs if nb_preleveurs > 0 else 0

        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#1e40af,#2563eb);border-radius:14px;
            padding:16px 22px;margin:10px 0 18px 0;display:flex;align-items:center;
            justify-content:space-between;flex-wrap:wrap;gap:10px">
            <div style="color:#fff">
              <div style="font-size:1.05rem;font-weight:800">📅 {ch_sel_label}</div>
              <div style="font-size:.82rem;color:#bfdbfe;margin-top:3px">
                {nb_jours} jour(s) ouvré(s) · {nb_preleveurs} préleveur(s)</div>
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
              <div style="background:rgba(255,255,255,.15);border-radius:10px;padding:10px 18px;text-align:center">
                <div style="font-size:.72rem;color:#bfdbfe;font-weight:700;text-transform:uppercase">/ préleveur</div>
                <div style="font-size:2rem;font-weight:900;color:#fff">{actes_par_prev:.1f}</div>
              </div>
            </div></div>""",
            unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("👤 Préleveurs",    nb_preleveurs)
        m2.metric("📍 Points actifs", len(st.session_state.points))
        m3.metric("🧪 Prélèv. J0",   len(ch_j0))
        m4.metric("📖 Lectures J2",   len(ch_j2))
        m5.metric("📗 Lectures J7",   len(ch_j7))

        st.divider()

        # ══════════════════════════════════════════════════════════════════
        # TABLEAU DÉDIÉ : FRÉQUENCES PAR CLASSE
        # ══════════════════════════════════════════════════════════════════
        st.markdown("#### 🏷️ Fréquences par classe de salle")
        st.caption(
            "L'**override** définit le **total de prélèvements par semaine pour toute la classe**. "
            "Les points sont répartis proportionnellement à leur fréquence individuelle (utilisée comme poids). "
            "Laissez **0** pour utiliser la fréquence propre à chaque point sans contrainte de classe.")

        all_classes = sorted({
            (pt.get('room_class') or '').strip()
            for pt in st.session_state.points
            if (pt.get('room_class') or '').strip()
        })

        class_override_key = f"class_override_{ch_sel_ws.isoformat()}"
        if class_override_key not in st.session_state:
            st.session_state[class_override_key] = {}

        if not all_classes:
            st.info("Aucune classe de salle définie sur les points de prélèvement.")
        else:
            hdr_cl = st.columns([1, 1, 2, 1, 3])
            for _hc, _hl in zip(hdr_cl,
                                 ["Classe", "Points", "Fréq. individuelle (poids)",
                                  "Total /sem ✏️", "Répartition proportionnelle"]):
                _hc.markdown(
                    f"<div style='background:#1e40af;border-radius:6px;padding:7px 10px;"
                    f"font-size:.7rem;font-weight:800;color:#fff;text-align:center'>{_hl}</div>",
                    unsafe_allow_html=True)

            for rc in all_classes:
                pts_rc  = [pt for pt in st.session_state.points
                           if (pt.get('room_class') or '').strip() == rc]
                nb_pts  = len(pts_rc)
                rc_color = {"A": "#22c55e", "B": "#84cc16", "C": "#f59e0b", "D": "#f97316"}.get(
                    rc.replace(' ', '').upper()[:1], "#6366f1")

                # Calcul poids (fréquence individuelle normalisée en /semaine)
                pt_freqs = []
                for pt in pts_rc:
                    try:
                        f = int(pt.get('frequency') or 1)
                        u = pt.get('frequency_unit', '/ semaine')
                        if '/ mois' in u:
                            f_week = round(f / 4.33)
                        elif '/ jour' in u:
                            f_week = f * nb_jours
                        else:
                            f_week = f
                        pt_freqs.append(max(1, f_week))
                    except Exception:
                        pt_freqs.append(1)
                total_poids = sum(pt_freqs) or 1

                cur_override = int(st.session_state[class_override_key].get(rc, 0))

                rc_cols = st.columns([1, 1, 2, 1, 3])
                with rc_cols[0]:
                    st.markdown(
                        f"<div style='background:{rc_color}22;border:1.5px solid {rc_color}55;"
                        f"border-radius:8px;padding:10px;text-align:center;font-weight:800;"
                        f"font-size:.95rem;color:{rc_color}'>{rc}</div>",
                        unsafe_allow_html=True)
                with rc_cols[1]:
                    st.markdown(
                        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:10px;text-align:center;font-size:.85rem;color:#475569'>"
                        f"<b>{nb_pts}</b></div>",
                        unsafe_allow_html=True)
                with rc_cols[2]:
                    freq_lines = "".join(
                        f"<div style='font-size:.68rem;color:#475569'>• {pt['label']} : {f}×/sem</div>"
                        for pt, f in zip(pts_rc, pt_freqs)
                    )
                    st.markdown(
                        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:8px 10px'>{freq_lines}</div>",
                        unsafe_allow_html=True)
                with rc_cols[3]:
                    new_val = st.number_input(
                        f"Override {rc}", min_value=0, max_value=500,
                        value=cur_override, step=1,
                        label_visibility="collapsed",
                        key=f"class_ov_{rc}_{ch_sel_ws.isoformat()}",
                        help="0 = fréquence individuelle · sinon = total hebdo pour toute la classe")
                    st.session_state[class_override_key][rc] = new_val
                with rc_cols[4]:
                    if new_val > 0:
                        alloc_lines   = []
                        total_assigned = 0
                        for i, (pt, poids) in enumerate(zip(pts_rc, pt_freqs)):
                            if i < len(pts_rc) - 1:
                                alloc = round(poids / total_poids * new_val)
                            else:
                                alloc = new_val - total_assigned
                            total_assigned += alloc
                            alloc_lines.append(
                                f"<div style='font-size:.68rem;color:#1e40af;font-weight:600'>"
                                f"• {pt['label']} : <b>{alloc}×/sem</b></div>")
                        st.markdown(
                            f"<div style='background:#eff6ff;border:1px solid #93c5fd;"
                            f"border-radius:6px;padding:8px 10px'>{''.join(alloc_lines)}</div>",
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                            f"border-radius:6px;padding:10px;text-align:center;"
                            f"font-size:.78rem;color:#94a3b8;font-style:italic'>"
                            f"Fréquences individuelles</div>",
                            unsafe_allow_html=True)

        st.divider()

        # ══════════════════════════════════════════════════════════════════
        # PLANNING HEBDO : DISPATCH PAR JOUR
        # ══════════════════════════════════════════════════════════════════
        st.markdown("#### 🗓️ Planning de prélèvements — dispatch journalier")

        def _get_weekly_alloc(points, class_overrides, working_days):
            """Retourne {pt_label: nb_fois_par_semaine} en respectant les overrides de classe."""
            from collections import Counter as _CtrA
            alloc   = {}
            nb_j    = len(working_days)

            classes_in_points = sorted({
                (pt.get('room_class') or '').strip()
                for pt in points
                if (pt.get('room_class') or '').strip()
            })

            for rc in classes_in_points:
                pts_rc   = [pt for pt in points if (pt.get('room_class') or '').strip() == rc]
                override = int(class_overrides.get(rc, 0))

                pt_freqs_rc = []
                for pt in pts_rc:
                    try:
                        f = int(pt.get('frequency') or 1)
                        u = pt.get('frequency_unit', '/ semaine')
                        if '/ mois' in u:
                            f_week = round(f / 4.33)
                        elif '/ jour' in u:
                            f_week = f * nb_j
                        else:
                            f_week = f
                        pt_freqs_rc.append(max(1, f_week))
                    except Exception:
                        pt_freqs_rc.append(1)

                total_poids = sum(pt_freqs_rc) or 1

                if override > 0:
                    total_assigned = 0
                    for i, (pt, poids) in enumerate(zip(pts_rc, pt_freqs_rc)):
                        if i < len(pts_rc) - 1:
                            a = round(poids / total_poids * override)
                        else:
                            a = override - total_assigned
                        total_assigned += a
                        alloc[pt['label']] = max(0, a)
                else:
                    for pt, f in zip(pts_rc, pt_freqs_rc):
                        alloc[pt['label']] = f

            return alloc

        def _dispatch_to_days(alloc, working_days):
            """Répartit les prélèvements sur les jours ouvrés.
            Règle : pas deux fois le même point le même jour sauf si fréquence > nb_jours."""
            from collections import defaultdict
            nb_j     = len(working_days)
            schedule = defaultdict(list)

            for label, weekly in alloc.items():
                if weekly <= 0 or nb_j == 0:
                    continue
                if weekly <= nb_j:
                    step   = nb_j / weekly
                    chosen = [int(i * step) for i in range(weekly)]
                    chosen = list(dict.fromkeys(min(c, nb_j - 1) for c in chosen))
                    if len(chosen) < weekly:
                        remaining = [i for i in range(nb_j) if i not in chosen]
                        chosen   += remaining[:weekly - len(chosen)]
                    for idx in chosen[:weekly]:
                        schedule[working_days[idx]].append(label)
                else:
                    per_day = weekly // nb_j
                    extra   = weekly % nb_j
                    for i, d in enumerate(working_days):
                        count = per_day + (1 if i < extra else 0)
                        for _ in range(count):
                            schedule[d].append(label)

            return schedule

        cur_overrides = st.session_state.get(class_override_key, {})
        weekly_alloc  = _get_weekly_alloc(st.session_state.points, cur_overrides, ch_working_days)
        daily_sched   = _dispatch_to_days(weekly_alloc, ch_working_days)

        if not st.session_state.points:
            st.info("Aucun point de prélèvement défini.")
        elif not ch_working_days:
            st.warning("Aucun jour ouvré cette semaine.")
        else:
            day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
            rc_colors = {"A": "#22c55e", "B": "#84cc16", "C": "#f59e0b", "D": "#f97316"}

            # En-têtes jours
            day_cols = st.columns(nb_jours)
            for i, (col, wd) in enumerate(zip(day_cols, ch_working_days)):
                nb_actes = len(daily_sched[wd])
                is_today = (wd == _today_dt)
                bg_hd    = "#2563eb" if is_today else "#1e40af"
                col.markdown(
                    f"<div style='background:{bg_hd};border-radius:8px;padding:8px;text-align:center'>"
                    f"<div style='color:#bfdbfe;font-size:.62rem;font-weight:700;text-transform:uppercase'>"
                    f"{day_names[wd.weekday()]}</div>"
                    f"<div style='color:#fff;font-size:.75rem;font-weight:600'>{wd.strftime('%d/%m')}</div>"
                    f"<div style='background:rgba(255,255,255,.25);border-radius:6px;margin-top:4px;"
                    f"padding:2px;color:#fff;font-size:.8rem;font-weight:800'>{nb_actes} acte(s)</div>"
                    f"</div>",
                    unsafe_allow_html=True)

            # Cartes par jour
            day_cols2 = st.columns(nb_jours)
            for i, (col, wd) in enumerate(zip(day_cols2, ch_working_days)):
                labels_today = daily_sched[wd]
                if not labels_today:
                    col.markdown(
                        "<div style='background:#f8fafc;border:1px dashed #e2e8f0;"
                        "border-radius:8px;padding:12px;text-align:center;"
                        "font-size:.7rem;color:#94a3b8;margin-top:4px'>—</div>",
                        unsafe_allow_html=True)
                else:
                    from collections import Counter as _Ctr2
                    cnt   = _Ctr2(labels_today)
                    cards = ""
                    for lbl, n in cnt.items():
                        pt_obj = next((p for p in st.session_state.points if p['label'] == lbl), None)
                        rc_pt  = (pt_obj.get('room_class') or '') if pt_obj else ''
                        bg_c   = rc_colors.get(rc_pt.replace(' ', '').upper()[:1], "#6366f1")
                        repeat = (
                            f" <span style='background:{bg_c};color:#fff;border-radius:4px;"
                            f"padding:0 4px;font-size:.55rem'>×{n}</span>"
                            if n > 1 else "")
                        cards += (
                            f"<div style='background:{bg_c}18;border:1px solid {bg_c}55;"
                            f"border-radius:6px;padding:5px 7px;margin-top:4px;"
                            f"font-size:.68rem;color:#0f172a;font-weight:600;line-height:1.3'>"
                            f"{lbl}{repeat}"
                            f"<div style='font-size:.58rem;color:{bg_c};font-weight:700'>"
                            f"Classe {rc_pt}</div></div>")
                    col.markdown(cards, unsafe_allow_html=True)

            # Résumé total
            total_dispatch = sum(len(v) for v in daily_sched.values())
            st.markdown(
                f"<div style='background:#f0fdf4;border:1px solid #86efac;border-radius:8px;"
                f"padding:10px 16px;margin-top:12px;font-size:.8rem;color:#166534;font-weight:600'>"
                f"✅ Total planifié cette semaine : <b>{total_dispatch} prélèvement(s)</b> "
                f"répartis sur {nb_jours} jour(s) ouvré(s)</div>",
                unsafe_allow_html=True)

        st.divider()

        # ══════════════════════════════════════════════════════════════════
        # TABLEAU DÉTAIL PAR POINT
        # ══════════════════════════════════════════════════════════════════
        st.markdown("#### 📍 Détail par point de prélèvement")
        risk_colors_ch = {"1":"#22c55e","2":"#84cc16","3":"#f59e0b","4":"#f97316","5":"#ef4444"}

        if not st.session_state.points:
            st.info("Aucun point défini. Créez-en dans **Paramètres → Points de prélèvement**.")
        else:
            hdr_cols = st.columns([2.2, 0.7, 0.8, 0.6, 1.5, 1.3, 0.8, 1.4])
            for _hc, _hl in zip(hdr_cols,
                                  ["Point","Type","Classe","Risque",
                                   "Fréquence du point","Prévu cette sem. ✏️","Réalisé","Statut"]):
                _hc.markdown(
                    f"<div style='background:#1e40af;border-radius:6px;padding:7px 8px;"
                    f"font-size:.68rem;font-weight:800;color:#fff;text-align:center'>{_hl}</div>",
                    unsafe_allow_html=True)

            total_prevu = 0; total_realise = 0

            for pt_i, pt in enumerate(st.session_state.points):
                rc        = (pt.get('room_class') or '').strip()
                row_bg    = "#f8fafc" if pt_i % 2 == 0 else "#ffffff"
                risk_val  = str(pt.get('risk_level', '—'))
                risk_col  = risk_colors_ch.get(risk_val, "#94a3b8")
                type_icon = "💨" if pt.get('type') == 'Air' else "🧴"

                class_ov_dict  = st.session_state.get(class_override_key, {})
                co_val         = class_ov_dict.get(rc, 0)
                class_override = int(co_val) if co_val and int(co_val) > 0 else None

                nb_prevu, freq_label, sess_key = _get_prevu_semaine(
                    pt, ch_sel_ws, nb_jours, class_override)

                realise = sum(1 for p in ch_j0 if p.get('label') == pt['label'])

                if nb_prevu == 0:
                    st_bg="#f8fafc"; st_border="#e2e8f0"; st_txt="#94a3b8"
                    st_icon="⏸️"; st_label="Non planifié"
                elif realise >= nb_prevu:
                    st_bg="#f0fdf4"; st_border="#86efac"; st_txt="#166534"
                    st_icon="✅"; st_label="Complet"
                elif realise > 0:
                    pct = int(realise / nb_prevu * 100)
                    st_bg="#fffbeb"; st_border="#fcd34d"; st_txt="#92400e"
                    st_icon="⏳"; st_label=f"{pct}%"
                else:
                    st_bg="#fef2f2"; st_border="#fca5a5"; st_txt="#991b1b"
                    st_icon="🔴"; st_label=f"0/{nb_prevu}"

                total_prevu   += nb_prevu
                total_realise += realise

                row_cols = st.columns([2.2, 0.7, 0.8, 0.6, 1.5, 1.3, 0.8, 1.4])
                with row_cols[0]:
                    st.markdown(
                        f"<div style='background:{row_bg};border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:8px 12px;font-size:.85rem;font-weight:700;color:#0f172a'>"
                        f"{type_icon} {pt['label']}</div>", unsafe_allow_html=True)
                with row_cols[1]:
                    st.markdown(
                        f"<div style='background:{row_bg};border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:8px;font-size:.78rem;color:#475569;text-align:center'>"
                        f"{pt.get('type','—')}</div>", unsafe_allow_html=True)
                with row_cols[2]:
                    st.markdown(
                        f"<div style='background:{row_bg};border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:8px;font-size:.78rem;color:#475569;text-align:center'>"
                        f"{rc or '—'}</div>", unsafe_allow_html=True)
                with row_cols[3]:
                    st.markdown(
                        f"<div style='background:{row_bg};border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:8px;text-align:center'>"
                        f"<span style='background:{risk_col}22;color:{risk_col};"
                        f"border:1px solid {risk_col}55;border-radius:6px;"
                        f"padding:2px 4px;font-size:.68rem;font-weight:700'>Nv.{risk_val}</span></div>",
                        unsafe_allow_html=True)
                with row_cols[4]:
                    badge = ""
                    if class_override is not None:
                        badge = (" <span style='background:#dbeafe;color:#1e40af;"
                                 "border-radius:4px;padding:1px 4px;font-size:.58rem'>"
                                 "▲ classe</span>")
                    st.markdown(
                        f"<div style='background:{row_bg};border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:8px;font-size:.72rem;color:#475569;text-align:center'>"
                        f"{freq_label}{badge}</div>", unsafe_allow_html=True)
                with row_cols[5]:
                    st.number_input(
                        "Prévu", min_value=0, max_value=100,
                        value=nb_prevu, step=1,
                        key=sess_key,
                        label_visibility="collapsed",
                        on_change=_persist_overrides)
                with row_cols[6]:
                    st.markdown(
                        f"<div style='background:{row_bg};border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:8px;font-size:1rem;font-weight:800;color:#0f172a;text-align:center'>"
                        f"{realise}</div>", unsafe_allow_html=True)
                with row_cols[7]:
                    st.markdown(
                        f"<div style='background:{st_bg};border:1px solid {st_border};"
                        f"border-radius:8px;padding:8px;text-align:center;"
                        f"font-size:.78rem;font-weight:700;color:{st_txt}'>"
                        f"{st_icon} {st_label}</div>", unsafe_allow_html=True)

            st.divider()
            taux     = int(total_realise / total_prevu * 100) if total_prevu > 0 else 0
            taux_col = "#22c55e" if taux >= 100 else "#f59e0b" if taux >= 50 else "#ef4444"
            st.markdown(
                f"<div style='background:#1e293b;border-radius:10px;padding:12px 16px;"
                f"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px'>"
                f"<div style='font-size:.9rem;font-weight:800;color:#fff'>TOTAL SEMAINE</div>"
                f"<div style='display:flex;gap:20px;align-items:center'>"
                f"<div style='text-align:center'><div style='font-size:.65rem;color:#94a3b8;"
                f"text-transform:uppercase'>Prévu</div>"
                f"<div style='font-size:1.4rem;font-weight:900;color:#93c5fd'>{total_prevu}</div></div>"
                f"<div style='text-align:center'><div style='font-size:.65rem;color:#94a3b8;"
                f"text-transform:uppercase'>Réalisé</div>"
                f"<div style='font-size:1.4rem;font-weight:900;color:#86efac'>{total_realise}</div></div>"
                f"<div style='background:rgba(255,255,255,.15);border-radius:8px;padding:8px 16px;"
                f"font-size:1rem;font-weight:800;color:{taux_col}'>{taux}% réalisé</div>"
                f"</div></div>", unsafe_allow_html=True)

            st.divider()

            # ── Planning mensuel automatique — semaine par semaine ────────
            st.markdown("#### 📅 Planning automatique — vue mensuelle")

            _pm_year  = st.session_state.get("cal_year",  _today_dt.year)
            _pm_month = st.session_state.get("cal_month", _today_dt.month)

            pm_nav1, pm_nav2, pm_nav3, pm_nav4, pm_nav5 = st.columns([1,1,3,1,1])
            with pm_nav1:
                if st.button("◄◄", key="pm_prev_year",  use_container_width=True):
                    st.session_state.cal_year -= 1; st.rerun()
            with pm_nav2:
                if st.button("◄",  key="pm_prev_month", use_container_width=True):
                    if st.session_state.cal_month == 1:
                        st.session_state.cal_month = 12; st.session_state.cal_year -= 1
                    else:
                        st.session_state.cal_month -= 1
                    st.rerun()
            with pm_nav3:
                _pm_year  = st.session_state.get("cal_year",  _today_dt.year)
                _pm_month = st.session_state.get("cal_month", _today_dt.month)
                st.markdown(
                    "<div style='text-align:center;background:linear-gradient(135deg,#1e40af,#2563eb);"
                    "border-radius:10px;padding:8px;color:#fff;font-weight:800;font-size:1rem'>"
                    + MOIS_FR[_pm_month] + " " + str(_pm_year) + "</div>",
                    unsafe_allow_html=True)
            with pm_nav4:
                if st.button("►",  key="pm_next_month", use_container_width=True):
                    if st.session_state.cal_month == 12:
                        st.session_state.cal_month = 1; st.session_state.cal_year += 1
                    else:
                        st.session_state.cal_month += 1
                    st.rerun()
            with pm_nav5:
                if st.button("►►", key="pm_next_year",  use_container_width=True):
                    st.session_state.cal_year += 1; st.rerun()
            if st.button("📍 Mois courant", key="pm_today"):
                st.session_state.cal_year  = _today_dt.year
                st.session_state.cal_month = _today_dt.month
                st.rerun()

            import calendar as _cal_pm
            import random  as _rnd_pm

            _pm_year  = st.session_state.get("cal_year",  _today_dt.year)
            _pm_month = st.session_state.get("cal_month", _today_dt.month)
            _, _pm_ndays  = _cal_pm.monthrange(_pm_year, _pm_month)
            _pm_start     = date_type(_pm_year, _pm_month, 1)
            _pm_end       = date_type(_pm_year, _pm_month, _pm_ndays)
            _pm_holidays  = get_holidays_cached(_pm_year)

            # Semaines qui touchent le mois (lundi de la semaine inclus si vendredi dans le mois)
            _pm_mondays = []
            _cur = _pm_start - timedelta(days=_pm_start.weekday())
            while _cur <= _pm_end:
                _pm_mondays.append(_cur)
                _cur += timedelta(weeks=1)

            if "pm_selected_day" not in st.session_state:
                st.session_state["pm_selected_day"] = None

            rcp_pm = {"1":"#22c55e","2":"#84cc16","3":"#f59e0b","4":"#f97316","5":"#ef4444"}

            for week_idx, week_monday in enumerate(_pm_mondays):
                # ── CORRECTION PRINCIPALE : 5 jours ouvrés complets sans limite de mois ──
                _wd_week = [
                    week_monday + timedelta(days=i)
                    for i in range(5)
                    if (week_monday + timedelta(days=i)) not in _pm_holidays
                ]
                if not _wd_week:
                    continue

                nb_wd_week = len(_wd_week)
                _plan_week   = {wd: [] for wd in _wd_week}
                _charge_week = {wd: 0  for wd in _wd_week}
                _to_repartir = []

                for pt in st.session_state.points:
                    rc_pt_pm  = (pt.get("room_class") or "").strip()
                    co_val_pm = st.session_state.get(class_override_key, {}).get(rc_pt_pm, 0)
                    # ── Seulement l'override de classe, ignorer fréquence individuelle si override actif ──
                    co_pm = int(co_val_pm) if co_val_pm and int(co_val_pm) > 0 else None
                    fu_pm = pt.get("frequency_unit", "/ semaine")
                    fr_pm = pt.get("frequency")
                    tache_pm = {
                        "label":      pt["label"],
                        "type":       pt.get("type", "—"),
                        "risk":       int(pt.get("risk_level", 1)),
                        "room_class": rc_pt_pm,
                    }
                    is_daily_pm = (
                        fu_pm == "/ jour" and co_pm is None
                        and fr_pm is not None and int(fr_pm or 0) > 0
                    )
                    if is_daily_pm:
                        for wd in _wd_week:
                            _plan_week[wd].append(tache_pm)
                            _charge_week[wd] += 1
                    else:
                        nb_pm, _, _ = _get_prevu_semaine(pt, week_monday, nb_wd_week, co_pm)
                        for _ in range(nb_pm):
                            _to_repartir.append(tache_pm)

                # Répartition équilibrée sur les 5 jours (sans limite de mois)
                _rng_pm = _rnd_pm.Random(_pm_year * 10000 + _pm_month * 100 + week_idx)
                _rng_pm.shuffle(_to_repartir)
                for t in _to_repartir:
                    wd_c = min(_wd_week, key=lambda d: _charge_week[d])
                    _plan_week[wd_c].append(t)
                    _charge_week[wd_c] += 1

                _we_end    = week_monday + timedelta(days=6)
                _total_sem = sum(len(v) for v in _plan_week.values())
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

                _day_cols = st.columns(len(_wd_week))
                for di, wd in enumerate(_wd_week):
                    taches_j   = _plan_week[wd]
                    prevu_j    = len(taches_j)
                    is_today_d = (wd == _today_dt)
                    is_past_d  = (wd < _today_dt)
                    # Grisé si hors du mois affiché
                    is_other_month = (wd.month != _pm_month)
                    realise_j  = sum(
                        1 for p in st.session_state.prelevements
                        if p.get("date")
                        and datetime.fromisoformat(p["date"]).date() == wd
                        and not p.get("archived", False)
                    )
                    j2_j = [s for s in st.session_state.schedules
                             if s["when"] == "J2"
                             and datetime.fromisoformat(s["due_date"]).date() == wd]
                    j7_j = [s for s in st.session_state.schedules
                             if s["when"] == "J7"
                             and datetime.fromisoformat(s["due_date"]).date() == wd]

                    bg_d     = "#dbeafe" if is_today_d else ("#f1f5f9" if is_other_month else ("#f8fafc" if is_past_d else "#ffffff"))
                    border_d = "2px solid #2563eb" if is_today_d else ("1px dashed #cbd5e1" if is_other_month else "1.5px solid #e2e8f0")
                    jour_col = "#1e40af" if is_today_d else ("#94a3b8" if is_other_month or is_past_d else "#475569")
                    op_d     = "0.6" if is_other_month else ("0.7" if is_past_d and not is_today_d else "1")

                    if realise_j >= prevu_j and prevu_j > 0:
                        stat_bg="#f0fdf4"; stat_col="#166534"; stat_lbl="✅"
                    elif realise_j > 0:
                        stat_bg="#fffbeb"; stat_col="#92400e"; stat_lbl=f"⏳{realise_j}/{prevu_j}"
                    elif prevu_j > 0:
                        stat_bg="#fef2f2"; stat_col="#991b1b"; stat_lbl=f"🔴{prevu_j}"
                    else:
                        stat_bg="#f8fafc"; stat_col="#94a3b8"; stat_lbl="—"

                    pts_html = ""
                    for t in taches_j[:5]:
                        rc_t = rcp_pm.get(str(t["risk"]), "#94a3b8")
                        icon = "💨" if t["type"] == "Air" else "🧴"
                        lbl  = t["label"][:18] + ("…" if len(t["label"]) > 18 else "")
                        pts_html += (
                            f"<div style='border-left:2px solid {rc_t};padding:1px 5px;"
                            f"font-size:.58rem;color:#0f172a;margin-bottom:1px'>"
                            f"{icon} {lbl}</div>")
                    if len(taches_j) > 5:
                        pts_html += f"<div style='font-size:.55rem;color:#94a3b8'>+{len(taches_j)-5}</div>"

                    lect_html = ""
                    if j2_j:
                        lect_html += f"<div style='font-size:.58rem;color:#d97706;margin-top:2px'>📖×{len(j2_j)}</div>"
                    if j7_j:
                        lect_html += f"<div style='font-size:.58rem;color:#0369a1'>📗×{len(j7_j)}</div>"

                    # Badge "autre mois"
                    autre_mois_badge = ""
                    if is_other_month:
                        autre_mois_badge = f"<div style='font-size:.5rem;color:#94a3b8;font-style:italic'>{wd.strftime('%b')}</div>"

                    is_selected = (st.session_state.get("pm_selected_day") == wd)
                    sel_border  = "2.5px solid #7c3aed" if is_selected else border_d
                    sel_bg      = "#faf5ff" if is_selected else bg_d

                    card_html = (
                        f"<div style='background:{sel_bg};border:{sel_border};border-radius:10px;"
                        f"padding:8px 6px;opacity:{op_d};min-height:100px'>"
                        f"<div style='font-size:.75rem;font-weight:800;color:{jour_col};text-align:center'>"
                        f"{JOURS_FR_LONG[wd.weekday()][:3]}</div>"
                        f"<div style='font-size:.7rem;color:#94a3b8;text-align:center;margin-bottom:2px'>"
                        f"{wd.strftime('%d/%m')}</div>"
                        f"{autre_mois_badge}"
                        f"<div style='background:{stat_bg};border-radius:6px;padding:2px 4px;"
                        f"text-align:center;font-size:.68rem;font-weight:800;color:{stat_col};"
                        f"margin-bottom:4px'>{stat_lbl}</div>"
                        f"{pts_html}{lect_html}</div>")

                    with _day_cols[di]:
                        st.markdown(card_html, unsafe_allow_html=True)
                        btn_lbl = "🔍 Détail" if not is_selected else "✖ Fermer"
                        if st.button(btn_lbl, key=f"pm_btn_{wd.isoformat()}", use_container_width=True):
                            if is_selected:
                                st.session_state["pm_selected_day"] = None
                            else:
                                st.session_state["pm_selected_day"] = wd
                            st.rerun()

            # Panel fixe bas de page : détail du jour sélectionné
            _sel = st.session_state.get("pm_selected_day")
            if _sel:
                import random as _rnd_fix
                _sel_monday  = _sel - timedelta(days=_sel.weekday())
                # Semaine complète sans limite de mois
                _wd_sel_week = [
                    _sel_monday + timedelta(days=i)
                    for i in range(5)
                    if (_sel_monday + timedelta(days=i)) not in _pm_holidays
                ]
                _plan_fix   = {wd: [] for wd in _wd_sel_week}
                _charge_fix = {wd: 0  for wd in _wd_sel_week}
                _torep_fix  = []
                _wi_fix = _pm_mondays.index(_sel_monday) if _sel_monday in _pm_mondays else 0
                for pt in st.session_state.points:
                    _rc_f = (pt.get("room_class") or "").strip()
                    _co_v = st.session_state.get(class_override_key, {}).get(_rc_f, 0)
                    _co_f = int(_co_v) if _co_v and int(_co_v) > 0 else None
                    _fu_f = pt.get("frequency_unit", "/ semaine")
                    _fr_f = pt.get("frequency")
                    _t_f  = {"label": pt["label"], "type": pt.get("type","—"),
                             "risk": int(pt.get("risk_level",1)), "room_class": _rc_f}
                    _is_d = (_fu_f == "/ jour" and _co_f is None
                             and _fr_f is not None and int(_fr_f or 0) > 0)
                    if _is_d:
                        for wd in _wd_sel_week:
                            _plan_fix[wd].append(_t_f); _charge_fix[wd] += 1
                    else:
                        _nb_f, _, _ = _get_prevu_semaine(pt, _sel_monday, len(_wd_sel_week), _co_f)
                        for _ in range(_nb_f): _torep_fix.append(_t_f)
                _rng_fix = _rnd_fix.Random(_pm_year * 10000 + _pm_month * 100 + _wi_fix)
                _rng_fix.shuffle(_torep_fix)
                for t in _torep_fix:
                    _wdc = min(_wd_sel_week, key=lambda d: _charge_fix[d])
                    _plan_fix[_wdc].append(t); _charge_fix[_wdc] += 1
                taches_sel_list = _plan_fix.get(_sel, [])

                j0r_sel = [p for p in st.session_state.prelevements
                            if p.get("date") and not p.get("archived",False)
                            and datetime.fromisoformat(p["date"]).date() == _sel]
                j2r_sel = [s for s in st.session_state.schedules
                            if s["when"]=="J2" and datetime.fromisoformat(s["due_date"]).date()==_sel]
                j7r_sel = [s for s in st.session_state.schedules
                            if s["when"]=="J7" and datetime.fromisoformat(s["due_date"]).date()==_sel]

                _day_lbl = f"{JOURS_FR_LONG[_sel.weekday()]} {_sel.strftime('%d/%m/%Y')}"
                _nb_t     = len(taches_sel_list)
                _nb_j0    = len(j0r_sel)
                _nb_j2    = len(j2r_sel)
                _nb_j7    = len(j7r_sel)
                rcp_fix   = {"1":"#22c55e","2":"#84cc16","3":"#f59e0b","4":"#f97316","5":"#ef4444"}

                _cards = ""
                for t in taches_sel_list:
                    _c = rcp_fix.get(str(t["risk"]),"#94a3b8")
                    _ic = "💨" if t["type"]=="Air" else "🧴"
                    _dn = any(p.get("label")==t["label"] for p in j0r_sel)
                    _bg = "#f0fdf4" if _dn else "#fff"
                    _bd = "#86efac" if _dn else _c+"44"
                    _cards += (f"<div style=background:{_bg};border:1px solid {_bd};"
                               f"border-left:3px solid {_c};border-radius:7px;"
                               f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px>"
                               f"<div style=font-size:.77rem;font-weight:700;color:#0f172a>{_ic} {'✅ ' if _dn else ''}{t['label']}</div>"
                               f"<div style=font-size:.63rem;color:#64748b>Cl. {t['room_class'] or '—'} · Nv.{t['risk']}</div></div>")
                for s in j2r_sel:
                    _dn = s["status"]=="done"
                    _lt = not _dn and _sel < _today_dt
                    _c  = "#22c55e" if _dn else ("#ef4444" if _lt else "#d97706")
                    _bg = "#f0fdf4" if _dn else ("#fef2f2" if _lt else "#fffbeb")
                    _st = "✅" if _dn else ("⚠️" if _lt else "⏳")
                    _cards += (f"<div style=background:{_bg};border:1px solid {_c}44;"
                               f"border-left:3px solid {_c};border-radius:7px;"
                               f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px>"
                               f"<div style=font-size:.77rem;font-weight:700;color:#0f172a>📖 J2 — {s['label'][:22]}</div>"
                               f"<div style=font-size:.63rem;color:{_c};font-weight:700>{_st} {'Fait' if _dn else ('Retard' if _lt else 'À faire')}</div></div>")
                for s in j7r_sel:
                    _dn = s["status"]=="done"
                    _lt = not _dn and _sel < _today_dt
                    _c  = "#22c55e" if _dn else ("#ef4444" if _lt else "#0369a1")
                    _bg = "#f0fdf4" if _dn else ("#fef2f2" if _lt else "#eff6ff")
                    _st = "✅" if _dn else ("⚠️" if _lt else "⏳")
                    _cards += (f"<div style=background:{_bg};border:1px solid {_c}44;"
                               f"border-left:3px solid {_c};border-radius:7px;"
                               f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px>"
                               f"<div style=font-size:.77rem;font-weight:700;color:#0f172a>📗 J7 — {s['label'][:22]}</div>"
                               f"<div style=font-size:.63rem;color:{_c};font-weight:700>{_st} {'Fait' if _dn else ('Retard' if _lt else 'À faire')}</div></div>")
                for p in j0r_sel:
                    _cards += (f"<div style=background:#faf5ff;border:1px solid #e9d5ff;"
                               f"border-left:3px solid #7c3aed;border-radius:7px;"
                               f"padding:6px 10px;flex-shrink:0;min-width:150px;max-width:200px>"
                               f"<div style=font-size:.77rem;font-weight:700;color:#0f172a>🧪 {p['label'][:22]}</div>"
                               f"<div style=font-size:.63rem;color:#64748b>{p.get('gelose','—')} · {p.get('operateur','—') or '—'}</div></div>")
                if not _cards:
                    _cards = "<div style=color:#94a3b8;font-size:.82rem;padding:8px 0;align-self:center>Aucune activité ce jour.</div>"
                _rbadge = f" · 🧪 {_nb_j0} réalisé" if _nb_j0 else ""
                st.markdown(
                    "<div style='position:fixed;bottom:0;left:0;right:0;z-index:9999;"
                    "background:linear-gradient(135deg,#0f172a,#1e293b);"
                    "border-top:3px solid #2563eb;padding:10px 20px 14px 20px;"
                    "box-shadow:0 -6px 32px rgba(0,0,0,.4)'>"
                    "<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>"
                    f"<div style='color:#fff;font-weight:800;font-size:.95rem'>📋 {_day_lbl}"
                    f"<span style='margin-left:10px;font-size:.75rem;font-weight:400;color:#93c5fd'>{_nb_t} prélèv. · {_nb_j2} J2 · {_nb_j7} J7{_rbadge}</span></div>"
                    "<span style='font-size:.7rem;color:#475569;font-style:italic'>Cliquez à nouveau sur le jour pour fermer</span>"
                    "</div>"
                    f"<div style='display:flex;gap:8px;overflow-x:auto;padding-bottom:2px'>{_cards}</div>"
                    "</div>"
                    "<div style='height:170px'></div>",
                    unsafe_allow_html=True)

            st.divider()
            taux     = int(total_realise / total_prevu * 100) if total_prevu > 0 else 0
            taux_col = "#22c55e" if taux >= 100 else "#f59e0b" if taux >= 50 else "#ef4444"
            st.markdown(
                f"<div style='background:#1e293b;border-radius:10px;padding:12px 16px;"
                f"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px'>"
                f"<div style='font-size:.9rem;font-weight:800;color:#fff'>TOTAL SEMAINE</div>"
                f"<div style='display:flex;gap:20px;align-items:center'>"
                f"<div style='text-align:center'><div style='font-size:.65rem;color:#94a3b8;"
                f"text-transform:uppercase'>Prévu</div>"
                f"<div style='font-size:1.4rem;font-weight:900;color:#93c5fd'>{total_prevu}</div></div>"
                f"<div style='text-align:center'><div style='font-size:.65rem;color:#94a3b8;"
                f"text-transform:uppercase'>Réalisé</div>"
                f"<div style='font-size:1.4rem;font-weight:900;color:#86efac'>{total_realise}</div></div>"
                f"<div style='background:rgba(255,255,255,.15);border-radius:8px;padding:8px 16px;"
                f"font-size:1rem;font-weight:800;color:{taux_col}'>{taux}% réalisé</div>"
                f"</div></div>", unsafe_allow_html=True)

            st.divider()


    # ═════════════════════════════════════════════════════════════════════════
    # ONGLET EXPORT EXCEL
    # ═════════════════════════════════════════════════════════════════════════
    with plan_tab_export:
        st.markdown("#### 📥 Exporter le planning en Excel")
        exp_scope = st.selectbox(
            "Période", ["Mois en cours","4 semaines à venir","Tout le planning"],
            key="exp_scope")
        exp_oper_filter = st.selectbox(
            "Filtrer par opérateur",
            ["Tous"] + [o['nom'] for o in st.session_state.operators],
            key="exp_oper")
        only_working = st.checkbox("Inclure uniquement les jours ouvrés", value=True)

        if st.button("📊 Générer Excel", use_container_width=True, key="gen_xlsx"):
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
            import io as _io

            wb = openpyxl.Workbook()
            C_BLUE="1E40AF"; C_BLUE2="2563EB"; C_BLUE_L="DBEAFE"
            C_PURPLE_L="F5F3FF"; C_YELLOW_L="FFFBEB"; C_TEAL_L="EFF6FF"
            C_WHITE="FFFFFF"; C_TEXT="0F172A"
            C_PURPLE="7C3AED"; C_YELLOW="D97706"; C_TEAL="0369A1"; C_GREEN="16A34A"
            thin   = Side(style="thin", color="E2E8F0")
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
            def fill(h):  return PatternFill("solid", fgColor=h)
            def font(size=10, bold=False, color=C_TEXT):
                return Font(name="Arial", size=size, bold=bold, color=color)
            def al_c(): return Alignment(horizontal="center", vertical="center", wrap_text=True)
            def al_l(): return Alignment(horizontal="left",   vertical="center", wrap_text=True)

            exp_today = _today_dt
            if exp_scope == "Mois en cours":
                first = exp_today.replace(day=1)
                last  = exp_today.replace(
                    day=cal_module.monthrange(exp_today.year, exp_today.month)[1])
                exp_dates = [first + timedelta(days=i) for i in range((last - first).days + 1)]
            elif exp_scope == "4 semaines à venir":
                ws_e = exp_today - timedelta(days=exp_today.weekday())
                exp_dates = [ws_e + timedelta(days=i) for i in range(28)]
            else:
                all_d = []
                for p in st.session_state.prelevements:
                    try: all_d.append(datetime.fromisoformat(p["date"]).date())
                    except: pass
                for s in st.session_state.schedules:
                    try: all_d.append(datetime.fromisoformat(s["due_date"]).date())
                    except: pass
                exp_dates = (
                    [min(all_d) + timedelta(days=i)
                     for i in range((max(all_d) - min(all_d)).days + 1)]
                    if all_d else [exp_today + timedelta(days=i) for i in range(7)])

            if only_working:
                exp_dates = [d for d in exp_dates if is_working_day(d)]

            ws1 = wb.active; ws1.title = "Planning"
            ws1.sheet_view.showGridLines = False
            ws1.merge_cells("A1:I1")
            ws1["A1"] = "PLANNING MICROBIOLOGIQUE — MicroSurveillance URC"
            ws1["A1"].font = Font(name="Arial", size=14, bold=True, color=C_WHITE)
            ws1["A1"].fill = fill(C_BLUE); ws1["A1"].alignment = al_c()
            ws1.row_dimensions[1].height = 30
            ws1.merge_cells("A2:I2")
            ws1["A2"] = (
                f"Généré le {exp_today.strftime('%d/%m/%Y')} — Jours ouvrés uniquement"
                if only_working else f"Généré le {exp_today.strftime('%d/%m/%Y')}")
            ws1["A2"].font = Font(name="Arial", size=9, color="475569")
            ws1["A2"].fill = fill(C_BLUE_L); ws1["A2"].alignment = al_c()
            ws1.row_dimensions[2].height = 18

            headers    = ["Date","Jour","Férié","Type","Point de prélèvement",
                          "Classe","Gélose","Opérateur","Statut"]
            col_widths = [14, 12, 10, 22, 32, 10, 28, 25, 14]
            for ci, (h, w) in enumerate(zip(headers, col_widths), start=1):
                c = ws1.cell(row=4, column=ci, value=h)
                c.font = Font(name="Arial", size=10, bold=True, color=C_WHITE)
                c.fill = fill(C_BLUE2); c.alignment = al_c(); c.border = border
                ws1.column_dimensions[get_column_letter(ci)].width = w
            ws1.row_dimensions[4].height = 22; ws1.freeze_panes = "A5"

            JOURS_XL = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
            row = 5
            for d in exp_dates:
                holidays_d = get_holidays_cached(d.year)
                is_h = d in holidays_d
                day_prelevs = [
                    p for p in st.session_state.prelevements
                    if p.get('date')
                    and datetime.fromisoformat(p['date']).date() == d
                    and not p.get('archived', False)
                    and (exp_oper_filter == "Tous"
                         or p.get('operateur','').startswith(exp_oper_filter))]
                day_j2 = [s for s in st.session_state.schedules
                           if s['when'] == 'J2'
                           and datetime.fromisoformat(s['due_date']).date() == d]
                day_j7 = [s for s in st.session_state.schedules
                           if s['when'] == 'J7'
                           and datetime.fromisoformat(s['due_date']).date() == d]
                if not day_prelevs and not day_j2 and not day_j7:
                    continue

                for p in day_prelevs:
                    rd = [d.strftime('%d/%m/%Y'), JOURS_XL[d.weekday()], "Oui" if is_h else "",
                          "Prélèvement J0", p['label'], p.get('room_class','—'),
                          p.get('gelose','—'), p.get('operateur','—'), "🧪 À réaliser"]
                    for ci, val in enumerate(rd, 1):
                        c = ws1.cell(row=row, column=ci, value=val)
                        c.fill=fill(C_PURPLE_L); c.alignment=al_l(); c.border=border; c.font=font()
                    ws1.cell(row=row, column=4).font = Font(
                        name="Arial", size=10, bold=True, color=C_PURPLE)
                    ws1.row_dimensions[row].height = 18; row += 1

                for sch in day_j2:
                    samp    = next((p for p in st.session_state.prelevements
                                    if p['id'] == sch['sample_id']), None)
                    is_done = sch['status'] == 'done'
                    rd = [d.strftime('%d/%m/%Y'), JOURS_XL[d.weekday()], "Oui" if is_h else "",
                          "Lecture J2", sch['label'],
                          samp.get('room_class','—') if samp else '—',
                          samp.get('gelose','—')     if samp else '—',
                          samp.get('operateur','—')  if samp else '—',
                          "✅ Faite" if is_done else "⏳ À faire"]
                    for ci, val in enumerate(rd, 1):
                        c = ws1.cell(row=row, column=ci, value=val)
                        c.fill=fill(C_YELLOW_L); c.alignment=al_l(); c.border=border; c.font=font()
                    ws1.cell(row=row, column=4).font = Font(
                        name="Arial", size=10, bold=True, color=C_YELLOW)
                    ws1.cell(row=row, column=9).font = Font(
                        name="Arial", size=10, bold=True,
                        color=C_GREEN if is_done else C_YELLOW)
                    ws1.row_dimensions[row].height = 18; row += 1

                for sch in day_j7:
                    samp    = next((p for p in st.session_state.prelevements
                                    if p['id'] == sch['sample_id']), None)
                    is_done = sch['status'] == 'done'
                    rd = [d.strftime('%d/%m/%Y'), JOURS_XL[d.weekday()], "Oui" if is_h else "",
                          "Lecture J7", sch['label'],
                          samp.get('room_class','—') if samp else '—',
                          samp.get('gelose','—')     if samp else '—',
                          samp.get('operateur','—')  if samp else '—',
                          "✅ Faite" if is_done else "⏳ À faire"]
                    for ci, val in enumerate(rd, 1):
                        c = ws1.cell(row=row, column=ci, value=val)
                        c.fill=fill(C_TEAL_L); c.alignment=al_l(); c.border=border; c.font=font()
                    ws1.cell(row=row, column=4).font = Font(
                        name="Arial", size=10, bold=True, color=C_TEAL)
                    ws1.cell(row=row, column=9).font = Font(
                        name="Arial", size=10, bold=True,
                        color=C_GREEN if is_done else C_TEAL)
                    ws1.row_dimensions[row].height = 18; row += 1

            buf = _io.BytesIO(); wb.save(buf); buf.seek(0)
            fname = f"planning_URC_{exp_today.strftime('%Y%m%d')}.xlsx"
            st.download_button(
                "⬇️ Télécharger le planning Excel",
                data=buf.getvalue(), file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
            st.success(f"✅ Fichier **{fname}** généré")
            
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 : PLAN URC
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "plan":
    st.markdown("#### 🗺️ Plan URC interactif — placement des prélèvements")

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Uploader le plan URC (PNG, JPG ou PDF)",
        type=["png", "jpg", "jpeg", "pdf"],
        key="plan_upload_main"
    )

    if uploaded:
        raw = uploaded.read()
        if uploaded.type == "application/pdf":
            try:
                import fitz
                import io as _io2
                with st.spinner("🔄 Conversion du PDF en cours..."):
                    doc  = fitz.open(stream=raw, filetype="pdf")
                    page = doc[0]
                    mat  = fitz.Matrix(2.0, 2.0)
                    pix  = page.get_pixmap(matrix=mat)
                    buf  = _io2.BytesIO(pix.tobytes("png"))
                    img_b64 = base64.b64encode(buf.read()).decode()
                    st.session_state.map_image = f"data:image/png;base64,{img_b64}"
                st.success("✅ PDF converti avec succès.")
            except ImportError:
                st.error("❌ PyMuPDF non installé — ajoutez `PyMuPDF` dans requirements.txt")
                st.stop()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
                st.stop()
        else:
            img_b64 = base64.b64encode(raw).decode()
            st.session_state.map_image = f"data:{uploaded.type};base64,{img_b64}"

    # ── Affichage ─────────────────────────────────────────────────────────────
    if st.session_state.get("map_image"):

        surv_points = [
            {
                "label":  r["prelevement"],
                "germ":   r["germ_match"],
                "ufc":    r["ufc"],
                "date":   r["date"],
                "status": r["status"],
            }
            for r in st.session_state.surveillance
        ]
        surv_json = json.dumps(surv_points, ensure_ascii=False)
        pts_json  = json.dumps(st.session_state.get("map_points", []), ensure_ascii=False)

        options_html = "".join(
            f'<option value="{r["label"]}">'
            f'{r["label"]} — {r["germ"]} ({r["ufc"]} UFC)'
            f'</option>'
            for r in surv_points
        )

        map_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: #1e293b;
  font-family: 'Segoe UI', sans-serif;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

/* ── Toolbar ── */
.toolbar {{
  padding: 8px 14px;
  background: #fff;
  border-bottom: 2px solid #e2e8f0;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  flex-shrink: 0;
}}
.toolbar input, .toolbar select {{
  background: #f8fafc;
  border: 1.5px solid #cbd5e1;
  border-radius: 6px;
  padding: 5px 9px;
  color: #1e293b;
  font-size: .75rem;
  outline: none;
}}
.toolbar input:focus, .toolbar select:focus {{
  border-color: #2563eb;
}}
.tb-btn {{
  background: #f8fafc;
  border: 1.5px solid #cbd5e1;
  border-radius: 6px;
  padding: 5px 10px;
  color: #1e293b;
  font-size: .75rem;
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
}}
.tb-btn:hover {{ background: #dbeafe; border-color: #2563eb; color: #1e40af; }}
.tb-btn.active {{ background: #2563eb; border-color: #2563eb; color: #fff; }}
.tb-btn.danger:hover {{ background: #fef2f2; border-color: #ef4444; color: #dc2626; }}
.legend {{
  margin-left: auto;
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: .65rem;
  color: #64748b;
}}
.legend-dot {{
  width: 10px; height: 10px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 3px;
}}

/* ── Map ── */
.map-wrap {{
  flex: 1;
  overflow: auto;
  position: relative;
  background: #1e293b;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}}
.map-inner {{
  position: relative;
  display: inline-block;
  margin: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,.5);
  border-radius: 4px;
  overflow: visible;
}}
#planImg {{
  display: block;
  max-width: 100%;
  border-radius: 4px;
  user-select: none;
  -webkit-user-drag: none;
}}

/* ── Points ── */
.point {{
  position: absolute;
  width: 28px; height: 28px;
  border-radius: 50%;
  border: 2.5px solid #fff;
  cursor: pointer;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,.6);
  z-index: 20;
  transition: transform .15s, box-shadow .15s;
  pointer-events: all;
}}
.point:hover {{
  transform: translate(-50%, -50%) scale(1.5);
  box-shadow: 0 4px 20px rgba(0,0,0,.7);
}}
.point.ok     {{ background: #22c55e; }}
.point.alert  {{ background: #f59e0b; }}
.point.action {{ background: #ef4444; }}
.point.none   {{ background: #475569; }}

/* ── Tooltip ── */
.tooltip {{
  position: fixed;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: .73rem;
  pointer-events: none;
  z-index: 9999;
  display: none;
  min-width: 210px;
  box-shadow: 0 6px 24px rgba(0,0,0,.18);
  line-height: 1.7;
}}
.tooltip.visible {{ display: block; }}
.tip-title {{
  font-weight: 800;
  font-size: .82rem;
  color: #1e293b;
  margin-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 5px;
}}
.tip-row {{ color: #475569; }}
.tip-row b {{ color: #1e293b; }}

/* ── Mode curseur ── */
.map-wrap.add-mode {{ cursor: crosshair; }}

/* ── Compteur ── */
#counter {{
  font-size: .72rem;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 4px 10px;
  font-weight: 600;
}}
</style></head><body>

<div class="toolbar">
  <input id="ptLabel" placeholder="🏷️ Nom du point" style="width:150px">
  <select id="ptSurv" style="width:220px">
    <option value="">— Lier à un résultat —</option>
    {options_html}
  </select>
  <button class="tb-btn" id="addBtn" onclick="toggleAdd()">📍 Placer un point</button>
  <button class="tb-btn" onclick="clearLast()">↩️ Annuler dernier</button>
  <button class="tb-btn danger" onclick="clearAll()">🗑️ Tout effacer</button>
  <span id="counter">0 point(s)</span>
  <div class="legend">
    <span><span class="legend-dot" style="background:#475569"></span>Non lié</span>
    <span><span class="legend-dot" style="background:#22c55e"></span>OK</span>
    <span><span class="legend-dot" style="background:#f59e0b"></span>Alerte</span>
    <span><span class="legend-dot" style="background:#ef4444"></span>Action</span>
  </div>
</div>

<div class="map-wrap" id="mapWrap">
  <div class="map-inner" id="mapInner">
    <img id="planImg" src="{st.session_state.map_image}" draggable="false" alt="Plan URC">
  </div>
</div>
<div id="tooltip" class="tooltip"></div>

<script>
let addMode = false;
let points  = {pts_json};
const surv  = {surv_json};

function updateCounter() {{
  document.getElementById('counter').textContent = points.length + ' point(s)';
}}

function toggleAdd() {{
  addMode = !addMode;
  const btn  = document.getElementById('addBtn');
  const wrap = document.getElementById('mapWrap');
  btn.classList.toggle('active', addMode);
  btn.textContent = addMode ? '✋ Annuler placement' : '📍 Placer un point';
  wrap.classList.toggle('add-mode', addMode);
}}

function renderPoints() {{
  document.querySelectorAll('.point').forEach(p => p.remove());
  const inner = document.getElementById('mapInner');
  points.forEach((pt, i) => {{
    const s      = surv.find(r => r.label === (pt.survLabel || pt.label));
    const status = s ? s.status : 'none';
    const div    = document.createElement('div');
    div.className   = 'point ' + status;
    div.style.left  = pt.x + '%';
    div.style.top   = pt.y + '%';
    div.textContent = i + 1;
    div.title       = pt.label;
    div.addEventListener('mouseenter', e => showTip(e, pt, s));
    div.addEventListener('mouseleave', hideTip);
    inner.appendChild(div);
  }});
  updateCounter();
}}

function showTip(e, pt, s) {{
  const t = document.getElementById('tooltip');
  const statusTxt = s
    ? (s.status === 'ok' ? '✅ Conforme' : s.status === 'alert' ? '⚠️ Alerte' : '🚨 Action requise')
    : null;
  t.innerHTML =
    '<div class="tip-title">📍 ' + pt.label + '</div>' +
    (s
      ? '<div class="tip-row">Germe : <b>' + s.germ + '</b></div>' +
        '<div class="tip-row">UFC/m³ : <b>' + s.ufc + '</b></div>' +
        '<div class="tip-row">Date : <b>' + s.date + '</b></div>' +
        '<div class="tip-row" style="margin-top:4px">Statut : <b>' + statusTxt + '</b></div>'
      : '<div class="tip-row" style="color:#94a3b8;font-style:italic">Non lié à un résultat</div>'
    );
  t.style.left = (e.clientX + 16) + 'px';
  t.style.top  = (e.clientY - 12) + 'px';
  t.classList.add('visible');
}}

function hideTip() {{
  document.getElementById('tooltip').classList.remove('visible');
}}

function clearLast() {{
  if (points.length === 0) return;
  points.pop();
  renderPoints();
}}

function clearAll() {{
  if (!confirm('Effacer tous les points du plan ?')) return;
  points = [];
  renderPoints();
}}

// Clic sur la carte pour placer un point
document.getElementById('mapInner').addEventListener('click', function(e) {{
  if (!addMode) return;
  if (e.target.classList.contains('point')) return;
  const img  = document.getElementById('planImg');
  const rect = img.getBoundingClientRect();
  if (e.clientX < rect.left || e.clientX > rect.right ||
      e.clientY < rect.top  || e.clientY > rect.bottom) return;
  const x         = ((e.clientX - rect.left) / rect.width  * 100).toFixed(2);
  const y         = ((e.clientY - rect.top)  / rect.height * 100).toFixed(2);
  const label     = document.getElementById('ptLabel').value.trim() || ('Point ' + (points.length + 1));
  const survLabel = document.getElementById('ptSurv').value || null;
  points.push({{ x: parseFloat(x), y: parseFloat(y), label, survLabel }});
  renderPoints();
  toggleAdd();
}});

// Tooltip suit la souris
document.addEventListener('mousemove', function(e) {{
  const t = document.getElementById('tooltip');
  if (t.classList.contains('visible')) {{
    t.style.left = (e.clientX + 16) + 'px';
    t.style.top  = (e.clientY - 12) + 'px';
  }}
}});

// Init
const img = document.getElementById('planImg');
if (img.complete && img.naturalWidth > 0) renderPoints();
else img.addEventListener('load', renderPoints);
</script>
</body></html>"""

        st.components.v1.html(map_html, height=720, scrolling=False)

    else:
        st.markdown("""
        <div style="background:#f8fafc;border:2px dashed #cbd5e1;border-radius:14px;
                    padding:72px 32px;text-align:center;color:#64748b;margin-top:16px">
          <div style="font-size:3.5rem;margin-bottom:12px">🗺️</div>
          <div style="font-size:1.1rem;font-weight:700;color:#1e293b;margin-bottom:6px">
            Aucun plan chargé
          </div>
          <div style="font-size:.85rem">
            Uploadez un plan URC en <strong>PNG</strong>, <strong>JPG</strong> ou <strong>PDF</strong>
          </div>
          <div style="font-size:.75rem;color:#94a3b8;margin-top:8px">
            Le PDF sera automatiquement converti en image
          </div>
        </div>""", unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 : HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "historique":
    st.markdown("### 📋 Historique de surveillance")
    surv  = st.session_state.surveillance
    total = len(surv)

    if surv:
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
                        import json as _json
                        supa.table("app_data").upsert({
                            "key": "surveillance",
                            "value": _json.dumps([], ensure_ascii=False)
                        }).execute()
                except Exception:
                    pass
                if os.path.exists(CSV_FILE):
                    os.remove(CSV_FILE)
                st.rerun()

        alerts  = sum(1 for r in surv if r["status"] == "alert")
        actions = sum(1 for r in surv if r["status"] == "action")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total",        total)
        c2.metric("✅ Conformes", total - alerts - actions)
        c3.metric("⚠️ Alertes",  alerts)
        c4.metric("🚨 Actions",   actions)
        st.divider()

        hist_tab_pts, hist_tab_germs, hist_tab_prev, hist_tab_liste = st.tabs([
            "📍 Stats par point",
            "🦠 Stats par germe",
            "👤 Répartition par préleveur",
            "📋 Liste des entrées",
        ])

        # ══════════════════════════════════════════════════════════════════
        # ONGLET 1 : STATS PAR POINT
        # ══════════════════════════════════════════════════════════════════
        with hist_tab_pts:
            from collections import defaultdict
            import json as _json_pts

            pts_stats = defaultdict(lambda: {
                "total": 0, "positives": 0, "negatives": 0,
                "germes": defaultdict(int)
            })
            for r in surv:
                pt   = r.get("prelevement", "—")
                ufc  = int(r.get("ufc", 0))
                germ = r.get("germ_match", "") or ""
                pts_stats[pt]["total"] += 1
                if ufc > 0 and germ not in ("Négatif", "—", ""):
                    pts_stats[pt]["positives"] += 1
                    pts_stats[pt]["germes"][germ] += 1
                else:
                    pts_stats[pt]["negatives"] += 1

            sorted_pts   = sorted(pts_stats.items(), key=lambda x: -x[1]["positives"])
            chart_labels = [p[:22] + "…" if len(p) > 22 else p for p, _ in sorted_pts]
            chart_neg    = [d["negatives"] for _, d in sorted_pts]
            chart_pos    = [d["positives"] for _, d in sorted_pts]
            chart_data   = {"labels": chart_labels, "neg": chart_neg, "pos": chart_pos}

            chart_html = f"""
            <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                        padding:16px;margin-bottom:18px">
              <div style="font-size:.8rem;font-weight:700;color:#1e40af;margin-bottom:10px">
                📊 Résultats par point de prélèvement
              </div>
              <div style="width:100%;height:180px">
                <canvas id="ptChart"></canvas>
              </div>
            </div>
            <script>
            (function(){{
              const d = {_json_pts.dumps(chart_data)};
              new Chart(document.getElementById('ptChart'), {{
                type: 'bar',
                data: {{
                  labels: d.labels,
                  datasets: [
                    {{ label: '✅ Négatifs', data: d.neg,
                       backgroundColor: '#22c55e88', borderColor: '#22c55e', borderWidth: 1 }},
                    {{ label: '🦠 Positifs', data: d.pos,
                       backgroundColor: '#ef444488', borderColor: '#ef4444', borderWidth: 1 }}
                  ]
                }},
                options: {{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'top', labels: {{ font: {{ size: 11 }} }} }} }},
                  scales: {{
                    x: {{ stacked: true, ticks: {{ font: {{ size: 10 }} }} }},
                    y: {{ stacked: true, beginAtZero: true, ticks: {{ stepSize: 1, font: {{ size: 10 }} }} }}
                  }}
                }}
              }});
            }})();
            </script>
            """
            st.components.v1.html(chart_html, height=240)

            st.markdown(
                "<div style='display:grid;grid-template-columns:2.5fr 0.7fr 0.7fr 0.7fr 1fr 2fr;"
                "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff'>Point</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Total</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>✅ Nég.</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🦠 Pos.</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Taux +</div>"
                "<div style='font-size:.72rem;font-weight:800;color:#fff'>Germes détectés</div>"
                "</div>",
                unsafe_allow_html=True)

            for ri, (pt_name, pt_data) in enumerate(sorted_pts):
                t    = pt_data["total"]
                pos  = pt_data["positives"]
                taux = pos / t * 100 if t > 0 else 0
                tc   = "#ef4444" if taux >= 50 else "#f59e0b" if taux > 0 else "#22c55e"
                germes_str = ", ".join(
                    g + "(" + str(n) + "x)"
                    for g, n in sorted(pt_data["germes"].items(), key=lambda x: -x[1])[:3]
                ) or "—"
                row_bg = "#f8fafc" if ri % 2 == 0 else "#ffffff"
                st.markdown(
                    "<div style='display:grid;grid-template-columns:2.5fr 0.7fr 0.7fr 0.7fr 1fr 2fr;"
                    "gap:4px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;"
                    "padding:9px 14px;align-items:center'>"
                    "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>📍 " + pt_name + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>" + str(t) + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#22c55e;text-align:center'>" + str(pt_data["negatives"]) + "</div>"
                    "<div style='text-align:center'><span style='background:" + tc + "22;color:" + tc + ";"
                    "border:1px solid " + tc + "55;border-radius:6px;padding:2px 8px;"
                    "font-size:.8rem;font-weight:700'>" + str(pos) + "</span></div>"
                    "<div style='font-size:.85rem;font-weight:700;color:" + tc + ";text-align:center'>" + str(round(taux, 0)) + "%</div>"
                    "<div style='font-size:.72rem;color:#475569;font-style:italic'>" + germes_str + "</div>"
                    "</div>",
                    unsafe_allow_html=True)

            st.markdown(
                "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                "<div style='font-size:.78rem;color:#94a3b8'>"
                + str(len(pts_stats)) + " point(s) — " + str(total) + " résultats"
                "</div></div>",
                unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════
        # ONGLET 2 : STATS PAR GERME
        # ══════════════════════════════════════════════════════════════════
        with hist_tab_germs:
            from collections import defaultdict
            import json as _json_germs

            germs_stats = defaultdict(lambda: {"count": 0, "ufc_sum": 0, "points": set()})
            total_pos   = 0
            for r in surv:
                germ = r.get("germ_match", "") or ""
                if germ in ("Négatif", "—", "") or int(r.get("ufc", 0)) == 0:
                    continue
                total_pos += 1
                germs_stats[germ]["count"]   += 1
                germs_stats[germ]["ufc_sum"] += int(r.get("ufc", 0))
                germs_stats[germ]["points"].add(r.get("prelevement", "—"))

            if not germs_stats:
                st.info("Aucun germe positif dans l'historique.")
            else:
                sorted_germs = sorted(germs_stats.items(), key=lambda x: -x[1]["count"])
                palette      = ["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e",
                                "#06b6d4","#6366f1","#a855f7","#ec4899","#14b8a6"]
                g_labels = [g[:28] for g, _ in sorted_germs]
                g_counts = [d["count"] for _, d in sorted_germs]
                g_colors = [palette[i % len(palette)] for i in range(len(g_labels))]

                gchart_data = {
                    "labels": g_labels,
                    "counts": g_counts,
                    "colors": g_colors,
                }
                gchart_html = f"""
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
                  const d = {_json_germs.dumps(gchart_data)};
                  new Chart(document.getElementById('germDoughnut'), {{
                    type: 'doughnut',
                    data: {{
                      labels: d.labels,
                      datasets: [{{ data: d.counts, backgroundColor: d.colors, borderWidth: 2 }}]
                    }},
                    options: {{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {{
                        legend: {{
                          position: 'bottom',
                          labels: {{ font: {{ size: 11 }}, boxWidth: 14, padding: 10 }}
                        }}
                      }}
                    }}
                  }});
                }})();
                </script>
                """
                st.components.v1.html(gchart_html, height=360)

                st.markdown(
                    "<div style='display:grid;grid-template-columns:2.5fr 0.7fr 1fr 1fr 2fr;"
                    "gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff'>Germe</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Cas</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>% positifs</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Moy. UFC</div>"
                    "<div style='font-size:.72rem;font-weight:800;color:#fff'>Points touchés</div>"
                    "</div>",
                    unsafe_allow_html=True)

                for gi, (gname, gdata) in enumerate(sorted_germs):
                    pct     = gdata["count"] / total_pos * 100 if total_pos > 0 else 0
                    avg_ufc = gdata["ufc_sum"] / gdata["count"] if gdata["count"] > 0 else 0
                    pts_str = ", ".join(list(gdata["points"])[:3])
                    bar_w   = int(pct)
                    row_bg  = "#f8fafc" if gi % 2 == 0 else "#ffffff"
                    st.markdown(
                        "<div style='display:grid;grid-template-columns:2.5fr 0.7fr 1fr 1fr 2fr;"
                        "gap:4px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;"
                        "padding:9px 14px;align-items:center'>"
                        "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>🦠 " + gname + "</div>"
                        "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>" + str(gdata["count"]) + "</div>"
                        "<div style='text-align:center'>"
                        "<div style='background:#e2e8f0;border-radius:4px;height:8px;margin-bottom:2px'>"
                        "<div style='background:#ef4444;border-radius:4px;height:8px;width:" + str(bar_w) + "%'></div></div>"
                        "<span style='font-size:.75rem;font-weight:700;color:#ef4444'>" + str(round(pct, 1)) + "%</span></div>"
                        "<div style='font-size:.85rem;font-weight:700;color:#475569;text-align:center'>" + str(round(avg_ufc, 0)) + "</div>"
                        "<div style='font-size:.72rem;color:#475569;font-style:italic'>" + pts_str + "</div>"
                        "</div>",
                        unsafe_allow_html=True)

                st.markdown(
                    "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                    "<div style='font-size:.78rem;color:#94a3b8'>"
                    + str(len(germs_stats)) + " germe(s) distinct(s) — " + str(total_pos) + " positifs"
                    "</div></div>",
                    unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════
        # ONGLET 3 : RÉPARTITION PAR PRÉLEVEUR
        # ══════════════════════════════════════════════════════════════════
        with hist_tab_prev:
            from collections import defaultdict

            prev_stats = defaultdict(lambda: {
                "total": 0, "positives": 0, "negatives": 0,
                "alertes": 0, "actions": 0, "germes": defaultdict(int)
            })
            for r in surv:
                op   = (r.get("operateur", "") or "Non renseigné").strip() or "Non renseigné"
                ufc  = int(r.get("ufc", 0))
                germ = r.get("germ_match", "") or ""
                st_r = r.get("status", "ok")
                prev_stats[op]["total"] += 1
                if ufc > 0 and germ not in ("Négatif", "—", ""):
                    prev_stats[op]["positives"] += 1
                    prev_stats[op]["germes"][germ] += 1
                else:
                    prev_stats[op]["negatives"] += 1
                if st_r == "alert":
                    prev_stats[op]["alertes"] += 1
                elif st_r == "action":
                    prev_stats[op]["actions"] += 1

            op_list   = sorted(prev_stats.items(), key=lambda x: -x[1]["total"])
            card_cols = st.columns(min(len(op_list), 4))
            for ci, (op_name, op_data) in enumerate(op_list):
                t        = op_data["total"]
                pos      = op_data["positives"]
                taux_pos = pos / t * 100 if t > 0 else 0
                tc       = "#ef4444" if taux_pos >= 30 else "#f59e0b" if taux_pos > 0 else "#22c55e"
                ini      = op_name[0].upper() if op_name != "Non renseigné" else "?"
                with card_cols[ci % len(card_cols)]:
                    st.markdown(
                        "<div style='background:#fff;border:1.5px solid #e2e8f0;border-radius:14px;"
                        "padding:18px 14px;text-align:center;margin-bottom:12px'>"
                        "<div style='background:#2563eb;color:#fff;border-radius:50%;width:48px;height:48px;"
                        "display:flex;align-items:center;justify-content:center;font-weight:800;"
                        "font-size:1.2rem;margin:0 auto 10px auto'>" + ini + "</div>"
                        "<div style='font-size:.92rem;font-weight:700;color:#0f172a;margin-bottom:6px'>" + op_name + "</div>"
                        "<div style='font-size:2rem;font-weight:900;color:#1e40af'>" + str(t) + "</div>"
                        "<div style='font-size:.68rem;color:#64748b;margin-bottom:10px'>résultat(s)</div>"
                        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px'>"
                        "<div style='background:#f0fdf4;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#22c55e'>" + str(op_data["negatives"]) + "</div>"
                        "<div style='font-size:.6rem;color:#166534'>✅ Nég.</div></div>"
                        "<div style='background:#fef2f2;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#ef4444'>" + str(pos) + "</div>"
                        "<div style='font-size:.6rem;color:#991b1b'>🦠 Pos.</div></div>"
                        "<div style='background:#fffbeb;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#f59e0b'>" + str(op_data["alertes"]) + "</div>"
                        "<div style='font-size:.6rem;color:#92400e'>⚠️ Alerte</div></div>"
                        "<div style='background:#fef2f2;border-radius:8px;padding:6px'>"
                        "<div style='font-size:1rem;font-weight:800;color:#dc2626'>" + str(op_data["actions"]) + "</div>"
                        "<div style='font-size:.6rem;color:#991b1b'>🚨 Action</div></div></div>"
                        "<div style='margin-top:10px;background:" + tc + "22;border:1px solid " + tc + "55;"
                        "border-radius:8px;padding:5px'>"
                        "<div style='font-size:.8rem;font-weight:800;color:" + tc + "'>"
                        + str(round(taux_pos, 0)) + "% positifs</div></div></div>",
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

            for ri, (op_name, op_data) in enumerate(op_list):
                t        = op_data["total"]
                pos      = op_data["positives"]
                taux_pos = pos / t * 100 if t > 0 else 0
                tc       = "#ef4444" if taux_pos >= 30 else "#f59e0b" if taux_pos > 0 else "#22c55e"
                top_g    = ", ".join(
                    g + "(" + str(n) + "x)"
                    for g, n in sorted(op_data["germes"].items(), key=lambda x: -x[1])[:3]
                ) or "—"
                row_bg = "#f8fafc" if ri % 2 == 0 else "#ffffff"
                st.markdown(
                    "<div style='display:grid;grid-template-columns:2fr 0.7fr 0.7fr 0.7fr 0.7fr 0.7fr 2fr;"
                    "gap:4px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;"
                    "padding:9px 14px;align-items:center'>"
                    "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>👤 " + op_name + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>" + str(t) + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#22c55e;text-align:center'>" + str(op_data["negatives"]) + "</div>"
                    "<div style='text-align:center'><span style='background:" + tc + "22;color:" + tc + ";"
                    "border-radius:6px;padding:2px 8px;font-size:.8rem;font-weight:700'>" + str(pos) + "</span></div>"
                    "<div style='font-size:1rem;font-weight:800;color:#f59e0b;text-align:center'>" + str(op_data["alertes"]) + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#ef4444;text-align:center'>" + str(op_data["actions"]) + "</div>"
                    "<div style='font-size:.72rem;color:#475569;font-style:italic'>" + top_g + "</div>"
                    "</div>",
                    unsafe_allow_html=True)

            st.markdown(
                "<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'>"
                "<div style='font-size:.78rem;color:#94a3b8'>"
                + str(len(op_list)) + " préleveur(s)"
                "</div></div>",
                unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════
        # ONGLET 4 : LISTE DES ENTRÉES
        # ══════════════════════════════════════════════════════════════════
        with hist_tab_liste:
            for r in reversed(surv):
                real_i = surv.index(r)
                ic = "🚨" if r["status"] == "action" else "⚠️" if r["status"] == "alert" else "✅"
                with st.expander(
                    ic + " " + r["date"] + " — " + r["prelevement"]
                    + " — " + r["germ_match"] + " — " + str(r["ufc"]) + " UFC/m³"
                ):
                    # ── Mode édition ──────────────────────────────────────
                    if st.session_state.get("edit_surv_idx") == real_i:
                        st.markdown("**✏️ Modifier cette entrée**")
                        e1, e2 = st.columns(2)
                        with e1:
                            new_germ    = st.text_input("Germe",      value=r.get("germ_match",""),  key=f"es_germ_{real_i}")
                            new_ufc     = st.number_input("UFC",       value=int(r.get("ufc",0)), min_value=0, key=f"es_ufc_{real_i}")
                            new_operateur = st.text_input("Opérateur", value=r.get("operateur",""), key=f"es_oper_{real_i}")
                        with e2:
                            new_remarque    = st.text_area("Remarque",    value=r.get("remarque",""),    height=70, key=f"es_rem_{real_i}")
                            new_commentaire = st.text_area("Commentaire", value=r.get("commentaire",""), height=70, key=f"es_com_{real_i}")
                        sb1, sb2 = st.columns(2)
                        with sb1:
                            if st.button("💾 Sauvegarder", key=f"es_save_{real_i}", use_container_width=True, type="primary"):
                                st.session_state.surveillance[real_i]["germ_match"]   = new_germ
                                st.session_state.surveillance[real_i]["germ_saisi"]   = new_germ
                                st.session_state.surveillance[real_i]["ufc"]          = new_ufc
                                st.session_state.surveillance[real_i]["operateur"]    = new_operateur
                                st.session_state.surveillance[real_i]["remarque"]     = new_remarque
                                st.session_state.surveillance[real_i]["commentaire"]  = new_commentaire
                                save_surveillance(st.session_state.surveillance)
                                st.session_state["edit_surv_idx"] = None
                                st.rerun()
                        with sb2:
                            if st.button("✕ Annuler", key=f"es_cancel_{real_i}", use_container_width=True):
                                st.session_state["edit_surv_idx"] = None
                                st.rerun()

                    # ── Mode lecture ──────────────────────────────────────
                    else:
                        c1, c2, c3, c4 = st.columns([3, 3, 3, 1])
                        c1.markdown(
                            "**Germe saisi :** " + r["germ_saisi"]
                            + "\n\n**Correspondance :** " + r["germ_match"]
                            + " (" + str(r["match_score"]) + ")")
                        c2.markdown(
                            "**UFC/m³ :** " + str(r["ufc"])
                            + "\n\n**Seuil alerte :** ≥" + str(r["alert_threshold"])
                            + " | **Seuil action :** ≥" + str(r["action_threshold"]))
                        c3.markdown(
                            "**Opérateur :** " + str(r.get("operateur", "N/A"))
                            + "\n\n**Remarque :** " + str(r.get("remarque", "—")))
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
# Suppression des onglets "Seuils par germe" et "Seuils par classe"
# Criticité du lieu (1–3) dans les Points de prélèvement
# ═══════════════════════════════════════════════════════════════════════════════

elif active == "parametres":
    can_edit = check_access_protege("Paramètres & Seuils")
    if not can_edit:
        st.info("👁️ Mode lecture seule — connectez-vous pour modifier les paramètres.")
    st.markdown("### ⚙️ Paramètres")

    (subtab_mesures, subtab_points,
     subtab_operateurs, subtab_backup, subtab_supabase) = st.tabs([
        "📋 Mesures correctives", "📍 Points de prélèvement",
        "👤 Opérateurs", "💾 Sauvegarde", "☁️ Base de données"
    ])

    # ── Constantes Points ──────────────────────────────────────────────────────
    LOC_CRIT_OPTS = [
        "1 — Limité",
        "2 — Modéré",
        "3 — Important",
        "4 — Maximal",
    ]
    LOC_CRIT_COLORS = {"1": "#22c55e", "2": "#0bb3f5", "3": "#efab44", "4": "#dc2626"}
    LOC_CRIT_LABELS = {"1": "Non critique", "2": "Modéré", "3": "Important", "4": "Maximal"}
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
        type_labels = {"alert": "⚠️ Alerte", "action": "🚨 Action", "both": "⚠️🚨 Alerte & Action"}
        type_colors = {"alert": "#f59e0b", "action": "#ef4444", "both": "#818cf8"}
        scope_r_map = {v: k for k, v in scope_labels.items()}
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
                        new_text = st.text_input("Texte *", value=m.get("text",""), key=f"em_text_{real_idx}")
                    with ec2:
                        cur_scope_lbl = scope_labels.get(m.get("scope","all"), "🌐 Toutes")
                        scope_opts    = list(scope_labels.values())
                        scope_idx     = scope_opts.index(cur_scope_lbl) if cur_scope_lbl in scope_opts else 0
                        new_scope_lbl = st.selectbox("Origine", scope_opts, index=scope_idx, key=f"em_scope_{real_idx}")
                        new_scope = scope_r_map.get(new_scope_lbl, "all")
                    with ec3:
                        cur_risk     = m.get("risk","all")
                        cur_risk_key = (str(cur_risk) if not isinstance(cur_risk, list)
                                        else json.dumps(cur_risk).replace(" ",""))
                        cur_risk_lbl = risk_opts_map.get(cur_risk_key, "🌐 Toutes")
                        risk_opts_list = list(risk_opts_map.values())
                        risk_idx = risk_opts_list.index(cur_risk_lbl) if cur_risk_lbl in risk_opts_list else 0
                        new_risk_lbl = st.selectbox("Criticité", risk_opts_list, index=risk_idx, key=f"em_risk_{real_idx}")
                        new_risk_key = risk_opts_rev.get(new_risk_lbl, "all")
                        new_risk = ("all" if new_risk_key == "all"
                                    else json.loads(new_risk_key) if new_risk_key.startswith("[")
                                    else int(new_risk_key))
                    with ec4:
                        cur_type_lbl = type_labels.get(m.get("type","alert"), "⚠️ Alerte")
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
                                st.session_state.origin_measures     = om
                                st.session_state["_edit_mesure_idx"] = None
                                st.session_state["_mesures_modifiees"] = True
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
                pt_type   = pt.get('type', '—')
                type_icon = "💨" if pt_type == "Air" else "🧴"
                loc_crit  = str(pt.get('location_criticality', 1))
                lc_color  = LOC_CRIT_COLORS.get(loc_crit, "#94a3b8")
                lc_label  = LOC_CRIT_LABELS.get(loc_crit, "—")
                room_cl   = pt.get('room_class', '—') or '—'
                freq      = pt.get('frequency', 1)
                freq_unit = pt.get('frequency_unit', '/ semaine')
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
                        f"🧫 {pt.get('gelose','—')[:12]}</div>"
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

        # ── Formulaire édition ─────────────────────────────────────────────────
        if st.session_state.get('_edit_point') is not None:
            idx = st.session_state._edit_point
            pt  = st.session_state.points[idx]
            st.markdown(f"### ✏️ Modifier — {pt['label']}")

            er1, er2, er3, er_room = st.columns([3, 1.5, 1, 1.5])
            with er1:
                new_label = st.text_input("Nom", value=pt['label'], key="pt_edit_label")
            with er2:
                new_type = st.selectbox(
                    "Type", ["Air", "Surface"],
                    index=["Air","Surface"].index(pt.get('type','Air'))
                    if pt.get('type','Air') in ["Air","Surface"] else 0,
                    key="pt_edit_type")
            with er_room:
                new_room = st.text_input(
                    "Classe ISO / GMP", value=pt.get('room_class', ''),
                    placeholder="Ex: A, B, C, D…", key="pt_edit_room")
            with er3:
                cur_lc  = int(pt.get('location_criticality', 1))
                lc_idx  = max(0, min(cur_lc - 1, 2))
                new_lc_lbl = st.selectbox(
                    "🏷️ Criticité du lieu *", LOC_CRIT_OPTS,
                    index=lc_idx, key="pt_edit_lc")
                new_lc = int(new_lc_lbl[0])
                lc_c   = LOC_CRIT_COLORS[str(new_lc)]
                st.markdown(
                    f"<div style='background:{lc_c}22;border:1px solid {lc_c}55;"
                    f"border-radius:6px;padding:4px 8px;text-align:center;"
                    f"font-size:.72rem;font-weight:700;color:{lc_c};margin-top:2px'>"
                    f"Niveau {new_lc} — {LOC_CRIT_LABELS[str(new_lc)]}</div>",
                    unsafe_allow_html=True)

            er4, er5, er6 = st.columns([2, 1, 2])
            with er4:
                g_opts = (["Gélose de sédimentation","Gélose TSA","Gélose Columbia","Autre"]
                          if new_type == "Air"
                          else ["Gélose contact TSA","Ecouvillonnage","Autre"])
                cur_g = pt.get('gelose', g_opts[0])
                g_idx = g_opts.index(cur_g) if cur_g in g_opts else 0
                new_gel = st.selectbox("Gélose", g_opts, index=g_idx, key="pt_edit_gelose")
            with er5:
                new_freq = st.number_input(
                    "🔁 Fréquence", min_value=1, max_value=31,
                    value=int(pt.get('frequency', 1)), step=1, key="pt_edit_freq")
            with er6:
                cur_unit = pt.get('frequency_unit', '/ semaine')
                unit_idx = PT_FREQ_UNIT_OPTS.index(cur_unit) if cur_unit in PT_FREQ_UNIT_OPTS else 1
                new_fu   = st.selectbox("Unité", PT_FREQ_UNIT_OPTS, index=unit_idx, key="pt_edit_freq_unit")

            
            eb1, eb2 = st.columns(2)
            with eb1:
                if st.button("✅ Enregistrer", key="pt_save_edit"):
                    st.session_state.points[idx] = {
                        "id":                   pt.get('id', f"p{idx+1}"),
                        "label":                new_label,
                        "type":                 new_type,
                        "gelose":               new_gel,
                        "location_criticality": new_lc,
                        "frequency":            new_freq,
                        "frequency_unit":       new_fu,
                        "room_class":           new_room.strip(),
                    }
                    save_points(st.session_state.points, supa=True)
                    st.session_state._edit_point = None
                    st.success("✅ Point mis à jour")
                    st.rerun()
            with eb2:
                if st.button("Annuler", key="pt_cancel_edit"):
                    st.session_state._edit_point = None
                    st.rerun()

        # ── Formulaire ajout ───────────────────────────────────────────────────
        elif can_edit:
            st.markdown("### ➕ Ajouter un point de prélèvement")

            np1, np2, np3, np_room_col = st.columns([3, 1.5, 1.5, 1.5])
            with np1:
                np_label = st.text_input(
                    "Nom *", placeholder="Ex: Salle 3 — Poste A", key="np_label")
            with np2:
                np_type = st.selectbox("Type", ["Air", "Surface"], key="np_type")
            with np_room_col:
                np_room = st.text_input(
                    "Classe ISO / GMP", placeholder="Ex: A, B, C, D…", key="np_room")
            with np3:
                np_lc_lbl = st.selectbox("🏷️ Criticité du lieu *", LOC_CRIT_OPTS, key="np_lc")
                np_lc = int(np_lc_lbl[0])
                lc_c  = LOC_CRIT_COLORS[str(np_lc)]
                st.markdown(
                    f"<div style='background:{lc_c}22;border:1px solid {lc_c}55;"
                    f"border-radius:6px;padding:4px 8px;text-align:center;"
                    f"font-size:.72rem;font-weight:700;color:{lc_c};margin-top:2px'>"
                    f"Niveau {np_lc} — {LOC_CRIT_LABELS[str(np_lc)]}</div>",
                    unsafe_allow_html=True)

            np4, np5, np6 = st.columns([2, 1, 2])
            with np4:
                g_opts_new = (["Gélose de sédimentation","Gélose TSA","Gélose Columbia","Autre"]
                              if np_type == "Air"
                              else ["Gélose contact TSA","Ecouvillonnage","Autre"])
                np_gel = st.selectbox("Gélose", g_opts_new, key="np_gelose")
            with np5:
                np_freq = st.number_input(
                    "🔁 Fréquence", min_value=1, max_value=31, value=1, step=1, key="np_freq")
            with np6:
                np_fu = st.selectbox("Unité", PT_FREQ_UNIT_OPTS, index=0, key="np_freq_unit")


            if st.button("➕ Ajouter", key="np_add"):
                if not np_label.strip():
                    st.error("Le nom est requis")
                else:
                    nid = f"p{len(st.session_state.points)+1}_{int(datetime.now().timestamp())}"
                    st.session_state.points.append({
                        "id":                   nid,
                        "label":                np_label.strip(),
                        "type":                 np_type,
                        "gelose":               np_gel,
                        "location_criticality": np_lc,
                        "frequency":            np_freq,
                        "frequency_unit":       np_fu,
                        "room_class":           np_room.strip(),
                    })
                    save_points(st.session_state.points, supa=True)
                    st.success(f"✅ Point **{np_label}** ajouté")
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
            st.markdown(f"### ✏️ Modifier — {op.get('nom','')}")
            ec1, ec2 = st.columns(2)
            with ec1:
                edit_nom = st.text_input("Nom *", value=op.get('nom',''), key="op_edit_nom")
            with ec2:
                cur_p    = op.get('profession','')
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
        backup_data = export_all_data()
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
                        save_germs(st.session_state.germs, supa=True)
                        save_prelevements(st.session_state.prelevements, supa=True)
                        save_schedules(st.session_state.schedules, supa=True)
                        save_surveillance(st.session_state.surveillance, supa=True)
                        save_points(st.session_state.points, supa=True)
                        save_operators(st.session_state.operators, supa=True)
                        save_pending_identifications(st.session_state.pending_identifications, supa=True)
                        save_origin_measures(st.session_state.origin_measures, supa=True)
                        st.session_state["_mesures_modifiees"] = False
                        st.success("✅ Toutes les données synchronisées !")
            with syn2:
                if can_edit:
                    if st.button("🔃 Recharger depuis Supabase", use_container_width=True):
                        st.session_state.germs                   = load_germs()
                        st.session_state.prelevements            = load_prelevements()
                        st.session_state.schedules               = load_schedules()
                        st.session_state.surveillance            = load_surveillance()
                        st.session_state.points                  = load_points()
                        st.session_state.operators               = load_operators()
                        st.session_state.pending_identifications = load_pending_identifications()
                        st.session_state.origin_measures         = load_origin_measures()
                        st.success("✅ Données rechargées depuis Supabase !")
                        st.rerun()