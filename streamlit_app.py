import streamlit as st
import json
import csv
import io
import os
import base64
from datetime import datetime, timedelta
import difflib

# Optional Supabase integration (falls back to local file persistence)
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

st.set_page_config(layout="wide", page_title="MicroSurveillance URC", page_icon="🦠")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap');

html,body,[class*="css"]{font-family:'Syne',sans-serif;font-size:16px}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#f8fafc!important}
[data-testid="stHeader"]{background:#f8fafc!important;border-bottom:1px solid #e2e8f0!important}
#MainMenu,footer{visibility:hidden}

/* Pleine largeur */
.block-container{max-width:100%!important;padding-left:1rem!important;padding-right:1rem!important}

p,li,div{color:#1e293b}
h1,h2,h3,h4{color:#0f172a!important}
.stMarkdown p,.stMarkdown li{color:#0f172a}

[data-testid="stSidebar"]{background:#ffffff!important;border-right:2px solid #e2e8f0!important;box-shadow:2px 0 12px rgba(0,0,0,.07)!important}
[data-testid="stSidebar"] *{color:#1e293b!important}
[data-testid="stSidebar"] p{color:#0f172a!important}

[data-testid="collapsedControl"]{background:#2563eb!important;border-radius:0 12px 12px 0!important;width:32px!important;min-width:32px!important;box-shadow:4px 0 16px rgba(37,99,235,.5)!important;border:none!important}
[data-testid="collapsedControl"]:hover{background:#1d4ed8!important}
[data-testid="collapsedControl"] svg{fill:#ffffff!important;stroke:#ffffff!important;width:20px!important;height:20px!important;opacity:1!important}
[data-testid="stSidebarCollapsedControl"]{background:#2563eb!important;border-radius:0 12px 12px 0!important;width:32px!important;box-shadow:4px 0 16px rgba(37,99,235,.5)!important}
[data-testid="stSidebarCollapsedControl"] svg{fill:#ffffff!important;stroke:#ffffff!important}
[data-testid="stSidebarCollapsedControl"]:hover{background:#1d4ed8!important}

.stButton>button{border-radius:8px!important;font-size:.82rem!important;font-weight:600!important;border:1.5px solid #e2e8f0!important;color:#1e293b!important;background:#ffffff!important;transition:all .15s}
.stButton>button:hover{background:#f1f5f9!important;border-color:#0f172a!important}
.stButton>button[kind="primary"]{background:#2563eb!important;color:#fff!important;border-color:#2563eb!important}
.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;border-color:#1d4ed8!important}

.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div,.stNumberInput>div>div>input{background:#ffffff!important;color:#1e293b!important;border:1.5px solid #cbd5e1!important;border-radius:8px!important}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:#2563eb!important;box-shadow:0 0 0 3px rgba(37,99,235,.15)!important}
label{color:#374151!important;font-size:.8rem!important;font-weight:600!important}
.stCheckbox label{color:#374151!important}
.stCheckbox span{color:#374151!important}

div[data-testid="stExpander"]{background:#ffffff!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;box-shadow:0 1px 4px rgba(0,0,0,.06)!important}
div[data-testid="stExpander"] summary,div[data-testid="stExpander"] summary *{color:#1e293b!important}
div[data-testid="stExpander"] summary svg{fill:#0f172a!important;stroke:#0f172a!important}

.stTabs [data-baseweb="tab-list"]{background:#f1f5f9!important;border-radius:10px!important;padding:3px!important;border:1.5px solid #e2e8f0!important}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#0f172a!important;border-radius:8px!important;font-weight:600!important}
.stTabs [aria-selected="true"]{background:#ffffff!important;color:#2563eb!important;box-shadow:0 1px 4px rgba(0,0,0,.1)!important}

[data-testid="stMetric"]{background:#fff!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;padding:12px!important}
[data-testid="stMetricValue"]{color:#0f172a!important}
[data-testid="stMetricLabel"]{color:#0f172a!important}

.stAlert{border-radius:10px!important}
.stSuccess>div{background:#f0fdf4!important;border:1px solid #86efac!important;color:#166534!important}
.stWarning>div{background:#fffbeb!important;border:1px solid #fcd34d!important;color:#92400e!important}
.stInfo>div{background:#eff6ff!important;border:1px solid #93c5fd!important;color:#1e40af!important}
.stError>div{background:#fef2f2!important;border:1px solid #fca5a5!important;color:#991b1b!important}

hr{border-color:#e2e8f0!important}

[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:#2563eb!important;color:#fff!important;border-color:#2563eb!important}
[data-testid="stSidebar"] .stButton>button{background:#f8fafc!important;color:#374151!important;border:1.5px solid #e2e8f0!important;font-size:.9rem!important;padding:10px 8px!important}
[data-testid="stSidebar"] .stButton>button:hover{background:#eff6ff!important;border-color:#93c5fd!important}
[data-testid="stSidebar"] p{font-size:.82rem!important}

.stSlider [data-testid="stThumbValue"]{color:#2563eb!important}
.stNumberInput button{background:#f1f5f9!important;border-color:#e2e8f0!important;color:#1e293b!important}
.stNumberInput button:hover{background:#e2e8f0!important}
.stDownloadButton>button{color:#2563eb!important;border-color:#93c5fd!important;background:#eff6ff!important}
.stDownloadButton>button:hover{background:#dbeafe!important}
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
        "action": "• Alerter le pharmacien responsable\n• Suspendre les préparations critiques si nécessaire\n• Nettoyage et désinfection renforcés de la zone\n• Vérification complète de l'installation (filtres, flux)\n• Enquête sur l'origine de la contamination\n• Prélèvements de contrôle avant reprise\n• Enregistrement et analyse des causes"
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
    dict(name="Staphylococcus spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Corynebacterium spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Cutibacterium acnes",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Micrococcus spp.",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Dermabacter hominis",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Brevibacterium epidermidis",path=["Germes","Bactéries","Humains","Peau / Muqueuses"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Streptococcus mitis/salivarius/sanguinis/anginosus",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Streptococcus pyogenes/agalactiae/pneumoniae",path=["Germes","Bactéries","Humains","Oropharynx / Gouttelettes"],risk=3,pathotype="Pathogène primaire",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Escherichia coli",path=["Germes","Bactéries","Humains","Flore fécale"],risk=4,pathotype="Pathogène opportuniste multirésistant (O157:H7 = pathogène primaire)",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Enterococcus spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Enterobacter spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Citrobacter spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Klebsiella pneumoniae",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Proteus spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Morganella spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Providencia spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Salmonella spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène primaire",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Shigella spp.",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène primaire",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Yersinia enterocolitica",path=["Germes","Bactéries","Humains","Flore fécale"],risk=3,pathotype="Pathogène primaire",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Pseudomonas spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Acinetobacter spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Paenibacillus spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé",comment=None),
    dict(name="Hafnia alvei",path=["Germes","Bactéries","Humains","Flore fécale"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Sphingomonas paucimobilis",path=["Germes","Bactéries","Environnemental","Humidité"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Sphingobium spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Methylobacterium spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Caulobacter crescentus",path=["Germes","Bactéries","Environnemental","Humidité"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Mycobacterium non tuberculeux",path=["Germes","Bactéries","Environnemental","Humidité"],risk=5,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance",apa="Risque de résistance",notes=None,comment=None),
    dict(name="Burkholderia cepacia",path=["Germes","Bactéries","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Burkholderia cepacia",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=4,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance (biofilm)",apa="Sensible",notes=None,comment=None),
    dict(name="Massilia spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Massilia spp.",path=["Germes","Bactéries","Environnemental","Humidité"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Bacillus spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé",comment=None),
    dict(name="Clostridium spp. (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé",comment=None),
    dict(name="Geobacillus stearothermophilus (SPORULES)",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=2,pathotype="Non pathogène",surfa="Risque de résistance (spore)",apa="Risque de résistance (spore)",notes="Sporulé thermophile",comment=None),
    dict(name="Arthrobacter spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Cellulomonas spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Curtobacterium spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Agrococcus spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Microbacterium spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Brevibacterium linens/casei",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=2,pathotype="Pathogène opportuniste",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Georgenia spp.",path=["Germes","Bactéries","Environnemental","Sol / Carton / Surface sèche"],risk=1,pathotype="Non pathogène",surfa="Sensible",apa="Sensible",notes=None,comment=None),
    dict(name="Candida spp.",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=3,pathotype="Pathogène opportuniste multirésistant",surfa="Sensible",apa="Sensible",notes="Levure",comment="Levures = pas de production de spores"),
    dict(name="Trichosporon spp.",path=["Germes","Champignons","Humain","Peau / Muqueuse"],risk=3,pathotype="Pathogène opportuniste résistant aux échinocandines",surfa="Sensible",apa="Sensible",notes="Levure",comment="Levures = pas de production de spores"),
    dict(name="Rhodotorula spp.",path=["Germes","Champignons","Environnemental","Humidité"],risk=3,pathotype="Pathogène opportuniste résistant aux échinocandines",surfa="Sensible",apa="Sensible",notes="Levure",comment="Levures = pas de production de spores"),
    dict(name="Fusarium spp.",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste multirésistant",surfa="Risque de résistance",apa="Risque de résistance",notes="Conidies 2-4um",comment="Production de spores (conidies) => dissémination dans l'air facilitée par petite taille (2-4 µm) + Résistance aux agents oxydants"),
    dict(name="Aureobasidium spp.",path=["Germes","Champignons","Environnemental","Humidité"],risk=4,pathotype="Pathogène opportuniste",surfa="Risque de résistance",apa="Sensible",notes="Blastospores + biofilm",comment="Production de blastospores (moins résistante aux agents oxydants et ne se dissémine pas dans l'air comme les conidies d'Aspergillus ou Fusarium) et production de biofilm"),
    dict(name="Mucorales",path=["Germes","Champignons","Environnemental","Sol / Carton / Surface sèche"],risk=5,pathotype="Pathogène opportuniste résistant aux échinocandines",surfa="Risque de résistance",apa="Risque modéré de résistance",notes="Sporangiospores",comment="Production de sporangiospores (moins résistant aux agents oxydants que les conidies d'Aspergillus ou Fusarium)"),
    dict(name="Alternaria spp.",path=["Germes","Champignons","Environnemental","Air"],risk=5,pathotype="Pathogène opportuniste",surfa="Risque de résistance",apa="Risque modéré de résistance",notes="Conidies grandes",comment="Production de spores (conidies) mais de plus grande taille, moins déshydratées et moins mélanisées que celles de Fusarium ou Aspergillus => Moins résistante à l'oxydation"),
    dict(name="Aspergillus spp.",path=["Germes","Champignons","Environnemental","Air"],risk=5,pathotype="Pathogène opportuniste",surfa="Risque de résistance",apa="Risque de résistance",notes="Conidies 2-4um",comment="Production de spores (conidies) => dissémination dans l'air facilitée par petite taille (2-4 µm) + Résistance aux agents oxydants"),
    dict(name="Cladosporium spp.",path=["Germes","Champignons","Environnemental","Air"],risk=4,pathotype="Très rarement pathogène",surfa="Risque de résistance",apa="Risque modéré de résistance",notes="Conidies grandes",comment="Production de spores (conidies) mais de plus grande taille, moins déshydratées et moins mélanisées => Moins résistante à l'oxydation"),
    dict(name="Penicillium spp.",path=["Germes","Champignons","Environnemental","Air"],risk=5,pathotype="Pathogène opportuniste",surfa="Risque de résistance",apa="Risque modéré de résistance",notes="Conidies",comment="Production de spores (conidies) mais moins déshydratées et moins mélanisées que celles de Fusarium ou Aspergillus => Moins résistantes à l'oxydation"),
    dict(name="Wallemia sebi",path=["Germes","Champignons","Environnemental","Air"],risk=4,pathotype="Très rarement pathogène",surfa="Risque de résistance",apa="Risque de résistance",notes="Arthroconidies",comment=None),
]


# ── PERSISTENCE ───────────────────────────────────────────────────────────────
def load_germs():
    defaults_by_name = {}
    for d in DEFAULT_GERMS:
        defaults_by_name.setdefault(d["name"], d)
    supa = get_supabase_client()
    if supa is not None:
        try:
            res = supa.table('app_state').select('value').eq('key','germs').execute()
            if res and getattr(res, 'data', None):
                row = res.data[0]
                try:
                    data = json.loads(row.get('value') if isinstance(row, dict) else row['value'])
                    for g in data:
                        dflt = defaults_by_name.get(g['name'], {})
                        if not g.get('notes'):
                            g['notes'] = dflt.get('notes', None)
                        if not g.get('comment'):
                            g['comment'] = dflt.get('comment', None)
                        g.setdefault('comment', None)
                        g.setdefault('notes', None)
                    return data
                except Exception:
                    pass
        except Exception:
            pass
    if os.path.exists(GERMS_FILE):
        try:
            with open(GERMS_FILE) as f:
                data = json.load(f)
            for g in data:
                dflt = defaults_by_name.get(g["name"], {})
                if not g.get("notes"):
                    g["notes"] = dflt.get("notes", None)
                if not g.get("comment"):
                    g["comment"] = dflt.get("comment", None)
                g.setdefault("comment", None)
                g.setdefault("notes", None)
            return data
        except:
            pass
    return [dict(g) for g in DEFAULT_GERMS]

def save_germs(germs):
    supa = get_supabase_client()
    if supa is not None:
        try:
            payload = {'key': 'germs', 'value': json.dumps(germs, ensure_ascii=False)}
            supa.table('app_state').upsert(payload).eq('key', 'germs').execute()
        except Exception:
            pass
    with open(GERMS_FILE, "w") as f:
        json.dump(germs, f, ensure_ascii=False, indent=2)

def load_thresholds():
    supa = get_supabase_client()
    if supa is not None:
        try:
            res = supa.table('app_state').select('value').eq('key','thresholds').execute()
            if res and getattr(res, 'data', None):
                row = res.data[0]
                raw = json.loads(row.get('value') if isinstance(row, dict) else row['value'])
                return {int(k): v for k, v in raw.items()}
        except Exception:
            pass
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            return {int(k): v for k, v in raw.items()}
        except:
            pass
    return {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}

def load_measures():
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            if "measures" in raw:
                return {int(k): v for k, v in raw["measures"].items()}
        except:
            pass
    return {k: dict(v) for k, v in DEFAULT_MEASURES.items()}

def save_thresholds_and_measures(thresholds, measures):
    data = {str(k): v for k, v in thresholds.items()}
    data["measures"] = {str(k): v for k, v in measures.items()}
    supa = get_supabase_client()
    if supa is not None:
        try:
            supa.table('app_state').upsert({'key': 'thresholds', 'value': json.dumps(data, ensure_ascii=False)}).eq('key','thresholds').execute()
        except Exception:
            pass
    with open(THRESHOLDS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_thresholds_for_risk(risk, thresholds):
    return thresholds.get(risk, {"alert": 25, "action": 40})

def load_origin_measures():
    supa = get_supabase_client()
    if supa is not None:
        try:
            res = supa.table('app_state').select('value').eq('key','measures').execute()
            if res and getattr(res, 'data', None):
                row = res.data[0]
                raw = json.loads(row.get('value') if isinstance(row, dict) else row['value'])
                if isinstance(raw, dict):
                    try:
                        items = [raw[k] for k in sorted(raw.keys(), key=lambda x: int(x))]
                    except Exception:
                        items = list(raw.values())
                    return [dict(m) for m in items]
                elif isinstance(raw, list):
                    return [dict(m) for m in raw]
        except Exception:
            pass
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            if "measures" in raw:
                mdata = raw["measures"]
                if isinstance(mdata, list):
                    return [dict(m) for m in mdata]
        except:
            pass
    return [dict(m) for m in DEFAULT_ORIGIN_MEASURES]

def save_origin_measures(measures):
    supa = get_supabase_client()
    if supa is not None:
        try:
            supa.table('app_state').upsert({'key': 'measures', 'value': json.dumps(measures, ensure_ascii=False)}).eq('key','measures').execute()
        except Exception:
            pass
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
        except:
            raw = {}
    else:
        raw = {}
    raw["measures"] = measures
    with open(THRESHOLDS_FILE, "w") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

def load_points():
    supa = get_supabase_client()
    if supa is not None:
        try:
            res = supa.table('app_state').select('value').eq('key','points').execute()
            if res and getattr(res, 'data', None):
                row = res.data[0]
                raw = json.loads(row.get('value') if isinstance(row, dict) else row['value'])
                if isinstance(raw, list):
                    return [dict(p) for p in raw]
        except Exception:
            pass
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, list):
                return [dict(p) for p in raw]
        except Exception:
            pass
    return []

def save_points(points):
    supa = get_supabase_client()
    if supa is not None:
        try:
            supa.table('app_state').upsert({'key': 'points', 'value': json.dumps(points, ensure_ascii=False)}).eq('key','points').execute()
        except Exception:
            pass
    try:
        with open(POINTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(points, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _load_json_key(key, local_file):
    supa = get_supabase_client()
    if supa is not None:
        try:
            res = supa.table('app_state').select('value').eq('key', key).execute()
            if res and getattr(res, 'data', None):
                row = res.data[0]
                raw = json.loads(row.get('value') if isinstance(row, dict) else row['value'])
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
    supa = get_supabase_client()
    if supa is not None:
        try:
            supa.table('app_state').upsert({'key': key, 'value': json.dumps(data, ensure_ascii=False)}).eq('key', key).execute()
        except Exception:
            pass
    try:
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_prelevements():
    return _load_json_key('prelevements', PRELEVEMENTS_FILE)

def save_prelevements(data):
    return _save_json_key('prelevements', data, PRELEVEMENTS_FILE)

def load_schedules():
    return _load_json_key('schedules', SCHEDULES_FILE)

def save_schedules(data):
    return _save_json_key('schedules', data, SCHEDULES_FILE)

def load_pending_identifications():
    return _load_json_key('pending_identifications', PENDING_FILE)

def save_pending_identifications(data):
    return _save_json_key('pending_identifications', data, PENDING_FILE)

def load_archived_samples():
    return _load_json_key('archived_samples', ARCHIVED_FILE)

def save_archived_samples(data):
    return _save_json_key('archived_samples', data, ARCHIVED_FILE)

def load_operators():
    return _load_json_key('operators', OPERATORS_FILE)

def save_operators(data):
    return _save_json_key('operators', data, OPERATORS_FILE)

def load_surveillance():
    supa = get_supabase_client()
    if supa is not None:
        try:
            res = supa.table('app_state').select('value').eq('key','surveillance').execute()
            if res and getattr(res, 'data', None):
                row = res.data[0]
                return json.loads(row.get('value') if isinstance(row, dict) else row['value'])
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
        except:
            pass
    return []

def save_surveillance(records):
    if not records:
        return
    supa = get_supabase_client()
    if supa is not None:
        try:
            supa.table('app_state').upsert({'key': 'surveillance', 'value': json.dumps(records, ensure_ascii=False)}).eq('key','surveillance').execute()
        except Exception:
            pass
    with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

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
    st.session_state.germs = [dict(g) for g in DEFAULT_GERMS]
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
    st.markdown('<p style="font-size:.75rem;color:#94a3b8;text-align:center">MicroSurveillance URC<br>v4.2</p>', unsafe_allow_html=True)

active = st.session_state.active_tab

# Global due-alert
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
    col_btn1, col_btn2 = st.columns([1,1])
    with col_btn1:
        if st.button("➕ Ajouter un germe", use_container_width=True):
            st.session_state.show_add = not st.session_state.show_add
            st.session_state.edit_idx = None
    with col_btn2:
        if st.button("💾 Sauvegarder", use_container_width=True):
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
    default_names_json = json.dumps([g["name"] for g in DEFAULT_GERMS], ensure_ascii=False)
    thresholds_json = json.dumps({str(k): v for k, v in st.session_state.thresholds.items()})

    # LOGIGRAMME — sans le dropdown "Sélectionner un point"
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
.right-panel{{width:300px;border-left:1px solid #e2e8f0;display:flex;flex-direction:column;background:#f1f5f9;flex-shrink:0}}
.sbox{{padding:10px;border-bottom:1px solid #e2e8f0}}
.sbox input{{width:100%;background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:7px 10px;color:#1e293b;font-size:.75rem;outline:none}}
.sbox input:focus{{border-color:#2563eb}}
.germ-list{{flex:1;overflow-y:auto;padding:5px;scrollbar-width:thin;scrollbar-color:#1e293b transparent}}
.germ-item{{display:flex;align-items:center;gap:7px;padding:5px 9px;border-radius:6px;cursor:pointer;transition:background .15s;font-size:.72rem;color:#0f172a;border:1px solid transparent;margin-bottom:2px}}
.germ-item:hover{{background:#ffffff;color:#1e293b}}
.germ-item.active{{background:#ffffff;border-color:#2563eb;color:#1e293b}}
.risk-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.info-panel{{border-top:1px solid #e2e8f0;padding:12px;background:#ffffff;display:none;max-height:420px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:#1e293b transparent}}
.info-panel.visible{{display:block}}
.info-name{{font-size:.85rem;font-weight:700;font-style:italic;color:#1e293b;margin-bottom:4px;line-height:1.3}}
.info-path{{font-size:.6rem;color:#2563eb;opacity:.8;margin-bottom:7px;font-family:monospace}}
.info-badge{{display:inline-flex;align-items:center;gap:5px;font-size:.63rem;padding:2px 9px;border-radius:20px;border:1px solid;margin-bottom:9px}}
.info-lbl{{font-size:.57rem;letter-spacing:.1em;text-transform:uppercase;color:#0f172a;margin-bottom:2px;margin-top:6px}}
.info-val{{font-size:.75rem;color:#1e293b;line-height:1.4}}
.sens{{display:flex;align-items:center;gap:7px;padding:5px 9px;border-radius:6px;border:1px solid #e2e8f0;font-size:.7rem;margin-top:2px}}
.ok{{color:#22c55e;font-weight:700}}.warn{{color:#f97316;font-weight:700}}.crit{{color:#ef4444;font-weight:700}}
.notes-box{{margin-top:6px;padding:6px 9px;border-radius:6px;background:rgba(37,99,235,0.04);border:1px solid rgba(37,99,235,0.15);font-size:.7rem;color:#0f172a;line-height:1.5}}
.threshold-row{{display:flex;gap:6px;margin-top:6px}}
.th-badge{{flex:1;text-align:center;padding:4px;border-radius:6px;font-size:.65rem;font-weight:600}}
.new-badge{{font-size:.55rem;background:rgba(56,189,248,0.15);color:#2563eb;border:1px solid #38bdf855;border-radius:4px;padding:1px 5px;margin-left:4px}}
</style></head><body>
<div class="app">
    <div class="tree-wrap"><svg id="svg"></svg></div>
    <div class="right-panel">
        <div class="sbox"><input type="text" id="sbox" placeholder="🔍 Rechercher un germe..." oninput="filterList()"></div>
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

function buildTree(){{
  const root={{name:"Germes",children:[]}};
  GERMS.forEach(g=>{{let cur=root;g.path.slice(1).forEach(n=>{{let c=cur.children&&cur.children.find(x=>x.name===n);if(!c){{c={{name:n,children:[]}};if(!cur.children)cur.children=[];cur.children.push(c);}}cur=c;}});}});
  function clean(n){{if(n.children&&n.children.length===0)delete n.children;else if(n.children)n.children.forEach(clean);}}
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
  svg.innerHTML='';svg.setAttribute('viewBox',`0 0 ${{maxX}} ${{maxY}}`);
  svg.setAttribute('height',maxY);svg.setAttribute('width',maxX);
  links.forEach(l=>{{
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    const x1=l.source.x+NODE_W,y1=l.source.y+NODE_H/2,x2=l.target.x,y2=l.target.y+NODE_H/2,mx=(x1+x2)/2;
    p.setAttribute('d',`M${{x1}},${{y1}} C${{mx}},${{y1}} ${{mx}},${{y2}} ${{x2}},${{y2}}`);
    p.setAttribute('class','link');p.dataset.source=l.source.name;p.dataset.target=l.target.name;
    p.dataset.sourcefull=l.source.fullPath.join('|||');p.dataset.targetfull=l.target.fullPath.join('|||');
    svg.appendChild(p);
  }});
  nodes.forEach(node=>{{
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class','node');g.setAttribute('transform',`translate(${{node.x}},${{node.y}})`);
    g.dataset.name=node.name;
    g.dataset.fullpath=node.fullPath.join('|||');
    const col=LEVEL_COLS[node.depth]||"#0f172a";g.style.setProperty('--col',col);
    const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
    rect.setAttribute('width',NODE_W);rect.setAttribute('height',NODE_H);rect.setAttribute('rx',5);rect.setAttribute('stroke',col);
    const text=document.createElementNS('http://www.w3.org/2000/svg','text');
    text.setAttribute('x',NODE_W/2);text.setAttribute('y',NODE_H/2+4);text.setAttribute('text-anchor','middle');
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
  const validLinkPairs=new Set();
  for(let i=1;i<=exactPath.length;i++)validNodePaths.add(exactPath.slice(0,i).join('|||'));
  for(let i=0;i<exactPath.length-1;i++)validLinkPairs.add(exactPath[i]+'>>'+exactPath[i+1]);
  document.querySelectorAll('.node').forEach(n=>{{n.classList.toggle('highlighted',validNodePaths.has(n.dataset.fullpath||''));}});
  document.querySelectorAll('.link').forEach(l=>{{
    const on=validNodePaths.has(l.dataset.sourcefull||'')&&validNodePaths.has(l.dataset.targetfull||'');
    l.classList.toggle('highlighted',on);
    if(on){{const depth=(l.dataset.sourcefull||'').split('|||').length-1;l.style.stroke=LEVEL_COLS[depth]||'#38bdf8';}}else l.style.stroke='';
  }});
}}
function clearHighlight(){{
  if(selectedPath){{highlightPath(selectedPath);return;}}
  document.querySelectorAll('.node').forEach(n=>n.classList.remove('highlighted'));
  document.querySelectorAll('.link').forEach(l=>{{l.classList.remove('highlighted');l.style.stroke=''}});
}}
function renderList(filter=''){{
  const list=document.getElementById('germList');list.innerHTML='';
  GERMS.filter(g=>g.name.toLowerCase().includes(filter.toLowerCase())).forEach(g=>{{
    const div=document.createElement('div');div.className='germ-item';div.dataset.name=g.name;
    const col=RISK_COLORS[g.risk];const isNew=!DEFAULT_NAMES.has(g.name);
    div.innerHTML=`<span class="risk-dot" style="background:${{col}}"></span><span style="flex:1">${{g.name}}${{isNew?'<span class="new-badge">new</span>':''}}</span><span style="font-size:.6rem;color:${{col}};font-weight:700">${{g.risk}}</span>`;
    div.addEventListener('click',()=>selectGerm(g));list.appendChild(div);
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
  const col=RISK_COLORS[g.risk];
  const th=THRESHOLDS[g.risk]||{{alert:25,action:40}};
  function sens(v){{if(!v)return['ok','✓'];const l=v.toLowerCase();if(l.includes('modéré'))return['warn','⚠'];if(l.includes('risque'))return['crit','✗'];return['ok','✓'];}}
  const[sc,si]=sens(g.surfa),[ac,ai]=sens(g.apa);
  const nh=g.notes?`<div class="info-lbl">📝 Notes</div><div class="notes-box">${{g.notes}}</div>`:'';
  const ch=g.comment?`<div class="info-lbl" style="color:#fb923c;margin-top:8px">💬 Commentaire</div><div class="notes-box" style="color:#fb923c;background:rgba(251,146,60,0.06);border-color:rgba(251,146,60,.35);font-style:italic">${{g.comment}}</div>`:'';
  panel.innerHTML=`
    <div class="info-name">${{g.name}}</div>
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
renderTree();renderList();
</script></body></html>"""

    st.components.v1.html(tree_html, height=920, scrolling=False)

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
# TAB 2 : SURVEILLANCE — Workflow J2/J7 avec navigation
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "surveillance":
    st.markdown("### 🔍 Identification & Surveillance microbiologique")

    # ── Nouveau prélèvement ──────────────────────────────────────────────────
    with st.expander("🧪 Nouveau prélèvement", expanded=False):
        if not st.session_state.points:
            st.info("Aucun point de prélèvement défini — allez dans **Paramètres → Points de prélèvement** pour en créer.")
        else:
            p_col1, p_col2, p_col3 = st.columns([3,2,1])
            with p_col1:
                point_labels = [f"{pt['label']} — {pt.get('type','?')} — {pt.get('room_class','?')}" for pt in st.session_state.points]
                sel_idx = st.selectbox("Point de prélèvement", list(range(len(point_labels))), format_func=lambda i: point_labels[i], key="new_prelev_point")
                selected_point = st.session_state.points[sel_idx]
                # Affichage détaillé du point sélectionné
                pt_type = selected_point.get('type', '—')
                pt_class = selected_point.get('room_class', '—')
                pt_gelose = selected_point.get('gelose', '—')
                type_icon = "💨" if pt_type == "Air" else "🧴"
                st.markdown(f"""<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:12px;margin-top:4px">
                  <div style="font-size:.75rem;font-weight:700;color:#0369a1;margin-bottom:8px">{type_icon} Détails du point sélectionné</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                    <div style="background:#ffffff;border-radius:6px;padding:8px;border:1px solid #e0f2fe">
                      <div style="font-size:.6rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em">Type de prélèvement</div>
                      <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:2px">{pt_type}</div>
                    </div>
                    <div style="background:#ffffff;border-radius:6px;padding:8px;border:1px solid #e0f2fe">
                      <div style="font-size:.6rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em">Classe de salle</div>
                      <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:2px">{pt_class}</div>
                    </div>
                    <div style="background:#ffffff;border-radius:6px;padding:8px;border:1px solid #e0f2fe;grid-column:1/-1">
                      <div style="font-size:.6rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em">Gélose utilisée</div>
                      <div style="font-size:.85rem;font-weight:700;color:#1d4ed8;margin-top:2px">🧫 {pt_gelose}</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with p_col2:
                # Liste déroulante opérateurs
                oper_list = [o['nom'] + (' — ' + o.get('profession','') if o.get('profession') else '') for o in st.session_state.operators]
                if oper_list:
                    oper_sel = st.selectbox("Opérateur", ["— Sélectionner —"] + oper_list, key="new_prelev_oper_sel")
                    p_oper = oper_sel if oper_sel != "— Sélectionner —" else ""
                else:
                    st.info("Aucun opérateur — ajoutez-en dans Paramètres → Opérateurs")
                    p_oper = st.text_input("Opérateur (manuel)", placeholder="Nom", key="new_prelev_oper_manual")
                p_date = st.date_input("Date prélèvement", value=datetime.today(), key="new_prelev_date")
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
                    j2_date = (p_date + timedelta(days=2)).isoformat()
                    j7_date = (p_date + timedelta(days=7)).isoformat()
                    st.session_state.schedules.append({
                        "id": f"sch_{pid}_J2",
                        "sample_id": pid,
                        "label": sample['label'],
                        "due_date": j2_date,
                        "when": "J2",
                        "status": "pending"
                    })
                    st.session_state.schedules.append({
                        "id": f"sch_{pid}_J7",
                        "sample_id": pid,
                        "label": sample['label'],
                        "due_date": j7_date,
                        "when": "J7",
                        "status": "pending"
                    })
                    save_schedules(st.session_state.schedules)
                    st.success(f"✅ Prélèvement **{sample['label']}** enregistré ! Lectures planifiées : J2 ({j2_date[:10]}) et J7 ({j7_date[:10]})")
                    st.rerun()

    st.divider()

    # ── WORKFLOW LECTURES J2/J7 ──────────────────────────────────────────────
    st.markdown("#### 📅 Lectures en attente")

    today = datetime.today().date()
    pending_schedules = [s for s in st.session_state.schedules if s["status"] == "pending"]
    overdue = [s for s in pending_schedules if datetime.fromisoformat(s["due_date"]).date() <= today]
    upcoming = [s for s in pending_schedules if datetime.fromisoformat(s["due_date"]).date() > today]

    if overdue:
        st.markdown(f'<div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;padding:12px 16px;margin-bottom:12px"><span style="color:#dc2626;font-weight:700">🔔 {len(overdue)} lecture(s) due(s) — à traiter dès que possible</span></div>', unsafe_allow_html=True)

    if upcoming:
        st.markdown(f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:10px 16px;margin-bottom:12px"><span style="color:#16a34a;font-size:.8rem">📆 {len(upcoming)} lecture(s) à venir</span></div>', unsafe_allow_html=True)

    if not pending_schedules:
        st.info("Aucune lecture planifiée — tous les prélèvements sont à jour.")

    # Logique J2 → J7 : n'afficher J7 que si J2 est déjà validée pour ce sample
    def should_show_schedule(s, all_schedules):
        """Affiche J2 toujours. Affiche J7 seulement si J2 est done pour ce sample."""
        if s['when'] == 'J2':
            return True
        if s['when'] == 'J7':
            j2 = next((x for x in all_schedules if x['sample_id'] == s['sample_id'] and x['when'] == 'J2'), None)
            if j2 is None or j2['status'] == 'done':
                return True
            return False
        return True

    all_pending = [s for s in st.session_state.schedules if s['status'] == 'pending']
    all_to_show = [s for s in (overdue + upcoming) if should_show_schedule(s, st.session_state.schedules)]
    for s in all_to_show:
        sched_date = datetime.fromisoformat(s["due_date"]).date()
        is_overdue = sched_date <= today
        border_col = "#ef4444" if is_overdue else "#3b82f6"
        bg_col = "#fef2f2" if is_overdue else "#eff6ff"
        badge_col = "#dc2626" if is_overdue else "#1d4ed8"
        status_txt = "EN RETARD" if is_overdue else f"dans {(sched_date - today).days}j"

        # Trouver le sample associé
        sample = next((p for p in st.session_state.prelevements if p['id'] == s['sample_id']), None)
        pt_type = sample.get('type', '?') if sample else '?'
        pt_gelose = sample.get('gelose', '?') if sample else '?'
        pt_class = sample.get('room_class', '?') if sample else '?'
        pt_oper = sample.get('operateur', '?') if sample else '?'

        with st.container():
            st.markdown(f"""<div style="background:{bg_col};border:1.5px solid {border_col};border-radius:10px;padding:14px 16px;margin-bottom:8px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                <div>
                  <span style="font-weight:700;font-size:.9rem;color:#0f172a">{s['label']}</span>
                  <span style="background:{border_col};color:#fff;font-size:.6rem;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">{s['when']}</span>
                  <span style="color:{badge_col};font-size:.65rem;font-weight:600;margin-left:6px">{status_txt}</span>
                </div>
                <span style="font-size:.75rem;color:#475569">📅 {s['due_date'][:10]}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:0">
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Type</div>
                  <div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_type}</div>
                </div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Gélose</div>
                  <div style="font-size:.75rem;font-weight:600;color:#1d4ed8">🧫 {pt_gelose}</div>
                </div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Classe</div>
                  <div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_class}</div>
                </div>
                <div style="background:#fff;border-radius:6px;padding:6px 8px;border:1px solid #e2e8f0">
                  <div style="font-size:.55rem;color:#64748b;text-transform:uppercase">Opérateur</div>
                  <div style="font-size:.75rem;font-weight:600;color:#0f172a">{pt_oper}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            btn_cols = st.columns([3, 1])
            with btn_cols[0]:
                if st.button(f"🔬 Traiter cette lecture ({s['when']})", key=f"proc_{s['id']}", use_container_width=True):
                    st.session_state.current_process = s['id']
                    st.rerun()
            with btn_cols[1]:
                if st.button("🗑️ Supprimer", key=f"del_sch_{s['id']}", use_container_width=True, help="Supprimer ce prélèvement et ses lectures planifiées"):
                    sample_id = s.get('sample_id')
                    st.session_state.schedules = [x for x in st.session_state.schedules if x['sample_id'] != sample_id]
                    save_schedules(st.session_state.schedules)
                    st.session_state.prelevements = [p for p in st.session_state.prelevements if p['id'] != sample_id]
                    save_prelevements(st.session_state.prelevements)
                    st.success("Prélèvement et lectures associées supprimés.")
                    st.rerun()

    # ── FORMULAIRE DE TRAITEMENT DE LECTURE ──────────────────────────────────
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
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
                  <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase;letter-spacing:.08em">Type</div>
                  <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{'💨' if pt_type=='Air' else '🧴'} {pt_type}</div>
                </div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
                  <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase;letter-spacing:.08em">Gélose</div>
                  <div style="font-size:.85rem;font-weight:700;color:#1d4ed8;margin-top:3px">🧫 {pt_gelose}</div>
                </div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
                  <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase;letter-spacing:.08em">Classe</div>
                  <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_class}</div>
                </div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
                  <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase;letter-spacing:.08em">Opérateur</div>
                  <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_oper}</div>
                </div>
                <div style="background:#eff6ff;border-radius:8px;padding:10px;text-align:center">
                  <div style="font-size:.6rem;color:#1e40af;text-transform:uppercase;letter-spacing:.08em">Date prélèv.</div>
                  <div style="font-size:.85rem;font-weight:700;color:#0f172a;margin-top:3px">{pt_date}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            lc1, lc2, lc3 = st.columns([2, 2, 1])
            with lc1:
                res = st.radio("Résultat de la lecture", ["✅ Négatif (0 colonie)", "🔴 Positif (colonies détectées)"], index=0, key=f"res_{proc_id}")
            with lc2:
                if "Positif" in res:
                    ncol = st.number_input("Nombre de colonies (UFC)", min_value=1, value=1, key=f"ncol_{proc_id}")
                else:
                    ncol = 0
            with lc3:
                st.markdown("<br>", unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])
            with btn_col1:
                if st.button("✅ Valider la lecture", use_container_width=True, key=f"submit_proc_{proc_id}"):
                    proc['status'] = 'done'
                    save_schedules(st.session_state.schedules)

                    if "Négatif" in res:
                        # J2 négatif → on attend J7 (déjà planifié)
                        # J7 négatif → archiver
                        j7_sch = next((x for x in st.session_state.schedules
                            if x['sample_id'] == proc['sample_id'] and x['when'] == 'J7' and x['status'] == 'pending'), None)

                        if proc['when'] == 'J7' or (proc['when'] == 'J2' and not j7_sch):
                            # Archive
                            if sample:
                                sample['archived'] = True
                                st.session_state.archived_samples.append(sample)
                                save_archived_samples(st.session_state.archived_samples)
                                save_prelevements(st.session_state.prelevements)
                            st.success("✅ Lecture négative — prélèvement archivé.")
                        else:
                            st.success(f"✅ Lecture {proc['when']} négative — en attente de la lecture J7 ({j7_sch['due_date'][:10] if j7_sch else '?'}).")

                        # Enregistrer dans historique
                        hist = {"date": str(today), "prelevement": proc['label'], "sample_id": proc.get('sample_id',''),
                            "germ_saisi": "", "germ_match": "Négatif", "match_score": "—",
                            "ufc": 0, "risk": 0, "alert_threshold": "—", "action_threshold": "—",
                            "status": "ok", "operateur": pt_oper, "remarque": f"Lecture {proc['when']} négative"}
                        st.session_state.surveillance.append(hist)
                        save_surveillance(st.session_state.surveillance)
                    else:
                        # Positif → créer entrée en attente d'identification
                        entry = {
                            "sample_id": proc['sample_id'],
                            "label": proc['label'],
                            "when": proc['when'],
                            "colonies": int(ncol),
                            "date": str(today),
                            "status": "pending"
                        }
                        st.session_state.pending_identifications.append(entry)
                        save_pending_identifications(st.session_state.pending_identifications)
                        st.success(f"🔴 Lecture {proc['when']} positive ({ncol} UFC) — identification du germe requise ci-dessous.")

                    st.session_state.current_process = None
                    st.rerun()

            with btn_col2:
                if st.button("↩️ Annuler / Retour", use_container_width=True, key=f"cancel_proc_{proc_id}"):
                    st.session_state.current_process = None
                    st.rerun()

    # ── IDENTIFICATIONS EN ATTENTE ────────────────────────────────────────────
    pending_ids = [p for p in st.session_state.pending_identifications if p.get('status') == 'pending']
    if pending_ids:
        st.markdown("---")
        st.markdown("#### 🔴 Identifications en attente (lectures positives)")
        for pi_idx, pi in enumerate(pending_ids):
            real_pi_idx = st.session_state.pending_identifications.index(pi)
            sample = next((p for p in st.session_state.prelevements if p['id'] == pi['sample_id']), None)
            pt_type = sample.get('type', '?') if sample else '?'
            pt_gelose = sample.get('gelose', '?') if sample else '?'
            pt_class = sample.get('room_class', '?') if sample else '?'
            pt_oper = sample.get('operateur', '?') if sample else '?'

            with st.expander(f"🔴 {pi['label']} — {pi['when']} — {pi['colonies']} UFC — {pi['date']}", expanded=True):
                st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:12px">
                  <div style="background:#fef2f2;border-radius:6px;padding:8px;text-align:center;border:1px solid #fca5a5">
                    <div style="font-size:.55rem;color:#dc2626;text-transform:uppercase">Type</div>
                    <div style="font-size:.8rem;font-weight:700;color:#0f172a">{'💨' if pt_type=='Air' else '🧴'} {pt_type}</div>
                  </div>
                  <div style="background:#fef2f2;border-radius:6px;padding:8px;text-align:center;border:1px solid #fca5a5">
                    <div style="font-size:.55rem;color:#dc2626;text-transform:uppercase">Gélose</div>
                    <div style="font-size:.8rem;font-weight:700;color:#1d4ed8">🧫 {pt_gelose}</div>
                  </div>
                  <div style="background:#fef2f2;border-radius:6px;padding:8px;text-align:center;border:1px solid #fca5a5">
                    <div style="font-size:.55rem;color:#dc2626;text-transform:uppercase">Classe</div>
                    <div style="font-size:.8rem;font-weight:700;color:#0f172a">{pt_class}</div>
                  </div>
                  <div style="background:#fef2f2;border-radius:6px;padding:8px;text-align:center;border:1px solid #fca5a5">
                    <div style="font-size:.55rem;color:#dc2626;text-transform:uppercase">UFC détectés</div>
                    <div style="font-size:.8rem;font-weight:700;color:#dc2626">{pi['colonies']}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                id_col1, id_col2 = st.columns([3, 1])
                with id_col1:
                    germ_input = st.text_input("Germe identifié *", placeholder="Ex: Pseudomonas aeruginosa", key=f"germ_id_{real_pi_idx}")
                    remarque = st.text_area("Remarque", height=60, key=f"rem_id_{real_pi_idx}")
                with id_col2:
                    date_id = st.date_input("Date identification", value=datetime.today(), key=f"date_id_{real_pi_idx}")
                    st.markdown("<br>", unsafe_allow_html=True)

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
                                record = {
                                    "date": str(date_id),
                                    "prelevement": pi['label'],
                                    "sample_id": pi.get('sample_id', ''),
                                    "germ_saisi": germ_input,
                                    "germ_match": match["name"],
                                    "match_score": f"{int(score*100)}%",
                                    "ufc": ufc,
                                    "risk": risk,
                                    "alert_threshold": th["alert"],
                                    "action_threshold": th["action"],
                                    "status": status,
                                    "operateur": pt_oper,
                                    "remarque": remarque
                                }
                                st.session_state.surveillance.append(record)
                                save_surveillance(st.session_state.surveillance)
                                # Marquer comme traité
                                st.session_state.pending_identifications[real_pi_idx]['status'] = 'done'
                                save_pending_identifications(st.session_state.pending_identifications)
                                col = RISK_COLORS.get(risk, "#0f172a")
                                status_txt = "🚨 Action requise" if status == "action" else "⚠️ Alerte" if status == "alert" else "✅ Conforme"
                                st.success(f"✅ {match['name']} identifié ({int(score*100)}%) — {ufc} UFC — {status_txt}")
                                st.rerun()
                            else:
                                st.warning(f"⚠️ Aucune correspondance pour **{germ_input}**. Vérifiez ou ajoutez ce germe.")
                        else:
                            st.error("Le nom du germe est obligatoire.")
                with idc2:
                    if st.button("↩️ Corriger la lecture (annuler)", use_container_width=True, key=f"cancel_id_{real_pi_idx}"):
                        # Remettre le schedule en pending pour permettre correction
                        matching_sch = next((x for x in st.session_state.schedules
                            if x['sample_id'] == pi['sample_id'] and x['when'] == pi['when'] and x['status'] == 'done'), None)
                        if matching_sch:
                            matching_sch['status'] = 'pending'
                            save_schedules(st.session_state.schedules)
                        st.session_state.pending_identifications.pop(real_pi_idx)
                        save_pending_identifications(st.session_state.pending_identifications)
                        st.success("Lecture annulée — vous pouvez la retraiter.")
                        st.rerun()
                with idc3:
                    if st.button("🗑️ Supprimer", use_container_width=True, key=f"del_id_{real_pi_idx}", help="Supprimer définitivement cette lecture en attente"):
                        st.session_state.pending_identifications.pop(real_pi_idx)
                        save_pending_identifications(st.session_state.pending_identifications)
                        st.success("Lecture supprimée.")
                        st.rerun()

    # ── DERNIERS PRÉLÈVEMENTS ─────────────────────────────────────────────────
    if st.session_state.surveillance:
        st.markdown("---")
        st.markdown("### 📋 Derniers résultats enregistrés")
        for r in list(reversed(st.session_state.surveillance[-10:])):
            sc = "#ef4444" if r["status"]=="action" else "#f59e0b" if r["status"]=="alert" else "#22c55e"
            ic = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
            ufc_display = f"{r['ufc']} UFC" if r.get('ufc') else "—"
            st.markdown(f"""
            <div style="background:#f8fafc;border-left:3px solid {sc};border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;gap:12px">
              <span style="font-size:1.1rem">{ic}</span>
              <div style="flex:1">
                <div style="font-size:.78rem;color:#1e293b;font-weight:600">{r['prelevement']} — <span style="font-style:italic">{r['germ_match']}</span></div>
                <div style="font-size:.68rem;color:#0f172a">{r['date']} · {ufc_display} · {r.get('operateur') or 'N/A'}</div>
              </div>
              <span style="font-size:.7rem;color:{sc};font-weight:700">{ufc_display}</span>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 : PLAN URC
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "plan":
    st.markdown("#### 🗺️ Plan URC interactif — placement des prélèvements")

    uploaded = st.file_uploader(
        "Uploader le plan URC (PNG, JPG ou PDF)",
        type=["png", "jpg", "jpeg", "pdf"],
        key="plan_upload_main"
    )

    if uploaded:
        raw = uploaded.read()
        if uploaded.type == "application/pdf":
            pdf_b64 = base64.b64encode(raw).decode()
            surv_points = [{"label": r["prelevement"], "germ": r["germ_match"],
                "ufc": r["ufc"], "date": r["date"], "status": r["status"]}
                for r in st.session_state.surveillance]
            surv_json = json.dumps(surv_points, ensure_ascii=False)
            pts_json = json.dumps(st.session_state.map_points, ensure_ascii=False)

            pdfjs_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f8fafc;color:#1e293b;font-family:'Segoe UI',sans-serif;height:82vh;display:flex;flex-direction:column}}
.toolbar{{padding:8px 12px;background:#ffffff;border-bottom:1.5px solid #e2e8f0;display:flex;gap:8px;align-items:center;flex-shrink:0;flex-wrap:wrap}}
.toolbar input,.toolbar select,.toolbar button{{background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:6px;padding:4px 8px;color:#1e293b;font-size:.75rem}}
.toolbar button{{cursor:pointer}}
.toolbar button:hover,.toolbar button.active{{background:#2563eb;color:#ffffff}}
.map-container{{flex:1;overflow:auto;position:relative;background:#f8fafc}}
.map-inner{{position:relative;display:inline-block}}
#pdfCanvas{{display:block}}
.point{{position:absolute;width:24px;height:24px;border-radius:50%;border:2px solid white;cursor:pointer;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:white;box-shadow:0 0 10px rgba(0,0,0,.6);transition:transform .2s;z-index:10}}
.point:hover{{transform:translate(-50%,-50%) scale(1.5)}}
.point.ok{{background:#22c55e}}.point.alert{{background:#f59e0b}}.point.action{{background:#ef4444}}.point.none{{background:#0f172a}}
.tooltip{{position:fixed;background:#ffffff;border:1.5px solid #e2e8f0;border-radius:8px;padding:10px;font-size:.72rem;pointer-events:none;z-index:1000;display:none;min-width:200px;box-shadow:0 4px 20px rgba(0,0,0,.15)}}
.tooltip.visible{{display:block}}
.legend{{display:flex;gap:10px;align-items:center;font-size:.65rem;color:#0f172a}}
.leg{{display:flex;align-items:center;gap:4px}}
.leg-dot{{width:9px;height:9px;border-radius:50%}}
</style></head><body>
<div class="toolbar">
  <input id="ptLabel" placeholder="Nom du point" style="width:130px">
  <select id="ptSurv" style="width:200px">
    <option value="">-- Lier à un prélèvement --</option>
    {''.join(f'<option value="{r["label"]}">{r["label"]} — {r["germ"]} ({r["ufc"]} UFC)</option>' for r in surv_points)}
  </select>
  <button id="addBtn" onclick="toggleAddMode()">📍 Placer un point</button>
  <button onclick="clearLast()">↩️ Annuler dernier</button>
  <button onclick="clearAll()">🗑️ Tout effacer</button>
  <span style="font-size:.7rem;color:#0f172a">Page :</span>
  <button onclick="prevPage()">◀</button>
  <span id="pageInfo" style="font-size:.72rem;color:#1e293b;min-width:50px;text-align:center">1 / 1</span>
  <button onclick="nextPage()">▶</button>
  <div class="legend">
    <div class="leg"><div class="leg-dot" style="background:#22c55e"></div>OK</div>
    <div class="leg"><div class="leg-dot" style="background:#f59e0b"></div>Alerte</div>
    <div class="leg"><div class="leg-dot" style="background:#ef4444"></div>Action</div>
  </div>
</div>
<div class="map-container" id="mapContainer">
  <div class="map-inner" id="mapInner">
    <canvas id="pdfCanvas"></canvas>
    <div id="tooltip" class="tooltip"></div>
  </div>
</div>
<script>
pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
const PDF_B64='{pdf_b64}';
const survData={surv_json};
let points={pts_json};
let addMode=false,pdfDoc=null,currentPage=1,totalPages=1;
const pdfData=atob(PDF_B64);
const pdfBytes=new Uint8Array(pdfData.length);
for(let i=0;i<pdfData.length;i++)pdfBytes[i]=pdfData.charCodeAt(i);
pdfjsLib.getDocument({{data:pdfBytes}}).promise.then(doc=>{{pdfDoc=doc;totalPages=doc.numPages;document.getElementById('pageInfo').textContent=`${{currentPage}} / ${{totalPages}}`;renderPage(currentPage);}});
function renderPage(n){{pdfDoc.getPage(n).then(page=>{{const vp=page.getViewport({{scale:1.5}});const canvas=document.getElementById('pdfCanvas');canvas.width=vp.width;canvas.height=vp.height;canvas.getContext('2d').clearRect(0,0,vp.width,vp.height);page.render({{canvasContext:canvas.getContext('2d'),viewport:vp}}).promise.then(()=>renderPoints());}});}}
function prevPage(){{if(currentPage>1){{currentPage--;document.getElementById('pageInfo').textContent=`${{currentPage}} / ${{totalPages}}`;renderPage(currentPage);}}}}
function nextPage(){{if(currentPage<totalPages){{currentPage++;document.getElementById('pageInfo').textContent=`${{currentPage}} / ${{totalPages}}`;renderPage(currentPage);}}}}
function toggleAddMode(){{addMode=!addMode;const btn=document.getElementById('addBtn');btn.classList.toggle('active',addMode);btn.textContent=addMode?'✋ Annuler':'📍 Placer un point';document.getElementById('mapContainer').style.cursor=addMode?'crosshair':'default';}}
function renderPoints(){{document.querySelectorAll('.point').forEach(p=>p.remove());const inner=document.getElementById('mapInner');points.forEach((pt,i)=>{{const surv=survData.find(s=>s.label===(pt.survLabel||pt.label));const status=surv?surv.status:'none';const div=document.createElement('div');div.className=`point ${{status}}`;div.style.left=pt.x+'%';div.style.top=pt.y+'%';div.textContent=i+1;div.addEventListener('mouseenter',e=>showTip(e,pt,surv));div.addEventListener('mouseleave',hideTip);inner.appendChild(div);}});}}
function showTip(e,pt,surv){{const t=document.getElementById('tooltip');const icon=surv?{{ok:'✅',alert:'⚠️',action:'🚨',none:'📍'}}[surv.status]||'📍':'📍';t.innerHTML=`<div style="font-weight:700;margin-bottom:6px;color:#1e293b">${{icon}} ${{pt.label}}</div>`+(surv?`<div>Germe : <span style="font-style:italic">${{surv.germ}}</span></div><div>UFC : <strong>${{surv.ufc}}</strong></div><div>Date : ${{surv.date}}</div>`:'<div style="font-size:.68rem">Aucune donnée liée</div>');t.style.left=(e.clientX+15)+'px';t.style.top=(e.clientY-10)+'px';t.classList.add('visible');}}
function hideTip(){{document.getElementById('tooltip').classList.remove('visible');}}
function clearLast(){{if(points.length>0){{points.pop();renderPoints();}}}}
function clearAll(){{if(confirm('Effacer tous les points ?')){{points=[];renderPoints();}}}}
document.getElementById('mapInner').addEventListener('click',function(e){{if(!addMode)return;const canvas=document.getElementById('pdfCanvas');const rect=canvas.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)return;const x=((e.clientX-rect.left)/rect.width*100);const y=((e.clientY-rect.top)/rect.height*100);const label=document.getElementById('ptLabel').value||`Point ${{points.length+1}}`;const survLabel=document.getElementById('ptSurv').value||null;points.push({{x,y,label,survLabel}});renderPoints();toggleAddMode();}});
</script></body></html>"""
            st.components.v1.html(pdfjs_html, height=700, scrolling=False)
        else:
            img_data = base64.b64encode(raw).decode()
            st.session_state.map_image = f"data:{uploaded.type};base64,{img_data}"

    if st.session_state.map_image and (not uploaded or uploaded.type != "application/pdf"):
        surv_points = [{"label": r["prelevement"], "germ": r["germ_match"],
            "ufc": r["ufc"], "date": r["date"], "status": r["status"]}
            for r in st.session_state.surveillance]
        surv_json = json.dumps(surv_points, ensure_ascii=False)
        pts_json = json.dumps(st.session_state.map_points, ensure_ascii=False)

        map_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f8fafc;color:#1e293b;font-family:'Segoe UI',sans-serif;height:80vh;display:flex;flex-direction:column}}
.toolbar{{padding:8px 12px;background:#ffffff;border-bottom:1.5px solid #e2e8f0;display:flex;gap:8px;align-items:center;flex-shrink:0;flex-wrap:wrap}}
.toolbar select,.toolbar input,.toolbar button{{background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:6px;padding:4px 8px;color:#1e293b;font-size:.75rem}}
.toolbar button{{cursor:pointer}}
.toolbar button:hover,.toolbar button.active{{background:#2563eb;color:#ffffff}}
.map-container{{flex:1;overflow:auto;position:relative;background:#f8fafc}}
.map-inner{{position:relative;display:inline-block;min-width:100%;min-height:100%}}
#planImg{{max-width:100%;display:block}}
.point{{position:absolute;width:24px;height:24px;border-radius:50%;border:2px solid white;cursor:pointer;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:white;box-shadow:0 0 10px rgba(0,0,0,.6);transition:transform .2s;z-index:10}}
.point:hover{{transform:translate(-50%,-50%) scale(1.5)}}
.point.ok{{background:#22c55e}}.point.alert{{background:#f59e0b}}.point.action{{background:#ef4444}}.point.none{{background:#0f172a}}
.tooltip{{position:fixed;background:#ffffff;border:1.5px solid #e2e8f0;border-radius:8px;padding:10px;font-size:.72rem;pointer-events:none;z-index:1000;display:none;min-width:200px}}
.tooltip.visible{{display:block}}
.legend{{display:flex;gap:10px;align-items:center;font-size:.65rem;color:#6b7280}}
.leg{{display:flex;align-items:center;gap:4px}}.leg-dot{{width:9px;height:9px;border-radius:50%}}
</style></head><body>
<div class="toolbar">
  <input id="ptLabel" placeholder="Nom du point" style="width:130px">
  <select id="ptSurv" style="width:200px">
    <option value="">-- Lier à un prélèvement --</option>
    {''.join(f'<option value="{r["label"]}">{r["label"]} — {r["germ"]} ({r["ufc"]} UFC)</option>' for r in surv_points)}
  </select>
  <button id="addBtn" onclick="toggleAddMode()">📍 Placer un point</button>
  <button onclick="clearLast()">↩️ Annuler dernier</button>
  <button onclick="clearAll()">🗑️ Tout effacer</button>
  <div class="legend">
    <div class="leg"><div class="leg-dot" style="background:#22c55e"></div>OK</div>
    <div class="leg"><div class="leg-dot" style="background:#f59e0b"></div>Alerte</div>
    <div class="leg"><div class="leg-dot" style="background:#ef4444"></div>Action</div>
    <div class="leg"><div class="leg-dot" style="background:#0f172a"></div>Non lié</div>
  </div>
</div>
<div class="map-container" id="mapContainer">
  <div class="map-inner" id="mapInner">
    <img id="planImg" src="{st.session_state.map_image}" draggable="false">
    <div id="tooltip" class="tooltip"></div>
  </div>
</div>
<script>
let addMode=false;let points={pts_json};const survData={surv_json};
function toggleAddMode(){{addMode=!addMode;const btn=document.getElementById('addBtn');btn.classList.toggle('active',addMode);btn.textContent=addMode?'✋ Annuler':'📍 Placer un point';document.getElementById('mapContainer').style.cursor=addMode?'crosshair':'default';}}
function renderPoints(){{document.querySelectorAll('.point').forEach(p=>p.remove());const img=document.getElementById('planImg');if(!img)return;const inner=document.getElementById('mapInner');points.forEach((pt,i)=>{{const surv=survData.find(s=>s.label===(pt.survLabel||pt.label));const status=surv?surv.status:'none';const div=document.createElement('div');div.className=`point ${{status}}`;div.style.left=pt.x+'%';div.style.top=pt.y+'%';div.textContent=i+1;div.addEventListener('mouseenter',e=>showTip(e,pt,surv,i));div.addEventListener('mouseleave',hideTip);inner.appendChild(div);}});}}
function showTip(e,pt,surv){{const t=document.getElementById('tooltip');const icon=surv?{{ok:'✅',alert:'⚠️',action:'🚨',none:'📍'}}[surv.status]||'📍':'📍';t.innerHTML=`<div style="font-weight:700;margin-bottom:6px">${{icon}} ${{pt.label}}</div>`+(surv?`<div>Germe : <i>${{surv.germ}}</i></div><div>UFC : <b>${{surv.ufc}}</b></div><div>Date : ${{surv.date}}</div>`:'<div>Aucune donnée liée</div>');t.style.left=(e.clientX+15)+'px';t.style.top=(e.clientY-10)+'px';t.classList.add('visible');}}
function hideTip(){{document.getElementById('tooltip').classList.remove('visible');}}
function clearLast(){{if(points.length>0){{points.pop();renderPoints();}}}}
function clearAll(){{if(confirm('Effacer tous les points ?')){{points=[];renderPoints();}}}}
document.getElementById('mapInner').addEventListener('click',function(e){{if(!addMode)return;const img=document.getElementById('planImg');if(!img)return;const rect=img.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)return;const x=((e.clientX-rect.left)/rect.width*100);const y=((e.clientY-rect.top)/rect.height*100);const label=document.getElementById('ptLabel').value||`Point ${{points.length+1}}`;const survLabel=document.getElementById('ptSurv').value||null;points.push({{x,y,label,survLabel}});renderPoints();toggleAddMode();}});
const img=document.getElementById('planImg');if(img)img.addEventListener('load',renderPoints);else renderPoints();
</script></body></html>"""
        st.components.v1.html(map_html, height=650, scrolling=False)
        st.info("💡 Nommez le point, liez-le à un prélèvement (optionnel), cliquez **📍 Placer**, puis cliquez sur le plan.")
    elif not uploaded:
        st.markdown('''<div style="background:#f8fafc;border:2px dashed #e2e8f0;border-radius:12px;padding:48px;text-align:center;color:#0f172a"><div style="font-size:2rem;margin-bottom:8px">🗺️</div><div>Uploadez un plan URC (PNG/JPG/PDF) pour placer les points de prélèvement</div></div>''', unsafe_allow_html=True)



# TAB PLANNING
# ================================================================================
elif active == "planning":
    st.markdown("### 📅 Planning des prélèvements & lectures")

    _today_dt = datetime.today().date()
    _JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    _MOIS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

    def _get_week_start(d):
        return d - timedelta(days=d.weekday())

    def _fmt_week(ws):
        we = ws + timedelta(days=6)
        return f"Semaine du {ws.day} {_MOIS_FR[ws.month]} au {we.day} {_MOIS_FR[we.month]} {we.year}"

    def _build_week_list():
        ws_set = set()
        ws_set.add(_get_week_start(_today_dt))
        for _p in st.session_state.prelevements:
            try: ws_set.add(_get_week_start(datetime.fromisoformat(_p["date"]).date()))
            except: pass
        for _s in st.session_state.schedules:
            try: ws_set.add(_get_week_start(datetime.fromisoformat(_s["due_date"]).date()))
            except: pass
        for _i in range(1, 5):
            ws_set.add(_get_week_start(_today_dt) + timedelta(weeks=_i))
        return sorted(ws_set)

    _week_starts = _build_week_list()
    _week_labels = [_fmt_week(ws) for ws in _week_starts]
    _cur_week_idx = 0
    for _i, _ws in enumerate(_week_starts):
        if _ws <= _today_dt < _ws + timedelta(days=7):
            _cur_week_idx = _i
            break

    plan_tab_view, plan_tab_edit, plan_tab_export = st.tabs(["📅 Vue planning", "✏️ Modifier le planning", "📥 Exporter en Excel"])

    # ═══════════════ VUE PLANNING — PATCHED ═══════════════
    with plan_tab_view:
        today_dt = _today_dt
        JOURS_FR = _JOURS_FR
        MOIS_FR = _MOIS_FR
        week_starts = _week_starts
        week_labels = _week_labels
        cur_week_idx = _cur_week_idx

        sel_week_label = st.selectbox("📆 Sélectionner la semaine", week_labels, index=cur_week_idx, label_visibility="collapsed", key="view_week_sel")
        sel_week_start = week_starts[week_labels.index(sel_week_label)]

        st.markdown(f"""<div style="background:linear-gradient(135deg,#1e40af,#2563eb);border-radius:12px;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between">
          <div style="color:#fff;font-weight:700;font-size:1rem">📅 {sel_week_label}</div>
          <div style="color:#bfdbfe;font-size:.75rem">Semaine {sel_week_start.isocalendar()[1]}</div>
        </div>""", unsafe_allow_html=True)

        def get_day_data(day):
            prelevs_day = [p for p in st.session_state.prelevements
                if p.get('date') and datetime.fromisoformat(p['date']).date() == day
                and not p.get('archived', False)]
            j2_due = [s for s in st.session_state.schedules
                if s['when'] == 'J2' and datetime.fromisoformat(s['due_date']).date() == day]
            j7_due = [s for s in st.session_state.schedules
                if s['when'] == 'J7' and datetime.fromisoformat(s['due_date']).date() == day]
            return prelevs_day, j2_due, j7_due

        # ── PATCH 1 APPLIED: nouveau rendu avec bouton 🗑️ sur J0 + date J0 dans J2/J7 ──
        has_any = False
        for day_offset in range(7):
            day = sel_week_start + timedelta(days=day_offset)
            jour_nom = JOURS_FR[day_offset]
            prelevs, j2, j7 = get_day_data(day)
            is_today = day == today_dt
            is_past = day < today_dt
            is_weekend = day_offset >= 5
            has_activity = bool(prelevs or j2 or j7)

            if not has_activity:
                if not is_weekend:
                    bg = "#eff6ff" if is_today else "#f8fafc"
                    border = "#2563eb" if is_today else "#e2e8f0"
                    today_lbl = " • AUJOURD'HUI" if is_today else ""
                    st.markdown(f'<div style="background:{bg};border:1.5px solid {border};border-radius:10px;padding:10px 16px;margin-bottom:6px;display:flex;align-items:center;gap:12px;opacity:{"1" if not is_past else "0.55"}"><span style="font-weight:700;color:{"#2563eb" if is_today else "#475569"};font-size:.82rem;min-width:130px">{jour_nom} {day.strftime("%d/%m")}{today_lbl}</span><span style="font-size:.72rem;color:#94a3b8;font-style:italic">Aucune activité planifiée</span></div>', unsafe_allow_html=True)
                continue

            has_any = True
            bg = "#fefce8" if is_weekend else ("#eff6ff" if is_today else "#ffffff")
            border = "#2563eb" if is_today else ("#f59e0b" if is_weekend else "#cbd5e1")
            bw = "2px"
            past_style = "opacity:0.7;" if is_past and not is_today else ""
            badges = ""
            if prelevs: badges += f'<span style="background:#7c3aed22;color:#7c3aed;border:1px solid #e9d5ff;border-radius:6px;padding:3px 9px;font-size:.6rem;font-weight:700">🧪 {len(prelevs)} prélèv.</span> '
            if j2: badges += f'<span style="background:#d9770622;color:#d97706;border:1px solid #fde68a;border-radius:6px;padding:3px 9px;font-size:.6rem;font-weight:700">📖 {len(j2)} J2</span> '
            if j7: badges += f'<span style="background:#0369a122;color:#0369a1;border:1px solid #bae6fd;border-radius:6px;padding:3px 9px;font-size:.6rem;font-weight:700">📗 {len(j7)} J7</span>'
            today_badge = f'<span style="background:#2563eb;color:#fff;font-size:.55rem;font-weight:700;padding:2px 8px;border-radius:8px;margin-left:8px">AUJOURD\'HUI</span>' if is_today else ""

            # En-tête du jour
            st.markdown(f'<div style="background:{bg};border:{bw} solid {border};border-radius:12px 12px 0 0;padding:12px 16px 10px 16px;margin-bottom:0;{past_style}"><div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px"><div><span style="font-weight:800;font-size:.95rem;color:{"#1e40af" if is_today else "#0f172a"}">{jour_nom} {day.strftime("%d/%m/%Y")}</span>{today_badge}</div><div style="display:flex;gap:6px;flex-wrap:wrap">{badges}</div></div></div>', unsafe_allow_html=True)

            # Prélèvements J0 avec bouton supprimer
            if prelevs:
                st.markdown(f'<div style="background:{bg};border-left:{bw} solid {border};border-right:{bw} solid {border};padding:6px 16px 4px 16px;{past_style}"><div style="font-size:.6rem;color:#7c3aed;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:4px">🧪 Prélèvements J0 à réaliser</div></div>', unsafe_allow_html=True)
                for p in prelevs:
                    _pc1, _pc2 = st.columns([11, 1])
                    with _pc1:
                        st.markdown(f'<div style="background:#faf5ff;border:1px solid #e9d5ff;border-radius:7px;padding:9px 12px;margin:0 16px 4px 16px"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span style="font-weight:700;color:#0f172a;font-size:.82rem">{p["label"]}</span><span style="background:#7c3aed;color:#fff;font-size:.55rem;padding:2px 7px;border-radius:5px">J0 — {p.get("type","—")}</span><span style="color:#475569;font-size:.7rem">Classe {p.get("room_class","—")}</span><span style="color:#475569;font-size:.7rem">🧫 {p.get("gelose","—")}</span><span style="color:#475569;font-size:.7rem;margin-left:auto">Oper. {p.get("operateur","—")}</span></div></div>', unsafe_allow_html=True)
                    with _pc2:
                        if st.button("🗑️", key=f"del_plan_p_{p['id']}_{day_offset}", help=f"Supprimer {p['label']} + lectures J2/J7"):
                            _sid = p['id']
                            st.session_state.schedules = [x for x in st.session_state.schedules if x['sample_id'] != _sid]
                            save_schedules(st.session_state.schedules)
                            st.session_state.prelevements = [x for x in st.session_state.prelevements if x['id'] != _sid]
                            save_prelevements(st.session_state.prelevements)
                            st.session_state.pending_identifications = [x for x in st.session_state.pending_identifications if x.get('sample_id') != _sid]
                            save_pending_identifications(st.session_state.pending_identifications)
                            st.success(f"✅ Prélèvement **{p['label']}** et ses lectures J2/J7 supprimés.")
                            st.rerun()

            # Lectures J2 (J0 + 2 jours) — avec date J0 visible
            if j2:
                j2_html = f'<div style="background:{bg};border-left:{bw} solid {border};border-right:{bw} solid {border};padding:6px 16px 4px 16px;{past_style}"><div style="font-size:.6rem;color:#d97706;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:4px">📖 Lectures J2 à réaliser (J0 + 2 jours)</div>'
                for sch in j2:
                    is_done = sch["status"] == "done"
                    is_late = not is_done and datetime.fromisoformat(sch["due_date"]).date() < today_dt
                    st_col = "#22c55e" if is_done else ("#ef4444" if is_late else "#d97706")
                    st_txt = "✅ Faite" if is_done else ("⚠️ En retard" if is_late else "⏳ À faire")
                    samp = next((p for p in st.session_state.prelevements if p["id"] == sch["sample_id"]), None)
                    j0_date = samp.get("date", "—") if samp else "—"
                    j2_html += f'<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:7px;padding:9px 12px;margin-bottom:4px"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span style="background:#d97706;color:#fff;font-size:.58rem;padding:2px 8px;border-radius:5px;font-weight:700">J2</span><span style="font-weight:700;color:#0f172a;font-size:.82rem">{sch["label"]}</span><span style="color:#475569;font-size:.7rem">🧫 {samp.get("gelose","—") if samp else "—"}</span><span style="background:#f0fdf4;color:#166534;border:1px solid #86efac;border-radius:4px;padding:1px 6px;font-size:.62rem;font-weight:600">📅 J0 : {j0_date}</span><span style="color:#475569;font-size:.7rem">Oper. {samp.get("operateur","—") if samp else "—"}</span><span style="color:{st_col};font-size:.72rem;font-weight:700;margin-left:auto">{st_txt}</span></div></div>'
                j2_html += "</div>"
                st.markdown(j2_html, unsafe_allow_html=True)

            # Lectures J7 (J0 + 7 jours) — avec date J0 visible
            if j7:
                j7_html = f'<div style="background:{bg};border-left:{bw} solid {border};border-right:{bw} solid {border};padding:6px 16px 4px 16px;{past_style}"><div style="font-size:.6rem;color:#0369a1;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:4px">📗 Lectures J7 à réaliser (J0 + 7 jours)</div>'
                for sch in j7:
                    is_done = sch["status"] == "done"
                    is_late = not is_done and datetime.fromisoformat(sch["due_date"]).date() < today_dt
                    st_col = "#22c55e" if is_done else ("#ef4444" if is_late else "#0369a1")
                    st_txt = "✅ Faite" if is_done else ("⚠️ En retard" if is_late else "⏳ À faire")
                    samp = next((p for p in st.session_state.prelevements if p["id"] == sch["sample_id"]), None)
                    j0_date = samp.get("date", "—") if samp else "—"
                    j7_html += f'<div style="background:#eff6ff;border:1px solid #bae6fd;border-radius:7px;padding:9px 12px;margin-bottom:4px"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span style="background:#0369a1;color:#fff;font-size:.58rem;padding:2px 8px;border-radius:5px;font-weight:700">J7</span><span style="font-weight:700;color:#0f172a;font-size:.82rem">{sch["label"]}</span><span style="color:#475569;font-size:.7rem">🧫 {samp.get("gelose","—") if samp else "—"}</span><span style="background:#f0fdf4;color:#166534;border:1px solid #86efac;border-radius:4px;padding:1px 6px;font-size:.62rem;font-weight:600">📅 J0 : {j0_date}</span><span style="color:#475569;font-size:.7rem">Oper. {samp.get("operateur","—") if samp else "—"}</span><span style="color:{st_col};font-size:.72rem;font-weight:700;margin-left:auto">{st_txt}</span></div></div>'
                j7_html += "</div>"
                st.markdown(j7_html, unsafe_allow_html=True)

            # Pied du cadre
            st.markdown(f'<div style="background:{bg};border-left:{bw} solid {border};border-right:{bw} solid {border};border-bottom:{bw} solid {border};border-radius:0 0 12px 12px;padding:4px 16px;margin-bottom:10px;{past_style}"></div>', unsafe_allow_html=True)

        if not has_any:
            st.markdown("""<div style="background:#f8fafc;border:2px dashed #e2e8f0;border-radius:12px;padding:48px;text-align:center">
              <div style="font-size:2.5rem;margin-bottom:12px">📅</div>
              <div style="font-size:.95rem;color:#475569;font-weight:600">Aucune activité cette semaine</div>
              <div style="font-size:.8rem;color:#94a3b8;margin-top:6px">Enregistrez des prélèvements dans l'onglet Identification & Surveillance</div>
            </div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown("#### Bilan de la semaine")
        week_prelevs = sum(1 for p in st.session_state.prelevements
            if p.get('date') and sel_week_start <= datetime.fromisoformat(p['date']).date() < sel_week_start + timedelta(days=7))
        week_j2 = [s for s in st.session_state.schedules if s['when']=='J2'
            and sel_week_start <= datetime.fromisoformat(s['due_date']).date() < sel_week_start + timedelta(days=7)]
        week_j7 = [s for s in st.session_state.schedules if s['when']=='J7'
            and sel_week_start <= datetime.fromisoformat(s['due_date']).date() < sel_week_start + timedelta(days=7)]
        j2_done = sum(1 for s in week_j2 if s['status']=='done')
        j7_done = sum(1 for s in week_j7 if s['status']=='done')
        total_pending = sum(1 for s in st.session_state.schedules if s['status']=='pending')
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("🧪 Prélèvements", week_prelevs)
        mc2.metric("📖 Lectures J2", f"{j2_done}/{len(week_j2)}", delta=f"{len(week_j2)-j2_done} restantes" if week_j2 else None, delta_color="inverse")
        mc3.metric("📗 Lectures J7", f"{j7_done}/{len(week_j7)}", delta=f"{len(week_j7)-j7_done} restantes" if week_j7 else None, delta_color="inverse")
        mc4.metric("⏳ Total en attente", total_pending)

    # ═══════════════ MODIFIER LE PLANNING ═══════════════
    with plan_tab_edit:
        st.markdown("""<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:12px 16px;margin-bottom:16px">
          <span style="color:#166534;font-weight:700;font-size:.85rem">✏️ Mode édition — modifiez, ajoutez ou supprimez des prélèvements et des lectures dans le planning</span>
        </div>""", unsafe_allow_html=True)

        edit_sub1, edit_sub2 = st.tabs(["Prélèvements planifiés", "Lectures planifiées (J2/J7)"])

        with edit_sub1:
            st.markdown("##### 🧪 Prélèvements actifs")
            active_prelevs = [p for p in st.session_state.prelevements if not p.get('archived', False)]
            if not active_prelevs:
                st.info("Aucun prélèvement actif. Créez-en dans l'onglet Identification & Surveillance.")
            else:
                for pe_i, pe in enumerate(active_prelevs):
                    real_pe_i = st.session_state.prelevements.index(pe)
                    pe_col1, pe_col2 = st.columns([5, 1])
                    with pe_col1:
                        pe_type = pe.get('type','—')
                        pe_class = pe.get('room_class','—')
                        pe_gelose = pe.get('gelose','—')
                        pe_oper = pe.get('operateur','—')
                        pe_date = pe.get('date','—')
                        st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:4px">
                          <span style="font-weight:700;color:#0f172a">{pe['label']}</span>
                          <span style="background:#7c3aed;color:#fff;font-size:.6rem;padding:2px 8px;border-radius:5px">{pe_type}</span>
                          <span style="color:#475569;font-size:.75rem">Classe {pe_class}</span>
                          <span style="color:#475569;font-size:.75rem">🧫 {pe_gelose}</span>
                          <span style="color:#475569;font-size:.75rem">Oper. {pe_oper}</span>
                          <span style="color:#475569;font-size:.75rem">📅 {pe_date}</span>
                        </div>""", unsafe_allow_html=True)
                    with pe_col2:
                        if st.button("✏️ Éditer", key=f"edit_pe_{real_pe_i}", use_container_width=True):
                            st.session_state[f"editing_pe_{real_pe_i}"] = True
                            st.rerun()

                    if st.session_state.get(f"editing_pe_{real_pe_i}", False):
                        with st.container():
                            ep1, ep2, ep3, ep4 = st.columns([3, 2, 2, 2])
                            with ep1:
                                new_label_pe = st.text_input("Nom / Point", value=pe['label'], key=f"ep_label_{real_pe_i}")
                            with ep2:
                                oper_list_pe = [o['nom'] + (' — ' + o.get('profession','') if o.get('profession') else '') for o in st.session_state.operators]
                                cur_oper = pe.get('operateur','')
                                oper_opts = ['— Sélectionner —'] + oper_list_pe
                                oper_idx = next((i+1 for i,o in enumerate(oper_list_pe) if o.startswith(cur_oper)), 0)
                                new_oper_pe = st.selectbox("Opérateur", oper_opts, index=oper_idx, key=f"ep_oper_{real_pe_i}")
                            with ep3:
                                new_date_pe = st.date_input("Date prél.", value=datetime.fromisoformat(pe['date']).date() if pe.get('date') else datetime.today().date(), key=f"ep_date_{real_pe_i}")
                            with ep4:
                                gelose_opts_pe = ["Gélose de sédimentation","Gélose contact (RODAC)","Gélose TSA","Gélose Columbia","Ecouvillonnage","Autre"]
                                cur_g = pe.get('gelose','—')
                                if cur_g not in gelose_opts_pe: gelose_opts_pe.append(cur_g)
                                g_idx = gelose_opts_pe.index(cur_g) if cur_g in gelose_opts_pe else 0
                                new_gelose_pe = st.selectbox("Gélose", gelose_opts_pe, index=g_idx, key=f"ep_gelose_{real_pe_i}")
                            epc1, epc2 = st.columns(2)
                            with epc1:
                                if st.button("✅ Enregistrer", key=f"ep_save_{real_pe_i}", use_container_width=True):
                                    st.session_state.prelevements[real_pe_i]['label'] = new_label_pe
                                    st.session_state.prelevements[real_pe_i]['operateur'] = new_oper_pe if new_oper_pe != '— Sélectionner —' else cur_oper
                                    st.session_state.prelevements[real_pe_i]['date'] = str(new_date_pe)
                                    st.session_state.prelevements[real_pe_i]['gelose'] = new_gelose_pe
                                    for sch in st.session_state.schedules:
                                        if sch['sample_id'] == pe['id']:
                                            days_offset = 2 if sch['when'] == 'J2' else 7
                                            sch['due_date'] = (new_date_pe + timedelta(days=days_offset)).isoformat()
                                    save_prelevements(st.session_state.prelevements)
                                    save_schedules(st.session_state.schedules)
                                    st.session_state[f"editing_pe_{real_pe_i}"] = False
                                    st.success(f"✅ Prélèvement mis à jour — lectures J2/J7 recalculées.")
                                    st.rerun()
                            with epc2:
                                if st.button("Annuler", key=f"ep_cancel_{real_pe_i}", use_container_width=True):
                                    st.session_state[f"editing_pe_{real_pe_i}"] = False
                                    st.rerun()

            st.divider()
            st.markdown("##### ➕ Ajouter un prélèvement manuellement")
            if not st.session_state.points:
                st.warning("Aucun point de prélèvement. Ajoutez-en dans Paramètres.")
            else:
                ap1, ap2, ap3 = st.columns([3, 2, 2])
                with ap1:
                    ap_point_labels = [f"{pt['label']} — {pt.get('type','?')}" for pt in st.session_state.points]
                    ap_sel = st.selectbox("Point de prélèvement", range(len(ap_point_labels)), format_func=lambda i: ap_point_labels[i], key="ap_point_sel")
                    ap_point = st.session_state.points[ap_sel]
                with ap2:
                    oper_list_ap = [o['nom'] + (' — ' + o.get('profession','') if o.get('profession') else '') for o in st.session_state.operators]
                    ap_oper = st.selectbox("Opérateur", ['— Sélectionner —'] + oper_list_ap, key="ap_oper_sel")
                with ap3:
                    ap_date = st.date_input("Date du prélèvement", value=datetime.today().date(), key="ap_date_sel")
                if st.button("➕ Ajouter au planning", use_container_width=True, key="ap_add_btn"):
                    pid = f"s{len(st.session_state.prelevements)+1}_{int(datetime.now().timestamp())}"
                    new_pe = {"id": pid, "label": ap_point['label'], "type": ap_point.get('type'), "gelose": ap_point.get('gelose','—'), "room_class": ap_point.get('room_class'), "operateur": ap_oper if ap_oper != '— Sélectionner —' else '', "date": str(ap_date), "archived": False}
                    st.session_state.prelevements.append(new_pe)
                    j2_d = (ap_date + timedelta(days=2)).isoformat()
                    j7_d = (ap_date + timedelta(days=7)).isoformat()
                    st.session_state.schedules.append({"id": f"sch_{pid}_J2", "sample_id": pid, "label": ap_point['label'], "due_date": j2_d, "when": "J2", "status": "pending"})
                    st.session_state.schedules.append({"id": f"sch_{pid}_J7", "sample_id": pid, "label": ap_point['label'], "due_date": j7_d, "when": "J7", "status": "pending"})
                    save_prelevements(st.session_state.prelevements)
                    save_schedules(st.session_state.schedules)
                    st.success(f"✅ Prélèvement ajouté — J2 le {j2_d[:10]}, J7 le {j7_d[:10]}")
                    st.rerun()

        with edit_sub2:
            st.markdown("##### 📖 Lectures planifiées")
            pending_schs = [s for s in st.session_state.schedules if s['status'] == 'pending']
            if not pending_schs:
                st.info("Aucune lecture planifiée en attente.")
            else:
                for sh_i, sh in enumerate(pending_schs):
                    real_sh_i = st.session_state.schedules.index(sh)
                    sh_date = datetime.fromisoformat(sh['due_date']).date()
                    is_sh_overdue = sh_date < _today_dt
                    samp_sh = next((p for p in st.session_state.prelevements if p['id'] == sh['sample_id']), None)
                    badge_col = "#d97706" if sh['when']=='J2' else "#0369a1"
                    overdue_badge = ' <span style="background:#ef4444;color:#fff;font-size:.55rem;padding:1px 6px;border-radius:6px">EN RETARD</span>' if is_sh_overdue else ''
                    sh_col1, sh_col2, sh_col3 = st.columns([5, 1, 1])
                    with sh_col1:
                        st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:9px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:2px">
                          <span style="background:{badge_col};color:#fff;font-size:.6rem;padding:2px 8px;border-radius:5px;font-weight:700">{sh['when']}</span>
                          <span style="font-weight:700;color:#0f172a;font-size:.82rem">{sh['label']}</span>
                          <span style="color:#475569;font-size:.75rem">📅 {sh_date.strftime('%d/%m/%Y')}</span>
                          {overdue_badge}
                          <span style="color:#475569;font-size:.72rem;margin-left:auto">Oper. {samp_sh.get('operateur','—') if samp_sh else '—'}</span>
                        </div>""", unsafe_allow_html=True)
                    with sh_col2:
                        if st.button("✏️", key=f"edit_sh_{real_sh_i}", use_container_width=True, help="Modifier la date"):
                            st.session_state[f"editing_sh_{real_sh_i}"] = True
                            st.rerun()
                    with sh_col3:
                        if st.button("🗑️", key=f"del_sh_edit_{real_sh_i}", use_container_width=True, help="Supprimer"):
                            st.session_state.schedules.pop(real_sh_i)
                            save_schedules(st.session_state.schedules)
                            st.success("Lecture supprimée.")
                            st.rerun()

                    if st.session_state.get(f"editing_sh_{real_sh_i}", False):
                        with st.container():
                            new_sh_date = st.date_input("Nouvelle date de lecture", value=sh_date, key=f"sh_date_{real_sh_i}")
                            sc1, sc2 = st.columns(2)
                            with sc1:
                                if st.button("✅ Enregistrer", key=f"sh_save_{real_sh_i}", use_container_width=True):
                                    st.session_state.schedules[real_sh_i]['due_date'] = new_sh_date.isoformat()
                                    save_schedules(st.session_state.schedules)
                                    st.session_state[f"editing_sh_{real_sh_i}"] = False
                                    st.success(f"✅ Date mise à jour : {new_sh_date}")
                                    st.rerun()
                            with sc2:
                                if st.button("Annuler", key=f"sh_cancel_{real_sh_i}", use_container_width=True):
                                    st.session_state[f"editing_sh_{real_sh_i}"] = False
                                    st.rerun()
    # ═══════════════ EXPORT EXCEL ═══════════════
    with plan_tab_export:
        st.markdown("#### 📥 Exporter le planning en Excel")
        exp_week_label = st.selectbox("📆 Choisir la période", ["Semaine en cours", "4 semaines à venir", "Tout le planning (toutes les semaines)"], key="exp_scope")
        exp_oper_filter = st.selectbox("Filtrer par opérateur (optionnel)", ["Tous les opérateurs"] + [o['nom'] for o in st.session_state.operators], key="exp_oper")

        if st.button("📊 Générer le fichier Excel", use_container_width=True, key="gen_xlsx"):
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, GradientFill
            from openpyxl.utils import get_column_letter
            import io as _io

            wb = openpyxl.Workbook()

            # ---- couleurs ----
            C_BLUE_DARK  = "1E40AF"
            C_BLUE_MID   = "2563EB"
            C_BLUE_LIGHT = "DBEAFE"
            C_PURPLE     = "7C3AED"
            C_PURPLE_LIGHT = "F5F3FF"
            C_YELLOW     = "D97706"
            C_YELLOW_LIGHT = "FFFBEB"
            C_TEAL       = "0369A1"
            C_TEAL_LIGHT = "EFF6FF"
            C_GREEN      = "16A34A"
            C_RED        = "DC2626"
            C_GREY       = "F8FAFC"
            C_GREY_MID   = "E2E8F0"
            C_WHITE      = "FFFFFF"
            C_TEXT       = "0F172A"

            thin = Side(style="thin", color=C_GREY_MID)
            border_cell = Border(left=thin, right=thin, top=thin, bottom=thin)

            def hdr_font(size=11, bold=True, color=C_WHITE):
                return Font(name="Arial", size=size, bold=bold, color=color)

            def cell_font(size=10, bold=False, color=C_TEXT):
                return Font(name="Arial", size=size, bold=bold, color=color)

            def fill(hex_col):
                return PatternFill("solid", fgColor=hex_col)

            def center():
                return Alignment(horizontal="center", vertical="center", wrap_text=True)

            def left():
                return Alignment(horizontal="left", vertical="center", wrap_text=True)

            # --- Determine date range ---
            exp_today = datetime.today().date()
            if exp_week_label == "Semaine en cours":
                exp_start = exp_today - timedelta(days=exp_today.weekday())
                exp_end = exp_start + timedelta(days=6)
                exp_dates = [exp_start + timedelta(days=i) for i in range(7)]
            elif exp_week_label == "4 semaines à venir":
                exp_start = exp_today - timedelta(days=exp_today.weekday())
                exp_end = exp_start + timedelta(weeks=4, days=6)
                exp_dates = [exp_start + timedelta(days=i) for i in range(28)]
            else:
                all_d = []
                for p in st.session_state.prelevements:
                    try: all_d.append(datetime.fromisoformat(p["date"]).date())
                    except: pass
                for s in st.session_state.schedules:
                    try: all_d.append(datetime.fromisoformat(s["due_date"]).date())
                    except: pass
                if all_d:
                    exp_start = min(all_d)
                    exp_end = max(all_d)
                    exp_dates = [exp_start + timedelta(days=i) for i in range((exp_end - exp_start).days + 1)]
                else:
                    exp_start = exp_today
                    exp_end = exp_today + timedelta(days=6)
                    exp_dates = [exp_start + timedelta(days=i) for i in range(7)]

            # ---- SHEET 1 : Vue chronologique ----
            ws1 = wb.active
            ws1.title = "Planning chronologique"
            ws1.sheet_view.showGridLines = False

            # Titre
            ws1.merge_cells("A1:G1")
            ws1["A1"] = "PLANNING MICROBIOLOGIQUE — MicroSurveillance URC"
            ws1["A1"].font = Font(name="Arial", size=14, bold=True, color=C_WHITE)
            ws1["A1"].fill = fill(C_BLUE_DARK)
            ws1["A1"].alignment = center()
            ws1.row_dimensions[1].height = 30

            ws1.merge_cells("A2:G2")
            ws1["A2"] = f"Généré le {exp_today.strftime('%d/%m/%Y')} — Période : {exp_start.strftime('%d/%m/%Y')} au {exp_end.strftime('%d/%m/%Y')}"
            ws1["A2"].font = Font(name="Arial", size=9, color="475569")
            ws1["A2"].fill = fill(C_BLUE_LIGHT)
            ws1["A2"].alignment = center()
            ws1.row_dimensions[2].height = 18

            # En-têtes colonnes
            headers = ["Date", "Jour", "Type d'activité", "Point de prélèvement", "Classe", "Gélose", "Opérateur", "Statut"]
            col_widths = [14, 12, 22, 30, 10, 30, 25, 14]
            hdr_fills = [C_BLUE_MID]*8

            for col_i, (h, w) in enumerate(zip(headers, col_widths), start=1):
                c = ws1.cell(row=4, column=col_i, value=h)
                c.font = hdr_font(10)
                c.fill = fill(C_BLUE_MID)
                c.alignment = center()
                c.border = border_cell
                ws1.column_dimensions[get_column_letter(col_i)].width = w

            ws1.row_dimensions[4].height = 22
            ws1.freeze_panes = "A5"

            row = 5
            JOURS_FR_XL = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

            for d in exp_dates:
                jour_nom_xl = JOURS_FR_XL[d.weekday()]
                is_wk = d.weekday() >= 5
                day_bg = "FEF9C3" if is_wk else C_WHITE

                # Prélèvements
                day_prelevs = [p for p in st.session_state.prelevements
                    if p.get('date') and datetime.fromisoformat(p['date']).date() == d
                    and not p.get('archived', False)
                    and (exp_oper_filter == "Tous les opérateurs" or p.get('operateur','').startswith(exp_oper_filter))]
                # J2
                day_j2 = [s for s in st.session_state.schedules
                    if s['when']=='J2' and datetime.fromisoformat(s['due_date']).date() == d
                    and (exp_oper_filter == "Tous les opérateurs" or
                         next((p for p in st.session_state.prelevements if p['id']==s['sample_id'] and p.get('operateur','').startswith(exp_oper_filter)), None) is not None)]
                # J7
                day_j7 = [s for s in st.session_state.schedules
                    if s['when']=='J7' and datetime.fromisoformat(s['due_date']).date() == d
                    and (exp_oper_filter == "Tous les opérateurs" or
                         next((p for p in st.session_state.prelevements if p['id']==s['sample_id'] and p.get('operateur','').startswith(exp_oper_filter)), None) is not None)]

                if not day_prelevs and not day_j2 and not day_j7:
                    continue

                for p in day_prelevs:
                    row_data = [d.strftime('%d/%m/%Y'), jour_nom_xl, "Prélèvement", p['label'], p.get('room_class','—'), p.get('gelose','—'), p.get('operateur','—'), "🧪 À réaliser"]
                    for col_i, val in enumerate(row_data, start=1):
                        c = ws1.cell(row=row, column=col_i, value=val)
                        c.font = cell_font(color=C_TEXT if col_i > 1 else C_TEXT, bold=(col_i==4))
                        c.fill = fill(C_PURPLE_LIGHT)
                        c.alignment = left()
                        c.border = border_cell
                    ws1.cell(row=row, column=3).font = Font(name="Arial", size=10, bold=True, color=C_PURPLE)
                    ws1.row_dimensions[row].height = 18
                    row += 1

                for sch in day_j2:
                    samp_xl = next((p for p in st.session_state.prelevements if p['id']==sch['sample_id']), None)
                    is_done = sch['status']=='done'
                    status_txt = "✅ Faite" if is_done else "⏳ À faire"
                    row_data = [d.strftime('%d/%m/%Y'), jour_nom_xl, "Lecture J2", sch['label'], samp_xl.get('room_class','—') if samp_xl else '—', samp_xl.get('gelose','—') if samp_xl else '—', samp_xl.get('operateur','—') if samp_xl else '—', status_txt]
                    for col_i, val in enumerate(row_data, start=1):
                        c = ws1.cell(row=row, column=col_i, value=val)
                        c.fill = fill(C_YELLOW_LIGHT)
                        c.alignment = left()
                        c.border = border_cell
                        c.font = cell_font()
                    ws1.cell(row=row, column=3).font = Font(name="Arial", size=10, bold=True, color=C_YELLOW)
                    ws1.cell(row=row, column=8).font = Font(name="Arial", size=10, bold=True, color=C_GREEN if is_done else C_YELLOW)
                    ws1.row_dimensions[row].height = 18
                    row += 1

                for sch in day_j7:
                    samp_xl = next((p for p in st.session_state.prelevements if p['id']==sch['sample_id']), None)
                    is_done = sch['status']=='done'
                    status_txt = "✅ Faite" if is_done else "⏳ À faire"
                    row_data = [d.strftime('%d/%m/%Y'), jour_nom_xl, "Lecture J7", sch['label'], samp_xl.get('room_class','—') if samp_xl else '—', samp_xl.get('gelose','—') if samp_xl else '—', samp_xl.get('operateur','—') if samp_xl else '—', status_txt]
                    for col_i, val in enumerate(row_data, start=1):
                        c = ws1.cell(row=row, column=col_i, value=val)
                        c.fill = fill(C_TEAL_LIGHT)
                        c.alignment = left()
                        c.border = border_cell
                        c.font = cell_font()
                    ws1.cell(row=row, column=3).font = Font(name="Arial", size=10, bold=True, color=C_TEAL)
                    ws1.cell(row=row, column=8).font = Font(name="Arial", size=10, bold=True, color=C_GREEN if is_done else C_TEAL)
                    ws1.row_dimensions[row].height = 18
                    row += 1

            # Total row
            ws1.cell(row=row, column=1, value=f"TOTAL LIGNES : {row - 5}").font = Font(name="Arial", size=9, bold=True, color="64748B")

            # ---- SHEET 2 : Vue par opérateur ----
            ws2 = wb.create_sheet("Par opérateur")
            ws2.sheet_view.showGridLines = False
            ws2.merge_cells("A1:F1")
            ws2["A1"] = "PLANNING PAR OPÉRATEUR"
            ws2["A1"].font = Font(name="Arial", size=13, bold=True, color=C_WHITE)
            ws2["A1"].fill = fill(C_BLUE_DARK)
            ws2["A1"].alignment = center()
            ws2.row_dimensions[1].height = 28

            col_w2 = [25, 14, 12, 22, 30, 30]
            hdrs2 = ["Opérateur", "Date", "Jour", "Type", "Point", "Gélose"]
            for ci, (h, w) in enumerate(zip(hdrs2, col_w2), start=1):
                c = ws2.cell(row=3, column=ci, value=h)
                c.font = hdr_font(10)
                c.fill = fill(C_BLUE_MID)
                c.alignment = center()
                c.border = border_cell
                ws2.column_dimensions[get_column_letter(ci)].width = w
            ws2.row_dimensions[3].height = 20
            ws2.freeze_panes = "A4"

            # Collect all activities
            all_acts = []
            for p in st.session_state.prelevements:
                if not p.get('archived', False) and p.get('date'):
                    try:
                        d = datetime.fromisoformat(p['date']).date()
                        if exp_start <= d <= exp_end:
                            all_acts.append((p.get('operateur','—'), d, "Prélèvement", p['label'], p.get('gelose','—')))
                    except: pass
            for sch in st.session_state.schedules:
                try:
                    d = datetime.fromisoformat(sch['due_date']).date()
                    if exp_start <= d <= exp_end:
                        samp_xl2 = next((p for p in st.session_state.prelevements if p['id']==sch['sample_id']), None)
                        oper_xl2 = samp_xl2.get('operateur','—') if samp_xl2 else '—'
                        gelose_xl2 = samp_xl2.get('gelose','—') if samp_xl2 else '—'
                        all_acts.append((oper_xl2, d, f"Lecture {sch['when']}", sch['label'], gelose_xl2))
                except: pass

            all_acts.sort(key=lambda x: (x[0], x[1]))
            JOURS_FR_XL2 = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
            r2 = 4
            type_fills = {"Prélèvement": C_PURPLE_LIGHT, "Lecture J2": C_YELLOW_LIGHT, "Lecture J7": C_TEAL_LIGHT}
            type_fonts = {"Prélèvement": C_PURPLE, "Lecture J2": C_YELLOW, "Lecture J7": C_TEAL}

            for oper_x, d_x, type_x, label_x, gelose_x in all_acts:
                bg_x = type_fills.get(type_x, C_WHITE)
                row_data2 = [oper_x, d_x.strftime('%d/%m/%Y'), JOURS_FR_XL2[d_x.weekday()], type_x, label_x, gelose_x]
                for ci, val in enumerate(row_data2, start=1):
                    c = ws2.cell(row=r2, column=ci, value=val)
                    c.fill = fill(bg_x)
                    c.alignment = left()
                    c.border = border_cell
                    c.font = cell_font(bold=(ci==1))
                ws2.cell(row=r2, column=4).font = Font(name="Arial", size=10, bold=True, color=type_fonts.get(type_x, C_TEXT))
                ws2.row_dimensions[r2].height = 17
                r2 += 1

            # ---- SHEET 3 : Légende ----
            ws3 = wb.create_sheet("Légende")
            ws3.sheet_view.showGridLines = False
            ws3["A1"] = "LÉGENDE & GUIDE"
            ws3["A1"].font = Font(name="Arial", size=13, bold=True, color=C_WHITE)
            ws3["A1"].fill = fill(C_BLUE_DARK)
            ws3.merge_cells("A1:C1")
            ws3["A1"].alignment = center()
            ws3.row_dimensions[1].height = 26
            ws3.column_dimensions["A"].width = 30
            ws3.column_dimensions["B"].width = 20
            ws3.column_dimensions["C"].width = 40

            legend_rows = [
                ("Type d'entrée", "Couleur de fond", "Description"),
                ("Prélèvement", "Violet clair", "Prélèvement microbiologique à réaliser"),
                ("Lecture J2", "Jaune clair", "Lecture de la gélose à J+2 après prélèvement"),
                ("Lecture J7", "Bleu clair", "Lecture de la gélose à J+7 après prélèvement"),
                ("", "", ""),
                ("Statut", "", ""),
                ("✅ Faite", "", "Lecture validée dans l'application"),
                ("⏳ À faire", "", "Lecture planifiée, non encore traitée"),
                ("⚠️ En retard", "", "Date de lecture dépassée sans validation"),
            ]
            leg_fills = [C_BLUE_MID, C_PURPLE_LIGHT, C_YELLOW_LIGHT, C_TEAL_LIGHT, C_WHITE, C_WHITE, C_WHITE, C_WHITE, C_WHITE]
            leg_fonts = [C_WHITE, C_PURPLE, C_YELLOW, C_TEAL, C_TEXT, C_TEXT, C_GREEN, "475569", C_RED]

            for lr_i, (lr_a, lr_b, lr_c) in enumerate(legend_rows, start=2):
                for ci, val in enumerate([lr_a, lr_b, lr_c], start=1):
                    c = ws3.cell(row=lr_i, column=ci, value=val)
                    c.fill = fill(leg_fills[lr_i-2])
                    c.alignment = left()
                    c.border = border_cell
                    c.font = Font(name="Arial", size=10, bold=(lr_i==2 or lr_a in ["Statut","Type d'entrée"]), color=leg_fonts[lr_i-2])
                ws3.row_dimensions[lr_i].height = 18

            # Save to buffer
            buf = _io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            filename = f"planning_URC_{exp_today.strftime('%Y%m%d')}.xlsx"
            st.download_button(
                label="⬇️ Télécharger le planning Excel",
                data=buf.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success(f"✅ Fichier **{filename}** généré — 3 feuilles : Vue chronologique, Par opérateur, Légende")

# TAB 4 : HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "historique":
    st.markdown("### 📋 Historique de surveillance")
    if st.session_state.surveillance:
        c_dl, c_cl = st.columns(2)
        with c_dl:
            csv_str = io.StringIO()
            writer = csv.DictWriter(csv_str, fieldnames=st.session_state.surveillance[0].keys())
            writer.writeheader(); writer.writerows(st.session_state.surveillance)
            st.download_button("⬇️ Télécharger CSV", csv_str.getvalue(), "surveillance.csv", "text/csv", use_container_width=True)
        with c_cl:
            if st.button("🗑️ Vider l'historique", use_container_width=True):
                st.session_state.surveillance = []
                if os.path.exists(CSV_FILE): os.remove(CSV_FILE)
                st.rerun()
        total = len(st.session_state.surveillance)
        alerts = sum(1 for r in st.session_state.surveillance if r["status"]=="alert")
        actions = sum(1 for r in st.session_state.surveillance if r["status"]=="action")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total", total); c2.metric("✅ Conformes", total-alerts-actions)
        c3.metric("⚠️ Alertes", alerts); c4.metric("🚨 Actions", actions)
        st.divider()
        for r in reversed(st.session_state.surveillance):
            sc = "#ef4444" if r["status"]=="action" else "#f59e0b" if r["status"]=="alert" else "#22c55e"
            ic = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
            with st.expander(f"{ic} {r['date']} — {r['prelevement']} — {r['germ_match']} — {r['ufc']} UFC/m³"):
                c1,c2,c3,c4 = st.columns([3,3,3,1])
                c1.markdown(f"**Germe saisi :** {r['germ_saisi']}")
                c1.markdown(f"**Correspondance :** {r['germ_match']} ({r['match_score']})")
                c2.markdown(f"**UFC/m³ :** {r['ufc']}")
                c2.markdown(f"**Seuil alerte :** ≥{r['alert_threshold']} | **Seuil action :** ≥{r['action_threshold']}")
                c3.markdown(f"**Opérateur :** {r.get('operateur','N/A')}")
                c3.markdown(f"**Remarque :** {r.get('remarque','—')}")
                with c4:
                    real_i = st.session_state.surveillance.index(r)
                    if st.button("🗑️", key=f"del_surv_{real_i}", help="Supprimer"):
                        st.session_state.surveillance.pop(real_i)
                        save_surveillance(st.session_state.surveillance)
                        st.rerun()
    else:
        st.info("Aucun prélèvement enregistré.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 : PARAMÈTRES & SEUILS
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "parametres":
    st.markdown("### ⚙️ Paramètres — Seuils & Mesures correctives")

    subtab_seuils, subtab_mesures, subtab_points, subtab_operateurs = st.tabs(["📏 Seuils par criticité", "📋 Mesures correctives par origine", "📍 Points de prélèvement", "👤 Opérateurs"])

    # ── SEUILS ────────────────────────────────────────────────────────────────
    with subtab_seuils:
        st.markdown("Configurez les seuils d'alerte et d'action **par niveau de criticité**.")
        thresholds = st.session_state.thresholds
        risk_info = [
            (5, "🔴 Criticité 5 — Critique",  "#ef4444"),
            (4, "🟠 Criticité 4 — Majeur",    "#f97316"),
            (3, "🟡 Criticité 3 — Important", "#f59e0b"),
            (2, "🟢 Criticité 2 — Modéré",    "#84cc16"),
            (1, "🟢 Criticité 1 — Limité",    "#22c55e"),
        ]
        new_thresholds = {}
        for risk, title, color in risk_info:
            th = thresholds.get(risk, DEFAULT_THRESHOLDS[risk])
            germs_list = ', '.join(sorted(set(g['name'] for g in st.session_state.germs if g['risk']==risk)))
            st.markdown(f"""<div style="background:#f8fafc;border-left:4px solid {color};border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:4px">
              <div style="font-size:.85rem;font-weight:700;color:{color}">{title}</div>
              <div style="font-size:.65rem;color:#0f172a;margin-top:2px">{germs_list[:150]}{'...' if len(germs_list)>150 else ''}</div>
            </div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                new_alert = st.number_input("⚠️ Seuil d'alerte (UFC/m³)", min_value=0, value=int(th.get("alert",10)), key=f"alert_{risk}")
            with c2:
                new_action = st.number_input("🚨 Seuil d'action (UFC/m³)", min_value=0, value=int(th.get("action",50)), key=f"action_{risk}")
            new_thresholds[risk] = {"alert": new_alert, "action": new_action}
            st.divider()

        cs, cr = st.columns(2)
        with cs:
            if st.button("💾 Sauvegarder les seuils", use_container_width=True):
                st.session_state.thresholds = new_thresholds
                save_thresholds_and_measures(new_thresholds, st.session_state.measures)
                st.success("✅ Seuils sauvegardés !")
        with cr:
            if st.button("↩️ Réinitialiser les seuils", use_container_width=True):
                st.session_state.thresholds = {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}
                save_thresholds_and_measures(st.session_state.thresholds, st.session_state.measures)
                st.success("✅ Seuils réinitialisés.")
                st.rerun()

    # ── MESURES CORRECTIVES ───────────────────────────────────────────────────
    with subtab_mesures:
        st.markdown("Gérez les **mesures correctives** applicables lors d'un dépassement de seuil.")
        om = st.session_state.origin_measures
        scope_options = ["all"] + list(dict.fromkeys(ALL_ORIGINS))
        scope_labels = {"all": "🌐 Toutes les origines", "Air": "💨 Air",
            "Humidité": "💧 Humidité", "Flore fécale": "🦠 Flore fécale",
            "Oropharynx / Gouttelettes": "😷 Oropharynx / Gouttelettes",
            "Peau / Muqueuses": "🖐️ Peau / Muqueuses", "Peau / Muqueuse": "🖐️ Peau / Muqueuse",
            "Sol / Carton / Surface sèche": "📦 Sol / Carton / Surface sèche",
        }
        type_labels = {"alert": "⚠️ Alerte", "action": "🚨 Action", "both": "⚠️🚨 Alerte & Action"}
        type_colors = {"alert": "#f59e0b", "action": "#ef4444", "both": "#818cf8"}
        risk_labels_filter = {"all": "🌐 Toutes criticités", "1": "🟢 C.1", "2": "🟢 C.2", "3": "🟡 C.3", "4": "🟠 C.4", "5": "🔴 C.5"}

        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1])
        with col_f1:
            filter_scope = st.selectbox("Filtrer par origine", ["Tout afficher"] + list(scope_labels.values()), key="filter_scope", label_visibility="collapsed")
        with col_f2:
            filter_risk_lbl = st.selectbox("Filtrer par criticité", list(risk_labels_filter.values()), key="filter_risk", label_visibility="collapsed")
            filter_risk_map = {v: k for k, v in risk_labels_filter.items()}
            active_risk_filter = filter_risk_map.get(filter_risk_lbl, "all")
        with col_f3:
            filter_type = st.selectbox("Type", ["Alerte & Action", "⚠️ Alerte seulement", "🚨 Action seulement"], key="filter_type", label_visibility="collapsed")
        with col_f4:
            if st.button("➕ Nouvelle mesure", use_container_width=True):
                st.session_state.show_new_measure = True

        scope_filter_map = {v: k for k, v in scope_labels.items()}
        active_scope_filter = scope_filter_map.get(filter_scope, None)
        active_type_filter = None if filter_type == "Alerte & Action" else ("alert" if "Alerte" in filter_type else "action")

        st.divider()

        if st.session_state.get("show_new_measure", False):
            with st.container():
                st.markdown("#### ➕ Nouvelle mesure corrective")
                nmc1, nmc2, nmc3, nmc4 = st.columns([3, 2, 1.5, 1.5])
                with nmc1:
                    nm_text = st.text_input("Texte de la mesure *", key="nm_text")
                with nmc2:
                    nm_scope_label = st.selectbox("Origine", list(scope_labels.values()), key="nm_scope")
                    nm_scope = scope_filter_map.get(nm_scope_label, "all")
                with nmc3:
                    risk_opts_nm = {"all":"🌐 Toutes","1":"🟢 1","2":"🟢 2","3":"🟡 3","4":"🟠 4","5":"🔴 5","[3,4,5]":"3-4-5","[4,5]":"4-5","[1,2,3]":"1-2-3"}
                    nm_risk_lbl = st.selectbox("Criticité", list(risk_opts_nm.values()), key="nm_risk")
                    nm_risk_key = {v: k for k, v in risk_opts_nm.items()}.get(nm_risk_lbl, "all")
                    if nm_risk_key == "all": nm_risk = "all"
                    elif nm_risk_key.startswith("["): nm_risk = json.loads(nm_risk_key)
                    else: nm_risk = int(nm_risk_key)
                with nmc4:
                    nm_type_label = st.selectbox("Type", list(type_labels.values()), key="nm_type")
                    nm_type = {v: k for k, v in type_labels.items()}.get(nm_type_label, "alert")
                nb1, nb2 = st.columns(2)
                with nb1:
                    if st.button("✅ Ajouter la mesure", use_container_width=True, key="nm_submit"):
                        if nm_text.strip():
                            new_id = f"m{len(om)+1:03d}_custom"
                            om.append({"id": new_id, "text": nm_text.strip(), "scope": nm_scope, "risk": nm_risk, "type": nm_type})
                            save_origin_measures(om)
                            st.session_state.origin_measures = om
                            st.session_state.show_new_measure = False
                            st.success("✅ Mesure ajoutée !")
                            st.rerun()
                        else:
                            st.error("Le texte est obligatoire.")
                with nb2:
                    if st.button("Annuler", use_container_width=True, key="nm_cancel"):
                        st.session_state.show_new_measure = False
                        st.rerun()

        def passes_filter(m):
            if active_scope_filter and active_scope_filter != "Tout afficher":
                if m["scope"] != active_scope_filter:
                    return False
            if active_type_filter:
                if m["type"] != active_type_filter and m["type"] != "both":
                    return False
            if active_risk_filter != "all":
                mr = m.get("risk", "all")
                if mr != "all":
                    if isinstance(mr, list):
                        if int(active_risk_filter) not in mr:
                            return False
                    else:
                        if str(mr) != active_risk_filter:
                            return False
            return True

        filtered_measures = [m for m in om if passes_filter(m)]
        from collections import OrderedDict
        groups = OrderedDict()
        for sc in (["all"] + list(dict.fromkeys(ALL_ORIGINS))):
            grp = [m for m in filtered_measures if m["scope"] == sc]
            if grp:
                groups[sc] = grp

        if not filtered_measures:
            st.info("Aucune mesure ne correspond aux filtres sélectionnés.")
        else:
            for scope_key, group_measures in groups.items():
                scope_lbl = scope_labels.get(scope_key, scope_key)
                st.markdown(f"""<div style="background:#f8fafc;border-left:3px solid #38bdf8;border-radius:0 8px 8px 0;padding:8px 14px;margin:12px 0 6px 0">
                  <span style="font-size:.78rem;font-weight:700;color:#38bdf8">{scope_lbl}</span>
                  <span style="font-size:.62rem;color:#0f172a;margin-left:8px">{len(group_measures)} mesure(s)</span>
                </div>""", unsafe_allow_html=True)

                for mi, m in enumerate(group_measures):
                    real_idx = om.index(m)
                    tcol = type_colors.get(m["type"], "#0f172a")
                    tlbl = type_labels.get(m["type"], m["type"])

                    if st.session_state.get(f"edit_m_{real_idx}", False):
                        with st.container():
                            ec1, ec2, ec3, ec4 = st.columns([3, 2, 1.5, 1.5])
                            with ec1:
                                edit_text = st.text_input("Texte", value=m["text"], key=f"et_{real_idx}")
                            with ec2:
                                cur_scope_lbl = scope_labels.get(m["scope"], m["scope"])
                                cur_scope_idx = list(scope_labels.values()).index(cur_scope_lbl) if cur_scope_lbl in scope_labels.values() else 0
                                edit_scope_lbl = st.selectbox("Origine", list(scope_labels.values()), index=cur_scope_idx, key=f"es_{real_idx}")
                                edit_scope = scope_filter_map.get(edit_scope_lbl, "all")
                            with ec3:
                                risk_opts_e = {"all":"🌐 Toutes","1":"🟢 1","2":"🟢 2","3":"🟡 3","4":"🟠 4","5":"🔴 5","[3,4,5]":"3-4-5","[4,5]":"4-5","[1,2,3]":"1-2-3"}
                                cur_mr = m.get("risk","all")
                                if cur_mr == "all": cur_rk = "all"
                                elif isinstance(cur_mr, list): cur_rk = str(cur_mr).replace(" ","")
                                else: cur_rk = str(cur_mr)
                                cur_r_lbl = risk_opts_e.get(cur_rk, "🌐 Toutes")
                                cur_r_idx = list(risk_opts_e.values()).index(cur_r_lbl) if cur_r_lbl in risk_opts_e.values() else 0
                                edit_risk_lbl = st.selectbox("Criticité", list(risk_opts_e.values()), index=cur_r_idx, key=f"er_{real_idx}")
                                edit_risk_key = {v: k for k, v in risk_opts_e.items()}.get(edit_risk_lbl, "all")
                                if edit_risk_key == "all": edit_risk = "all"
                                elif edit_risk_key.startswith("["): edit_risk = json.loads(edit_risk_key)
                                else: edit_risk = int(edit_risk_key)
                            with ec4:
                                cur_type_lbl = type_labels.get(m["type"], m["type"])
                                cur_type_idx = list(type_labels.values()).index(cur_type_lbl) if cur_type_lbl in type_labels.values() else 0
                                edit_type_lbl = st.selectbox("Type", list(type_labels.values()), index=cur_type_idx, key=f"ety_{real_idx}")
                                edit_type = {v: k for k, v in type_labels.items()}.get(edit_type_lbl, "alert")
                            eb1, eb2 = st.columns(2)
                            with eb1:
                                if st.button("✅ Valider", use_container_width=True, key=f"ev_{real_idx}"):
                                    om[real_idx] = {**m, "text": edit_text, "scope": edit_scope, "risk": edit_risk, "type": edit_type}
                                    save_origin_measures(om)
                                    st.session_state.origin_measures = om
                                    st.session_state[f"edit_m_{real_idx}"] = False
                                    st.rerun()
                            with eb2:
                                if st.button("Annuler", use_container_width=True, key=f"ec_{real_idx}"):
                                    st.session_state[f"edit_m_{real_idx}"] = False
                                    st.rerun()
                    else:
                        mr = m.get("risk", "all")
                        if mr == "all": risk_badge = "🌐"
                        elif isinstance(mr, list):
                            rcols = {1:"#22c55e",2:"#84cc16",3:"#f59e0b",4:"#f97316",5:"#ef4444"}
                            risk_badge = " ".join(f'<span style="color:{rcols.get(r,"#0f172a")};font-weight:700">{r}</span>' for r in mr)
                        else: risk_badge = str(mr)
                        row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([4.5, 1.2, 1.5, 0.8, 0.8])
                        with row_c1:
                            st.markdown(f'<div style="padding:6px 0;font-size:.8rem;color:#1e293b">• {m["text"]}</div>', unsafe_allow_html=True)
                        with row_c2:
                            st.markdown(f'<div style="padding:6px 0;font-size:.63rem;color:#0f172a;text-align:center">Nv.{risk_badge}</div>', unsafe_allow_html=True)
                        with row_c3:
                            st.markdown(f'<div style="padding:6px 0;font-size:.65rem;color:{tcol};font-weight:600;text-align:center">{tlbl}</div>', unsafe_allow_html=True)
                        with row_c4:
                            if st.button("✏️", key=f"edit_btn_{real_idx}"):
                                st.session_state[f"edit_m_{real_idx}"] = True
                                st.rerun()
                        with row_c5:
                            if st.button("🗑️", key=f"del_m_{real_idx}"):
                                om.pop(real_idx)
                                save_origin_measures(om)
                                st.session_state.origin_measures = om
                                st.rerun()

        st.divider()
        col_sr, col_def = st.columns(2)
        with col_sr:
            if st.button("💾 Sauvegarder les mesures", use_container_width=True):
                save_origin_measures(om)
                st.success("✅ Mesures sauvegardées !")
        with col_def:
            if st.button("↩️ Réinitialiser les mesures par défaut", use_container_width=True):
                st.session_state.origin_measures = [dict(m) for m in DEFAULT_ORIGIN_MEASURES]
                save_origin_measures(st.session_state.origin_measures)
                st.success("✅ Mesures réinitialisées.")
                st.rerun()

    # ── POINTS DE PRÉLÈVEMENT — TYPE: Air / Surface + Gélose ─────────────────
    with subtab_points:
        st.markdown("Gérez les points de prélèvement — définissez le nom, le type, la classe et la gélose utilisée.")

        if not st.session_state.points:
            st.info("Aucun point défini pour le moment.")
        else:
            for i, pt in enumerate(list(st.session_state.points)):
                gelose = pt.get('gelose', '—')
                pt_type = pt.get('type', '—')
                pt_class = pt.get('room_class', '—')
                type_icon = "💨" if pt_type == "Air" else "🧴"
                c1, c2, c3 = st.columns([5, 1, 1])
                with c1:
                    st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:8px 14px;display:flex;gap:16px;align-items:center">
                      <span style="font-weight:700;font-size:.85rem;color:#1e293b">{type_icon} {pt['label']}</span>
                      <span style="background:#eff6ff;color:#1d4ed8;border-radius:6px;padding:2px 8px;font-size:.65rem;font-weight:600">{pt_type}</span>
                      <span style="background:#f8fafc;color:#475569;border-radius:6px;padding:2px 8px;font-size:.65rem;border:1px solid #e2e8f0">Classe : {pt_class}</span>
                      <span style="background:#f0fdf4;color:#166534;border-radius:6px;padding:2px 8px;font-size:.65rem;border:1px solid #86efac">🧫 {gelose}</span>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    if st.button("✏️", key=f"edit_pt_{i}"):
                        st.session_state._edit_point = i
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_pt_{i}"):
                        st.session_state.points.pop(i)
                        save_points(st.session_state.points)
                        st.success("Point supprimé")
                        st.rerun()

        st.divider()

        if st.session_state.get('_edit_point') is not None:
            idx = st.session_state._edit_point
            pt = st.session_state.points[idx]
            st.markdown(f"### ✏️ Modifier le point — {pt['label']}")
            ec1, ec2, ec3, ec4 = st.columns([3, 2, 2, 2])
            with ec1:
                new_label = st.text_input("Nom du point", value=pt['label'], key="pt_edit_label")
            with ec2:
                new_type = st.selectbox("Type de prélèvement", ["Air", "Surface"], index=["Air", "Surface"].index(pt.get('type', 'Air')) if pt.get('type', 'Air') in ["Air", "Surface"] else 0, key="pt_edit_type")
            with ec3:
                new_room = st.text_input("Classe de salle", value=pt.get('room_class', ''), key="pt_edit_room", placeholder="Ex: ISO 5, Classe D...")
            with ec4:
                # Gélose selon le type
                if new_type == "Air":
                    gelose_opts = ["Gélose de sédimentation", "Gélose TSA (sédimentation)", "Gélose Columbia (sédimentation)", "Autre"]
                else:
                    gelose_opts = ["Gélose contact (RODAC)", "Gélose contact TSA", "Gélose contact Columbia", "Ecouvillonnage", "Autre"]
                cur_gelose = pt.get('gelose', gelose_opts[0])
                if cur_gelose in gelose_opts:
                    gelose_idx = gelose_opts.index(cur_gelose)
                else:
                    gelose_opts.append(cur_gelose)
                    gelose_idx = len(gelose_opts) - 1
                new_gelose = st.selectbox("Gélose", gelose_opts, index=gelose_idx, key="pt_edit_gelose")

            if st.button("✅ Enregistrer les modifications", key="pt_save_edit"):
                st.session_state.points[idx] = {
                    "id": pt.get('id', f"p{idx+1}"),
                    "label": new_label,
                    "type": new_type,
                    "room_class": new_room,
                    "gelose": new_gelose
                }
                save_points(st.session_state.points)
                st.session_state._edit_point = None
                st.success("✅ Point mis à jour")
                st.rerun()
            if st.button("Annuler", key="pt_cancel_edit"):
                st.session_state._edit_point = None
                st.rerun()
        else:
            st.markdown("### ➕ Ajouter un point de prélèvement")
            np_col1, np_col2, np_col3, np_col4 = st.columns([3, 2, 2, 2])
            with np_col1:
                np_label = st.text_input("Nom du point *", placeholder="Ex: Salle 3 — Poste A", key="np_label")
            with np_col2:
                np_type = st.selectbox("Type de prélèvement", ["Air", "Surface"], key="np_type")
            with np_col3:
                np_room = st.text_input("Classe de salle", placeholder="Ex: ISO 5, Classe D", key="np_room")
            with np_col4:
                if np_type == "Air":
                    gelose_opts_new = ["Gélose de sédimentation", "Gélose TSA (sédimentation)", "Gélose Columbia (sédimentation)", "Autre"]
                else:
                    gelose_opts_new = ["Gélose contact (RODAC)", "Gélose contact TSA", "Gélose contact Columbia", "Ecouvillonnage", "Autre"]
                np_gelose = st.selectbox("Gélose", gelose_opts_new, key="np_gelose")

            if st.button("➕ Ajouter le point", key="np_add"):
                if not np_label.strip():
                    st.error("Le nom du point est requis")
                else:
                    nid = f"p{len(st.session_state.points)+1}_{int(datetime.now().timestamp())}"
                    st.session_state.points.append({
                        "id": nid,
                        "label": np_label.strip(),
                        "type": np_type,
                        "room_class": np_room.strip(),
                        "gelose": np_gelose
                    })
                    save_points(st.session_state.points)
                    st.success(f"✅ Point **{np_label}** ajouté ({np_type} — {np_gelose})")
                    st.rerun()

    # ── OPÉRATEURS ────────────────────────────────────────────────────────────
    with subtab_operateurs:
        st.markdown("Gérez la liste des opérateurs habilités à réaliser les prélèvements microbiologiques.")

        ops = st.session_state.operators

        if not ops:
            st.info("Aucun opérateur enregistré. Ajoutez-en ci-dessous.")
        else:
            st.markdown(f"""<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:12px 16px;margin-bottom:16px">
              <span style="font-size:.75rem;color:#0369a1;font-weight:700">👥 {len(ops)} opérateur(s) enregistré(s)</span>
            </div>""", unsafe_allow_html=True)

            for i, op in enumerate(ops):
                nom = op.get('nom', '—')
                profession = op.get('profession', '—')
                oc1, oc2, oc3 = st.columns([5, 1, 1])
                with oc1:
                    st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;display:flex;gap:16px;align-items:center">
                      <div style="background:#2563eb;color:#fff;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;flex-shrink:0">{nom[0].upper() if nom else '?'}</div>
                      <div>
                        <div style="font-weight:700;font-size:.9rem;color:#0f172a">{nom}</div>
                        <div style="font-size:.72rem;color:#475569;margin-top:2px">👔 {profession}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                with oc2:
                    if st.button("✏️", key=f"edit_op_{i}"):
                        st.session_state._edit_operator = i
                        st.rerun()
                with oc3:
                    if st.button("🗑️", key=f"del_op_{i}"):
                        ops.pop(i)
                        save_operators(ops)
                        st.session_state.operators = ops
                        st.success("Opérateur supprimé.")
                        st.rerun()

        st.divider()

        # Edit operator
        if st.session_state.get('_edit_operator') is not None:
            idx = st.session_state._edit_operator
            op = st.session_state.operators[idx]
            st.markdown(f"### ✏️ Modifier l'opérateur — {op.get('nom','')}")
            ec1, ec2 = st.columns(2)
            with ec1:
                edit_nom = st.text_input("Nom complet *", value=op.get('nom',''), key="op_edit_nom")
            with ec2:
                profession_opts = [
                    "Préparateur en pharmacie hospitalière",
                    "Pharmacien",
                    "Technicien de laboratoire",
                    "Infirmier(e)",
                    "Aide-soignant(e)",
                    "Agent de stérilisation",
                    "Responsable qualité",
                    "Autre",
                ]
                cur_prof = op.get('profession', '')
                if cur_prof not in profession_opts:
                    profession_opts.append(cur_prof)
                prof_idx = profession_opts.index(cur_prof) if cur_prof in profession_opts else 0
                edit_prof = st.selectbox("Profession / Fonction *", profession_opts, index=prof_idx, key="op_edit_prof")

            eb1, eb2 = st.columns(2)
            with eb1:
                if st.button("✅ Enregistrer les modifications", use_container_width=True, key="op_save_edit"):
                    if edit_nom.strip():
                        st.session_state.operators[idx] = {"nom": edit_nom.strip(), "profession": edit_prof}
                        save_operators(st.session_state.operators)
                        st.session_state._edit_operator = None
                        st.success("✅ Opérateur mis à jour")
                        st.rerun()
                    else:
                        st.error("Le nom est obligatoire.")
            with eb2:
                if st.button("Annuler", use_container_width=True, key="op_cancel_edit"):
                    st.session_state._edit_operator = None
                    st.rerun()
        else:
            # Add new operator
            st.markdown("### ➕ Ajouter un opérateur")
            nc1, nc2 = st.columns(2)
            with nc1:
                new_nom = st.text_input("Nom complet *", placeholder="Ex: Marie Dupont", key="op_new_nom")
            with nc2:
                profession_opts_new = [
                    "Préparateur en pharmacie hospitalière",
                    "Pharmacien",
                    "Technicien de laboratoire",
                    "Infirmier(e)",
                    "Aide-soignant(e)",
                    "Agent de stérilisation",
                    "Responsable qualité",
                    "Autre",
                ]
                new_prof = st.selectbox("Profession / Fonction *", profession_opts_new, key="op_new_prof")

            if st.button("➕ Ajouter l'opérateur", key="op_add"):
                if not new_nom.strip():
                    st.error("Le nom est obligatoire.")
                elif any(o['nom'].lower() == new_nom.strip().lower() for o in st.session_state.operators):
                    st.error("Un opérateur avec ce nom existe déjà.")
                else:
                    st.session_state.operators.append({"nom": new_nom.strip(), "profession": new_prof})
                    save_operators(st.session_state.operators)
                    st.success(f"✅ Opérateur **{new_nom}** ajouté ({new_prof})")
                    st.rerun()