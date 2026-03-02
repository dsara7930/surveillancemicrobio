import streamlit as st
import json
import csv
import io
import os
import base64
import calendar as cal_module
from datetime import datetime, timedelta, date as date_type
import difflib

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
    "Peau / Muqueuses","Peau / Muqueuse","Sol / Carton / Surface sèche",
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
    {"id":"m050","text":"Vérifier les procédures d'habillage et port des EPI","scope":"Peau / Muqueuses","risk":"all","type":"alert"},
    {"id":"m051","text":"Contrôler la technique de friction hydro-alcoolique","scope":"Peau / Muqueuses","risk":"all","type":"alert"},
    {"id":"m052","text":"Renforcer la formation du personnel (hygiène des mains)","scope":"Peau / Muqueuses","risk":[3,4,5],"type":"action"},
    {"id":"m053","text":"Vérifier l'absence de lésion cutanée chez le personnel","scope":"Peau / Muqueuses","risk":[4,5],"type":"action"},
    {"id":"m054","text":"Enquête sur le personnel intervenant dans la zone","scope":"Peau / Muqueuses","risk":[4,5],"type":"action"},
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
    # ── BACTÉRIES — HUMAINS — PEAU / MUQUEUSES ─────────────────────────────────
    dict(name="Staphylococcus epidermidis",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=3,pathotype="Pathogène opportuniste multirésistant (SCN)",surfa="Sensible",apa="Sensible",notes="Staphylocoque coagulase négatif (SCN)",comment="Principal contaminant cutané des ZAC — biofilm fréquent sur cathéters"),
    dict(name="Staphylococcus aureus",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=4,pathotype="Pathogène primaire — SARM possible",surfa="Sensible",apa="Sensible",notes="SARM si résistant méticilline",comment="Portage nasal fréquent (20-30% population). SARM = problème majeur en milieu hospitalier"),
    dict(name="Staphylococcus spp. (autres SCN)",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes="Staphylocoque coagulase négatif",comment=None),
    dict(name="Corynebacterium spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment="Flore cutanée commensale résiduelle — indicateur d'hygiène des mains insuffisante"),
    dict(name="Cutibacterium acnes",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes="Anaérobie strict",comment="Bactérie anaérobie — indicateur de contamination par les follicules pileux / pores cutanés"),
    dict(name="Micrococcus spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=1,pathotype="Commensal cutané — faible pouvoir pathogène",surfa="Sensible",apa="Sensible",notes=None,comment="Très fréquent dans l'air des ZAC — peu pathogène mais indicateur de contamination humaine"),
    dict(name="Dermabacter hominis",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Brevibacterium spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment="Odeur caractéristique de fromage — indicateur de présence cutanée"),
    dict(name="Rothia spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment="Présent sur peau et muqueuses buccales"),
    dict(name="Aerococcus spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Gemella spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),

    # ── BACTÉRIES — HUMAINS — OROPHARYNX / GOUTTELETTES ────────────────────────
    dict(name="Streptococcus mitis / salivarius / sanguinis / anginosus",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],risk=2,pathotype="Pathogène opportuniste (strepto alpha-hémolytique)",surfa="Sensible",apa="Sensible",notes=None,comment="Indicateur de parole ou d'absence de masque en ZAC"),
    dict(name="Streptococcus pyogenes / agalactiae / pneumoniae",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],risk=3,pathotype="Pathogène primaire (strepto beta-hémolytique)",surfa="Sensible",apa="Sensible",notes=None,comment="Pathogène communautaire — présence en ZAC signe un personnel symptomatique non évincé"),
    dict(name="Neisseria spp.",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],risk=2,pathotype="Commensal oropharyngé",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Haemophilus spp.",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],risk=3,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment="Présence possible en cas d'infection ORL active du personnel"),

    # ── BACTÉRIES — HUMAINS — FLORE FÉCALE ─────────────────────────────────────
    dict(name="Escherichia coli",path=["Germes","Bactéries","Humains","Flore fécale"],risk=4,pathotype="Pathogène opportuniste multirésistant — BLSE/EPC possible",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment="Présence en ZAC = défaut majeur d'hygiène des mains. BLSE/EPC = alerte maximale"),
    dict(name="Klebsiella pneumoniae",path=["Germes","Bactéries","Humains","Flore fécale"],risk=4,pathotype="Pathogène opportuniste multirésistant — BLSE/EPC possible",surfa="Sensible",apa="Sensible",notes=None,comment="Productrice fréquente de BLSE et carbapénémases (KPC, NDM, OXA-48)"),
    dict(name="Klebsiella oxytoca",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Enterococcus faecalis / faecium",path=["Germes","Bactéries","Humains","Flore fécale"],risk=4,pathotype="Pathogène opportuniste — ERV possible",surfa="Sensible",apa="Sensible",notes=None,comment="ERV (Entérocoque Résistant aux Glycopeptides) = risque nosocomial majeur"),
    dict(name="Enterobacter cloacae / aerogenes",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant — céphalosporinase inductible",surfa="Sensible",apa="Sensible",notes=None,comment="Céphalosporinase de bas niveau inductible — attention aux traitements par C3G"),
    dict(name="Citrobacter spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Proteus mirabilis",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment="Uréase positif — indicateur de contamination fécale/urinaire"),
    dict(name="Serratia marcescens",path=["Germes","Bactéries","Humains","Flore fécale"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment="Pigment rouge (prodigiosine) — bactérie redoutée en milieu hospitalier, biofilm persistant"),
    dict(name="Morganella morganii",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Hafnia spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),

    # ── BACTÉRIES — ENVIRONNEMENTAL — HUMIDITÉ ──────────────────────────────────
    dict(name="Pseudomonas aeruginosa",path=["Germes","Bactéries","Environnemental","Humidité"],risk=5,pathotype="Pathogène opportuniste multirésistant — BMR prioritaire",surfa="Risque de résistance (biofilm)",apa="Sensible",notes="Biofilm +++",comment="Pathogène redouté en oncohématologie. Biofilm résistant sur surfaces humides, robinets, éviers. EPC-PA émergent"),
    dict(name="Pseudomonas spp. (autres)",path=["Germes","Bactéries","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Acinetobacter baumannii",path=["Germes","Bactéries","Environnemental","Humidité"],risk=5,pathotype="Pathogène opportuniste multirésistant — BMR prioritaire OMS",surfa="Risque de résistance (biofilm)",apa="Sensible",notes="Résistance extrême",comment="Survie prolongée sur surfaces sèches (jusqu'à plusieurs semaines). Résistance pan-antibiotique émergente"),
    dict(name="Acinetobacter spp. (autres)",path=["Germes","Bactéries","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Stenotrophomonas maltophilia",path=["Germes","Bactéries","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste multirésistant — résistance intrinsèque aux carbapénèmes",surfa="Risque de résistance (biofilm)",apa="Sensible",notes="Résistance carbapénèmes",comment="Résistance intrinsèque aux carbapénèmes et à de nombreux antibiotiques — réservoir eau et surfaces humides"),
    dict(name="Burkholderia cepacia complex",path=["Germes","Bactéries","Environnemental","Humidité"],risk=5,pathotype="Pathogène opportuniste multirésistant — interdit en préparations",surfa="Risque de résistance (biofilm)",apa="Risque de résistance",notes="Résistance intrinsèque ++++",comment="Contaminant de solutions aqueuses et antiseptiques (chlorhexidine). Résistance quasi-totale. Redouté en mucoviscidose"),
    dict(name="Ralstonia spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Risque modéré de résistance",notes=None,comment="Contaminant de l'eau purifiée et des solutions injectables — surveillance critique en URC"),
    dict(name="Chryseobacterium spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=3,pathotype="Pathogène opportuniste",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment="Présent dans l'eau et environnements humides — résistance aux carbapénèmes"),
    dict(name="Sphingomonas spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=3,pathotype="Pathogène opportuniste",surfa="Risque modéré de résistance",apa="Sensible",notes=None,comment="Résistant à la chlorhexidine — contaminant eau purifiée"),
    dict(name="Methylobacterium spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=2,pathotype="Pathogène opportuniste",surfa="Risque modéré de résistance",apa="Sensible",notes="Colonie rose-rouge",comment="Colonie rose-rouge caractéristique — contaminant eau purifiée et condensats"),
    dict(name="Mycobacterium fortuitum / chelonae / abscessus",path=["Germes","Bactéries","Environnemental","Humidité"],risk=5,pathotype="Pathogène opportuniste — mycobactérie à croissance rapide",surfa="Risque de résistance",apa="Risque de résistance (spore)",notes="Mycobactérie à croissance rapide",comment="MCR (Mycobactérie à Croissance Rapide) — résistance aux désinfectants usuels. Réservoir : eau, sols, biofilm. Croissance 3-7 jours sur gélose"),

    # ── BACTÉRIES — ENVIRONNEMENTAL — SOL / CARTON / SURFACE SÈCHE ─────────────
    dict(name="Bacillus subtilis / licheniformis (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=4,pathotype="Pathogène opportuniste — spore résistante",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé",comment="Spores résistantes à la chaleur sèche (160°C / 2h nécessaire), aux UV et à la plupart des désinfectants. Indicateur de dé-cartonnage insuffisant"),
    dict(name="Bacillus cereus (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène primaire — toxines + spores résistantes",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé — toxinogène",comment="Production de toxines thermostables. Spores extrêmement résistantes. Redouté en préparations injectables"),
    dict(name="Bacillus anthracis (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène primaire — agent de bioterrorisme classe A",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé — classe A",comment="Exceptionnel mais à signalement immédiat. Spores stabilisées des mois dans l'environnement"),
    dict(name="Clostridium spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste — spore anaérobie",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé — anaérobie",comment="C. difficile : colite pseudomembraneuse. Spores résistantes à l'alcool — décontamination au chlore uniquement"),
    dict(name="Paenibacillus spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=3,pathotype="Pathogène opportuniste — sporulé",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé",comment="Sol et matières organiques — parfois confondu avec Bacillus à l'identification"),
    dict(name="Brevibacillus spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=3,pathotype="Pathogène opportuniste — sporulé",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé",comment=None),

    # ── CHAMPIGNONS — HUMAIN — PEAU / MUQUEUSE ──────────────────────────────────
    dict(name="Candida albicans",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=4,pathotype="Pathogène opportuniste — levure pathogène primaire",surfa="Sensible",apa="Sensible",notes="Levure — dimorphique",comment="Dimorphique : levure à 37°C, filaments invasifs en conditions de stress. Commensal muqueux — candidémie redoutée en immunodépression"),
    dict(name="Candida auris",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=5,pathotype="Pathogène opportuniste multirésistant — émergent pandémique",surfa="Risque de résistance",apa="Risque de résistance",notes="Levure — multirésistante émergente",comment="Levure émergente résistante aux 3 classes d'antifongiques. Persistance sur surfaces plusieurs semaines. Épidémies hospitalières mondiales"),
    dict(name="Candida glabrata / Nakaseomyces glabrata",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=4,pathotype="Pathogène opportuniste — résistance azolés fréquente",surfa="Sensible",apa="Sensible",notes="Levure — résistance azolés",comment="Résistance intrinsèque réductrice aux azolés. Mortalité élevée en candidémie chez immunodéprimé"),
    dict(name="Candida parapsilosis",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=3,pathotype="Pathogène opportuniste — lié aux mains",surfa="Sensible",apa="Sensible",notes="Levure — transmission manuportée",comment="Transmission manuportée +++ — indicateur direct d'hygiène des mains. Biofilm sur cathéters"),
    dict(name="Candida tropicalis",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes="Levure",comment=None),
    dict(name="Candida krusei / Pichia kudriavzevii",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=4,pathotype="Pathogène opportuniste — résistance intrinsèque fluconazole",surfa="Sensible",apa="Sensible",notes="Levure — résistance fluconazole",comment="Résistance intrinsèque au fluconazole"),
    dict(name="Trichosporon spp.",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=4,pathotype="Pathogène opportuniste — levure filamenteuse",surfa="Risque de résistance",apa="Risque de résistance",notes="Levure filamenteuse",comment="Résistance aux échinocandines — mortalité élevée chez immunodéprimé profond"),
    dict(name="Malassezia spp.",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=2,pathotype="Commensal cutané — lipophile",surfa="Sensible",apa="Sensible",notes="Levure lipophile",comment="Indicateur de contamination cutanée — pousse sur milieu supplémenté en lipides"),

    # ── CHAMPIGNONS — ENVIRONNEMENTAL — AIR ─────────────────────────────────────
    dict(name="Aspergillus fumigatus",path=["Germes","Champignons","Environnemental","Air"],risk=5,pathotype="Pathogène opportuniste — aspergillose invasive mortelle",surfa="Risque de résistance",apa="Risque de résistance",notes="Conidies 2-3 µm — thermophile",comment="Conidies de 2-3 µm — pénétration profonde dans les voies respiratoires. Aspergilllose invasive mortelle chez immunodéprimé. Résistance aux azolés émergente (TR34/L98H)"),
    dict(name="Aspergillus niger",path=["Germes","Champignons","Environnemental","Air"],risk=4,pathotype="Pathogène opportuniste",surfa="Risque de résistance",apa="Risque de résistance",notes="Conidies noires — productrices d'ochratoxine",comment="Conidies noires caractéristiques. Production possible d'ochratoxine A (mycotoxine). Indicateur de matériaux humides/cartons"),
    dict(name="Aspergillus flavus",path=["Germes","Champignons","Environnemental","Air"],risk=5,pathotype="Pathogène opportuniste — producteurd'aflatoxine",surfa="Risque de résistance",apa="Risque de résistance",notes="Conidies vertes — aflatoxine",comment="Producteur d'aflatoxines B1 (cancérogène classe 1). 2ème cause d'aspergillose invasive après A. fumigatus"),
    dict(name="Aspergillus terreus",path=["Germes","Champignons","Environnemental","Air"],risk=5,pathotype="Pathogène opportuniste — résistance amphotéricine B",surfa="Risque de résistance",apa="Risque de résistance",notes="Résistance AmB intrinsèque",comment="Résistance intrinsèque à l'amphotéricine B — options thérapeutiques très limitées"),
    dict(name="Penicillium spp.",path=["Germes","Champignons","Environnemental","Air"],risk=4,pathotype="Pathogène opportuniste",surfa="Risque de résistance",apa="Risque modéré de résistance",notes="Conidies 2-5 µm",comment="Très fréquent dans l'air intérieur — indicateur de qualité de l'air et de l'intégrité des filtres HEPA"),
    dict(name="Cladosporium spp.",path=["Germes","Champignons","Environnemental","Air"],risk=3,pathotype="Pathogène opportuniste",surfa="Risque modéré de résistance",apa="Sensible",notes="Conidies en chaînes",comment="Moisissure aérienne très fréquente — indicateur d'infiltration d'air extérieur non filtré"),
    dict(name="Alternaria spp.",path=["Germes","Champignons","Environnemental","Air"],risk=3,pathotype="Pathogène opportuniste",surfa="Risque modéré de résistance",apa="Sensible",notes="Conidies septées en massue",comment="Moisissure extérieure — indicateur de défaut de filtration ou d'étanchéité"),
    dict(name="Curvularia spp.",path=["Germes","Champignons","Environnemental","Air"],risk=3,pathotype="Pathogène opportuniste",surfa="Risque modéré de résistance",apa="Sensible",notes=None,comment="Moisissure mélanisée (phéohyphomycose) — traitement difficile"),

    # ── CHAMPIGNONS — ENVIRONNEMENTAL — SOL / CARTON / SURFACE SÈCHE ───────────
    dict(name="Fusarium solani / oxysporum",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance",apa="Risque de résistance",notes="Macroconidies falciformes",comment="2ème cause d'infection fongique invasive après Aspergillus. Résistance aux azolés et amphotéricine B. Macroconidies en forme de faucille"),
    dict(name="Mucor / Rhizopus spp.",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène primaire — mucormycose angioinvasive",surfa="Risque de résistance",apa="Risque de résistance",notes="Sporangiospores — angioinvasif",comment="Mucormycose angioinvasive (mortalité > 50%). Spores omniprésentes — cartons et substrats organiques. Résistance aux échinocandines et voriconazole"),
    dict(name="Lichtheimia / Cunninghamella spp.",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste — mucorales",surfa="Risque de résistance",apa="Risque de résistance",notes="Mucorales",comment="Mucorales rares mais mortalité > 70% chez immunodéprimé"),
    dict(name="Scedosporium / Lomentospora spp.",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste — résistance étendue",surfa="Risque de résistance",apa="Risque de résistance",notes="Résistance étendue aux antifongiques",comment="Lomentospora prolificans : résistance pan-antifongique. Pronostic très sombre en immunodépression profonde"),
    dict(name="Trichoderma spp.",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=3,pathotype="Pathogène opportuniste",surfa="Risque modéré de résistance",apa="Sensible",notes="Conidies vertes — parasites d'autres champignons",comment="Contaminant de végétaux et matières organiques — indicateur de mauvais dé-cartonnage"),
    dict(name="Scopulariopsis spp.",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=3,pathotype="Pathogène opportuniste",surfa="Risque de résistance",apa="Risque de résistance",notes=None,comment="Résistance à l'amphotéricine B fréquente"),

    # ── CHAMPIGNONS — ENVIRONNEMENTAL — HUMIDITÉ ────────────────────────────────
    dict(name="Exophiala / Rhinocladiella spp.",path=["Germes","Champignons","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste — champignon noir",surfa="Risque de résistance",apa="Risque de résistance",notes="Champignon mélanisé — chromomycose",comment="Champignons noirs (mélanisés) — résistance naturelle aux UV et désinfectants oxydants. Réservoir : eaux, drains, siphons"),
    dict(name="Cladophialophora spp.",path=["Germes","Champignons","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste — phéohyphomycose",surfa="Risque de résistance",apa="Risque de résistance",notes="Champignon mélanisé",comment="Phéohyphomycose cérébrale possible. Résistance liée à la mélanine pariétale"),
]

# Nom court de référence pour chaque germe (pour la liste sidebar du logigramme)
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
    except Exception:
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

def load_germs():
    """Charge les germes et synchronise TOUJOURS depuis DEFAULT_GERMS.
    
    Logique de fusion :
    - Pour chaque germe de DEFAULT_GERMS → ses champs officiels (path, risk, pathotype,
      surfa, apa, notes, comment) sont TOUJOURS mis à jour depuis le code.
    - Les germes ajoutés par l'utilisateur (non présents dans DEFAULT_GERMS) sont conservés.
    - Les germes de DEFAULT_GERMS absents des données sauvegardées sont réintégrés.
    - L'ordre : germes DEFAULT en premier, puis germes custom.
    """
    defaults_by_name = {d["name"]: d for d in DEFAULT_GERMS}
    saved = []

    raw_json = _supa_get('germs')
    if raw_json:
        try:
            saved = json.loads(raw_json)
        except Exception:
            saved = []

    if not saved and os.path.exists(GERMS_FILE):
        try:
            with open(GERMS_FILE) as f:
                saved = json.load(f)
        except Exception:
            saved = []

    saved_by_name = {g.get("name", ""): g for g in saved}
    merged = []
    synced_count = 0

    # 1. Parcourir DEFAULT_GERMS dans l'ordre — toujours en premier dans la liste
    for dflt in DEFAULT_GERMS:
        name = dflt["name"]
        if name in saved_by_name:
            # Germe existant : on écrase les champs officiels depuis le code
            g = dict(saved_by_name[name])
            old_risk = g.get("risk")
            for field in ["path", "risk", "pathotype", "surfa", "apa", "notes", "comment"]:
                g[field] = dflt[field]
            if old_risk != dflt["risk"]:
                synced_count += 1
        else:
            # Germe absent → on l'ajoute depuis les defaults
            g = dict(dflt)
            synced_count += 1
        merged.append(g)

    # 2. Conserver les germes custom (non présents dans DEFAULT_GERMS) à la fin
    for g in saved:
        name = g.get("name", "")
        if name and name not in defaults_by_name:
            merged.append(dict(g))

    return merged, synced_count

def save_germs(germs):
    js = json.dumps(germs, ensure_ascii=False)
    _supa_upsert('germs', js)
    try:
        with open(GERMS_FILE, "w") as f:
            f.write(js)
    except Exception:
        pass

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
    defaults_by_id = {m["id"]: m for m in DEFAULT_ORIGIN_MEASURES}
    saved = []
    raw_json = _supa_get('measures')
    if raw_json:
        try:
            raw = json.loads(raw_json)
            if isinstance(raw, list):
                saved = raw
        except Exception:
            saved = []
    if not saved and os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            if "measures" in raw and isinstance(raw["measures"], list):
                saved = raw["measures"]
        except Exception:
            saved = []
    saved_ids = {m.get("id") for m in saved}
    merged = [dict(m) for m in saved]
    for dflt in DEFAULT_ORIGIN_MEASURES:
        if dflt["id"] not in saved_ids:
            merged.append(dict(dflt))
    return merged if merged else [dict(m) for m in DEFAULT_ORIGIN_MEASURES]

def save_origin_measures(measures):
    js = json.dumps(measures, ensure_ascii=False)
    _supa_upsert('measures', js)
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
def save_points(d): _save_json_key('points', d, POINTS_FILE)
def load_prelevements(): return _load_json_key('prelevements', PRELEVEMENTS_FILE)
def save_prelevements(d): _save_json_key('prelevements', d, PRELEVEMENTS_FILE)
def load_schedules(): return _load_json_key('schedules', SCHEDULES_FILE)
def save_schedules(d): _save_json_key('schedules', d, SCHEDULES_FILE)
def load_pending_identifications(): return _load_json_key('pending_identifications', PENDING_FILE)
def save_pending_identifications(d): _save_json_key('pending_identifications', d, PENDING_FILE)
def load_archived_samples(): return _load_json_key('archived_samples', ARCHIVED_FILE)
def save_archived_samples(d): _save_json_key('archived_samples', d, ARCHIVED_FILE)
def load_operators(): return _load_json_key('operators', OPERATORS_FILE)
def save_operators(d): _save_json_key('operators', d, OPERATORS_FILE)

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
    if not records:
        return
    js = json.dumps(records, ensure_ascii=False)
    _supa_upsert('surveillance', js)
    try:
        with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
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
    }

def import_all_data(data: dict):
    try:
        required = ["germs", "points", "operators", "prelevements", "schedules", "surveillance"]
        for key in required:
            if key not in data:
                return False, f"Clé manquante dans le fichier : '{key}'"
        st.session_state.germs                   = [dict(g) for g in data["germs"]]
        # Resynchroniser depuis DEFAULT_GERMS après import
        _germs_sync, _ = load_germs()
        # Garder les germes custom de l'import qui ne sont pas dans defaults
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

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "germs" not in st.session_state:
    _germs, _synced = load_germs()
    st.session_state.germs = _germs
    st.session_state.germs_synced_count = _synced
    # Sauvegarder immédiatement après sync
    if _synced > 0:
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

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
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
due_global = [s for s in st.session_state.schedules if s["status"] == "pending" and datetime.fromisoformat(s["due_date"]).date() <= today]
if due_global and not st.session_state.due_alert_shown:
    st.warning(f"🔔 {len(due_global)} lecture(s) due aujourd'hui ou en retard — consultez l'onglet Identification & Surveillance.")
    if st.button("Voir les lectures dues", use_container_width=True):
        st.session_state.active_tab = "surveillance"
        st.session_state.due_alert_shown = True
        st.rerun()
    st.session_state.due_alert_shown = True

st.markdown('<h1 style="font-size:1.3rem;letter-spacing:.1em;text-transform:uppercase;color:#1e40af!important;margin-bottom:0">🦠 MicroSurveillance URC</h1>', unsafe_allow_html=True)
st.caption("Surveillance microbiologique — Unité de Reconstitution des Chimiothérapies")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 : LOGIGRAMME
# ═══════════════════════════════════════════════════════════════════════════════
if active == "logigramme":
    # ── Bannière de synchronisation au démarrage ──────────────────────────────
    _synced = st.session_state.get("germs_synced_count", 0)
    _total_default = len(DEFAULT_GERMS)
    _total_germs = len(st.session_state.germs)
    _custom_count = _total_germs - _total_default if _total_germs > _total_default else 0

    st.markdown(f"""<div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);border:1.5px solid #93c5fd;border-radius:12px;padding:12px 18px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
        <span style="font-size:1.4rem">🦠</span>
        <div>
          <div style="font-weight:800;color:#1e40af;font-size:.88rem">Base de données germes — synchronisée</div>
          <div style="font-size:.7rem;color:#3b82f6;margin-top:2px">
            {_total_default} germes standards · {_custom_count} germe(s) personnalisé(s) · {_total_germs} au total
          </div>
        </div>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <div style="background:#ffffff;border:1px solid #93c5fd;border-radius:8px;padding:6px 12px;text-align:center">
          <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase;font-weight:700">Standard</div>
          <div style="font-size:1.1rem;font-weight:800;color:#1e40af">{_total_default}</div>
        </div>
        <div style="background:#ffffff;border:1px solid #86efac;border-radius:8px;padding:6px 12px;text-align:center">
          <div style="font-size:.6rem;color:#166534;text-transform:uppercase;font-weight:700">Custom</div>
          <div style="font-size:1.1rem;font-weight:800;color:#166534">{_custom_count}</div>
        </div>
        <div style="background:#ffffff;border:1px solid #fcd34d;border-radius:8px;padding:6px 12px;text-align:center">
          <div style="font-size:.6rem;color:#92400e;text-transform:uppercase;font-weight:700">Total</div>
          <div style="font-size:1.1rem;font-weight:800;color:#92400e">{_total_germs}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    if _synced > 0:
        st.success(f"✅ Synchronisation : {_synced} germe(s) mis à jour / ajouté(s) depuis la base de référence du code.")

    col_btn1, col_btn2 = st.columns([1,1])
    with col_btn1:
        if st.button("➕ Ajouter un germe", use_container_width=True):
            st.session_state.show_add = not st.session_state.show_add
            st.session_state.edit_idx = None
    with col_btn2:
        if st.button("💾 Sauvegarder", use_container_width=True, key="save_germs_btn"):
            save_germs(st.session_state.germs)
            st.success("✅ Germes sauvegardés !")

    def germ_form(existing=None, idx=None):
        is_edit = existing is not None
        with st.container():
            st.markdown(f"### {'✏️ Modifier' if is_edit else '➕ Ajouter'} un germe")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_name = st.text_input("Nom du germe *", value=existing["name"] if is_edit else "", placeholder="Ex: Listeria spp.")
                new_famille = st.selectbox("Famille *", ["Bactéries","Champignons"],
                    index=["Bactéries","Champignons"].index(existing["path"][1]) if is_edit else 0)
                new_origine = st.selectbox("Origine *", ["Humains / Humain","Environnemental"],
                    index=0 if (not is_edit or existing["path"][2] in ["Humains","Humain"]) else 1)
            with c2:
                if new_famille == "Bactéries":
                    cats = ["Peau / Muqueuses","Oropharynx / Gouttelettes","Flore fécale"] if "Humain" in new_origine else ["Humidité","Sol / Carton / Surface sèche"]
                else:
                    cats = ["Peau / Muqueuse"] if "Humain" in new_origine else ["Humidité","Sol / Carton / Surface sèche","Air"]
                cur_cat = existing["path"][3] if is_edit and existing["path"][3] in cats else cats[0]
                new_cat = st.selectbox("Catégorie *", cats, index=cats.index(cur_cat) if cur_cat in cats else 0)
                new_pathotype = st.text_input("Type de pathogène", value=existing.get("pathotype","") if is_edit else "")
                new_notes = st.text_area("📝 Notes", value=existing.get("notes","") or "" if is_edit else "", height=55)
                new_comment = st.text_area("💬 Commentaire détaillé", value=existing.get("comment","") or "" if is_edit else "", height=55)
            with c3:
                risk_opts = ["1 — Limité","2 — Modéré","3 — Important","4 — Majeur","5 — Critique"]
                new_risk_raw = st.selectbox("Criticité *", risk_opts, index=(existing["risk"]-1) if is_edit else 1)
                risk_num = int(new_risk_raw[0])
                th = get_thresholds_for_risk(risk_num, st.session_state.thresholds)
                st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin-top:4px">
                    <div style="font-size:.62rem;color:#0f172a;margin-bottom:6px;letter-spacing:.1em">SEUILS AUTO (criticité {risk_num})</div>
                    <div style="display:flex;gap:8px">
                      <div style="flex:1;text-align:center;background:#fffbeb;border:1px solid #fcd34d;border-radius:6px;padding:5px;font-size:.68rem;color:#b45309;font-weight:600">⚠️ Alerte<br>≥ {th['alert']} UFC</div>
                      <div style="flex:1;text-align:center;background:#fef2f2;border:1px solid #fca5a5;border-radius:6px;padding:5px;font-size:.68rem;color:#dc2626;font-weight:600">🚨 Action<br>≥ {th['action']} UFC</div>
                    </div></div>""", unsafe_allow_html=True)
                new_surfa = st.selectbox("Surfa'Safe *",
                    ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (biofilm)","Risque de résistance (spore)"],
                    index=["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (biofilm)","Risque de résistance (spore)"].index(existing["surfa"]) if is_edit and existing.get("surfa") in ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (biofilm)","Risque de résistance (spore)"] else 0)
                new_apa = st.selectbox("APA *",
                    ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (spore)"],
                    index=["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (spore)"].index(existing["apa"]) if is_edit and existing.get("apa") in ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (spore)"] else 0)

            cb1, cb2 = st.columns([1,1])
            with cb1:
                if st.button("✅ " + ("Modifier" if is_edit else "Ajouter"), use_container_width=True, key="form_submit"):
                    if not new_name.strip():
                        st.error("Le nom est obligatoire.")
                        return
                    origine_node = ("Humains" if new_famille=="Bactéries" else "Humain") if "Humain" in new_origine else "Environnemental"
                    new_germ = dict(name=new_name.strip(), path=["Germes",new_famille,origine_node,new_cat],
                        risk=risk_num, pathotype=new_pathotype or "Non défini",
                        surfa=new_surfa, apa=new_apa,
                        notes=new_notes.strip() or None, comment=new_comment.strip() or None)
                    if is_edit:
                        st.session_state.germs[idx] = new_germ
                        st.session_state.edit_idx = None
                    else:
                        if any(g["name"].lower()==new_name.strip().lower() for g in st.session_state.germs):
                            st.error("Ce germe existe déjà.")
                            return
                        st.session_state.germs.append(new_germ)
                        st.session_state.show_add = False
                    save_germs(st.session_state.germs)
                    st.rerun()
            with cb2:
                if st.button("Annuler", use_container_width=True, key="form_cancel"):
                    st.session_state.show_add = False
                    st.session_state.edit_idx = None
                    st.rerun()

    if st.session_state.show_add and st.session_state.edit_idx is None:
        germ_form()
    if st.session_state.edit_idx is not None:
        germ_form(existing=st.session_state.germs[st.session_state.edit_idx], idx=st.session_state.edit_idx)

    st.divider()

    germs_json = json.dumps(st.session_state.germs, ensure_ascii=False)
    default_names_json = json.dumps(sorted(DEFAULT_GERM_NAMES), ensure_ascii=False)
    thresholds_json = json.dumps({str(k): v for k, v in st.session_state.thresholds.items()})

    # ─────────────────────────────────────────────────────────────────────────
    # LOGIGRAMME HTML — BUG CORRIGÉ : cur=c est maintenant DANS le forEach
    # ─────────────────────────────────────────────────────────────────────────
    tree_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f8fafc;color:#1e293b;font-family:'Segoe UI',sans-serif;height:95vh;overflow:hidden}}
.app{{display:flex;height:95vh}}
.tree-wrap{{flex:1;overflow:auto;padding:8px;scrollbar-width:thin;scrollbar-color:#1e293b transparent}}
svg{{min-width:900px;width:100%;height:100%}}
.node rect{{fill:#ffffff;stroke:#e2e8f0;stroke-width:1.5;transition:all 0.2s;cursor:pointer}}
.node.highlighted rect{{stroke-width:2.5;filter:drop-shadow(0 0 4px rgba(0,0,0,.15))}}
.node text{{font-size:11px;fill:#0f172a;pointer-events:none;font-family:'Courier New',monospace}}
.node.highlighted text{{fill:#0f172a;font-weight:600}}
.link{{fill:none;stroke:#e2e8f0;stroke-width:1.5;transition:all 0.3s}}
.link.highlighted{{stroke-width:2.5}}
.right-panel{{width:480px;border-left:2px solid #e2e8f0;display:flex;flex-direction:column;background:#f1f5f9;flex-shrink:0}}
.sbox{{padding:12px 14px;border-bottom:1px solid #e2e8f0}}
.sbox input{{width:100%;background:#ffffff;border:1.5px solid #e2e8f0;border-radius:10px;padding:10px 14px;color:#1e293b;font-size:.95rem;outline:none}}
.sbox input:focus{{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.1)}}
.germ-list{{flex:1;overflow-y:auto;padding:6px;scrollbar-width:thin;scrollbar-color:#cbd5e1 transparent}}
.germ-item{{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;cursor:pointer;transition:background .15s;font-size:.88rem;color:#0f172a;border:1px solid transparent;margin-bottom:3px;line-height:1.35}}
.germ-item:hover{{background:#ffffff;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.germ-item.active{{background:#ffffff;border-color:#2563eb;box-shadow:0 1px 6px rgba(37,99,235,.2)}}
.risk-dot{{width:11px;height:11px;border-radius:50%;flex-shrink:0}}
.germ-count{{font-size:.75rem;color:#64748b;padding:6px 14px;text-align:center;border-bottom:1px solid #e2e8f0;background:#f8fafc;font-weight:600}}
.group-header{{font-size:.68rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#475569;padding:10px 12px 4px 12px;background:#e2e8f0;margin:6px -6px 3px -6px;border-radius:4px}}
.info-panel{{border-top:2px solid #e2e8f0;padding:16px;background:#ffffff;display:none;max-height:560px;overflow-y:auto}}
.info-panel.visible{{display:block}}
.info-name{{font-size:1rem;font-weight:700;font-style:italic;color:#1e293b;margin-bottom:5px}}
.info-path{{font-size:.72rem;color:#2563eb;opacity:.85;margin-bottom:9px;font-family:monospace}}
.info-badge{{display:inline-flex;align-items:center;gap:6px;font-size:.75rem;padding:4px 12px;border-radius:20px;border:1px solid;margin-bottom:11px;font-weight:600}}
.info-lbl{{font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:#475569;margin-bottom:3px;margin-top:8px;font-weight:700}}
.info-val{{font-size:.88rem;color:#1e293b;line-height:1.5}}
.sens{{display:flex;align-items:center;gap:9px;padding:7px 11px;border-radius:8px;border:1px solid #e2e8f0;font-size:.85rem;margin-top:3px}}
.ok{{color:#22c55e;font-weight:700;font-size:1rem}}.warn{{color:#f97316;font-weight:700;font-size:1rem}}.crit{{color:#ef4444;font-weight:700;font-size:1rem}}
.notes-box{{margin-top:8px;padding:9px 12px;border-radius:8px;background:rgba(37,99,235,0.04);border:1px solid rgba(37,99,235,0.18);font-size:.85rem;color:#0f172a;line-height:1.6}}
.threshold-row{{display:flex;gap:8px;margin-top:8px}}
.th-badge{{flex:1;text-align:center;padding:7px 4px;border-radius:8px;font-size:.78rem;font-weight:700}}
.info-name{{font-size:.85rem;font-weight:700;font-style:italic;color:#1e293b;margin-bottom:4px}}
.info-path{{font-size:.6rem;color:#2563eb;opacity:.8;margin-bottom:7px;font-family:monospace}}
.info-badge{{display:inline-flex;align-items:center;gap:5px;font-size:.63rem;padding:2px 9px;border-radius:20px;border:1px solid;margin-bottom:9px}}
.info-lbl{{font-size:.57rem;letter-spacing:.1em;text-transform:uppercase;color:#0f172a;margin-bottom:2px;margin-top:6px}}
.info-val{{font-size:.75rem;color:#1e293b;line-height:1.4}}
.sens{{display:flex;align-items:center;gap:7px;padding:5px 9px;border-radius:6px;border:1px solid #e2e8f0;font-size:.7rem;margin-top:2px}}
.ok{{color:#22c55e;font-weight:700}}.warn{{color:#f97316;font-weight:700}}.crit{{color:#ef4444;font-weight:700}}
.notes-box{{margin-top:6px;padding:6px 9px;border-radius:6px;background:rgba(37,99,235,0.04);border:1px solid rgba(37,99,235,0.15);font-size:.7rem;color:#0f172a;line-height:1.5}}
.threshold-row{{display:flex;gap:6px;margin-top:6px}}
.th-badge{{flex:1;text-align:center;padding:4px;border-radius:6px;font-size:.65rem;font-weight:600}}
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
const RISK_COLORS={{"1":"#22c55e","2":"#84cc16","3":"#f59e0b","4":"#f97316","5":"#ef4444"}};
const RISK_LABELS={{"1":"Limité","2":"Modéré","3":"Important","4":"Majeur","5":"Critique"}};
const THRESHOLDS={thresholds_json};
const DEFAULT_NAMES=new Set({default_names_json});
const NODE_W=190,NODE_H=28,H_GAP=28,V_GAP=10;
const LEVEL_COLS=["#38bdf8","#818cf8","#fb923c","#34d399","#a3e635"];

// ✅ BUG CORRIGÉ : cur=c est maintenant DANS le forEach (portée correcte)
function buildTree(){{
  const root={{name:"Germes",children:[]}};
  GERMS.forEach(g=>{{
    let cur=root;
    g.path.slice(1).forEach(n=>{{
      let c=cur.children&&cur.children.find(x=>x.name===n);
      if(!c){{
        c={{name:n,children:[]}};
        if(!cur.children)cur.children=[];
        cur.children.push(c);
      }}
      cur=c;  // ← déplacé ICI, à l'intérieur du forEach
    }});
  }});
  function clean(n){{
    if(n.children&&n.children.length===0)delete n.children;
    else if(n.children)n.children.forEach(clean);
  }}
  clean(root);
  return root;
}}

function computeLayout(node,depth=0,y=0){{
  node.depth=depth;node.x=depth*(NODE_W+H_GAP);
  if(!node.children||!node.children.length){{node.y=y;return y+NODE_H;}}
  let cy=y;
  node.children.forEach(c=>{{cy=computeLayout(c,depth+1,cy);cy+=V_GAP;}});
  cy-=V_GAP;node.y=(y+cy)/2;return cy+V_GAP;
}}

function allNodes(n){{return[n,...(n.children||[]).flatMap(allNodes)];}}
function allLinks(n){{return(n.children||[]).flatMap(c=>[{{source:n,target:c}},...allLinks(c)]);}}
function buildPaths(n,p=[]){{n.fullPath=[...p,n.name];(n.children||[]).forEach(c=>buildPaths(c,n.fullPath));}}

function renderTree(){{
  const tree=buildTree();
  computeLayout(tree);
  buildPaths(tree);
  const nodes=allNodes(tree),links=allLinks(tree);
  const maxY=Math.max(...nodes.map(n=>n.y))+NODE_H+20;
  const maxX=Math.max(...nodes.map(n=>n.x))+NODE_W+20;
  const svg=document.getElementById('svg');
  svg.innerHTML='';
  svg.setAttribute('viewBox',`0 0 ${{maxX}} ${{maxY}}`);
  svg.setAttribute('height',maxY);
  svg.setAttribute('width',maxX);

  links.forEach(l=>{{
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    const x1=l.source.x+NODE_W,y1=l.source.y+NODE_H/2,x2=l.target.x,y2=l.target.y+NODE_H/2,mx=(x1+x2)/2;
    p.setAttribute('d',`M${{x1}},${{y1}} C${{mx}},${{y1}} ${{mx}},${{y2}} ${{x2}},${{y2}}`);
    p.setAttribute('class','link');
    p.dataset.source=l.source.name;p.dataset.target=l.target.name;
    p.dataset.sourcefull=l.source.fullPath.join('|||');
    p.dataset.targetfull=l.target.fullPath.join('|||');
    svg.appendChild(p);
  }});

  nodes.forEach(node=>{{
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class','node');
    g.setAttribute('transform',`translate(${{node.x}},${{node.y}})`);
    g.dataset.name=node.name;g.dataset.fullpath=node.fullPath.join('|||');
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
  const validNodePaths=new Set();
  for(let i=1;i<=exactPath.length;i++)validNodePaths.add(exactPath.slice(0,i).join('|||'));
  document.querySelectorAll('.node').forEach(n=>{{
    n.classList.toggle('highlighted',validNodePaths.has(n.dataset.fullpath||''));
  }});
  document.querySelectorAll('.link').forEach(l=>{{
    const on=validNodePaths.has(l.dataset.sourcefull||'')&&validNodePaths.has(l.dataset.targetfull||'');
    l.classList.toggle('highlighted',on);
    if(on){{
      const depth=(l.dataset.sourcefull||'').split('|||').length-1;
      l.style.stroke=LEVEL_COLS[depth]||'#38bdf8';
    }}else l.style.stroke='';
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

  // Grouper par catégorie (path[3])
  const groups={{}};
  filtered.forEach(g=>{{
    const cat=(g.path&&g.path[3])||'Autres';
    if(!groups[cat])groups[cat]=[];
    groups[cat].push(g);
  }});

  Object.keys(groups).sort().forEach(cat=>{{
    // En-tête de groupe
    const header=document.createElement('div');
    header.style.cssText='';
    header.className='group-header';
    header.textContent=cat;
    list.appendChild(header);

    groups[cat].forEach(g=>{{
      const div=document.createElement('div');
      div.className='germ-item';div.dataset.name=g.name;
      const col=RISK_COLORS[g.risk];
      const isCustom=!DEFAULT_NAMES.has(g.name);
      const hasSporule=g.notes&&g.notes.toLowerCase().includes('sporul');
      const hasResistance=g.surfa&&g.surfa.toLowerCase().includes('risque');
      let badges='';
      if(hasSporule)badges+='<span style="font-size:.5rem;background:#fef3c7;color:#92400e;border-radius:3px;padding:0 4px;margin-left:3px">🧬</span>';
      if(hasResistance)badges+='<span style="font-size:.5rem;background:#fee2e2;color:#991b1b;border-radius:3px;padding:0 4px;margin-left:2px">⚠</span>';
      if(isCustom)badges+='<span style="font-size:.5rem;background:rgba(56,189,248,0.15);color:#2563eb;border-radius:3px;padding:0 4px;margin-left:2px">★</span>';
      div.innerHTML=`<span class="risk-dot" style="background:${{col}}"></span><span style="flex:1;line-height:1.3">${{g.name}}${{badges}}</span><span style="font-size:.65rem;color:${{col}};font-weight:800;flex-shrink:0">${{g.risk}}</span>`;
      div.addEventListener('click',()=>selectGerm(g));
      list.appendChild(div);
    }});
  }});
}}

function filterList(){{renderList(document.getElementById('sbox').value);}}

function selectGerm(g){{
  selectedPath=g.path;
  highlightPath(g.path);
  document.querySelectorAll('.germ-item').forEach(el=>el.classList.toggle('active',el.dataset.name===g.name));
  showInfo(g);
}}

function showInfo(g){{
  const panel=document.getElementById('infoPanel');
  panel.classList.add('visible');
  const col=RISK_COLORS[g.risk];
  const th=THRESHOLDS[g.risk]||{{alert:25,action:40}};
  function sens(v){{
    if(!v)return['ok','✓'];
    const l=v.toLowerCase();
    if(l.includes('modéré'))return['warn','⚠'];
    if(l.includes('risque'))return['crit','✗'];
    return['ok','✓'];
  }}
  const[sc,si]=sens(g.surfa),[ac,ai]=sens(g.apa);
  const nh=g.notes?`<div class="info-lbl">📝 Notes</div><div class="notes-box">${{g.notes}}</div>`:'';
  const ch=g.comment?`<div class="info-lbl" style="color:#fb923c;margin-top:8px">💬 Commentaire</div><div class="notes-box" style="color:#fb923c;background:rgba(251,146,60,0.06);border-color:rgba(251,146,60,.35);font-style:italic">${{g.comment}}</div>`:'';
  panel.innerHTML=`<div class="info-name">${{g.name}}</div>
    <div class="info-path">${{g.path.join(' › ')}}</div>
    <div class="info-badge" style="color:${{col}};background:${{col}}22;border-color:${{col}}55">
      <span style="width:7px;height:7px;border-radius:50%;background:${{col}};display:inline-block"></span>
      Niveau ${{g.risk}} — ${{RISK_LABELS[g.risk]}}
    </div>
    <div class="info-lbl">Pathogénicité</div><div class="info-val">${{g.pathotype}}</div>
    <div class="info-lbl">Surfa'Safe</div><div class="sens"><span class="${{sc}}">${{si}}</span>${{g.surfa}}</div>
    <div class="info-lbl">Acide Peracétique</div><div class="sens"><span class="${{ac}}">${{ai}}</span>${{g.apa}}</div>
    <div class="info-lbl">Seuils UFC/m³ (criticité ${{g.risk}})</div>
    <div class="threshold-row">
      <div class="th-badge" style="background:rgba(245,158,11,.1);color:#f59e0b;border:1px solid #f59e0b44">⚠️ Alerte ≥ ${{th.alert}}</div>
      <div class="th-badge" style="background:rgba(239,68,68,.1);color:#ef4444;border:1px solid #ef444444">🚨 Action ≥ ${{th.action}}</div>
    </div>
    ${{nh}}${{ch}}`;
}}

renderTree();
renderList();
</script></body></html>"""

    st.components.v1.html(tree_html, height=1200, scrolling=False)

    st.markdown("### ✏️ Gérer les germes")
    search_edit = st.text_input("Filtrer", placeholder="Rechercher un germe...", label_visibility="collapsed")
    filtered = [g for g in st.session_state.germs if search_edit.lower() in g["name"].lower()] if search_edit else st.session_state.germs
    for g in filtered:
        real_idx = st.session_state.germs.index(g)
        col_n, col_r, col_e, col_d = st.columns([4,1,1,1])
        with col_n:
            c = RISK_COLORS[g["risk"]]
            st.markdown(f'<span style="color:{c};font-size:.75rem">●</span> <span style="font-size:.8rem;font-style:italic">{g["name"]}</span>', unsafe_allow_html=True)
        with col_r:
            st.markdown(f'<span style="font-size:.72rem;color:{RISK_COLORS[g["risk"]]}">Nv.{g["risk"]}</span>', unsafe_allow_html=True)
        with col_e:
            if st.button("✏️", key=f"edit_{real_idx}"):
                st.session_state.edit_idx = real_idx
                st.session_state.show_add = False
                st.rerun()
        with col_d:
            if st.button("🗑️", key=f"del_{real_idx}"):
                st.session_state.germs.pop(real_idx)
                save_germs(st.session_state.germs)
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 : SURVEILLANCE
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "surveillance":
    st.markdown("### 🔍 Identification & Surveillance microbiologique")

    with st.expander("🧪 Nouveau prélèvement", expanded=False):
        if not st.session_state.points:
            st.info("Aucun point de prélèvement défini — allez dans **Paramètres → Points de prélèvement** pour en créer.")
        else:
            p_col1, p_col2, p_col3 = st.columns([3,2,1])
            with p_col1:
                point_labels = [f"{pt['label']} — {pt.get('type','?')} — {pt.get('room_class','?')}" for pt in st.session_state.points]
                sel_idx = st.selectbox("Point de prélèvement", list(range(len(point_labels))), format_func=lambda i: point_labels[i], key="new_prelev_point")
                selected_point = st.session_state.points[sel_idx]
                pt_type = selected_point.get('type', '—')
                pt_class = selected_point.get('room_class', '—')
                pt_gelose = selected_point.get('gelose', '—')
                type_icon = "💨" if pt_type == "Air" else "🧴"
                st.markdown(f"""<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:12px;margin-top:4px">
                  <div style="font-size:.75rem;font-weight:700;color:#0369a1;margin-bottom:8px">{type_icon} Détails du point sélectionné</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                    <div style="background:#ffffff;border-radius:6px;padding:8px;border:1px solid #e0f2fe"><div style="font-size:.6rem;color:#64748b;text-transform:uppercase">Type</div><div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:2px">{pt_type}</div></div>
                    <div style="background:#ffffff;border-radius:6px;padding:8px;border:1px solid #e0f2fe"><div style="font-size:.6rem;color:#64748b;text-transform:uppercase">Classe</div><div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:2px">{pt_class}</div></div>
                    <div style="background:#ffffff;border-radius:6px;padding:8px;border:1px solid #e0f2fe;grid-column:1/-1"><div style="font-size:.6rem;color:#64748b;text-transform:uppercase">Gélose</div><div style="font-size:.85rem;font-weight:700;color:#1d4ed8;margin-top:2px">🧫 {pt_gelose}</div></div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with p_col2:
                oper_list = [o['nom'] + (' — ' + o.get('profession','') if o.get('profession') else '') for o in st.session_state.operators]
                if oper_list:
                    oper_sel = st.selectbox("Opérateur", ["— Sélectionner —"] + oper_list, key="new_prelev_oper_sel")
                    p_oper = oper_sel if oper_sel != "— Sélectionner —" else ""
                else:
                    st.info("Aucun opérateur — ajoutez-en dans Paramètres")
                    p_oper = st.text_input("Opérateur (manuel)", placeholder="Nom", key="new_prelev_oper_manual")
                p_date = st.date_input("Date prélèvement", value=datetime.today(), key="new_prelev_date")
                j2_date_calc = next_working_day_offset(p_date, 2)
                j7_date_calc = next_working_day_offset(p_date, 5)
                st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:8px;margin-top:6px;font-size:.7rem;color:#166534">
                  📅 J2 (2 jours ouvrés) : <strong>{j2_date_calc.strftime('%d/%m/%Y')}</strong><br>
                  📅 J7 (5 jours ouvrés) : <strong>{j7_date_calc.strftime('%d/%m/%Y')}</strong>
                </div>""", unsafe_allow_html=True)
            with p_col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Enregistrer\nprélèvement", use_container_width=True, key="save_prelev"):
                    pid = f"s{len(st.session_state.prelevements)+1}_{int(datetime.now().timestamp())}"
                    sample = {
                        "id": pid,
                        "label": selected_point['label'],
                        "type": selected_point.get('type'),
                        "gelose": selected_point.get('gelose', '—'),
                        "room_class": selected_point.get('room_class'),
                        "operateur": p_oper,
                        "date": str(p_date),
                        "archived": False
                    }
                    st.session_state.prelevements.append(sample)
                    save_prelevements(st.session_state.prelevements)
                    st.session_state.schedules.append({
                        "id": f"sch_{pid}_J2",
                        "sample_id": pid,
                        "label": sample['label'],
                        "due_date": j2_date_calc.isoformat(),
                        "when": "J2",
                        "status": "pending"
                    })
                    st.session_state.schedules.append({
                        "id": f"sch_{pid}_J7",
                        "sample_id": pid,
                        "label": sample['label'],
                        "due_date": j7_date_calc.isoformat(),
                        "when": "J7",
                        "status": "pending"
                    })
                    save_schedules(st.session_state.schedules)
                    st.success(f"✅ **{sample['label']}** enregistré ! J2 → {j2_date_calc.strftime('%d/%m/%Y')} | J7 → {j7_date_calc.strftime('%d/%m/%Y')} (jours ouvrés)")
                    st.rerun()

    st.divider()
    st.markdown("#### 📅 Lectures en attente")

    pending_schedules = [s for s in st.session_state.schedules if s["status"] == "pending"]
    overdue = [s for s in pending_schedules if datetime.fromisoformat(s["due_date"]).date() <= today]
    upcoming = [s for s in pending_schedules if datetime.fromisoformat(s["due_date"]).date() > today]

    if overdue:
        st.markdown(f'<div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;padding:12px 16px;margin-bottom:12px"><span style="color:#dc2626;font-weight:700">🔔 {len(overdue)} lecture(s) due(s) — à traiter dès que possible</span></div>', unsafe_allow_html=True)
    if upcoming:
        st.markdown(f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:10px 16px;margin-bottom:12px"><span style="color:#16a34a;font-size:.8rem">📆 {len(upcoming)} lecture(s) à venir</span></div>', unsafe_allow_html=True)
    if not pending_schedules:
        st.info("Aucune lecture planifiée — tous les prélèvements sont à jour.")

    def should_show_schedule(s, all_schedules):
        if s['when'] == 'J2': return True
        if s['when'] == 'J7':
            j2 = next((x for x in all_schedules if x['sample_id'] == s['sample_id'] and x['when'] == 'J2'), None)
            return j2 is None or j2['status'] == 'done'
        return True

    all_to_show = [s for s in (overdue + upcoming) if should_show_schedule(s, st.session_state.schedules)]
    for s in all_to_show:
        sched_date = datetime.fromisoformat(s["due_date"]).date()
        is_overdue = sched_date <= today
        border_col = "#ef4444" if is_overdue else "#3b82f6"
        bg_col = "#fef2f2" if is_overdue else "#eff6ff"
        badge_col = "#dc2626" if is_overdue else "#1d4ed8"
        status_txt = "EN RETARD" if is_overdue else f"dans {(sched_date - today).days}j"
        sample = next((p for p in st.session_state.prelevements if p['id'] == s['sample_id']), None)
        pt_type = sample.get('type', '?') if sample else '?'
        pt_gelose = sample.get('gelose', '?') if sample else '?'
        pt_class = sample.get('room_class', '?') if sample else '?'
        pt_oper = sample.get('operateur', '?') if sample else '?'

        with st.container():
            st.markdown(f"""<div style="background:{bg_col};border:1.5px solid {border_col};border-radius:10px;padding:14px 16px;margin-bottom:8px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                <div><span style="font-weight:700;font-size:.9rem;color:#0f172a">{s['label']}</span>
                  <span style="background:{border_col};color:#fff;font-size:.6rem;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">{s['when']}</span>
                  <span style="color:{badge_col};font-size:.65rem;font-weight:600;margin-left:6px">{status_txt}</span>
                </div>
                <span style="font-size:.75rem;color:#475569">📅 {s['due_date'][:10]}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px">
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0"><div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Type</div><div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_type}</div></div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0"><div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Gélose</div><div style="font-size:.75rem;font-weight:600;color:#1d4ed8">🧫 {pt_gelose}</div></div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0"><div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Classe</div><div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_class}</div></div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0"><div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Opérateur</div><div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_oper}</div></div>
              </div>
            </div>""", unsafe_allow_html=True)
            btn_cols = st.columns([3, 1])
            with btn_cols[0]:
                if st.button(f"🔬 Traiter cette lecture ({s['when']})", key=f"proc_{s['id']}", use_container_width=True):
                    st.session_state.current_process = s['id']
                    st.rerun()
            with btn_cols[1]:
                if st.button("🗑️ Supprimer", key=f"del_sch_{s['id']}", use_container_width=True):
                    sample_id = s.get('sample_id')
                    st.session_state.schedules = [x for x in st.session_state.schedules if x['sample_id'] != sample_id]
                    save_schedules(st.session_state.schedules)
                    st.session_state.prelevements = [p for p in st.session_state.prelevements if p['id'] != sample_id]
                    save_prelevements(st.session_state.prelevements)
                    st.success("Prélèvement et lectures associées supprimés.")
                    st.rerun()

    if st.session_state.current_process:
        proc_id = st.session_state.current_process
        proc = next((x for x in st.session_state.schedules if x['id'] == proc_id), None)
        if proc:
            sample = next((p for p in st.session_state.prelevements if p['id'] == proc['sample_id']), None)
            pt_type = sample.get('type', '?') if sample else '?'
            pt_gelose = sample.get('gelose', '?') if sample else '?'
            pt_class = sample.get('room_class', '?') if sample else '?'
            pt_oper = sample.get('operateur', '?') if sample else '?'
            pt_date = sample.get('date', '?') if sample else '?'

            st.markdown("---")
            st.markdown(f"""<div style="background:#f8fafc;border:2px solid #2563eb;border-radius:12px;padding:16px;margin-bottom:16px">
              <div style="font-size:1rem;font-weight:700;color:#1e40af;margin-bottom:12px">🔬 Traitement lecture — <span style="font-style:italic">{proc['label']}</span>
                <span style="background:#2563eb;color:#fff;font-size:.65rem;font-weight:700;padding:3px 10px;border-radius:10px;margin-left:8px">{proc['when']}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px">
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center"><div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Type</div><div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{'💨' if pt_type=='Air' else '🧴'} {pt_type}</div></div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center"><div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Gélose</div><div style="font-size:.85rem;font-weight:700;color:#1d4ed8;margin-top:3px">🧫 {pt_gelose}</div></div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center"><div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Classe</div><div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_class}</div></div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center"><div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Opérateur</div><div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_oper}</div></div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center"><div style="font-size:.6rem;color:#1e40af;text-transform:uppercase">Date prélèv.</div><div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_date}</div></div>
              </div>
            </div>""", unsafe_allow_html=True)

            lc1, lc2 = st.columns([2, 2])
            with lc1:
                res = st.radio("Résultat", ["✅ Négatif (0 colonie)", "🔴 Positif (colonies détectées)"], index=0, key=f"res_{proc_id}")
            with lc2:
                if "Positif" in res:
                    ncol = st.number_input("Nombre de colonies (UFC)", min_value=1, value=1, key=f"ncol_{proc_id}")
                else:
                    ncol = 0

            btn_col1, btn_col2 = st.columns([2, 2])
            with btn_col1:
                if st.button("✅ Valider la lecture", use_container_width=True, key=f"submit_proc_{proc_id}"):
                    proc['status'] = 'done'
                    save_schedules(st.session_state.schedules)
                    if "Négatif" in res:
                        j7_sch = next((x for x in st.session_state.schedules if x['sample_id'] == proc['sample_id'] and x['when'] == 'J7' and x['status'] == 'pending'), None)
                        if proc['when'] == 'J7' or (proc['when'] == 'J2' and not j7_sch):
                            if sample:
                                sample['archived'] = True
                                st.session_state.archived_samples.append(sample)
                                save_archived_samples(st.session_state.archived_samples)
                                save_prelevements(st.session_state.prelevements)
                            st.success("✅ Lecture négative — prélèvement archivé.")
                        else:
                            st.success(f"✅ Lecture J2 négative — en attente J7 ({j7_sch['due_date'][:10] if j7_sch else '?'}).")
                        hist = {"date": str(today), "prelevement": proc['label'], "sample_id": proc.get('sample_id',''),
                            "germ_saisi": "", "germ_match": "Négatif", "match_score": "—",
                            "ufc": 0, "risk": 0, "alert_threshold": "—", "action_threshold": "—",
                            "status": "ok", "operateur": pt_oper, "remarque": f"Lecture {proc['when']} négative"}
                        st.session_state.surveillance.append(hist)
                        save_surveillance(st.session_state.surveillance)
                    else:
                        entry = {"sample_id": proc['sample_id'], "label": proc['label'], "when": proc['when'], "colonies": int(ncol), "date": str(today), "status": "pending"}
                        st.session_state.pending_identifications.append(entry)
                        save_pending_identifications(st.session_state.pending_identifications)
                        st.success(f"🔴 {proc['when']} positive ({ncol} UFC) — identification requise ci-dessous.")
                    st.session_state.current_process = None
                    st.rerun()
            with btn_col2:
                if st.button("↩️ Annuler / Retour", use_container_width=True, key=f"cancel_proc_{proc_id}"):
                    st.session_state.current_process = None
                    st.rerun()

    pending_ids = [p for p in st.session_state.pending_identifications if p.get('status') == 'pending']
    if pending_ids:
        st.markdown("---")
        st.markdown("#### 🔴 Identifications en attente")
        for pi_idx, pi in enumerate(pending_ids):
            real_pi_idx = st.session_state.pending_identifications.index(pi)
            sample = next((p for p in st.session_state.prelevements if p['id'] == pi['sample_id']), None)
            pt_gelose = sample.get('gelose', '?') if sample else '?'
            pt_oper = sample.get('operateur', '?') if sample else '?'
            with st.expander(f"🔴 {pi['label']} — {pi['when']} — {pi['colonies']} UFC — {pi['date']}", expanded=True):
                id_col1, id_col2 = st.columns([3, 1])
                with id_col1:
                    germ_input = st.text_input("Germe identifié *", placeholder="Ex: Pseudomonas aeruginosa", key=f"germ_id_{real_pi_idx}")
                    remarque = st.text_area("Remarque", height=60, key=f"rem_id_{real_pi_idx}")
                with id_col2:
                    date_id = st.date_input("Date identification", value=datetime.today(), key=f"date_id_{real_pi_idx}")
                idc1, idc2, idc3 = st.columns([2, 2, 1])
                with idc1:
                    if st.button("🔍 Analyser & Enregistrer", use_container_width=True, key=f"submit_id_{real_pi_idx}"):
                        if germ_input.strip():
                            match, score = find_germ_match(germ_input, st.session_state.germs)
                            if match and score > 0.4:
                                risk = match["risk"]
                                th = get_thresholds_for_risk(risk, st.session_state.thresholds)
                                ufc = pi['colonies']
                                status = "action" if ufc >= th["action"] else "alert" if ufc >= th["alert"] else "ok"
                                record = {"date": str(date_id), "prelevement": pi['label'], "sample_id": pi.get('sample_id',''),
                                    "germ_saisi": germ_input, "germ_match": match["name"], "match_score": f"{int(score*100)}%",
                                    "ufc": ufc, "risk": risk, "alert_threshold": th["alert"], "action_threshold": th["action"],
                                    "status": status, "operateur": pt_oper, "remarque": remarque}
                                st.session_state.surveillance.append(record)
                                save_surveillance(st.session_state.surveillance)
                                st.session_state.pending_identifications[real_pi_idx]['status'] = 'done'
                                save_pending_identifications(st.session_state.pending_identifications)
                                status_txt = "🚨 Action requise" if status == "action" else "⚠️ Alerte" if status == "alert" else "✅ Conforme"
                                st.success(f"✅ {match['name']} ({int(score*100)}%) — {ufc} UFC — {status_txt}")
                                st.rerun()
                            else:
                                st.warning(f"⚠️ Aucune correspondance pour **{germ_input}**.")
                        else:
                            st.error("Le nom du germe est obligatoire.")
                with idc2:
                    if st.button("↩️ Corriger la lecture", use_container_width=True, key=f"cancel_id_{real_pi_idx}"):
                        matching_sch = next((x for x in st.session_state.schedules if x['sample_id'] == pi['sample_id'] and x['when'] == pi['when'] and x['status'] == 'done'), None)
                        if matching_sch:
                            matching_sch['status'] = 'pending'
                            save_schedules(st.session_state.schedules)
                        st.session_state.pending_identifications.pop(real_pi_idx)
                        save_pending_identifications(st.session_state.pending_identifications)
                        st.rerun()
                with idc3:
                    if st.button("🗑️", use_container_width=True, key=f"del_id_{real_pi_idx}"):
                        st.session_state.pending_identifications.pop(real_pi_idx)
                        save_pending_identifications(st.session_state.pending_identifications)
                        st.rerun()

    if st.session_state.surveillance:
        st.markdown("---")
        st.markdown("### 📋 Derniers résultats")
        for r in list(reversed(st.session_state.surveillance[-10:])):
            sc = "#ef4444" if r["status"]=="action" else "#f59e0b" if r["status"]=="alert" else "#22c55e"
            ic = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
            ufc_display = f"{r['ufc']} UFC" if r.get('ufc') else "—"
            st.markdown(f"""<div style="background:#f8fafc;border-left:3px solid {sc};border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;gap:12px">
              <span style="font-size:1.1rem">{ic}</span>
              <div style="flex:1"><div style="font-size:.78rem;color:#1e293b;font-weight:600">{r['prelevement']} — <span style="font-style:italic">{r['germ_match']}</span></div>
              <div style="font-size:.68rem;color:#0f172a">{r['date']} · {ufc_display} · {r.get('operateur') or 'N/A'}</div></div>
              <span style="font-size:.7rem;color:{sc};font-weight:700">{ufc_display}</span>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 : PLANNING
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "planning":
    st.markdown("### 📅 Planning des prélèvements & lectures")

    _today_dt = datetime.today().date()
    MOIS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    JOURS_FR_COURT = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]
    JOURS_FR = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]

    plan_tab_view, plan_tab_charge, plan_tab_export = st.tabs(["📅 Calendrier", "📊 Charge hebdo", "📥 Export Excel"])

    with plan_tab_view:
        nav_c1, nav_c2, nav_c3, nav_c4, nav_c5 = st.columns([1, 1, 3, 1, 1])
        with nav_c1:
            if st.button("◀◀", use_container_width=True, key="cal_prev_year"):
                st.session_state.cal_year -= 1; st.rerun()
        with nav_c2:
            if st.button("◀", use_container_width=True, key="cal_prev_month"):
                if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
                else: st.session_state.cal_month -= 1
                st.rerun()
        with nav_c3:
            st.markdown("<div style='text-align:center;background:linear-gradient(135deg,#1e40af,#2563eb);border-radius:10px;padding:10px;color:#fff;font-weight:800;font-size:1.1rem'>📅 " + MOIS_FR[st.session_state.cal_month] + " " + str(st.session_state.cal_year) + "</div>", unsafe_allow_html=True)
        with nav_c4:
            if st.button("▶", use_container_width=True, key="cal_next_month"):
                if st.session_state.cal_month == 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
                else: st.session_state.cal_month += 1
                st.rerun()
        with nav_c5:
            if st.button("▶▶", use_container_width=True, key="cal_next_year"):
                st.session_state.cal_year += 1; st.rerun()

        if st.button("📍 Aujourd'hui", key="cal_today"):
            st.session_state.cal_year = _today_dt.year; st.session_state.cal_month = _today_dt.month; st.rerun()

        cal_year = st.session_state.cal_year
        cal_month = st.session_state.cal_month
        holidays_this_month = get_holidays_cached(cal_year)

        # ── Générer les prélèvements prévisionnels depuis les points ─────────
        def get_working_days_of_month(year, month):
            import calendar as _cal
            _, n = _cal.monthrange(year, month)
            hols = get_holidays_cached(year)
            return [date_type(year, month, d) for d in range(1, n+1)
                    if date_type(year, month, d).weekday() < 5 and date_type(year, month, d) not in hols]

        def generate_planned_days(pt, year, month):
            freq = int(pt.get('frequency', 1))
            unit = pt.get('frequency_unit', '/ semaine')
            wdays = get_working_days_of_month(year, month)
            if not wdays: return []
            if unit == '/ jour':
                return wdays
            elif unit == '/ semaine':
                from collections import defaultdict
                weeks = defaultdict(list)
                for d in wdays:
                    weeks[d.isocalendar()[1]].append(d)
                result = []
                for wk_days in weeks.values():
                    step = max(1, len(wk_days) // max(1, freq))
                    result.extend([wk_days[i] for i in range(0, len(wk_days), step)][:freq])
                return sorted(set(result))
            elif unit == '/ mois':
                step = max(1, len(wdays) // max(1, freq))
                return [wdays[i] for i in range(0, len(wdays), step)][:freq]
            return []

        planned_j0 = {}
        planned_j2 = {}
        planned_j7 = {}
        for pt in st.session_state.points:
            for d0 in generate_planned_days(pt, cal_year, cal_month):
                planned_j0.setdefault(d0, []).append(pt['label'])
                planned_j2[next_working_day_offset(d0, 2)] = planned_j2.get(next_working_day_offset(d0, 2), 0) + 1
                planned_j7[next_working_day_offset(d0, 5)] = planned_j7.get(next_working_day_offset(d0, 5), 0) + 1

        def get_day_activities(d):
            j0r = [p for p in st.session_state.prelevements if p.get('date') and datetime.fromisoformat(p['date']).date()==d and not p.get('archived',False)]
            j2r = [s for s in st.session_state.schedules if s['when']=='J2' and datetime.fromisoformat(s['due_date']).date()==d]
            j7r = [s for s in st.session_state.schedules if s['when']=='J7' and datetime.fromisoformat(s['due_date']).date()==d]
            return j0r, j2r, j7r, planned_j0.get(d,[]), planned_j2.get(d,0), planned_j7.get(d,0)

        cal_weeks = cal_module.monthcalendar(cal_year, cal_month)

        hdr = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px;margin-bottom:3px">'
        for i, jour in enumerate(JOURS_FR_COURT):
            cc = "#ef4444" if i >= 5 else "#1e40af"
            hdr += '<div style="text-align:center;padding:8px 4px;font-weight:800;font-size:.78rem;color:' + cc + ';border-radius:6px;background:#eff6ff">' + jour + '</div>'
        hdr += '</div>'

        legend = (
            '<div style="display:flex;gap:8px;margin:10px 0;flex-wrap:wrap;background:#f8fafc;border-radius:8px;padding:10px">'
            '<div style="display:flex;align-items:center;gap:4px"><div style="width:11px;height:11px;border-radius:3px;background:#7c3aed"></div><span style="font-size:.68rem;color:#1e293b">Prélèv. réel</span></div>'
            '<div style="display:flex;align-items:center;gap:4px"><div style="width:11px;height:11px;border-radius:3px;background:#d97706"></div><span style="font-size:.68rem;color:#1e293b">J2 réel</span></div>'
            '<div style="display:flex;align-items:center;gap:4px"><div style="width:11px;height:11px;border-radius:3px;background:#0369a1"></div><span style="font-size:.68rem;color:#1e293b">J7 réel</span></div>'
            '<div style="display:flex;align-items:center;gap:4px"><div style="width:11px;height:11px;border-radius:3px;border:2px dashed #7c3aed"></div><span style="font-size:.68rem;color:#7c3aed">Prélèv. prévu</span></div>'
            '<div style="display:flex;align-items:center;gap:4px"><div style="width:11px;height:11px;border-radius:3px;border:2px dashed #d97706"></div><span style="font-size:.68rem;color:#d97706">J2 prévu</span></div>'
            '<div style="display:flex;align-items:center;gap:4px"><div style="width:11px;height:11px;border-radius:3px;border:2px dashed #0369a1"></div><span style="font-size:.68rem;color:#0369a1">J7 prévu</span></div>'
            '</div>'
        )

        # ── Grille calendrier mensuelle ───────────────────────────────────────
        # État pour le jour sélectionné (détail au clic)
        if 'cal_selected_day' not in st.session_state:
            st.session_state.cal_selected_day = None

        grid = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px">'
        day_has_content = {}
        for week in cal_weeks:
            for day_idx, day_num in enumerate(week):
                is_weekend = day_idx >= 5
                if day_num == 0:
                    grid += '<div style="background:#f8fafc;border-radius:8px;min-height:90px"></div>'
                    continue
                d = date_type(cal_year, cal_month, day_num)
                is_today = d == _today_dt
                is_holiday = d in holidays_this_month
                is_non_working = is_weekend or is_holiday
                is_past = d < _today_dt
                j0r, j2r, j7r, j0p, j2p_count, j7p_count = get_day_activities(d)

                bg = "#dbeafe" if is_today else ("#f1f5f9" if is_non_working else "#ffffff")
                bdr = "2px solid #2563eb" if is_today else "1px solid #e2e8f0"
                dnc = "#2563eb" if is_today else ("#94a3b8" if is_non_working else "#0f172a")
                op = "0.65" if is_past and not is_today else "1"

                b = ""
                # Réels J0 (plein violet)
                if j0r:
                    b += '<div style="background:#7c3aed;color:#fff;border-radius:4px;padding:1px 5px;font-size:.6rem;font-weight:700;margin-top:2px">🧪 ' + str(len(j0r)) + ' J0</div>'
                # J2 réels depuis schedules
                for s in j2r:
                    done = s['status'] == 'done'
                    late = not done and d < _today_dt
                    sc = "#22c55e" if done else ("#ef4444" if late else "#d97706")
                    si = "✅" if done else ("⚠️" if late else "📖")
                    b += '<div style="background:' + sc + ';color:#fff;border-radius:4px;padding:1px 5px;font-size:.6rem;font-weight:700;margin-top:2px">' + si + ' J2</div>'
                # J7 réels depuis schedules
                for s in j7r:
                    done = s['status'] == 'done'
                    late = not done and d < _today_dt
                    sc = "#22c55e" if done else ("#ef4444" if late else "#0369a1")
                    si = "✅" if done else ("⚠️" if late else "📗")
                    b += '<div style="background:' + sc + ';color:#fff;border-radius:4px;padding:1px 5px;font-size:.6rem;font-weight:700;margin-top:2px">' + si + ' J7</div>'
                # Prévisionnels (tiretés) si pas de réel
                if not j0r and j0p and not is_non_working:
                    b += '<div style="border:1.5px dashed #7c3aed;color:#7c3aed;border-radius:4px;padding:1px 5px;font-size:.6rem;font-weight:700;margin-top:2px">🧪 ' + str(len(j0p)) + ' prévu</div>'
                if not j2r and j2p_count and not is_non_working:
                    b += '<div style="border:1.5px dashed #d97706;color:#d97706;border-radius:4px;padding:1px 5px;font-size:.6rem;font-weight:700;margin-top:2px">📖 ' + str(j2p_count) + ' J2</div>'
                if not j7r and j7p_count and not is_non_working:
                    b += '<div style="border:1.5px dashed #0369a1;color:#0369a1;border-radius:4px;padding:1px 5px;font-size:.6rem;font-weight:700;margin-top:2px">📗 ' + str(j7p_count) + ' J7</div>'

                hlbl = ""
                if is_holiday and not is_weekend:
                    hlbl = '<div style="font-size:.5rem;color:#ef4444;font-weight:600;margin-top:2px">Férié</div>'
                elif is_weekend:
                    hlbl = '<div style="font-size:.5rem;color:#94a3b8;margin-top:2px">Repos</div>'

                has_content = bool(j0r or j2r or j7r or (j0p and not is_non_working))
                day_has_content[d] = {"j0r": j0r, "j2r": j2r, "j7r": j7r, "j0p": j0p}

                grid += '<div style="background:' + bg + ';border:' + bdr + ';border-radius:8px;padding:6px;min-height:90px;opacity:' + op + ';display:flex;flex-direction:column"><div style="font-weight:800;font-size:.9rem;color:' + dnc + ';margin-bottom:2px">' + str(day_num) + '</div>' + hlbl + b + '</div>'
        grid += '</div>'

        st.markdown(legend, unsafe_allow_html=True)
        st.markdown(hdr + grid, unsafe_allow_html=True)

        # ── Détail du jour sélectionné ────────────────────────────────────────
        st.markdown("---")
        st.markdown("**💡 Détail par jour** — sélectionnez un jour ci-dessous pour voir le détail des prélèvements :")
        import calendar as _cal2
        _, n_days = _cal2.monthrange(cal_year, cal_month)
        working_days_month = [date_type(cal_year, cal_month, d) for d in range(1, n_days+1)
                              if date_type(cal_year, cal_month, d).weekday() < 5
                              and date_type(cal_year, cal_month, d) not in holidays_this_month]
        if working_days_month:
            day_options = {d.strftime('%A %d/%m') + (" 📍" if day_has_content.get(d) else ""): d for d in working_days_month}
            sel_day_label = st.selectbox("Jour à détailler", list(day_options.keys()), label_visibility="collapsed", key="cal_day_detail_sel")
            sel_day = day_options[sel_day_label]
            data = day_has_content.get(sel_day, {"j0r": [], "j2r": [], "j7r": [], "j0p": []})
            j0r_d = data["j0r"]; j2r_d = data["j2r"]; j7r_d = data["j7r"]; j0p_d = data["j0p"]

            if not j0r_d and not j2r_d and not j7r_d and not j0p_d:
                st.info("Aucune activité ce jour.")
            else:
                det_cols = st.columns(3)
                with det_cols[0]:
                    st.markdown("**🧪 Prélèvements J0 réels**")
                    if j0r_d:
                        for p in j0r_d:
                            st.markdown(
                                "<div style='background:#faf5ff;border:1px solid #e9d5ff;border-left:3px solid #7c3aed;border-radius:8px;padding:8px 12px;margin-bottom:4px'>"
                                "<div style='font-weight:700;color:#0f172a;font-size:.82rem'>" + p['label'] + "</div>"
                                "<div style='font-size:.7rem;color:#475569;margin-top:3px'>Type : " + p.get('type','—') + " · Classe : " + p.get('room_class','—') + "</div>"
                                "<div style='font-size:.7rem;color:#475569'>Opérateur : " + (p.get('operateur','—') or '—') + "</div>"
                                "<div style='font-size:.7rem;color:#475569'>Gélose : " + p.get('gelose','—') + "</div>"
                                "</div>",
                                unsafe_allow_html=True
                            )
                    elif j0p_d:
                        for lbl in j0p_d:
                            st.markdown(
                                "<div style='border:1.5px dashed #7c3aed;border-radius:8px;padding:8px 12px;margin-bottom:4px'>"
                                "<div style='font-weight:600;color:#7c3aed;font-size:.82rem'>📋 " + lbl + " (prévu)</div>"
                                "</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown("<span style='font-size:.75rem;color:#94a3b8'>Aucun prélèvement</span>", unsafe_allow_html=True)

                with det_cols[1]:
                    st.markdown("**📖 Lectures J2**")
                    if j2r_d:
                        for s in j2r_d:
                            samp = next((p for p in st.session_state.prelevements if p['id']==s['sample_id']), None)
                            done = s['status']=='done'; late = not done and sel_day < _today_dt
                            st_col = "#22c55e" if done else ("#ef4444" if late else "#d97706")
                            st_txt = "✅ Faite" if done else ("⚠️ En retard" if late else "⏳ À faire")
                            st.markdown(
                                "<div style='background:#fffbeb;border:1px solid #fde68a;border-left:3px solid #d97706;border-radius:8px;padding:8px 12px;margin-bottom:4px'>"
                                "<div style='font-weight:700;color:#0f172a;font-size:.82rem'>" + s['label'] + "</div>"
                                "<div style='font-size:.7rem;color:#475569;margin-top:3px'>J0 : " + (samp.get('date','—') if samp else '—') + "</div>"
                                "<div style='font-size:.7rem;color:#475569'>Opérateur : " + (samp.get('operateur','—') if samp else '—') + "</div>"
                                "<div style='font-size:.72rem;font-weight:700;color:" + st_col + ";margin-top:3px'>" + st_txt + "</div>"
                                "</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown("<span style='font-size:.75rem;color:#94a3b8'>Aucune lecture J2</span>", unsafe_allow_html=True)

                with det_cols[2]:
                    st.markdown("**📗 Lectures J7**")
                    if j7r_d:
                        for s in j7r_d:
                            samp = next((p for p in st.session_state.prelevements if p['id']==s['sample_id']), None)
                            done = s['status']=='done'; late = not done and sel_day < _today_dt
                            st_col = "#22c55e" if done else ("#ef4444" if late else "#0369a1")
                            st_txt = "✅ Faite" if done else ("⚠️ En retard" if late else "⏳ À faire")
                            st.markdown(
                                "<div style='background:#eff6ff;border:1px solid #bae6fd;border-left:3px solid #0369a1;border-radius:8px;padding:8px 12px;margin-bottom:4px'>"
                                "<div style='font-weight:700;color:#0f172a;font-size:.82rem'>" + s['label'] + "</div>"
                                "<div style='font-size:.7rem;color:#475569;margin-top:3px'>J0 : " + (samp.get('date','—') if samp else '—') + "</div>"
                                "<div style='font-size:.7rem;color:#475569'>Opérateur : " + (samp.get('operateur','—') if samp else '—') + "</div>"
                                "<div style='font-size:.72rem;font-weight:700;color:" + st_col + ";margin-top:3px'>" + st_txt + "</div>"
                                "</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown("<span style='font-size:.75rem;color:#94a3b8'>Aucune lecture J7</span>", unsafe_allow_html=True)
    # ── Fonctions utilitaires semaine ────────────────────────────────────────
    def get_week_start(d):
        return d - timedelta(days=d.weekday())
    def fmt_week(ws):
        we = ws + timedelta(days=6)
        return ws.strftime('%d/%m') + ' – ' + we.strftime('%d/%m/%Y')

    with plan_tab_charge:
        st.markdown("### 📊 Charge hebdomadaire — Préleveurs & Points")

        # ── Sélection de la semaine ────────────────────────────────────────────
        ch_ws_set = set()
        ch_ws_set.add(get_week_start(_today_dt))
        for _p in st.session_state.prelevements:
            try: ch_ws_set.add(get_week_start(datetime.fromisoformat(_p["date"]).date()))
            except: pass
        for _i in range(1, 9):
            ch_ws_set.add(get_week_start(_today_dt) + timedelta(weeks=_i))
        ch_week_starts = sorted(ch_ws_set)
        ch_week_labels = [fmt_week(ws) for ws in ch_week_starts]
        ch_cur_idx = 0
        for _i, _ws in enumerate(ch_week_starts):
            if _ws <= _today_dt < _ws + timedelta(days=7):
                ch_cur_idx = _i
                break

        csel_col1, csel_col2, csel_col3 = st.columns([3, 1, 0.6])
        with csel_col1:
            ch_sel_label = st.selectbox("Semaine", ch_week_labels, index=ch_cur_idx, label_visibility="collapsed", key="ch_week_sel")
        with csel_col2:
            nb_preleveurs = st.number_input("Nb préleveurs", min_value=1, max_value=20, value=max(1, len(st.session_state.operators)), step=1, key="ch_nb_prev",
                help="Nombre de préleveurs disponibles cette semaine")
        with csel_col3:
            st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
            if st.button("🔄", use_container_width=True, key="ch_refresh", help="Recalculer la charge"):
                st.rerun()

        ch_sel_ws = ch_week_starts[ch_week_labels.index(ch_sel_label)]
        ch_sel_we = ch_sel_ws + timedelta(days=6)
        ch_holidays = get_holidays_cached(ch_sel_ws.year)

        # ── Calcul des jours ouvrés de la semaine ─────────────────────────────
        ch_working_days = [ch_sel_ws + timedelta(days=i) for i in range(5)
                           if (ch_sel_ws + timedelta(days=i)) not in ch_holidays]
        nb_jours = len(ch_working_days)

        # ── Prélèvements planifiés sur la semaine ─────────────────────────────
        ch_j0 = [p for p in st.session_state.prelevements
                 if p.get('date') and ch_sel_ws <= datetime.fromisoformat(p['date']).date() <= ch_sel_we
                 and not p.get('archived', False)]
        ch_j2 = [s for s in st.session_state.schedules
                 if s['when'] == 'J2' and ch_sel_ws <= datetime.fromisoformat(s['due_date']).date() <= ch_sel_we]
        ch_j7 = [s for s in st.session_state.schedules
                 if s['when'] == 'J7' and ch_sel_ws <= datetime.fromisoformat(s['due_date']).date() <= ch_sel_we]

        total_actes = len(ch_j0) + len(ch_j2) + len(ch_j7)
        actes_par_jour = total_actes / nb_jours if nb_jours > 0 else 0
        actes_par_preleveur = total_actes / nb_preleveurs if nb_preleveurs > 0 else 0

        # ── Bandeau semaine ───────────────────────────────────────────────────
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1e40af,#2563eb);border-radius:14px;padding:16px 22px;margin:10px 0 18px 0;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
          <div style="color:#fff">
            <div style="font-size:1.05rem;font-weight:800">📅 {ch_sel_label}</div>
            <div style="font-size:.82rem;color:#bfdbfe;margin-top:3px">{nb_jours} jour(s) ouvré(s) · {nb_preleveurs} préleveur(s) disponible(s)</div>
          </div>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <div style="background:rgba(255,255,255,.15);border-radius:10px;padding:10px 18px;text-align:center;min-width:80px">
              <div style="font-size:.72rem;color:#bfdbfe;font-weight:700;text-transform:uppercase">Actes total</div>
              <div style="font-size:2rem;font-weight:900;color:#fff">{total_actes}</div>
            </div>
            <div style="background:rgba(255,255,255,.15);border-radius:10px;padding:10px 18px;text-align:center;min-width:80px">
              <div style="font-size:.72rem;color:#bfdbfe;font-weight:700;text-transform:uppercase">/ jour</div>
              <div style="font-size:2rem;font-weight:900;color:#fff">{actes_par_jour:.1f}</div>
            </div>
            <div style="background:rgba(255,255,255,.15);border-radius:10px;padding:10px 18px;text-align:center;min-width:80px">
              <div style="font-size:.72rem;color:#bfdbfe;font-weight:700;text-transform:uppercase">/ préleveur</div>
              <div style="font-size:2rem;font-weight:900;color:#fff">{actes_par_preleveur:.1f}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Métriques synthèse ────────────────────────────────────────────────
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("👤 Préleveurs", nb_preleveurs)
        m2.metric("📍 Points actifs", len(st.session_state.points))
        m3.metric("🧪 Prélèv. J0", len(ch_j0))
        m4.metric("📖 Lectures J2", len(ch_j2))
        m5.metric("📗 Lectures J7", len(ch_j7))

        st.divider()

        # ── Points de prélèvement — charge par point ─────────────────────────
        st.markdown("#### 📍 Points de prélèvement — charge par point")
        if not st.session_state.points:
            st.info("Aucun point de prélèvement défini. Créez-en dans **Paramètres → Points de prélèvement**.")
        else:
            risk_colors_ch = {"1":"#22c55e","2":"#84cc16","3":"#f59e0b","4":"#f97316","5":"#ef4444"}
            st.markdown("<div style='display:grid;grid-template-columns:2.2fr 1fr 1fr 0.7fr 1fr 1fr 1.5fr;gap:6px;background:#1e40af;border-radius:10px 10px 0 0;padding:12px 16px'><div style='font-size:.78rem;font-weight:800;color:#fff'>Point</div><div style='font-size:.78rem;font-weight:800;color:#fff;text-align:center'>Type</div><div style='font-size:.78rem;font-weight:800;color:#fff;text-align:center'>Classe</div><div style='font-size:.78rem;font-weight:800;color:#fff;text-align:center'>Risque</div><div style='font-size:.78rem;font-weight:800;color:#fff;text-align:center'>Prévu/sem.</div><div style='font-size:.78rem;font-weight:800;color:#fff;text-align:center'>Réalisé</div><div style='font-size:.78rem;font-weight:800;color:#fff;text-align:center'>Statut</div></div>", unsafe_allow_html=True)

            total_prevu = 0
            total_realise = 0

            for pt_i, pt in enumerate(st.session_state.points):
                # Fréquence auto depuis le point
                pt_freq = pt.get('frequency', None)
                pt_freq_unit = pt.get('frequency_unit', '/ semaine')
                if pt_freq is not None:
                    if pt_freq_unit == '/ jour':
                        prevu = int(pt_freq) * nb_jours
                    elif pt_freq_unit == '/ mois':
                        prevu = max(1, round(pt_freq / 4))
                    else:
                        prevu = int(pt_freq)
                else:
                    prevu = 2 if pt.get('type') == 'Air' else 1

                realise = sum(1 for p in ch_j0 if p.get('label') == pt['label'])

                if realise >= prevu:
                    st_bg="#f0fdf4";st_border="#86efac";st_txt="#166534";st_icon="✅";st_label="Complet"
                elif realise > 0:
                    pct=int(realise/prevu*100)
                    st_bg="#fffbeb";st_border="#fcd34d";st_txt="#92400e";st_icon="⏳";st_label=str(pct)+"%"
                else:
                    st_bg="#fef2f2";st_border="#fca5a5";st_txt="#991b1b";st_icon="🔴";st_label="0/"+str(prevu)

                total_prevu += prevu
                total_realise += realise

                type_icon = "💨" if pt.get('type') == 'Air' else "🧴"
                row_bg = "#f8fafc" if pt_i % 2 == 0 else "#ffffff"
                risk_val = str(pt.get('risk_level','—'))
                risk_col = risk_colors_ch.get(risk_val, "#94a3b8")

                row = (
                    "<div style='display:grid;grid-template-columns:2.2fr 1fr 1fr 0.7fr 1fr 1fr 1.5fr;gap:6px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;padding:11px 16px;align-items:center'>"
                    "<div style='font-size:.9rem;font-weight:700;color:#0f172a'>" + type_icon + " " + pt['label'] + "</div>"
                    "<div style='font-size:.82rem;color:#475569;text-align:center'>" + pt.get('type','—') + "</div>"
                    "<div style='font-size:.82rem;color:#475569;text-align:center'>" + pt.get('room_class','—') + "</div>"
                    "<div style='text-align:center'><span style='background:" + risk_col + "22;color:" + risk_col + ";border:1px solid " + risk_col + "55;border-radius:6px;padding:2px 6px;font-size:.72rem;font-weight:700'>Nv." + risk_val + "</span></div>"
                    "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>" + str(prevu) + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#0f172a;text-align:center'>" + str(realise) + "</div>"
                    "<div style='background:" + st_bg + ";border:1px solid " + st_border + ";border-radius:8px;padding:4px 10px;text-align:center;font-size:.82rem;font-weight:700;color:" + st_txt + "'>" + st_icon + " " + st_label + "</div>"
                    "</div>"
                )
                st.markdown(row, unsafe_allow_html=True)

            taux = int(total_realise / total_prevu * 100) if total_prevu > 0 else 0
            taux_col = "#22c55e" if taux >= 100 else "#f59e0b" if taux >= 50 else "#ef4444"
            st.markdown("<div style='display:grid;grid-template-columns:2.2fr 1fr 1fr 0.7fr 1fr 1fr 1.5fr;gap:6px;background:#1e293b;border-radius:0 0 10px 10px;padding:12px 16px;align-items:center'><div style='font-size:.9rem;font-weight:800;color:#fff'>TOTAL SEMAINE</div><div></div><div></div><div></div><div style='font-size:1.1rem;font-weight:900;color:#93c5fd;text-align:center'>" + str(total_prevu) + "</div><div style='font-size:1.1rem;font-weight:900;color:#86efac;text-align:center'>" + str(total_realise) + "</div><div style='background:rgba(255,255,255,.1);border-radius:8px;padding:5px 10px;text-align:center;font-size:.9rem;font-weight:800;color:" + taux_col + "'>" + str(taux) + "% réalisé</div></div>", unsafe_allow_html=True)

            st.divider()

            # ── Charge par jour ouvré — répartition automatique ───────────────
            st.markdown("#### 📅 Planning automatique par jour ouvré")

            if nb_jours == 0:
                st.warning("Aucun jour ouvré cette semaine.")
            else:
                # ── Algorithme de répartition ─────────────────────────────────
                # 1. Construire la liste de toutes les tâches à planifier
                taches = []
                for pt in st.session_state.points:
                    pt_freq = pt.get('frequency', 1)
                    pt_freq_unit = pt.get('frequency_unit', '/ semaine')
                    if pt_freq_unit == '/ jour':
                        nb_fois = int(pt_freq) * nb_jours
                    elif pt_freq_unit == '/ mois':
                        nb_fois = max(1, round(pt_freq / 4))
                    else:
                        nb_fois = int(pt_freq)
                    risk = int(pt.get('risk_level', 1))
                    for _ in range(nb_fois):
                        taches.append({
                            "label": pt['label'],
                            "type": pt.get('type','—'),
                            "risk": risk,
                        })
                # 2. Trier par risque décroissant (points critiques prioritaires)
                taches.sort(key=lambda x: -x['risk'])

                # 3. Répartir sur les jours ouvrés en round-robin équilibré
                #    en tenant compte du nb de préleveurs par jour
                capacite_par_jour = nb_preleveurs  # tâches simultanées par jour
                planning = {wd: [] for wd in ch_working_days}
                # Compteur de charge par jour
                charge_jour = {wd: 0 for wd in ch_working_days}

                for tache in taches:
                    # Choisir le jour avec le moins de charge
                    jour_cible = min(ch_working_days, key=lambda d: charge_jour[d])
                    planning[jour_cible].append(tache)
                    charge_jour[jour_cible] += 1

                # 4. Calculer stats réelles sur la semaine
                real_par_jour = {}
                for wd in ch_working_days:
                    dj0 = sum(1 for p in ch_j0 if datetime.fromisoformat(p['date']).date() == wd)
                    dj2 = sum(1 for s in ch_j2 if datetime.fromisoformat(s['due_date']).date() == wd)
                    dj7 = sum(1 for s in ch_j7 if datetime.fromisoformat(s['due_date']).date() == wd)
                    real_par_jour[wd] = {"j0": dj0, "j2": dj2, "j7": dj7, "total": dj0+dj2+dj7}

                risk_colors_plan = {"1":"#22c55e","2":"#84cc16","3":"#f59e0b","4":"#f97316","5":"#ef4444"}
                JOURS_FR2 = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi"]
                day_cols = st.columns(nb_jours)

                for di, wd in enumerate(ch_working_days):
                    taches_j = planning[wd]
                    prevu_j = len(taches_j)
                    real_j = real_par_jour[wd]
                    realise_j = real_j["j0"]
                    is_today_d = wd == _today_dt

                    bg_d = "#eff6ff" if is_today_d else "#f8fafc"
                    border_d = "2px solid #2563eb" if is_today_d else "1.5px solid #e2e8f0"
                    jour_col = "#1e40af" if is_today_d else "#475569"

                    # Badge statut jour
                    if realise_j >= prevu_j and prevu_j > 0:
                        stat_bg="#f0fdf4";stat_col="#166534";stat_lbl="✅ Complet"
                    elif realise_j > 0:
                        stat_bg="#fffbeb";stat_col="#92400e";stat_lbl="⏳ "+str(realise_j)+"/"+str(prevu_j)
                    elif prevu_j > 0:
                        stat_bg="#fef2f2";stat_col="#991b1b";stat_lbl="🔴 0/"+str(prevu_j)
                    else:
                        stat_bg="#f8fafc";stat_col="#94a3b8";stat_lbl="— Libre"

                    # Liste des points du jour (max 5 affichés)
                    pts_html = ""
                    for ti, t in enumerate(taches_j[:6]):
                        rc = risk_colors_plan.get(str(t['risk']), "#94a3b8")
                        icon = "💨" if t['type']=="Air" else "🧴"
                        label_short = t['label'][:22] + ("…" if len(t['label'])>22 else "")
                        pts_html += (
                            "<div style='background:#fff;border:1px solid " + rc + "44;border-left:3px solid " + rc + ";border-radius:6px;padding:3px 7px;font-size:.62rem;font-weight:600;color:#0f172a;text-align:left;margin-bottom:2px'>"
                            + icon + " " + label_short +
                            "</div>"
                        )
                    if len(taches_j) > 6:
                        pts_html += "<div style='font-size:.6rem;color:#94a3b8;font-style:italic'>+" + str(len(taches_j)-6) + " autres</div>"
                    if not taches_j:
                        pts_html = "<div style='font-size:.7rem;color:#94a3b8;font-style:italic;margin-top:4px'>Rien à planifier</div>"

                    # Lectures J2/J7 réelles
                    lectures_html = ""
                    if real_j["j2"]: lectures_html += "<div style='background:#d9770622;color:#d97706;border-radius:6px;padding:2px 6px;font-size:.65rem;font-weight:700;margin-top:3px'>📖 " + str(real_j["j2"]) + " lecture J2</div>"
                    if real_j["j7"]: lectures_html += "<div style='background:#0369a122;color:#0369a1;border-radius:6px;padding:2px 6px;font-size:.65rem;font-weight:700;margin-top:3px'>📗 " + str(real_j["j7"]) + " lecture J7</div>"

                    card = (
                        "<div style='background:" + bg_d + ";border:" + border_d + ";border-radius:12px;padding:12px;'>"
                        "<div style='font-size:.82rem;font-weight:800;color:" + jour_col + ";text-align:center'>" + JOURS_FR2[wd.weekday()] + "</div>"
                        "<div style='font-size:.72rem;color:#94a3b8;text-align:center;margin-bottom:8px'>" + wd.strftime('%d/%m') + "</div>"
                        "<div style='background:" + stat_bg + ";border-radius:8px;padding:5px;text-align:center;font-size:.75rem;font-weight:800;color:" + stat_col + ";margin-bottom:8px'>" + stat_lbl + "</div>"
                        "<div style='font-size:.68rem;color:#475569;font-weight:700;margin-bottom:4px;text-align:center'>📋 " + str(prevu_j) + " prélèv. prévus · " + str(nb_preleveurs) + " préleveur(s)</div>"
                        + pts_html + lectures_html +
                        "</div>"
                    )
                    with day_cols[di]:
                        st.markdown(card, unsafe_allow_html=True)

                # ── Résumé de répartition ─────────────────────────────────────
                st.divider()
                charge_min = min(charge_jour.values()) if charge_jour else 0
                charge_max = max(charge_jour.values()) if charge_jour else 0
                charge_moy = sum(charge_jour.values()) / nb_jours if nb_jours > 0 else 0
                par_prev = charge_moy / nb_preleveurs if nb_preleveurs > 0 else 0
                st.markdown(
                    "<div style='background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:12px;padding:14px 20px;display:flex;gap:20px;flex-wrap:wrap;align-items:center'>"
                    "<div style='color:#fff'><div style='font-size:.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase'>Charge min/jour</div><div style='font-size:1.4rem;font-weight:900;color:#93c5fd'>" + str(charge_min) + "</div></div>"
                    "<div style='color:#fff'><div style='font-size:.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase'>Charge max/jour</div><div style='font-size:1.4rem;font-weight:900;color:#fbbf24'>" + str(charge_max) + "</div></div>"
                    "<div style='color:#fff'><div style='font-size:.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase'>Moy./jour</div><div style='font-size:1.4rem;font-weight:900;color:#86efac'>" + str(round(charge_moy,1)) + "</div></div>"
                    "<div style='color:#fff'><div style='font-size:.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase'>Par préleveur/jour</div><div style='font-size:1.4rem;font-weight:900;color:#f9a8d4'>" + str(round(par_prev,1)) + "</div></div>"
                    "<div style='flex:1;text-align:right;font-size:.72rem;color:#475569'>⬆️ Points à risque élevé planifiés en priorité</div>"
                    "</div>",
                    unsafe_allow_html=True
                )

    with plan_tab_export:
        st.markdown("#### 📥 Exporter le planning en Excel")
        exp_scope = st.selectbox("Période", ["Mois en cours", "4 semaines à venir", "Tout le planning"], key="exp_scope")
        exp_oper_filter = st.selectbox("Filtrer par opérateur", ["Tous"] + [o['nom'] for o in st.session_state.operators], key="exp_oper")
        only_working = st.checkbox("Inclure uniquement les jours ouvrés", value=True)
        if st.button("📊 Générer Excel", use_container_width=True, key="gen_xlsx"):
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
            import io as _io
            wb = openpyxl.Workbook()
            C_BLUE="1E40AF";C_BLUE2="2563EB";C_BLUE_L="DBEAFE"
            C_PURPLE_L="F5F3FF";C_YELLOW_L="FFFBEB";C_TEAL_L="EFF6FF"
            C_WHITE="FFFFFF";C_TEXT="0F172A";C_GREY="F8FAFC"
            C_PURPLE="7C3AED";C_YELLOW="D97706";C_TEAL="0369A1"
            C_GREEN="16A34A";C_RED="DC2626"
            thin=Side(style="thin",color="E2E8F0")
            border=Border(left=thin,right=thin,top=thin,bottom=thin)
            def fill(h): return PatternFill("solid",fgColor=h)
            def font(size=10,bold=False,color=C_TEXT): return Font(name="Arial",size=size,bold=bold,color=color)
            def al_c(): return Alignment(horizontal="center",vertical="center",wrap_text=True)
            def al_l(): return Alignment(horizontal="left",vertical="center",wrap_text=True)
            exp_today=_today_dt
            if exp_scope=="Mois en cours":
                first=exp_today.replace(day=1)
                last=exp_today.replace(day=cal_module.monthrange(exp_today.year,exp_today.month)[1])
                exp_dates=[first+timedelta(days=i) for i in range((last-first).days+1)]
            elif exp_scope=="4 semaines à venir":
                ws=exp_today-timedelta(days=exp_today.weekday())
                exp_dates=[ws+timedelta(days=i) for i in range(28)]
            else:
                all_d=[]
                for p in st.session_state.prelevements:
                    try: all_d.append(datetime.fromisoformat(p["date"]).date())
                    except: pass
                for s in st.session_state.schedules:
                    try: all_d.append(datetime.fromisoformat(s["due_date"]).date())
                    except: pass
                if all_d:
                    exp_dates=[min(all_d)+timedelta(days=i) for i in range((max(all_d)-min(all_d)).days+1)]
                else:
                    exp_dates=[exp_today+timedelta(days=i) for i in range(7)]
            if only_working:
                exp_dates=[d for d in exp_dates if is_working_day(d)]
            ws1=wb.active;ws1.title="Planning";ws1.sheet_view.showGridLines=False
            ws1.merge_cells("A1:H1");ws1["A1"]="PLANNING MICROBIOLOGIQUE — MicroSurveillance URC"
            ws1["A1"].font=Font(name="Arial",size=14,bold=True,color=C_WHITE)
            ws1["A1"].fill=fill(C_BLUE);ws1["A1"].alignment=al_c();ws1.row_dimensions[1].height=30
            ws1.merge_cells("A2:H2")
            ws1["A2"]=f"Généré le {exp_today.strftime('%d/%m/%Y')} — Jours ouvrés uniquement" if only_working else f"Généré le {exp_today.strftime('%d/%m/%Y')}"
            ws1["A2"].font=Font(name="Arial",size=9,color="475569");ws1["A2"].fill=fill(C_BLUE_L);ws1["A2"].alignment=al_c();ws1.row_dimensions[2].height=18
            headers=["Date","Jour","Férié","Type","Point de prélèvement","Classe","Gélose","Opérateur","Statut"]
            col_widths=[14,12,10,22,32,10,28,25,14]
            for ci,(h,w) in enumerate(zip(headers,col_widths),start=1):
                c=ws1.cell(row=4,column=ci,value=h)
                c.font=Font(name="Arial",size=10,bold=True,color=C_WHITE)
                c.fill=fill(C_BLUE2);c.alignment=al_c();c.border=border
                ws1.column_dimensions[get_column_letter(ci)].width=w
            ws1.row_dimensions[4].height=22;ws1.freeze_panes="A5"
            JOURS_XL=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
            row=5
            for d in exp_dates:
                holidays_d=get_holidays_cached(d.year)
                is_h=d in holidays_d
                day_prelevs=[p for p in st.session_state.prelevements
                    if p.get('date') and datetime.fromisoformat(p['date']).date()==d and not p.get('archived',False)
                    and (exp_oper_filter=="Tous" or p.get('operateur','').startswith(exp_oper_filter))]
                day_j2=[s for s in st.session_state.schedules if s['when']=='J2' and datetime.fromisoformat(s['due_date']).date()==d]
                day_j7=[s for s in st.session_state.schedules if s['when']=='J7' and datetime.fromisoformat(s['due_date']).date()==d]
                if not day_prelevs and not day_j2 and not day_j7: continue
                for p in day_prelevs:
                    rd=[d.strftime('%d/%m/%Y'),JOURS_XL[d.weekday()],"Oui" if is_h else "","Prélèvement J0",p['label'],p.get('room_class','—'),p.get('gelose','—'),p.get('operateur','—'),"🧪 À réaliser"]
                    for ci,val in enumerate(rd,1):
                        c=ws1.cell(row=row,column=ci,value=val);c.fill=fill(C_PURPLE_L);c.alignment=al_l();c.border=border;c.font=font()
                    ws1.cell(row=row,column=4).font=Font(name="Arial",size=10,bold=True,color=C_PURPLE)
                    ws1.row_dimensions[row].height=18;row+=1
                for sch in day_j2:
                    samp=next((p for p in st.session_state.prelevements if p['id']==sch['sample_id']),None)
                    is_done=sch['status']=='done';rd=[d.strftime('%d/%m/%Y'),JOURS_XL[d.weekday()],"Oui" if is_h else "","Lecture J2",sch['label'],samp.get('room_class','—') if samp else '—',samp.get('gelose','—') if samp else '—',samp.get('operateur','—') if samp else '—',"✅ Faite" if is_done else "⏳ À faire"]
                    for ci,val in enumerate(rd,1):
                        c=ws1.cell(row=row,column=ci,value=val);c.fill=fill(C_YELLOW_L);c.alignment=al_l();c.border=border;c.font=font()
                    ws1.cell(row=row,column=4).font=Font(name="Arial",size=10,bold=True,color=C_YELLOW)
                    ws1.cell(row=row,column=9).font=Font(name="Arial",size=10,bold=True,color=C_GREEN if is_done else C_YELLOW)
                    ws1.row_dimensions[row].height=18;row+=1
                for sch in day_j7:
                    samp=next((p for p in st.session_state.prelevements if p['id']==sch['sample_id']),None)
                    is_done=sch['status']=='done';rd=[d.strftime('%d/%m/%Y'),JOURS_XL[d.weekday()],"Oui" if is_h else "","Lecture J7",sch['label'],samp.get('room_class','—') if samp else '—',samp.get('gelose','—') if samp else '—',samp.get('operateur','—') if samp else '—',"✅ Faite" if is_done else "⏳ À faire"]
                    for ci,val in enumerate(rd,1):
                        c=ws1.cell(row=row,column=ci,value=val);c.fill=fill(C_TEAL_L);c.alignment=al_l();c.border=border;c.font=font()
                    ws1.cell(row=row,column=4).font=Font(name="Arial",size=10,bold=True,color=C_TEAL)
                    ws1.cell(row=row,column=9).font=Font(name="Arial",size=10,bold=True,color=C_GREEN if is_done else C_TEAL)
                    ws1.row_dimensions[row].height=18;row+=1
            buf=_io.BytesIO();wb.save(buf);buf.seek(0)
            fname=f"planning_URC_{exp_today.strftime('%Y%m%d')}.xlsx"
            st.download_button("⬇️ Télécharger le planning Excel",data=buf.getvalue(),file_name=fname,mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
            st.success(f"✅ Fichier **{fname}** généré avec jours ouvrés uniquement")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 : PLAN URC
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "plan":
    st.markdown("#### 🗺️ Plan URC interactif — placement des prélèvements")
    uploaded = st.file_uploader("Uploader le plan URC (PNG, JPG ou PDF)", type=["png","jpg","jpeg","pdf"], key="plan_upload_main")
    if uploaded:
        raw = uploaded.read()
        if uploaded.type == "application/pdf":
            pdf_b64 = base64.b64encode(raw).decode()
            surv_points = [{"label": r["prelevement"], "germ": r["germ_match"], "ufc": r["ufc"], "date": r["date"], "status": r["status"]} for r in st.session_state.surveillance]
            surv_json = json.dumps(surv_points, ensure_ascii=False)
            pts_json = json.dumps(st.session_state.map_points, ensure_ascii=False)
            st.info("Plan PDF chargé — utilisez l'interface ci-dessous pour placer les points.")
        else:
            img_data = base64.b64encode(raw).decode()
            st.session_state.map_image = f"data:{uploaded.type};base64,{img_data}"

    if st.session_state.map_image and (not uploaded or uploaded.type != "application/pdf"):
        surv_points = [{"label": r["prelevement"], "germ": r["germ_match"], "ufc": r["ufc"], "date": r["date"], "status": r["status"]} for r in st.session_state.surveillance]
        surv_json = json.dumps(surv_points, ensure_ascii=False)
        pts_json = json.dumps(st.session_state.map_points, ensure_ascii=False)
        map_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#f8fafc;color:#1e293b;font-family:'Segoe UI',sans-serif;height:80vh;display:flex;flex-direction:column}}
.toolbar{{padding:8px 12px;background:#fff;border-bottom:1.5px solid #e2e8f0;display:flex;gap:8px;align-items:center;flex-shrink:0;flex-wrap:wrap}}
.toolbar select,.toolbar input,.toolbar button{{background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:6px;padding:4px 8px;color:#1e293b;font-size:.75rem}}
.toolbar button{{cursor:pointer}}.toolbar button:hover,.toolbar button.active{{background:#2563eb;color:#fff}}
.map-container{{flex:1;overflow:auto;position:relative}}.map-inner{{position:relative;display:inline-block;min-width:100%;min-height:100%}}
#planImg{{max-width:100%;display:block}}
.point{{position:absolute;width:24px;height:24px;border-radius:50%;border:2px solid white;cursor:pointer;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:white;box-shadow:0 0 10px rgba(0,0,0,.6);transition:transform .2s;z-index:10}}
.point:hover{{transform:translate(-50%,-50%) scale(1.5)}}.point.ok{{background:#22c55e}}.point.alert{{background:#f59e0b}}.point.action{{background:#ef4444}}.point.none{{background:#0f172a}}
.tooltip{{position:fixed;background:#fff;border:1.5px solid #e2e8f0;border-radius:8px;padding:10px;font-size:.72rem;pointer-events:none;z-index:1000;display:none;min-width:200px;box-shadow:0 4px 20px rgba(0,0,0,.15)}}
.tooltip.visible{{display:block}}
</style></head><body>
<div class="toolbar">
  <input id="ptLabel" placeholder="Nom du point" style="width:130px">
  <select id="ptSurv" style="width:200px"><option value="">-- Lier à un prélèvement --</option>{''.join(f'<option value="{r["label"]}">{r["label"]} — {r["germ"]} ({r["ufc"]} UFC)</option>' for r in surv_points)}</select>
  <button id="addBtn" onclick="toggleAddMode()">📍 Placer un point</button>
  <button onclick="clearLast()">↩️ Annuler dernier</button>
  <button onclick="clearAll()">🗑️ Tout effacer</button>
  <span style="font-size:.65rem;color:#94a3b8">✅OK 🟡Alerte 🔴Action</span>
</div>
<div class="map-container" id="mapContainer"><div class="map-inner" id="mapInner"><img id="planImg" src="{st.session_state.map_image}" draggable="false"><div id="tooltip" class="tooltip"></div></div></div>
<script>
let addMode=false;let points={pts_json};const survData={surv_json};
function toggleAddMode(){{addMode=!addMode;const btn=document.getElementById('addBtn');btn.classList.toggle('active',addMode);btn.textContent=addMode?'✋ Annuler':'📍 Placer un point';document.getElementById('mapContainer').style.cursor=addMode?'crosshair':'default';}}
function renderPoints(){{document.querySelectorAll('.point').forEach(p=>p.remove());const img=document.getElementById('planImg');if(!img)return;const inner=document.getElementById('mapInner');points.forEach((pt,i)=>{{const surv=survData.find(s=>s.label===(pt.survLabel||pt.label));const status=surv?surv.status:'none';const div=document.createElement('div');div.className=`point ${{status}}`;div.style.left=pt.x+'%';div.style.top=pt.y+'%';div.textContent=i+1;div.addEventListener('mouseenter',e=>showTip(e,pt,surv));div.addEventListener('mouseleave',hideTip);inner.appendChild(div);}});}}
function showTip(e,pt,surv){{const t=document.getElementById('tooltip');t.innerHTML=`<div style="font-weight:700;margin-bottom:6px">${{pt.label}}</div>`+(surv?`<div>Germe : <i>${{surv.germ}}</i></div><div>UFC : <b>${{surv.ufc}}</b></div><div>Date : ${{surv.date}}</div>`:'<div>Non lié</div>');t.style.left=(e.clientX+15)+'px';t.style.top=(e.clientY-10)+'px';t.classList.add('visible');}}
function hideTip(){{document.getElementById('tooltip').classList.remove('visible');}}
function clearLast(){{if(points.length>0){{points.pop();renderPoints();}}}}
function clearAll(){{if(confirm('Effacer tous les points ?')){{points=[];renderPoints();}}}}
document.getElementById('mapInner').addEventListener('click',function(e){{if(!addMode)return;const img=document.getElementById('planImg');if(!img)return;const rect=img.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)return;const x=((e.clientX-rect.left)/rect.width*100);const y=((e.clientY-rect.top)/rect.height*100);const label=document.getElementById('ptLabel').value||`Point ${{points.length+1}}`;const survLabel=document.getElementById('ptSurv').value||null;points.push({{x,y,label,survLabel}});renderPoints();toggleAddMode();}});
const img=document.getElementById('planImg');if(img)img.addEventListener('load',renderPoints);else renderPoints();
</script></body></html>"""
        st.components.v1.html(map_html, height=650, scrolling=False)
    elif not uploaded:
        st.markdown('''<div style="background:#f8fafc;border:2px dashed #e2e8f0;border-radius:12px;padding:48px;text-align:center;color:#0f172a"><div style="font-size:2rem;margin-bottom:8px">🗺️</div><div>Uploadez un plan URC (PNG/JPG/PDF)</div></div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 : HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "historique":
    st.markdown("### 📋 Historique de surveillance")
    surv = st.session_state.surveillance
    total = len(surv)

    if surv:
        c_dl, c_cl = st.columns(2)
        with c_dl:
            csv_str = io.StringIO()
            writer = csv.DictWriter(csv_str, fieldnames=surv[0].keys())
            writer.writeheader(); writer.writerows(surv)
            st.download_button("⬇️ Télécharger CSV", csv_str.getvalue(), "surveillance.csv", "text/csv", use_container_width=True)
        with c_cl:
            if st.button("🗑️ Vider l'historique", use_container_width=True):
                st.session_state.surveillance = []
                if os.path.exists(CSV_FILE): os.remove(CSV_FILE)
                st.rerun()
        alerts = sum(1 for r in surv if r["status"]=="alert")
        actions = sum(1 for r in surv if r["status"]=="action")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total", total); c2.metric("✅ Conformes", total-alerts-actions); c3.metric("⚠️ Alertes", alerts); c4.metric("🚨 Actions", actions)
        st.divider()

        hist_tab_pts, hist_tab_germs, hist_tab_prev, hist_tab_liste = st.tabs([
            "📍 Stats par point", "🦠 Stats par germe", "👤 Répartition par préleveur", "📋 Liste des entrées"
        ])

        with hist_tab_pts:
            from collections import defaultdict
            pts_stats = defaultdict(lambda: {"total":0,"positives":0,"negatives":0,"germes":defaultdict(int)})
            for r in surv:
                pt = r.get("prelevement","—")
                pts_stats[pt]["total"] += 1
                ufc = int(r.get("ufc",0))
                germ = r.get("germ_match","") or ""
                if ufc > 0 and germ not in ("Négatif","—",""):
                    pts_stats[pt]["positives"] += 1
                    pts_stats[pt]["germes"][germ] += 1
                else:
                    pts_stats[pt]["negatives"] += 1
            st.markdown("<div style='display:grid;grid-template-columns:2.5fr 0.7fr 0.7fr 0.7fr 1fr 2fr;gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'><div style='font-size:.72rem;font-weight:800;color:#fff'>Point</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Total</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>✅ Nég.</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🦠 Pos.</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Taux +</div><div style='font-size:.72rem;font-weight:800;color:#fff'>Germes détectés</div></div>", unsafe_allow_html=True)
            for ri, (pt_name, pt_data) in enumerate(sorted(pts_stats.items(), key=lambda x: -x[1]["positives"])):
                t = pt_data["total"]; pos = pt_data["positives"]
                taux = pos/t*100 if t>0 else 0
                tc = "#ef4444" if taux>=50 else "#f59e0b" if taux>0 else "#22c55e"
                germes_str = ", ".join(g + "(" + str(n) + "x)" for g,n in sorted(pt_data["germes"].items(), key=lambda x:-x[1])[:3]) or "—"
                row_bg = "#f8fafc" if ri%2==0 else "#ffffff"
                row = ("<div style='display:grid;grid-template-columns:2.5fr 0.7fr 0.7fr 0.7fr 1fr 2fr;gap:4px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;padding:9px 14px;align-items:center'>"
                    "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>📍 " + pt_name + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>" + str(t) + "</div>"
                    "<div style='font-size:1rem;font-weight:800;color:#22c55e;text-align:center'>" + str(pt_data["negatives"]) + "</div>"
                    "<div style='text-align:center'><span style='background:" + tc + "22;color:" + tc + ";border:1px solid " + tc + "55;border-radius:6px;padding:2px 8px;font-size:.8rem;font-weight:700'>" + str(pos) + "</span></div>"
                    "<div style='font-size:.85rem;font-weight:700;color:" + tc + ";text-align:center'>" + str(round(taux,0)) + "%</div>"
                    "<div style='font-size:.72rem;color:#475569;font-style:italic'>" + germes_str + "</div>"
                    "</div>")
                st.markdown(row, unsafe_allow_html=True)
            st.markdown("<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'><div style='font-size:.78rem;color:#94a3b8'>" + str(len(pts_stats)) + " point(s) — " + str(total) + " résultats</div></div>", unsafe_allow_html=True)

        with hist_tab_germs:
            from collections import defaultdict
            germs_stats = defaultdict(lambda: {"count":0,"ufc_sum":0,"points":set()})
            total_pos = 0
            for r in surv:
                germ = r.get("germ_match","") or ""
                if germ in ("Négatif","—","") or int(r.get("ufc",0))==0: continue
                total_pos += 1
                germs_stats[germ]["count"] += 1
                germs_stats[germ]["ufc_sum"] += int(r.get("ufc",0))
                germs_stats[germ]["points"].add(r.get("prelevement","—"))
            if not germs_stats:
                st.info("Aucun germe positif dans l'historique.")
            else:
                st.markdown("<div style='display:grid;grid-template-columns:2.5fr 0.7fr 1fr 1fr 2fr;gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'><div style='font-size:.72rem;font-weight:800;color:#fff'>Germe</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Cas</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>% des positifs</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Moy. UFC</div><div style='font-size:.72rem;font-weight:800;color:#fff'>Points touchés</div></div>", unsafe_allow_html=True)
                for gi, (gname, gdata) in enumerate(sorted(germs_stats.items(), key=lambda x:-x[1]["count"])):
                    pct = gdata["count"]/total_pos*100 if total_pos>0 else 0
                    avg_ufc = gdata["ufc_sum"]/gdata["count"] if gdata["count"]>0 else 0
                    pts_str = ", ".join(list(gdata["points"])[:3])
                    bar_w = int(pct)
                    row_bg = "#f8fafc" if gi%2==0 else "#ffffff"
                    row = ("<div style='display:grid;grid-template-columns:2.5fr 0.7fr 1fr 1fr 2fr;gap:4px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;padding:9px 14px;align-items:center'>"
                        "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>🦠 " + gname + "</div>"
                        "<div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>" + str(gdata["count"]) + "</div>"
                        "<div style='text-align:center'><div style='background:#e2e8f0;border-radius:4px;height:8px;margin-bottom:2px'><div style='background:#ef4444;border-radius:4px;height:8px;width:" + str(bar_w) + "%'></div></div><span style='font-size:.75rem;font-weight:700;color:#ef4444'>" + str(round(pct,1)) + "%</span></div>"
                        "<div style='font-size:.85rem;font-weight:700;color:#475569;text-align:center'>" + str(round(avg_ufc,0)) + "</div>"
                        "<div style='font-size:.72rem;color:#475569;font-style:italic'>" + pts_str + "</div>"
                        "</div>")
                    st.markdown(row, unsafe_allow_html=True)
                st.markdown("<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'><div style='font-size:.78rem;color:#94a3b8'>" + str(len(germs_stats)) + " germe(s) distinct(s) — " + str(total_pos) + " positifs</div></div>", unsafe_allow_html=True)

        with hist_tab_prev:
            from collections import defaultdict
            prev_stats = defaultdict(lambda: {"total":0,"positives":0,"negatives":0,"alertes":0,"actions":0,"germes":defaultdict(int)})
            for r in surv:
                op = (r.get("operateur","") or "Non renseigné").strip() or "Non renseigné"
                prev_stats[op]["total"] += 1
                ufc = int(r.get("ufc",0)); status = r.get("status","ok"); germ = r.get("germ_match","") or ""
                if ufc>0 and germ not in ("Négatif","—",""):
                    prev_stats[op]["positives"] += 1; prev_stats[op]["germes"][germ] += 1
                else:
                    prev_stats[op]["negatives"] += 1
                if status=="alert": prev_stats[op]["alertes"] += 1
                elif status=="action": prev_stats[op]["actions"] += 1
            op_list = sorted(prev_stats.items(), key=lambda x:-x[1]["total"])
            card_cols = st.columns(min(len(op_list),4))
            for ci, (op_name, op_data) in enumerate(op_list):
                t=op_data["total"]; pos=op_data["positives"]
                taux_pos=pos/t*100 if t>0 else 0
                tc="#ef4444" if taux_pos>=30 else "#f59e0b" if taux_pos>0 else "#22c55e"
                ini=op_name[0].upper() if op_name!="Non renseigné" else "?"
                with card_cols[ci%len(card_cols)]:
                    st.markdown("<div style='background:#fff;border:1.5px solid #e2e8f0;border-radius:14px;padding:18px 14px;text-align:center;margin-bottom:12px'><div style='background:#2563eb;color:#fff;border-radius:50%;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.2rem;margin:0 auto 10px auto'>" + ini + "</div><div style='font-size:.92rem;font-weight:700;color:#0f172a;margin-bottom:6px'>" + op_name + "</div><div style='font-size:2rem;font-weight:900;color:#1e40af'>" + str(t) + "</div><div style='font-size:.68rem;color:#64748b;margin-bottom:10px'>résultat(s)</div><div style='display:grid;grid-template-columns:1fr 1fr;gap:6px'><div style='background:#f0fdf4;border-radius:8px;padding:6px'><div style='font-size:1rem;font-weight:800;color:#22c55e'>" + str(op_data["negatives"]) + "</div><div style='font-size:.6rem;color:#166534'>✅ Nég.</div></div><div style='background:#fef2f2;border-radius:8px;padding:6px'><div style='font-size:1rem;font-weight:800;color:#ef4444'>" + str(pos) + "</div><div style='font-size:.6rem;color:#991b1b'>🦠 Pos.</div></div><div style='background:#fffbeb;border-radius:8px;padding:6px'><div style='font-size:1rem;font-weight:800;color:#f59e0b'>" + str(op_data["alertes"]) + "</div><div style='font-size:.6rem;color:#92400e'>⚠️ Alerte</div></div><div style='background:#fef2f2;border-radius:8px;padding:6px'><div style='font-size:1rem;font-weight:800;color:#dc2626'>" + str(op_data["actions"]) + "</div><div style='font-size:.6rem;color:#991b1b'>🚨 Action</div></div></div><div style='margin-top:10px;background:" + tc + "22;border:1px solid " + tc + "55;border-radius:8px;padding:5px'><div style='font-size:.8rem;font-weight:800;color:" + tc + "'>" + str(round(taux_pos,0)) + "% positifs</div></div></div>", unsafe_allow_html=True)
            st.divider()
            st.markdown("<div style='display:grid;grid-template-columns:2fr 0.7fr 0.7fr 0.7fr 0.7fr 0.7fr 2fr;gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px'><div style='font-size:.72rem;font-weight:800;color:#fff'>Préleveur</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>Total</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>✅</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🦠</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>⚠️</div><div style='font-size:.72rem;font-weight:800;color:#fff;text-align:center'>🚨</div><div style='font-size:.72rem;font-weight:800;color:#fff'>Germes fréquents</div></div>", unsafe_allow_html=True)
            for ri, (op_name, op_data) in enumerate(op_list):
                t=op_data["total"]; pos=op_data["positives"]
                taux_pos=pos/t*100 if t>0 else 0
                tc="#ef4444" if taux_pos>=30 else "#f59e0b" if taux_pos>0 else "#22c55e"
                top_g=", ".join(g+"("+str(n)+"x)" for g,n in sorted(op_data["germes"].items(),key=lambda x:-x[1])[:3]) or "—"
                row_bg="#f8fafc" if ri%2==0 else "#ffffff"
                st.markdown("<div style='display:grid;grid-template-columns:2fr 0.7fr 0.7fr 0.7fr 0.7fr 0.7fr 2fr;gap:4px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;padding:9px 14px;align-items:center'><div style='font-size:.88rem;font-weight:700;color:#0f172a'>👤 " + op_name + "</div><div style='font-size:1rem;font-weight:800;color:#1e40af;text-align:center'>" + str(t) + "</div><div style='font-size:1rem;font-weight:800;color:#22c55e;text-align:center'>" + str(op_data["negatives"]) + "</div><div style='text-align:center'><span style='background:" + tc + "22;color:" + tc + ";border-radius:6px;padding:2px 8px;font-size:.8rem;font-weight:700'>" + str(pos) + "</span></div><div style='font-size:1rem;font-weight:800;color:#f59e0b;text-align:center'>" + str(op_data["alertes"]) + "</div><div style='font-size:1rem;font-weight:800;color:#ef4444;text-align:center'>" + str(op_data["actions"]) + "</div><div style='font-size:.72rem;color:#475569;font-style:italic'>" + top_g + "</div></div>", unsafe_allow_html=True)
            st.markdown("<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px'><div style='font-size:.78rem;color:#94a3b8'>" + str(len(op_list)) + " préleveur(s)</div></div>", unsafe_allow_html=True)

        with hist_tab_liste:
            for r in reversed(surv):
                ic = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
                with st.expander(ic + " " + r["date"] + " — " + r["prelevement"] + " — " + r["germ_match"] + " — " + str(r["ufc"]) + " UFC/m³"):
                    c1,c2,c3,c4 = st.columns([3,3,3,1])
                    c1.markdown("**Germe saisi :** " + r["germ_saisi"] + "\n\n**Correspondance :** " + r["germ_match"] + " (" + str(r["match_score"]) + ")")
                    c2.markdown("**UFC/m³ :** " + str(r["ufc"]) + "\n\n**Seuil alerte :** ≥" + str(r["alert_threshold"]) + " | **Seuil action :** ≥" + str(r["action_threshold"]))
                    c3.markdown("**Opérateur :** " + str(r.get("operateur","N/A")) + "\n\n**Remarque :** " + str(r.get("remarque","—")))
                    with c4:
                        real_i = surv.index(r)
                        if st.button("🗑️", key="del_surv_" + str(real_i)):
                            st.session_state.surveillance.pop(real_i)
                            save_surveillance(st.session_state.surveillance)
                            st.rerun()
    else:
        st.info("Aucun prélèvement enregistré.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 : PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "parametres":
    st.markdown("### ⚙️ Paramètres — Seuils & Mesures correctives")

    subtab_seuils, subtab_mesures, subtab_points, subtab_operateurs, subtab_backup, subtab_supabase = st.tabs([
        "📏 Seuils", "📋 Mesures correctives", "📍 Points de prélèvement", "👤 Opérateurs", "💾 Sauvegarde", "☁️ Base de données"
    ])

    with subtab_seuils:
        st.markdown("Configurez les seuils d'alerte et d'action **par niveau de criticité**.")
        thresholds = st.session_state.thresholds
        risk_info = [(5,"🔴 Criticité 5 — Critique","#ef4444"),(4,"🟠 Criticité 4 — Majeur","#f97316"),(3,"🟡 Criticité 3 — Important","#f59e0b"),(2,"🟢 Criticité 2 — Modéré","#84cc16"),(1,"🟢 Criticité 1 — Limité","#22c55e")]
        new_thresholds = {}
        for risk, title, color in risk_info:
            th = thresholds.get(risk, DEFAULT_THRESHOLDS[risk])
            germs_list = ', '.join(sorted(set(g['name'] for g in st.session_state.germs if g['risk']==risk)))
            st.markdown(f"""<div style="background:#f8fafc;border-left:4px solid {color};border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:4px">
              <div style="font-size:.85rem;font-weight:700;color:{color}">{title}</div>
              <div style="font-size:.65rem;color:#0f172a;margin-top:2px">{germs_list[:150]}{'...' if len(germs_list)>150 else ''}</div>
            </div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: new_alert = st.number_input("⚠️ Seuil alerte (UFC/m³)", min_value=0, value=int(th.get("alert",10)), key=f"alert_{risk}")
            with c2: new_action = st.number_input("🚨 Seuil action (UFC/m³)", min_value=0, value=int(th.get("action",50)), key=f"action_{risk}")
            new_thresholds[risk] = {"alert": new_alert, "action": new_action}
            st.divider()
        cs, cr = st.columns(2)
        with cs:
            if st.button("💾 Sauvegarder les seuils", use_container_width=True):
                st.session_state.thresholds = new_thresholds
                save_thresholds_and_measures(new_thresholds, st.session_state.measures)
                st.success("✅ Seuils sauvegardés !")
        with cr:
            if st.button("↩️ Réinitialiser", use_container_width=True, key="reinit_seuils"):
                st.session_state.thresholds = {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}
                save_thresholds_and_measures(st.session_state.thresholds, st.session_state.measures)
                st.success("✅ Seuils réinitialisés."); st.rerun()

    with subtab_mesures:
        om = st.session_state.origin_measures
        scope_labels = {"all":"🌐 Toutes","Air":"💨 Air","Humidité":"💧 Humidité","Flore fécale":"🦠 Flore fécale","Oropharynx / Gouttelettes":"😷 Oropharynx","Peau / Muqueuses":"🖐️ Peau / Muqueuses","Peau / Muqueuse":"🖐️ Peau / Muqueuse","Sol / Carton / Surface sèche":"📦 Sol / Surface sèche"}
        type_labels = {"alert":"⚠️ Alerte","action":"🚨 Action","both":"⚠️🚨 Alerte & Action"}
        type_colors = {"alert":"#f59e0b","action":"#ef4444","both":"#818cf8"}
        col_f1, col_f2, col_f3, col_f4 = st.columns([2,1.5,1.5,1])
        with col_f1:
            filter_scope = st.selectbox("Origine", ["Tout afficher"]+list(scope_labels.values()), label_visibility="collapsed", key="filter_scope")
        with col_f2:
            filter_risk_lbl = st.selectbox("Criticité", ["🌐 Tout","🟢 1","🟢 2","🟡 3","🟠 4","🔴 5"], label_visibility="collapsed", key="filter_risk")
        with col_f3:
            filter_type = st.selectbox("Type", ["Tout","⚠️ Alerte","🚨 Action"], label_visibility="collapsed", key="filter_type")
        with col_f4:
            if st.button("➕ Nouvelle", use_container_width=True): st.session_state.show_new_measure = True
        scope_filter_map = {v: k for k, v in scope_labels.items()}
        active_scope = scope_filter_map.get(filter_scope, None) if filter_scope != "Tout afficher" else None
        active_risk = filter_risk_lbl.split()[-1] if filter_risk_lbl != "🌐 Tout" else None
        active_type = ("alert" if "Alerte" in filter_type else "action") if filter_type != "Tout" else None

        if st.session_state.get("show_new_measure", False):
            with st.container():
                st.markdown("#### ➕ Nouvelle mesure")
                nmc1, nmc2, nmc3, nmc4 = st.columns([3,2,1.5,1.5])
                with nmc1: nm_text = st.text_input("Texte *", key="nm_text")
                with nmc2:
                    nm_scope_label = st.selectbox("Origine", list(scope_labels.values()), key="nm_scope")
                    nm_scope = scope_filter_map.get(nm_scope_label, "all")
                with nmc3:
                    risk_opts_nm = {"all":"🌐 Toutes","1":"🟢 1","2":"🟢 2","3":"🟡 3","4":"🟠 4","5":"🔴 5","[3,4,5]":"3-4-5","[4,5]":"4-5","[1,2,3]":"1-2-3"}
                    nm_risk_lbl = st.selectbox("Criticité", list(risk_opts_nm.values()), key="nm_risk")
                    nm_risk_key = {v:k for k,v in risk_opts_nm.items()}.get(nm_risk_lbl,"all")
                    nm_risk = "all" if nm_risk_key=="all" else json.loads(nm_risk_key) if nm_risk_key.startswith("[") else int(nm_risk_key)
                with nmc4:
                    nm_type_label = st.selectbox("Type", list(type_labels.values()), key="nm_type")
                    nm_type = {v:k for k,v in type_labels.items()}.get(nm_type_label,"alert")
                nb1, nb2 = st.columns(2)
                with nb1:
                    if st.button("✅ Ajouter", use_container_width=True, key="nm_submit"):
                        if nm_text.strip():
                            om.append({"id":f"m{len(om)+1:03d}_custom","text":nm_text.strip(),"scope":nm_scope,"risk":nm_risk,"type":nm_type})
                            save_origin_measures(om); st.session_state.origin_measures=om; st.session_state.show_new_measure=False; st.rerun()
                with nb2:
                    if st.button("Annuler", use_container_width=True, key="nm_cancel"):
                        st.session_state.show_new_measure=False; st.rerun()

        def passes_filter(m):
            if active_scope and m["scope"] != active_scope: return False
            if active_type and m["type"] != active_type and m["type"] != "both": return False
            if active_risk:
                mr = m.get("risk","all")
                if mr != "all":
                    if isinstance(mr, list):
                        if int(active_risk) not in mr: return False
                    else:
                        if str(mr) != active_risk: return False
            return True

        for m in [m for m in om if passes_filter(m)]:
            real_idx = om.index(m)
            tcol = type_colors.get(m["type"],"#0f172a"); tlbl = type_labels.get(m["type"],m["type"])
            row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([4.5,1.2,1.5,0.8,0.8])
            with row_c1: st.markdown(f'<div style="padding:6px 0;font-size:.8rem;color:#1e293b">• {m["text"]}</div>', unsafe_allow_html=True)
            with row_c3: st.markdown(f'<div style="padding:6px 0;font-size:.65rem;color:{tcol};font-weight:600;text-align:center">{tlbl}</div>', unsafe_allow_html=True)
            with row_c4:
                if st.button("✏️", key=f"edit_btn_{real_idx}"): st.session_state[f"edit_m_{real_idx}"]=True; st.rerun()
            with row_c5:
                if st.button("🗑️", key=f"del_m_{real_idx}"): om.pop(real_idx); save_origin_measures(om); st.session_state.origin_measures=om; st.rerun()

        st.divider()
        col_sr, col_def = st.columns(2)
        with col_sr:
            if st.button("💾 Sauvegarder", use_container_width=True, key="save_mesures"): save_origin_measures(om); st.success("✅ Sauvegardé !")
        with col_def:
            if st.button("↩️ Réinitialiser", use_container_width=True, key="reinit_mesures"):
                st.session_state.origin_measures=[dict(m) for m in DEFAULT_ORIGIN_MEASURES]; save_origin_measures(st.session_state.origin_measures); st.rerun()

    with subtab_points:
        st.markdown("Gérez les points de prélèvement.")
        PT_RISK_OPTS = ["1 — Limité", "2 — Modéré", "3 — Important", "4 — Majeur", "5 — Critique"]
        PT_RISK_COLORS = {"1":"#22c55e","2":"#84cc16","3":"#f59e0b","4":"#f97316","5":"#ef4444"}
        PT_FREQ_UNIT_OPTS = ["/ jour", "/ semaine", "/ mois"]
        if not st.session_state.points:
            st.info("Aucun point défini.")
        else:
            st.markdown("""<div style="display:grid;grid-template-columns:2.2fr 0.9fr 0.9fr 0.9fr 0.7fr 1.1fr 0.5fr 0.5fr;gap:4px;background:#1e40af;border-radius:10px 10px 0 0;padding:10px 14px">
              <div style="font-size:.72rem;font-weight:800;color:#fff">Point</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Type</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Classe</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Gélose</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Risque</div>
              <div style="font-size:.72rem;font-weight:800;color:#fff;text-align:center">Fréquence</div>
              <div></div><div></div>
            </div>""", unsafe_allow_html=True)
            for i, pt in enumerate(list(st.session_state.points)):
                pt_type = pt.get('type','—'); type_icon = "💨" if pt_type=="Air" else "🧴"
                risk_val = str(pt.get('risk_level','—'))
                risk_col = PT_RISK_COLORS.get(risk_val, "#94a3b8")
                freq = pt.get('frequency', 1); freq_unit = pt.get('frequency_unit','/ semaine')
                freq_short = str(freq) + "x/" + ("j" if "jour" in freq_unit else "sem" if "sem" in freq_unit else "mois")
                row_bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
                c1, c2 = st.columns([8, 1])
                with c1:
                    risk_badge = "<span style='background:" + risk_col + "22;color:" + risk_col + ";border:1px solid " + risk_col + "55;border-radius:6px;padding:2px 7px;font-size:.72rem;font-weight:700'>Nv." + risk_val + "</span>"
                    freq_badge = "<span style='background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe;border-radius:6px;padding:2px 8px;font-size:.75rem;font-weight:700'>🔁 " + freq_short + "</span>"
                    gelose_short = pt.get('gelose','—')[:16]
                    row_html = (
                        "<div style='display:grid;grid-template-columns:2.2fr 0.9fr 0.9fr 0.9fr 0.7fr 1.1fr;gap:4px;background:" + row_bg + ";border:1px solid #e2e8f0;border-top:none;padding:9px 14px;align-items:center'>"
                        "<div style='font-size:.88rem;font-weight:700;color:#0f172a'>" + type_icon + " " + pt['label'] + "</div>"
                        "<div style='font-size:.75rem;color:#475569;text-align:center'>" + pt_type + "</div>"
                        "<div style='font-size:.75rem;color:#475569;text-align:center'>" + pt.get('room_class','—') + "</div>"
                        "<div style='font-size:.72rem;color:#1d4ed8;text-align:center'>🧫 " + gelose_short + "</div>"
                        "<div style='text-align:center'>" + risk_badge + "</div>"
                        "<div style='text-align:center'>" + freq_badge + "</div>"
                        "</div>"
                    )
                    st.markdown(row_html, unsafe_allow_html=True)
                with c2:
                    btn_e, btn_d = st.columns(2)
                    with btn_e:
                        if st.button("✏️", key=f"edit_pt_{i}"): st.session_state._edit_point=i; st.rerun()
                    with btn_d:
                        if st.button("🗑️", key=f"del_pt_{i}"): st.session_state.points.pop(i); save_points(st.session_state.points); st.rerun()
            st.markdown("<div style='background:#1e293b;border-radius:0 0 10px 10px;padding:8px 14px;margin-bottom:16px'><div style='font-size:.78rem;font-weight:700;color:#94a3b8'>" + str(len(st.session_state.points)) + " point(s)</div></div>", unsafe_allow_html=True)
        st.divider()
        if st.session_state.get('_edit_point') is not None:
            idx = st.session_state._edit_point; pt = st.session_state.points[idx]
            st.markdown(f"### ✏️ Modifier — {pt['label']}")
            er1, er2, er3, er4 = st.columns([3,2,2,2])
            with er1: new_label = st.text_input("Nom", value=pt['label'], key="pt_edit_label")
            with er2: new_type = st.selectbox("Type", ["Air","Surface"], index=["Air","Surface"].index(pt.get('type','Air')) if pt.get('type','Air') in ["Air","Surface"] else 0, key="pt_edit_type")
            with er3: new_room = st.text_input("Classe", value=pt.get('room_class',''), key="pt_edit_room", placeholder="Ex: ISO 5")
            with er4:
                gelose_opts = ["Gélose de sédimentation","Gélose TSA","Gélose Columbia","Autre"] if new_type=="Air" else ["Gélose contact (RODAC)","Gélose contact TSA","Ecouvillonnage","Autre"]
                cur_g = pt.get('gelose',gelose_opts[0]); g_idx = gelose_opts.index(cur_g) if cur_g in gelose_opts else 0
                new_gelose = st.selectbox("Gélose", gelose_opts, index=g_idx, key="pt_edit_gelose")
            er5, er6, er7 = st.columns([2,1,2])
            with er5:
                cur_risk_str = str(pt.get('risk_level','1'))
                cur_risk_opt = next((o for o in PT_RISK_OPTS if o.startswith(cur_risk_str)), PT_RISK_OPTS[0])
                new_risk_opt = st.selectbox("🎯 Niveau de risque", PT_RISK_OPTS, index=PT_RISK_OPTS.index(cur_risk_opt), key="pt_edit_risk")
                new_risk = int(new_risk_opt[0])
            with er6:
                new_freq = st.number_input("🔁 Fréquence", min_value=1, max_value=31, value=int(pt.get('frequency',1)), step=1, key="pt_edit_freq")
            with er7:
                cur_unit = pt.get('frequency_unit','/ semaine')
                unit_idx = PT_FREQ_UNIT_OPTS.index(cur_unit) if cur_unit in PT_FREQ_UNIT_OPTS else 1
                new_freq_unit = st.selectbox("Unité", PT_FREQ_UNIT_OPTS, index=unit_idx, key="pt_edit_freq_unit")
            eb1, eb2 = st.columns(2)
            with eb1:
                if st.button("✅ Enregistrer", key="pt_save_edit"):
                    st.session_state.points[idx] = {"id":pt.get('id',f"p{idx+1}"),"label":new_label,"type":new_type,"room_class":new_room,"gelose":new_gelose,"risk_level":new_risk,"frequency":new_freq,"frequency_unit":new_freq_unit}
                    save_points(st.session_state.points); st.session_state._edit_point=None; st.success("✅ Point mis à jour"); st.rerun()
            with eb2:
                if st.button("Annuler", key="pt_cancel_edit"): st.session_state._edit_point=None; st.rerun()
        else:
            st.markdown("### ➕ Ajouter un point")
            np_r1, np_r2, np_r3, np_r4 = st.columns([3,2,2,2])
            with np_r1: np_label = st.text_input("Nom *", placeholder="Ex: Salle 3 — Poste A", key="np_label")
            with np_r2: np_type = st.selectbox("Type", ["Air","Surface"], key="np_type")
            with np_r3: np_room = st.text_input("Classe", placeholder="Ex: ISO 5", key="np_room")
            with np_r4:
                gelose_opts_new = ["Gélose de sédimentation","Gélose TSA","Gélose Columbia","Autre"] if np_type=="Air" else ["Gélose contact (RODAC)","Gélose contact TSA","Ecouvillonnage","Autre"]
                np_gelose = st.selectbox("Gélose", gelose_opts_new, key="np_gelose")
            np_r5, np_r6, np_r7 = st.columns([2,1,2])
            with np_r5:
                np_risk_opt = st.selectbox("🎯 Niveau de risque", PT_RISK_OPTS, index=0, key="np_risk")
                np_risk = int(np_risk_opt[0])
            with np_r6:
                np_freq = st.number_input("🔁 Fréquence", min_value=1, max_value=31, value=1, step=1, key="np_freq")
            with np_r7:
                np_freq_unit = st.selectbox("Unité", PT_FREQ_UNIT_OPTS, index=0, key="np_freq_unit")
            if st.button("➕ Ajouter", key="np_add"):
                if not np_label.strip(): st.error("Le nom est requis")
                else:
                    nid = f"p{len(st.session_state.points)+1}_{int(datetime.now().timestamp())}"
                    st.session_state.points.append({"id":nid,"label":np_label.strip(),"type":np_type,"room_class":np_room.strip(),"gelose":np_gelose,"risk_level":np_risk,"frequency":np_freq,"frequency_unit":np_freq_unit})
                    save_points(st.session_state.points); st.success(f"✅ Point **{np_label}** ajouté"); st.rerun()

    with subtab_operateurs:
        ops = st.session_state.operators
        if not ops: st.info("Aucun opérateur enregistré.")
        else:
            st.markdown(f'<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:12px 16px;margin-bottom:16px"><span style="font-size:.75rem;color:#0369a1;font-weight:700">👥 {len(ops)} opérateur(s)</span></div>', unsafe_allow_html=True)
            for i, op in enumerate(ops):
                nom = op.get('nom','—'); profession = op.get('profession','—')
                oc1, oc2, oc3 = st.columns([5,1,1])
                with oc1:
                    st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;display:flex;gap:16px;align-items:center">
                      <div style="background:#2563eb;color:#fff;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;flex-shrink:0">{nom[0].upper() if nom else '?'}</div>
                      <div><div style="font-weight:700;font-size:.9rem;color:#0f172a">{nom}</div><div style="font-size:.72rem;color:#475569;margin-top:2px">👔 {profession}</div></div>
                    </div>""", unsafe_allow_html=True)
                with oc2:
                    if st.button("✏️", key=f"edit_op_{i}"): st.session_state._edit_operator=i; st.rerun()
                with oc3:
                    if st.button("🗑️", key=f"del_op_{i}"):
                        ops.pop(i); save_operators(ops); st.session_state.operators=ops; st.rerun()
        st.divider()
        if st.session_state.get('_edit_operator') is not None:
            idx = st.session_state._edit_operator; op = st.session_state.operators[idx]
            st.markdown(f"### ✏️ Modifier — {op.get('nom','')}")
            ec1, ec2 = st.columns(2)
            with ec1: edit_nom = st.text_input("Nom *", value=op.get('nom',''), key="op_edit_nom")
            with ec2:
                p_opts = ["Préparateur en pharmacie hospitalière","Pharmacien","Interne de pharmacie"]
                cur_p = op.get('profession',''); p_idx = p_opts.index(cur_p) if cur_p in p_opts else 0
                edit_prof = st.selectbox("Profession *", p_opts, index=p_idx, key="op_edit_prof")
            eb1, eb2 = st.columns(2)
            with eb1:
                if st.button("✅ Enregistrer", use_container_width=True, key="op_save_edit"):
                    if edit_nom.strip():
                        st.session_state.operators[idx]={"nom":edit_nom.strip(),"profession":edit_prof}; save_operators(st.session_state.operators); st.session_state._edit_operator=None; st.success("✅ Mis à jour"); st.rerun()
                    else: st.error("Le nom est obligatoire.")
            with eb2:
                if st.button("Annuler", use_container_width=True, key="op_cancel_edit"): st.session_state._edit_operator=None; st.rerun()
        else:
            st.markdown("### ➕ Ajouter un opérateur")
            nc1, nc2 = st.columns(2)
            with nc1: new_nom = st.text_input("Nom *", placeholder="Ex: Marie Dupont", key="op_new_nom")
            with nc2:
                p_opts_new = ["Préparateur en pharmacie hospitalière","Pharmacien","Interne de pharmacie"]
                new_prof = st.selectbox("Profession *", p_opts_new, key="op_new_prof")
            if st.button("➕ Ajouter", key="op_add"):
                if not new_nom.strip(): st.error("Le nom est obligatoire.")
                elif any(o['nom'].lower()==new_nom.strip().lower() for o in st.session_state.operators): st.error("Cet opérateur existe déjà.")
                else:
                    st.session_state.operators.append({"nom":new_nom.strip(),"profession":new_prof}); save_operators(st.session_state.operators); st.success(f"✅ **{new_nom}** ajouté"); st.rerun()

    with subtab_backup:
        st.markdown("### 💾 Sauvegarde & Restauration des données")
        supa_connected = get_supabase_client() is not None
        if supa_connected:
            st.success("✅ **Supabase actif** — vos données sont automatiquement persistantes dans le cloud.")
        else:
            st.warning("⚠️ **Supabase non configuré** — sans base de données cloud, vos données ne survivent pas à un redémarrage du serveur.")
        st.markdown("""<div style="background:#fffbeb;border:1.5px solid #fcd34d;border-radius:12px;padding:16px 20px;margin:12px 0">
          <div style="font-weight:800;color:#92400e;font-size:.95rem;margin-bottom:8px">📋 Pourquoi sauvegarder ?</div>
          <div style="font-size:.82rem;color:#78350f;line-height:1.8">
            Chaque modification du code provoque un redémarrage. Sans Supabase, toutes les données locales sont <strong>effacées</strong>.<br>
            ✅ <strong>Solution 1</strong> : configurer Supabase (onglet ☁️).<br>
            ✅ <strong>Solution 2</strong> : exporter avant chaque update, réimporter après.
          </div>
        </div>""", unsafe_allow_html=True)
        st.divider()
        st.markdown("#### ⬇️ Exporter toutes les données")
        backup_data = export_all_data()
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        backup_filename = f"backup_URC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        b_col1.metric("🦠 Germes", len(backup_data["germs"]))
        b_col2.metric("🧪 Prélèvements", len(backup_data["prelevements"]))
        b_col3.metric("📅 Lectures planif.", len(backup_data["schedules"]))
        b_col4.metric("📋 Historique", len(backup_data["surveillance"]))
        st.download_button(
            label=f"⬇️ Télécharger la sauvegarde ({len(backup_json)//1024 + 1} Ko)",
            data=backup_json, file_name=backup_filename, mime="application/json",
            use_container_width=True, key="main_export_btn"
        )
        st.divider()
        st.markdown("#### ⬆️ Restaurer depuis une sauvegarde")
        st.markdown("""<div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;padding:12px 16px;margin-bottom:12px">
          <span style="color:#dc2626;font-weight:700;font-size:.82rem">⚠️ La restauration remplace TOUTES les données actuelles sans possibilité d'annulation.</span>
        </div>""", unsafe_allow_html=True)
        uploaded_backup = st.file_uploader("Choisir un fichier de sauvegarde (.json)", type=["json"], key="backup_uploader")
        if uploaded_backup is not None:
            try:
                backup_content = json.loads(uploaded_backup.read().decode("utf-8"))
                meta = backup_content.get("_meta", {})
                st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:14px 18px;margin-bottom:12px">
                  <div style="font-weight:700;color:#166534;font-size:.85rem;margin-bottom:8px">📁 Contenu du fichier détecté</div>
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:.75rem;color:#0f172a">
                    <div>🦠 Germes : <strong>{len(backup_content.get("germs",[]))}</strong></div>
                    <div>🧪 Prélèvements : <strong>{len(backup_content.get("prelevements",[]))}</strong></div>
                    <div>📅 Lectures : <strong>{len(backup_content.get("schedules",[]))}</strong></div>
                    <div>👤 Opérateurs : <strong>{len(backup_content.get("operators",[]))}</strong></div>
                    <div>📍 Points : <strong>{len(backup_content.get("points",[]))}</strong></div>
                    <div>📋 Historique : <strong>{len(backup_content.get("surveillance",[]))}</strong></div>
                  </div>
                  <div style="font-size:.68rem;color:#475569;margin-top:8px">Exporté le : {meta.get("exported_at","—")[:19].replace("T"," ")} | Version : {meta.get("version","?")}</div>
                </div>""", unsafe_allow_html=True)
                if st.session_state.get("confirm_restore", False):
                    st.error("🚨 Dernière confirmation : toutes les données actuelles seront remplacées.")
                    r_col1, r_col2 = st.columns(2)
                    with r_col1:
                        if st.button("✅ OUI — Restaurer maintenant", use_container_width=True, key="confirm_restore_yes"):
                            ok, msg = import_all_data(backup_content)
                            st.session_state.confirm_restore = False
                            if ok: st.success(f"✅ {msg}"); st.rerun()
                            else: st.error(msg)
                    with r_col2:
                        if st.button("❌ Annuler", use_container_width=True, key="confirm_restore_no"):
                            st.session_state.confirm_restore = False; st.rerun()
                else:
                    if st.button("⬆️ Restaurer ces données", use_container_width=True, key="restore_btn"):
                        st.session_state.confirm_restore = True; st.rerun()
            except json.JSONDecodeError:
                st.error("❌ Fichier JSON invalide.")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with subtab_supabase:
        st.markdown("### ☁️ Configuration Supabase")
        supa_ok = get_supabase_client() is not None
        if supa_ok:
            st.success("✅ **Supabase connecté** — toutes les modifications sont synchronisées en temps réel.")
        else:
            st.error("🔴 **Supabase non connecté** — les données sont sauvegardées en local uniquement.")
        st.markdown("""<div style="background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;padding:20px;margin-top:16px">
          <div style="font-size:.95rem;font-weight:700;color:#0f172a;margin-bottom:12px">📋 Comment configurer Supabase</div>
          <div style="font-size:.82rem;color:#1e293b;line-height:1.8">
            <strong>1.</strong> Créez un compte sur <strong>supabase.com</strong><br>
            <strong>2.</strong> Créez un nouveau projet<br>
            <strong>3.</strong> Dans l'éditeur SQL, exécutez le code ci-dessous<br>
          </div>
        </div>""", unsafe_allow_html=True)
        st.code("""CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE app_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_all" ON app_state FOR ALL USING (true) WITH CHECK (true);""", language="sql")
        st.markdown("""<div style="background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;padding:20px;margin-top:12px">
          <div style="font-size:.82rem;color:#1e293b;line-height:1.8">
            <strong>4.</strong> Dans <em>Project Settings → API</em>, copiez :<br>
            &nbsp;&nbsp;• <strong>Project URL</strong> → <code>SUPABASE_URL</code><br>
            &nbsp;&nbsp;• <strong>anon/public key</strong> → <code>SUPABASE_KEY</code><br>
          </div>
        </div>""", unsafe_allow_html=True)
        st.code("""SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGci..."  # votre clé anon""", language="toml")
        if supa_ok:
            st.divider()
            st.markdown("### 🔄 Actions Supabase")
            col_sync1, col_sync2 = st.columns(2)
            with col_sync1:
                if st.button("🔄 Forcer la synchronisation", use_container_width=True):
                    save_germs(st.session_state.germs)
                    save_prelevements(st.session_state.prelevements)
                    save_schedules(st.session_state.schedules)
                    save_surveillance(st.session_state.surveillance)
                    save_points(st.session_state.points)
                    save_operators(st.session_state.operators)
                    save_pending_identifications(st.session_state.pending_identifications)
                    save_origin_measures(st.session_state.origin_measures)
                    st.success("✅ Toutes les données synchronisées avec Supabase !")
            with col_sync2:
                if st.button("🔃 Recharger depuis Supabase", use_container_width=True):
                    st.session_state.germs = load_germs()
                    st.session_state.prelevements = load_prelevements()
                    st.session_state.schedules = load_schedules()
                    st.session_state.surveillance = load_surveillance()
                    st.session_state.points = load_points()
                    st.session_state.operators = load_operators()
                    st.session_state.pending_identifications = load_pending_identifications()
                    st.session_state.origin_measures = load_origin_measures()
                    st.success("✅ Données rechargées depuis Supabase !")
                    st.rerun()