import streamlit as st
import json
import csv
import io
import os
import base64
from datetime import datetime
import difflib

st.set_page_config(page_title="MicroSurveillance URC", page_icon="🦠", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif}
.stApp,[data-testid="stAppViewContainer"]{background:#0a0e1a}
[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
[data-testid="stSidebar"]{background:#0d1321!important;border-right:1px solid #1e2d45}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding:1rem}
.stButton>button{border-radius:8px;font-size:.8rem}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div{background:#111827!important;color:#e2e8f0!important;border-color:#1e2d45!important}
label{color:#94a3b8!important;font-size:.78rem!important}
.stAlert{border-radius:10px}
h1,h2,h3{color:#e2e8f0!important}
div[data-testid="stExpander"]{background:#111827;border:1px solid #1e2d45;border-radius:10px}
div[data-testid="stNumberInput"] input{background:#111827!important;color:#e2e8f0!important}
</style>""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
RISK_COLORS = {1:"#22c55e",2:"#84cc16",3:"#f59e0b",4:"#f97316",5:"#ef4444"}
RISK_LABELS = {1:"Limité",2:"Modéré",3:"Important",4:"Majeur",5:"Critique"}
CSV_FILE = "surveillance_data.csv"
GERMS_FILE = "germs_data.json"
THRESHOLDS_FILE = "thresholds_config.json"

# Seuils par défaut selon criticité
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

# 4th-level origin nodes (used for corrective measures scope)
ALL_ORIGINS = [
    "Air",
    "Humidité", 
    "Flore fécale",
    "Oropharynx / Gouttelettes",
    "Peau / Muqueuses",
    "Peau / Muqueuse",
    "Sol / Carton / Surface sèche",
    "Sol / Carton / Surface sèche",
    "Sol / Carton / Surface sèche",
]

MEASURES_FILE = "measures_config.json"

# Default checklist measures per origin
# Each measure: {"id": str, "text": str, "scope": "all"|origin_name, "type": "alert"|"action"|"both"}
DEFAULT_ORIGIN_MEASURES = [
    # risk: "all" = toutes criticités, ou liste ex: [4,5] = criticité 4 et 5 uniquement
    # ── Toutes origines, toutes criticités ───────────────────────────────────
    {"id":"m001","text":"Documenter l'événement dans le registre qualité","scope":"all","risk":"all","type":"alert"},
    {"id":"m002","text":"Programmer un prélèvement de contrôle","scope":"all","risk":"all","type":"alert"},
    {"id":"m003","text":"Surveiller l'évolution des prochains résultats","scope":"all","risk":"all","type":"alert"},
    # ── Toutes origines, criticité 3-4-5 ─────────────────────────────────────
    {"id":"m004","text":"Informer le responsable qualité","scope":"all","risk":[3,4,5],"type":"alert"},
    {"id":"m005","text":"Augmenter la fréquence de surveillance","scope":"all","risk":[3,4,5],"type":"alert"},
    {"id":"m006","text":"Renforcer le bionettoyage de la zone concernée","scope":"all","risk":[3,4,5],"type":"alert"},
    # ── Toutes origines, criticité 4-5 — ACTION ───────────────────────────────
    {"id":"m010","text":"Alerter le pharmacien responsable et la direction","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m011","text":"Isoler la zone contaminée","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m012","text":"ARRÊT des préparations critiques si nécessaire","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m013","text":"Décontamination renforcée avec désinfectant adapté (Surfa'Safe / APA)","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m014","text":"Ne pas reprendre l'activité avant résultat conforme","scope":"all","risk":[4,5],"type":"action"},
    {"id":"m015","text":"Déclaration d'événement indésirable (fiche EI)","scope":"all","risk":[4,5],"type":"action"},
    # ── Toutes origines, criticité 1-2-3 — ACTION ─────────────────────────────
    {"id":"m016","text":"Renforcer le bionettoyage de la zone","scope":"all","risk":[1,2,3],"type":"action"},
    {"id":"m017","text":"Vérifier les procédures de bionettoyage en vigueur","scope":"all","risk":[1,2,3],"type":"action"},
    {"id":"m018","text":"Informer le responsable d'équipe","scope":"all","risk":[1,2,3],"type":"action"},
    # ── Air — Alerte ──────────────────────────────────────────────────────────
    {"id":"m020","text":"Contrôler l'intégrité des filtres HEPA","scope":"Air","risk":"all","type":"alert"},
    {"id":"m021","text":"Vérifier les flux d'air et la pression différentielle","scope":"Air","risk":"all","type":"alert"},
    {"id":"m022","text":"Contrôler les entrées / sorties de matériel (cartons, vêtements)","scope":"Air","risk":[3,4,5],"type":"alert"},
    # ── Air — Action ──────────────────────────────────────────────────────────
    {"id":"m023","text":"Contrôler l'étanchéité des jonctions de filtres HEPA","scope":"Air","risk":[4,5],"type":"action"},
    {"id":"m024","text":"Bilan fongique complet (Aspergillus, Fusarium, Penicillium)","scope":"Air","risk":[4,5],"type":"action"},
    {"id":"m025","text":"Décontamination par nébulisation H2O2 si moisissure critique","scope":"Air","risk":[5],"type":"action"},
    # ── Humidité — Alerte ─────────────────────────────────────────────────────
    {"id":"m030","text":"Identifier et traiter les sources d'humidité","scope":"Humidité","risk":"all","type":"alert"},
    {"id":"m031","text":"Vérifier l'étanchéité des canalisations et conduites d'eau","scope":"Humidité","risk":"all","type":"alert"},
    {"id":"m032","text":"Contrôler le taux d'humidité relative de la salle","scope":"Humidité","risk":[3,4,5],"type":"alert"},
    # ── Humidité — Action ─────────────────────────────────────────────────────
    {"id":"m033","text":"Nettoyage et désinfection renforcés des surfaces humides","scope":"Humidité","risk":"all","type":"action"},
    {"id":"m034","text":"Décontamination au peroxyde d'hydrogène si Pseudomonas/Mycobactérie","scope":"Humidité","risk":[4,5],"type":"action"},
    {"id":"m035","text":"Recherche et élimination de tout biofilm résiduel","scope":"Humidité","risk":[4,5],"type":"action"},
    # ── Sol / Carton / Surface sèche — Alerte ────────────────────────────────
    {"id":"m040","text":"Contrôler les entrées de matières premières et emballages","scope":"Sol / Carton / Surface sèche","risk":"all","type":"alert"},
    {"id":"m041","text":"Renforcer le bionettoyage des sols et surfaces","scope":"Sol / Carton / Surface sèche","risk":"all","type":"alert"},
    {"id":"m042","text":"Vérifier le protocole de dé-cartonnage à l'entrée","scope":"Sol / Carton / Surface sèche","risk":[3,4,5],"type":"alert"},
    # ── Sol / Carton / Surface sèche — Action ────────────────────────────────
    {"id":"m043","text":"Retrait et destruction des cartons et emballages suspects","scope":"Sol / Carton / Surface sèche","risk":"all","type":"action"},
    {"id":"m044","text":"Décontamination sporicide si spores détectées (Bacillus, Clostridium)","scope":"Sol / Carton / Surface sèche","risk":[4,5],"type":"action"},
    {"id":"m045","text":"Bilan sporal complet de la zone","scope":"Sol / Carton / Surface sèche","risk":[5],"type":"action"},
    # ── Peau / Muqueuses — Alerte ─────────────────────────────────────────────
    {"id":"m050","text":"Vérifier les procédures d'habillage et port des EPI","scope":"Peau / Muqueuses","risk":"all","type":"alert"},
    {"id":"m051","text":"Contrôler la technique de friction hydro-alcoolique","scope":"Peau / Muqueuses","risk":"all","type":"alert"},
    # ── Peau / Muqueuses — Action ─────────────────────────────────────────────
    {"id":"m052","text":"Renforcer la formation du personnel (hygiène des mains)","scope":"Peau / Muqueuses","risk":[3,4,5],"type":"action"},
    {"id":"m053","text":"Vérifier l'absence de lésion cutanée chez le personnel","scope":"Peau / Muqueuses","risk":[4,5],"type":"action"},
    {"id":"m054","text":"Enquête sur le personnel intervenant dans la zone","scope":"Peau / Muqueuses","risk":[4,5],"type":"action"},
    # ── Peau / Muqueuse — Alerte ─────────────────────────────────────────────
    {"id":"m055","text":"Vérifier les procédures d'habillage et port des EPI","scope":"Peau / Muqueuse","risk":"all","type":"alert"},
    {"id":"m056","text":"Contrôler la technique de friction hydro-alcoolique","scope":"Peau / Muqueuse","risk":"all","type":"alert"},
    # ── Peau / Muqueuse — Action ─────────────────────────────────────────────
    {"id":"m057","text":"Renforcer la formation du personnel (hygiène des mains)","scope":"Peau / Muqueuse","risk":[3,4,5],"type":"action"},
    {"id":"m058","text":"Vérifier l'absence de lésion cutanée ou infection fongique","scope":"Peau / Muqueuse","risk":[4,5],"type":"action"},
    # ── Flore fécale — Alerte ────────────────────────────────────────────────
    {"id":"m060","text":"Vérifier les procédures de lavage des mains","scope":"Flore fécale","risk":"all","type":"alert"},
    {"id":"m061","text":"Contrôler la chaîne de décontamination des équipements","scope":"Flore fécale","risk":"all","type":"alert"},
    # ── Flore fécale — Action ────────────────────────────────────────────────
    {"id":"m062","text":"Recherche de source de contamination fécale","scope":"Flore fécale","risk":[3,4,5],"type":"action"},
    {"id":"m063","text":"Nettoyage désinfectant à spectre large (entérobactéries/ERV)","scope":"Flore fécale","risk":"all","type":"action"},
    {"id":"m064","text":"Test de portage pour le personnel si E. coli / Entérocoque multirésistant","scope":"Flore fécale","risk":[4,5],"type":"action"},
    # ── Oropharynx / Gouttelettes — Alerte ───────────────────────────────────
    {"id":"m070","text":"Vérifier le port correct du masque FFP2 ou chirurgical","scope":"Oropharynx / Gouttelettes","risk":"all","type":"alert"},
    {"id":"m071","text":"Rappeler l'interdiction de parler dans la ZAC","scope":"Oropharynx / Gouttelettes","risk":"all","type":"alert"},
    # ── Oropharynx / Gouttelettes — Action ───────────────────────────────────
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
    # Build a lookup from DEFAULT_GERMS by name for backfilling
    defaults_by_name = {}
    for d in DEFAULT_GERMS:
        defaults_by_name.setdefault(d["name"], d)
    if os.path.exists(GERMS_FILE):
        try:
            with open(GERMS_FILE) as f:
                data = json.load(f)
            for g in data:
                dflt = defaults_by_name.get(g["name"], {})
                # Backfill notes/comment from defaults if missing or null in saved file
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
    with open(GERMS_FILE, "w") as f:
        json.dump(germs, f, ensure_ascii=False, indent=2)

def load_thresholds():
    if os.path.exists(THRESHOLDS_FILE):
        try:
            with open(THRESHOLDS_FILE) as f:
                raw = json.load(f)
            # Keys stored as strings in JSON
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
    with open(THRESHOLDS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_thresholds_for_risk(risk, thresholds):
    return thresholds.get(risk, {"alert": 25, "action": 40})

def load_origin_measures():
    if os.path.exists(MEASURES_FILE):
        try:
            with open(MEASURES_FILE) as f:
                return json.load(f)
        except:
            pass
    return [dict(m) for m in DEFAULT_ORIGIN_MEASURES]

def save_origin_measures(measures):
    with open(MEASURES_FILE, "w") as f:
        json.dump(measures, f, ensure_ascii=False, indent=2)

def load_surveillance():
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
    st.session_state.germs = load_germs()
    # Auto-save after load to persist any backfilled notes/comments
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
if "simplified_plan" not in st.session_state:
    st.session_state.simplified_plan = None
if "simplified_plan_orig" not in st.session_state:
    st.session_state.simplified_plan_orig = None

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-size:.7rem;letter-spacing:.15em;text-transform:uppercase;color:#64748b;margin-bottom:12px">NAVIGATION</p>', unsafe_allow_html=True)
    tabs_cfg = [
        ("logigramme",   "📊", "Logigramme"),
        ("surveillance", "🔍", "Identification & Surveillance"),
        ("plan",         "🗺️", "Plan URC"),
        ("historique",   "📋", "Historique"),
        ("parametres",   "⚙️", "Paramètres & Seuils"),
    ]
    for key, icon, label in tabs_cfg:
        t = "primary" if st.session_state.active_tab == key else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True, type=t):
            st.session_state.active_tab = key
            st.rerun()
    st.divider()
    st.markdown('<p style="font-size:.62rem;color:#64748b;text-align:center">MicroSurveillance URC<br>v4.0</p>', unsafe_allow_html=True)

active = st.session_state.active_tab

st.markdown('<h1 style="font-size:1.3rem;letter-spacing:.1em;text-transform:uppercase;color:#38bdf8!important;margin-bottom:0">🦠 MicroSurveillance URC</h1>', unsafe_allow_html=True)
st.caption("Surveillance microbiologique — Unité de Reconstitution des Chimiothérapies")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 : LOGIGRAMME
# ═══════════════════════════════════════════════════════════════════════════════
if active == "logigramme":
    col_btn1, col_btn2 = st.columns([1,1])
    with col_btn1:
        if st.button("➕ Ajouter un germe", use_container_width=True, type="primary"):
            st.session_state.show_add = not st.session_state.show_add
            st.session_state.edit_idx = None
    with col_btn2:
        if st.button("💾 Sauvegarder", use_container_width=True):
            save_germs(st.session_state.germs)
            st.success("✅ Germes sauvegardés !")

    def germ_form(existing=None, idx=None):
        is_edit = existing is not None
        with st.container(border=True):
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
                    cats = ["Peau / Muqueuse"] if "Humain" in new_origine else ["Humidité","Sol / Carton / Surface sèche","Sol / Carton / Surface sèche","Air"]
                cur_cat = existing["path"][3] if is_edit and existing["path"][3] in cats else cats[0]
                new_cat = st.selectbox("Catégorie *", cats, index=cats.index(cur_cat) if cur_cat in cats else 0)
                new_pathotype = st.text_input("Type de pathogène", value=existing.get("pathotype","") if is_edit else "")
                new_notes = st.text_area("📝 Notes", value=existing.get("notes","") or "" if is_edit else "", height=55, help="Courte note affichée sous le nom (ex: Sporulé, Levure...)")
                new_comment = st.text_area("💬 Commentaire détaillé", value=existing.get("comment","") or "" if is_edit else "", height=55, help="Commentaire long affiché en bas de la fiche (mécanisme, résistance...)")
            with c3:
                risk_opts = ["1 — Limité","2 — Modéré","3 — Important","4 — Majeur","5 — Critique"]
                new_risk_raw = st.selectbox("Criticité *", risk_opts, index=(existing["risk"]-1) if is_edit else 1)
                risk_num = int(new_risk_raw[0])
                # Show auto thresholds
                th = get_thresholds_for_risk(risk_num, st.session_state.thresholds)
                st.markdown(f"""<div style="background:#111827;border:1px solid #1e2d45;border-radius:8px;padding:10px;margin-top:4px">
                    <div style="font-size:.62rem;color:#64748b;margin-bottom:6px;letter-spacing:.1em">SEUILS AUTO (criticité {risk_num})</div>
                    <div style="display:flex;gap:8px">
                      <div style="flex:1;text-align:center;background:rgba(245,158,11,.1);border:1px solid #f59e0b44;border-radius:6px;padding:5px;font-size:.68rem;color:#f59e0b;font-weight:600">⚠️ Alerte<br>≥ {th['alert']} UFC</div>
                      <div style="flex:1;text-align:center;background:rgba(239,68,68,.1);border:1px solid #ef444444;border-radius:6px;padding:5px;font-size:.68rem;color:#ef4444;font-weight:600">🚨 Action<br>≥ {th['action']} UFC</div>
                    </div></div>""", unsafe_allow_html=True)
                new_surfa = st.selectbox("Surfa'Safe *",
                    ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (biofilm)","Risque de résistance (spore)"],
                    index=["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (biofilm)","Risque de résistance (spore)"].index(existing["surfa"]) if is_edit and existing.get("surfa") in ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (biofilm)","Risque de résistance (spore)"] else 0)
                new_apa = st.selectbox("APA *",
                    ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (spore)"],
                    index=["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (spore)"].index(existing["apa"]) if is_edit and existing.get("apa") in ["Sensible","Risque modéré de résistance","Risque de résistance","Risque de résistance (spore)"] else 0)

            cb1, cb2 = st.columns([1,1])
            with cb1:
                if st.button("✅ " + ("Modifier" if is_edit else "Ajouter"), type="primary", use_container_width=True, key="form_submit"):
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

    tree_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0e1a;color:#e2e8f0;font-family:'Segoe UI',sans-serif;height:85vh;overflow:hidden}}
.app{{display:flex;height:85vh}}
.tree-wrap{{flex:1;overflow:auto;padding:16px;scrollbar-width:thin;scrollbar-color:#1e2d45 transparent}}
svg{{min-width:700px}}
.node rect{{fill:#111827;stroke:#1e2d45;stroke-width:1.5;transition:all 0.2s;cursor:pointer}}
.node.highlighted rect{{stroke-width:2.5;filter:drop-shadow(0 0 6px var(--col))}}
.node text{{font-size:11px;fill:#64748b;pointer-events:none;font-family:'Courier New',monospace}}
.node.highlighted text{{fill:#fff;font-weight:600}}
.link{{fill:none;stroke:#1e2d45;stroke-width:1.5;transition:all 0.3s}}
.link.highlighted{{stroke-width:2.5}}
.right-panel{{width:300px;border-left:1px solid #1e2d45;display:flex;flex-direction:column;background:#0d1321;flex-shrink:0}}
.sbox{{padding:10px;border-bottom:1px solid #1e2d45}}
.sbox input{{width:100%;background:#111827;border:1px solid #1e2d45;border-radius:8px;padding:7px 10px;color:#e2e8f0;font-size:.75rem;outline:none}}
.sbox input:focus{{border-color:#38bdf8}}
.germ-list{{flex:1;overflow-y:auto;padding:5px;scrollbar-width:thin;scrollbar-color:#1e2d45 transparent}}
.germ-item{{display:flex;align-items:center;gap:7px;padding:5px 9px;border-radius:6px;cursor:pointer;transition:background .15s;font-size:.72rem;color:#94a3b8;border:1px solid transparent;margin-bottom:2px}}
.germ-item:hover{{background:#111827;color:#e2e8f0}}
.germ-item.active{{background:#111827;border-color:#38bdf8;color:#e2e8f0}}
.risk-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.info-panel{{border-top:1px solid #1e2d45;padding:12px;background:#111827;display:none;max-height:380px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:#1e2d45 transparent}}
.info-panel.visible{{display:block}}
.info-name{{font-size:.85rem;font-weight:700;font-style:italic;color:#e2e8f0;margin-bottom:4px;line-height:1.3}}
.info-path{{font-size:.6rem;color:#38bdf8;opacity:.8;margin-bottom:7px;font-family:monospace}}
.info-badge{{display:inline-flex;align-items:center;gap:5px;font-size:.63rem;padding:2px 9px;border-radius:20px;border:1px solid;margin-bottom:9px}}
.info-lbl{{font-size:.57rem;letter-spacing:.1em;text-transform:uppercase;color:#64748b;margin-bottom:2px;margin-top:6px}}
.info-val{{font-size:.75rem;color:#e2e8f0;line-height:1.4}}
.sens{{display:flex;align-items:center;gap:7px;padding:5px 9px;border-radius:6px;border:1px solid #1e2d45;font-size:.7rem;margin-top:2px}}
.ok{{color:#22c55e;font-weight:700}}.warn{{color:#f97316;font-weight:700}}.crit{{color:#ef4444;font-weight:700}}
.notes-box{{margin-top:6px;padding:6px 9px;border-radius:6px;background:rgba(56,189,248,0.05);border:1px solid rgba(56,189,248,0.1);font-size:.7rem;color:#94a3b8;line-height:1.5}}
.threshold-row{{display:flex;gap:6px;margin-top:6px}}
.th-badge{{flex:1;text-align:center;padding:4px;border-radius:6px;font-size:.65rem;font-weight:600}}
.new-badge{{font-size:.55rem;background:rgba(56,189,248,0.15);color:#38bdf8;border:1px solid #38bdf855;border-radius:4px;padding:1px 5px;margin-left:4px}}
</style></head><body>
<div class="app">
  <div class="tree-wrap"><svg id="svg"></svg></div>
  <div class="right-panel">
    <div class="sbox"><input type="text" id="sbox" placeholder="🔍 Rechercher..." oninput="filterList()"></div>
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
    const col=LEVEL_COLS[node.depth]||"#64748b";g.style.setProperty('--col',col);
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
  // exactPath is the full path array from root to the hovered node
  // Build a set of "parentPath|childPath" pairs that are valid for this exact branch
  const pathStr = exactPath.join('|||');
  const validNodePaths = new Set();
  const validLinkPairs = new Set();
  // All prefixes of exactPath are valid nodes
  for(let i=1;i<=exactPath.length;i++){{
    validNodePaths.add(exactPath.slice(0,i).join('|||'));
  }}
  // All consecutive pairs in exactPath are valid links
  for(let i=0;i<exactPath.length-1;i++){{
    validLinkPairs.add(exactPath[i]+'>>'+exactPath[i+1]);
  }}
  document.querySelectorAll('.node').forEach(n=>{{
    const nodePath = n.dataset.fullpath||'';
    n.classList.toggle('highlighted', validNodePaths.has(nodePath));
  }});
  document.querySelectorAll('.link').forEach(l=>{{
    // Use full paths stored on link to avoid matching same-named nodes in different branches
    const srcFullPath = l.dataset.sourcefull||'';
    const tgtFullPath = l.dataset.targetfull||'';
    const on = validNodePaths.has(srcFullPath) && validNodePaths.has(tgtFullPath);
    l.classList.toggle('highlighted',on);
    if(on){{
      const depth=srcFullPath.split('|||').length-1;
      l.style.stroke=LEVEL_COLS[depth]||'#38bdf8';
    }} else l.style.stroke='';
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
  const tree=buildTree();computeLayout(tree);buildPaths(tree);
  const leaf=allNodes(tree).find(n=>n.name===g.path[g.path.length-1]);
  if(leaf)document.querySelector('.tree-wrap').scrollTo({{top:Math.max(0,leaf.y-150),behavior:'smooth'}});
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

    st.components.v1.html(tree_html, height=750, scrolling=False)

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

    with st.form("surveillance_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            germ_input = st.text_input("Germe identifié *", placeholder="Ex: Pseudomonas aeruginosa")
            prelevement = st.text_input("Point de prélèvement *", placeholder="Ex: Salle 3 - Poste A")
        with c2:
            ufc = st.number_input("UFC/m³ *", min_value=0, value=0)
            date_prelev = st.date_input("Date", value=datetime.today())
        with c3:
            operateur = st.text_input("Opérateur", placeholder="Nom")
            remarque = st.text_area("Remarque", height=80)
        submitted = st.form_submit_button("🔍 Analyser & Enregistrer", type="primary", use_container_width=True)

    if submitted and germ_input and prelevement:
        match, score = find_germ_match(germ_input, st.session_state.germs)
        if match and score > 0.4:
            risk = match["risk"]
            th = get_thresholds_for_risk(risk, st.session_state.thresholds)
            alert_th = th["alert"]
            action_th = th["action"]
            col = RISK_COLORS[risk]

            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e2d45;border-radius:12px;padding:16px;margin:12px 0">
              <div style="font-size:.7rem;color:#64748b;margin-bottom:4px">CORRESPONDANCE TROUVÉE ({int(score*100)}%)</div>
              <div style="font-size:1rem;font-weight:700;font-style:italic;color:#e2e8f0">{match['name']}</div>
              <div style="font-size:.65rem;color:#38bdf8;margin:4px 0">{' › '.join(match['path'])}</div>
              <span style="display:inline-flex;align-items:center;gap:5px;font-size:.65rem;padding:2px 9px;border-radius:20px;border:1px solid {col}55;color:{col};background:{col}22">
                Niveau {risk} — {RISK_LABELS[risk]}
              </span>
              <span style="margin-left:8px;font-size:.65rem;color:#64748b">Seuil alerte ≥{alert_th} UFC · Seuil action ≥{action_th} UFC</span>
            </div>
            """, unsafe_allow_html=True)

            # Get origin (4th path node) for this germ
            germ_origin = match["path"][3] if len(match["path"]) > 3 else None
            # Filter origin measures: "all" scope + matching origin scope, filtered by type
            def get_origin_measures_for(mtype):
                ms_list = st.session_state.origin_measures
                def risk_matches(m, r):
                    mr = m.get("risk", "all")
                    if mr == "all": return True
                    if isinstance(mr, list): return r in mr
                    return False
                relevant = [m for m in ms_list
                    if (m["scope"] == "all" or m["scope"] == germ_origin)
                    and (m["type"] == mtype or m["type"] == "both")
                    and risk_matches(m, risk)]
                return relevant

            def render_checklist(items, color, bg_color):
                lines = "".join(f'<div style="display:flex;align-items:flex-start;gap:8px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05)"><span style="color:{color};font-size:.9rem;margin-top:1px">☐</span><span style="font-size:.78rem;color:#e2e8f0;line-height:1.5">{m["text"]}</span></div>' for m in items)
                return lines or f'<div style="font-size:.75rem;color:#64748b;padding:5px">Aucune mesure configurée pour cette origine.</div>'

            status = "ok"
            if ufc >= action_th:
                status = "action"
                action_items = get_origin_measures_for("action")
                checklist_html = render_checklist(action_items, "#ef4444", "rgba(239,68,68,0.1)")
                origin_lbl = f" — Origine : {germ_origin}" if germ_origin else ""
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.15);border:3px solid #ef4444;border-radius:12px;padding:20px;margin:12px 0">
                  <div style="font-size:1.6rem;font-weight:800;color:#ef4444;text-align:center">🚨 SEUIL D'ACTION DÉPASSÉ</div>
                  <div style="font-size:1rem;color:#fca5a5;margin-top:6px;text-align:center">{ufc} UFC/m³ ≥ {action_th} UFC/m³ — <i>{match['name']}</i></div>
                  <div style="font-size:.8rem;color:#ef4444;margin-top:4px;text-align:center;font-weight:600">Point : {prelevement}{origin_lbl}</div>
                  <div style="margin-top:14px;background:rgba(239,68,68,0.08);border-radius:8px;padding:12px">
                    <div style="font-size:.72rem;color:#ef4444;font-weight:700;letter-spacing:.1em;margin-bottom:8px">⚡ MESURES CORRECTIVES IMMÉDIATES ({len(action_items)} actions)</div>
                    {checklist_html}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            elif ufc >= alert_th:
                status = "alert"
                alert_items = get_origin_measures_for("alert")
                checklist_html = render_checklist(alert_items, "#f59e0b", "rgba(245,158,11,0.1)")
                origin_lbl = f" — Origine : {germ_origin}" if germ_origin else ""
                st.markdown(f"""
                <div style="background:rgba(245,158,11,0.12);border:2px solid #f59e0b;border-radius:12px;padding:16px;margin:12px 0">
                  <div style="font-size:1.3rem;font-weight:700;color:#f59e0b;text-align:center">⚠️ SEUIL D'ALERTE DÉPASSÉ</div>
                  <div style="font-size:.9rem;color:#fcd34d;margin-top:4px;text-align:center">{ufc} UFC/m³ ≥ {alert_th} UFC/m³ — <i>{match['name']}</i></div>
                  <div style="font-size:.8rem;color:#f59e0b;margin-top:4px;text-align:center">Point : {prelevement}{origin_lbl}</div>
                  <div style="margin-top:12px;background:rgba(245,158,11,0.08);border-radius:8px;padding:12px">
                    <div style="font-size:.72rem;color:#f59e0b;font-weight:700;letter-spacing:.1em;margin-bottom:8px">📋 MESURES À METTRE EN PLACE ({len(alert_items)} actions)</div>
                    {checklist_html}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success(f"✅ Résultat conforme — {ufc} UFC/m³ (seuil alerte: ≥{alert_th}, seuil action: ≥{action_th})")

            record = {"date": str(date_prelev), "prelevement": prelevement,
                "germ_saisi": germ_input, "germ_match": match["name"],
                "match_score": f"{int(score*100)}%", "ufc": ufc, "risk": risk,
                "alert_threshold": alert_th, "action_threshold": action_th,
                "status": status, "operateur": operateur, "remarque": remarque}
            st.session_state.surveillance.append(record)
            save_surveillance(st.session_state.surveillance)
        else:
            st.warning(f"⚠️ Aucune correspondance fiable pour **{germ_input}**. Vérifiez le nom ou ajoutez ce germe.")

    if st.session_state.surveillance:
        st.markdown("### 📋 Derniers prélèvements")
        for r in list(reversed(st.session_state.surveillance[-10:])):
            sc = "#ef4444" if r["status"]=="action" else "#f59e0b" if r["status"]=="alert" else "#22c55e"
            ic = "🚨" if r["status"]=="action" else "⚠️" if r["status"]=="alert" else "✅"
            st.markdown(f"""
            <div style="background:#111827;border-left:3px solid {sc};border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;gap:12px">
              <span style="font-size:1.1rem">{ic}</span>
              <div style="flex:1">
                <div style="font-size:.78rem;color:#e2e8f0;font-weight:600">{r['prelevement']} — <span style="font-style:italic">{r['germ_match']}</span></div>
                <div style="font-size:.68rem;color:#64748b">{r['date']} · {r['ufc']} UFC/m³ · {r.get('operateur') or 'N/A'}</div>
              </div>
              <span style="font-size:.7rem;color:{sc};font-weight:700">{r['ufc']} UFC</span>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 : PLAN URC
# ═══════════════════════════════════════════════════════════════════════════════
elif active == "plan":
    try:
        import cv2
        CV2_OK = True
    except ImportError:
        CV2_OK = False
    try:
        import numpy as np
        NP_OK = True
    except ImportError:
        NP_OK = False
    try:
        from PIL import Image as PILImage
        PIL_OK = True
    except ImportError:
        PIL_OK = False

    def img_to_b64(arr):
        pil = PILImage.fromarray(arr)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def simplify_plan_image(img_array, sensitivity=50, wall_thickness=2, remove_text=True):
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        thresh_val = max(50, min(230, 255 - sensitivity))
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)
        if remove_text:
            nb_components, output, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
            sizes = stats[1:, -1]
            clean = np.zeros_like(binary)
            for i in range(len(sizes)):
                if sizes[i] >= 120:
                    clean[output == i + 1] = 255
        else:
            clean = binary.copy()
        kclose = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kclose)
        contours_all, hierarchy = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS)
        result = np.ones((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8) * 255
        if contours_all and hierarchy is not None:
            for i, cnt in enumerate(contours_all):
                area = cv2.contourArea(cnt)
                if area < 30:
                    continue
                th = wall_thickness + 1 if area > 10000 else wall_thickness if area > 2000 else max(1, wall_thickness - 1)
                cv2.drawContours(result, [cnt], -1, (20, 20, 20), th)
        return result

    # ── SOUS-ONGLETS PLAN ─────────────────────────────────────────────────────
    plan_tab1, plan_tab2 = st.tabs(["🗺️ Plan interactif", "✂️ Simplifier un plan"])

    # ─────────────────────────────────────────────────────────────────────────
    # PLAN TAB 1 : placement points
    # ─────────────────────────────────────────────────────────────────────────
    with plan_tab1:
        st.markdown("#### 🗺️ Plan URC interactif — placement des prélèvements")

        uploaded = st.file_uploader(
            "Uploader le plan URC (PNG, JPG ou PDF)",
            type=["png", "jpg", "jpeg", "pdf"],
            key="plan_upload_main"
        )

        if uploaded:
            raw = uploaded.read()
            if uploaded.type == "application/pdf":
                # PDF : rendu côté navigateur via PDF.js (aucune dépendance serveur)
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
body{{background:#0a0e1a;color:#e2e8f0;font-family:'Segoe UI',sans-serif;height:82vh;display:flex;flex-direction:column}}
.toolbar{{padding:8px 12px;background:#111827;border-bottom:1px solid #1e2d45;display:flex;gap:8px;align-items:center;flex-shrink:0;flex-wrap:wrap}}
.toolbar input{{background:#0a0e1a;border:1px solid #1e2d45;border-radius:6px;padding:4px 8px;color:#e2e8f0;font-size:.75rem}}
.toolbar select{{background:#0a0e1a;border:1px solid #1e2d45;border-radius:6px;padding:4px 8px;color:#e2e8f0;font-size:.75rem}}
.toolbar button{{background:#1e2d45;border:none;border-radius:6px;padding:5px 12px;color:#e2e8f0;cursor:pointer;font-size:.75rem}}
.toolbar button:hover,.toolbar button.active{{background:#38bdf8;color:#0a0e1a}}
.map-container{{flex:1;overflow:auto;position:relative;background:#0a0e1a}}
.map-inner{{position:relative;display:inline-block}}
#pdfCanvas{{display:block}}
.point{{position:absolute;width:24px;height:24px;border-radius:50%;border:2px solid white;cursor:pointer;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:white;box-shadow:0 0 10px rgba(0,0,0,.6);transition:transform .2s;z-index:10}}
.point:hover{{transform:translate(-50%,-50%) scale(1.5)}}
.point.ok{{background:#22c55e}}.point.alert{{background:#f59e0b}}.point.action{{background:#ef4444}}.point.none{{background:#64748b}}
.tooltip{{position:fixed;background:#111827;border:1px solid #1e2d45;border-radius:8px;padding:10px;font-size:.72rem;pointer-events:none;z-index:1000;display:none;min-width:200px;box-shadow:0 4px 20px rgba(0,0,0,.5)}}
.tooltip.visible{{display:block}}
.legend{{display:flex;gap:10px;align-items:center;font-size:.65rem;color:#64748b}}
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
  <span style="font-size:.7rem;color:#64748b">Page :</span>
  <button onclick="prevPage()">◀</button>
  <span id="pageInfo" style="font-size:.72rem;color:#e2e8f0;min-width:50px;text-align:center">1 / 1</span>
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
let addMode=false, pdfDoc=null, currentPage=1, totalPages=1;

// Load PDF from base64
const pdfData=atob(PDF_B64);
const pdfBytes=new Uint8Array(pdfData.length);
for(let i=0;i<pdfData.length;i++) pdfBytes[i]=pdfData.charCodeAt(i);
pdfjsLib.getDocument({{data:pdfBytes}}).promise.then(doc=>{{
  pdfDoc=doc; totalPages=doc.numPages;
  document.getElementById('pageInfo').textContent=`${{currentPage}} / ${{totalPages}}`;
  renderPage(currentPage);
}});

function renderPage(n){{
  pdfDoc.getPage(n).then(page=>{{
    const vp=page.getViewport({{scale:1.5}});
    const canvas=document.getElementById('pdfCanvas');
    canvas.width=vp.width; canvas.height=vp.height;
    canvas.getContext('2d').clearRect(0,0,vp.width,vp.height);
    page.render({{canvasContext:canvas.getContext('2d'),viewport:vp}}).promise.then(()=>renderPoints());
  }});
}}
function prevPage(){{if(currentPage>1){{currentPage--;document.getElementById('pageInfo').textContent=`${{currentPage}} / ${{totalPages}}`;renderPage(currentPage);}}}}
function nextPage(){{if(currentPage<totalPages){{currentPage++;document.getElementById('pageInfo').textContent=`${{currentPage}} / ${{totalPages}}`;renderPage(currentPage);}}}}

function toggleAddMode(){{addMode=!addMode;const btn=document.getElementById('addBtn');btn.classList.toggle('active',addMode);btn.textContent=addMode?'✋ Annuler':'📍 Placer un point';document.getElementById('mapContainer').style.cursor=addMode?'crosshair':'default';}}
function renderPoints(){{
  document.querySelectorAll('.point').forEach(p=>p.remove());
  const canvas=document.getElementById('pdfCanvas');
  const inner=document.getElementById('mapInner');
  points.forEach((pt,i)=>{{
    const surv=survData.find(s=>s.label===(pt.survLabel||pt.label));
    const status=surv?surv.status:'none';
    const div=document.createElement('div');div.className=`point ${{status}}`;
    div.style.left=pt.x+'%';div.style.top=pt.y+'%';div.textContent=i+1;
    div.addEventListener('mouseenter',e=>showTip(e,pt,surv));
    div.addEventListener('mouseleave',hideTip);
    inner.appendChild(div);
  }});
}}
function showTip(e,pt,surv){{const t=document.getElementById('tooltip');const icon=surv?{{ok:'✅',alert:'⚠️',action:'🚨',none:'📍'}}[surv.status]||'📍':'📍';t.innerHTML=`<div style="font-weight:700;margin-bottom:6px;color:#e2e8f0">${{icon}} ${{pt.label}}</div>`+(surv?`<div style="color:#64748b">Germe : <span style="color:#e2e8f0;font-style:italic">${{surv.germ}}</span></div><div style="color:#64748b">UFC : <span style="color:#e2e8f0;font-weight:600">${{surv.ufc}}</span></div><div style="color:#64748b">Date : ${{surv.date}}</div>`:'<div style="color:#64748b;font-size:.68rem">Aucune donnée liée</div>');t.style.left=(e.clientX+15)+'px';t.style.top=(e.clientY-10)+'px';t.classList.add('visible');}}
function hideTip(){{document.getElementById('tooltip').classList.remove('visible');}}
function clearLast(){{if(points.length>0){{points.pop();renderPoints();}}}}
function clearAll(){{if(confirm('Effacer tous les points ?')){{points=[];renderPoints();}}}}
document.getElementById('mapInner').addEventListener('click',function(e){{
  if(!addMode)return;
  const canvas=document.getElementById('pdfCanvas');
  const rect=canvas.getBoundingClientRect();
  if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)return;
  const x=((e.clientX-rect.left)/rect.width*100);
  const y=((e.clientY-rect.top)/rect.height*100);
  const label=document.getElementById('ptLabel').value||`Point ${{points.length+1}}`;
  const survLabel=document.getElementById('ptSurv').value||null;
  points.push({{x,y,label,survLabel}});renderPoints();toggleAddMode();
}});
</script></body></html>"""

                st.components.v1.html(pdfjs_html, height=700, scrolling=False)
                st.info("💡 Le PDF est rendu directement dans le navigateur — aucune conversion serveur requise.")

            else:
                # Image classique
                img_data = base64.b64encode(raw).decode()
                st.session_state.map_image = f"data:{uploaded.type};base64,{img_data}"
                st.session_state.map_image_type = "image"

        if st.session_state.map_image and (not uploaded or uploaded.type != "application/pdf"):
            surv_points = [{"label": r["prelevement"], "germ": r["germ_match"],
                "ufc": r["ufc"], "date": r["date"], "status": r["status"]}
                for r in st.session_state.surveillance]
            surv_json = json.dumps(surv_points, ensure_ascii=False)
            pts_json = json.dumps(st.session_state.map_points, ensure_ascii=False)

            map_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0e1a;color:#e2e8f0;font-family:'Segoe UI',sans-serif;height:80vh;display:flex;flex-direction:column}}
.toolbar{{padding:8px 12px;background:#111827;border-bottom:1px solid #1e2d45;display:flex;gap:8px;align-items:center;flex-shrink:0;flex-wrap:wrap}}
.toolbar select,.toolbar input{{background:#0a0e1a;border:1px solid #1e2d45;border-radius:6px;padding:4px 8px;color:#e2e8f0;font-size:.75rem}}
.toolbar button{{background:#1e2d45;border:none;border-radius:6px;padding:5px 12px;color:#e2e8f0;cursor:pointer;font-size:.75rem}}
.toolbar button:hover,.toolbar button.active{{background:#38bdf8;color:#0a0e1a}}
.map-container{{flex:1;overflow:auto;position:relative;background:#0a0e1a}}
.map-inner{{position:relative;display:inline-block;min-width:100%;min-height:100%}}
#planImg{{max-width:100%;display:block}}
.point{{position:absolute;width:24px;height:24px;border-radius:50%;border:2px solid white;cursor:pointer;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:white;box-shadow:0 0 10px rgba(0,0,0,.6);transition:transform .2s;z-index:10}}
.point:hover{{transform:translate(-50%,-50%) scale(1.5)}}
.point.ok{{background:#22c55e}}.point.alert{{background:#f59e0b}}.point.action{{background:#ef4444}}.point.none{{background:#64748b}}
.tooltip{{position:fixed;background:#111827;border:1px solid #1e2d45;border-radius:8px;padding:10px;font-size:.72rem;pointer-events:none;z-index:1000;display:none;min-width:200px}}
.tooltip.visible{{display:block}}
.legend{{display:flex;gap:10px;align-items:center;font-size:.65rem;color:#64748b}}
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
  <div class="legend">
    <div class="leg"><div class="leg-dot" style="background:#22c55e"></div>OK</div>
    <div class="leg"><div class="leg-dot" style="background:#f59e0b"></div>Alerte</div>
    <div class="leg"><div class="leg-dot" style="background:#ef4444"></div>Action</div>
    <div class="leg"><div class="leg-dot" style="background:#64748b"></div>Non lié</div>
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
function showTip(e,pt,surv,i){{const t=document.getElementById('tooltip');const icon=surv?{{ok:'✅',alert:'⚠️',action:'🚨',none:'📍'}}[surv.status]||'📍':'📍';t.innerHTML=`<div style="font-weight:700;margin-bottom:6px;color:#e2e8f0">${{icon}} ${{pt.label}}</div>`+(surv?`<div style="color:#64748b">Germe : <span style="color:#e2e8f0;font-style:italic">${{surv.germ}}</span></div><div style="color:#64748b">UFC : <span style="color:#e2e8f0;font-weight:600">${{surv.ufc}}</span></div><div style="color:#64748b">Date : ${{surv.date}}</div>`:'<div style="color:#64748b;font-size:.68rem">Aucune donnée liée</div>');t.style.left=(e.clientX+15)+'px';t.style.top=(e.clientY-10)+'px';t.classList.add('visible');}}
function hideTip(){{document.getElementById('tooltip').classList.remove('visible');}}
function clearLast(){{if(points.length>0){{points.pop();renderPoints();}}}}
function clearAll(){{if(confirm('Effacer tous les points ?')){{points=[];renderPoints();}}}}
document.getElementById('mapInner').addEventListener('click',function(e){{if(!addMode)return;const img=document.getElementById('planImg');if(!img)return;const rect=img.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)return;const x=((e.clientX-rect.left)/rect.width*100);const y=((e.clientY-rect.top)/rect.height*100);const label=document.getElementById('ptLabel').value||`Point ${{points.length+1}}`;const survLabel=document.getElementById('ptSurv').value||null;points.push({{x,y,label,survLabel}});renderPoints();toggleAddMode();}});
const img=document.getElementById('planImg');if(img)img.addEventListener('load',renderPoints);else renderPoints();
</script></body></html>"""

            st.components.v1.html(map_html, height=650, scrolling=False)
            st.info("💡 Nommez le point, liez-le à un prélèvement (optionnel), cliquez **📍 Placer**, puis cliquez sur le plan.")
        elif not uploaded:
            st.markdown('''<div style="background:#111827;border:2px dashed #1e2d45;border-radius:12px;padding:48px;text-align:center;color:#64748b"><div style="font-size:2rem;margin-bottom:8px">🗺️</div><div>Uploadez un plan URC (PNG/JPG/PDF) pour placer les points de prélèvement</div></div>''', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PLAN TAB 2 : simplification
    # ─────────────────────────────────────────────────────────────────────────
    with plan_tab2:
        st.markdown("#### ✂️ Simplificateur de plan — extraction des contours")
        st.markdown("Transformez un plan d'architecte complexe en plan épuré **noir et blanc** conservant uniquement les **contours des pièces et des meubles**.")

        up_simp = st.file_uploader(
            "Uploader le plan à simplifier (PNG ou JPG)",
            type=["png", "jpg", "jpeg"],
            key="plan_simplify_upload"
        )

        # PDF → PNG converter widget (browser-side, no server deps)
        with st.expander("📄 Convertir un PDF en PNG d'abord", expanded=False):
            up_pdf = st.file_uploader("Uploader le PDF à convertir", type=["pdf"], key="pdf_convert_upload")
            if up_pdf:
                pdf_b64_conv = base64.b64encode(up_pdf.read()).decode()
                conv_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<style>
body{{background:#111827;color:#e2e8f0;font-family:'Segoe UI',sans-serif;padding:12px;margin:0}}
button{{background:#38bdf8;border:none;border-radius:8px;padding:8px 18px;color:#0a0e1a;font-weight:700;cursor:pointer;font-size:.8rem;margin:4px}}
button.sec{{background:#1e2d45;color:#e2e8f0}}
canvas{{border:1px solid #1e2d45;border-radius:6px;max-width:100%;margin-top:8px;display:block}}
.row{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px}}
select{{background:#0a0e1a;border:1px solid #1e2d45;border-radius:6px;padding:5px 8px;color:#e2e8f0;font-size:.78rem}}
</style></head><body>
<div class="row">
  <button class="sec" onclick="prevPage()">◀</button>
  <span id="pi" style="font-size:.75rem">Page 1 / 1</span>
  <button class="sec" onclick="nextPage()">▶</button>
  <select id="dpi"><option value="1.5">150 dpi</option><option value="2" selected>200 dpi</option><option value="3">300 dpi</option></select>
  <button onclick="downloadPNG()">⬇️ Télécharger page en PNG</button>
</div>
<canvas id="cv"></canvas>
<script>
pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
const b64='{pdf_b64_conv}';
const raw=atob(b64);const bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
let doc=null,cur=1,tot=1;
pdfjsLib.getDocument({{data:bytes}}).promise.then(d=>{{doc=d;tot=d.numPages;document.getElementById('pi').textContent=`Page ${{cur}} / ${{tot}}`;render();}});
function render(){{if(!doc)return;const scale=parseFloat(document.getElementById('dpi').value);doc.getPage(cur).then(p=>{{const vp=p.getViewport({{scale}});const cv=document.getElementById('cv');cv.width=vp.width;cv.height=vp.height;p.render({{canvasContext:cv.getContext('2d'),viewport:vp}}).promise;}});}}
function prevPage(){{if(cur>1){{cur--;document.getElementById('pi').textContent=`Page ${{cur}} / ${{tot}}`;render();}}}}
function nextPage(){{if(cur<tot){{cur++;document.getElementById('pi').textContent=`Page ${{cur}} / ${{tot}}`;render();}}}}
function downloadPNG(){{const cv=document.getElementById('cv');const a=document.createElement('a');a.download=`plan_page_${{cur}}.png`;a.href=cv.toDataURL('image/png');a.click();}}
document.getElementById('dpi').addEventListener('change',render);
</script></body></html>"""
                st.components.v1.html(conv_html, height=520, scrolling=False)
                st.info("👆 Sélectionnez la page souhaitée, choisissez la résolution, puis cliquez **⬇️ Télécharger page en PNG**. Re-uploadez ensuite ce PNG dans le simplificateur ci-dessus.")

        if up_simp:
            if not CV2_OK or not NP_OK:
                st.warning("⚠️ OpenCV non disponible. Installez-le avec : `pip install opencv-python-headless numpy`")
            else:
                raw_bytes = up_simp.read()
                pil_img = PILImage.open(io.BytesIO(raw_bytes)).convert("RGB")
                img_arr_orig = np.array(pil_img)

                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1:
                    sensitivity = st.slider("🎚️ Sensibilité", 20, 120, 60,
                        help="Plus élevé = plus de détails (risque de bruit)")
                with sc2:
                    wall_thickness = st.slider("📏 Épaisseur traits", 1, 4, 2)
                with sc3:
                    remove_text = st.checkbox("🔤 Supprimer textes", value=True,
                        help="Supprime annotations, dimensions, m², etc.")
                with sc4:
                    dpi_out = st.selectbox("📐 Résolution sortie", ["Standard", "Haute résolution"])

                if st.button("✂️ Simplifier le plan", type="primary", use_container_width=True):
                    with st.spinner("Extraction des contours en cours..."):
                        h, w = img_arr_orig.shape[:2]
                        if max(h, w) > 2000:
                            scale = 2000 / max(h, w)
                            img_resized = cv2.resize(img_arr_orig,
                                (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                        else:
                            img_resized = img_arr_orig.copy()
                        simplified = simplify_plan_image(img_resized,
                            sensitivity=sensitivity, wall_thickness=wall_thickness,
                            remove_text=remove_text)
                        st.session_state.simplified_plan = simplified
                        st.session_state.simplified_plan_orig = img_arr_orig

                if st.session_state.get("simplified_plan") is not None:
                    cmp1, cmp2 = st.columns(2)
                    with cmp1:
                        st.markdown("**Plan original**")
                        st.image(st.session_state.simplified_plan_orig, use_container_width=True)
                    with cmp2:
                        st.markdown("**Plan simplifié (contours)**")
                        st.image(st.session_state.simplified_plan, use_container_width=True)

                    simplified_pil = PILImage.fromarray(st.session_state.simplified_plan)
                    buf_png = io.BytesIO()
                    simplified_pil.save(buf_png, format="PNG")

                    dl1, dl2, dl3 = st.columns(3)
                    with dl1:
                        st.download_button("⬇️ Télécharger PNG", buf_png.getvalue(),
                            "plan_simplifie.png", "image/png", use_container_width=True)
                    with dl2:
                        factor = 2 if dpi_out == "Haute résolution" else 1
                        h2, w2 = st.session_state.simplified_plan.shape[:2]
                        hires = cv2.resize(st.session_state.simplified_plan,
                            (w2 * factor, h2 * factor), interpolation=cv2.INTER_NEAREST) if factor > 1 else st.session_state.simplified_plan
                        buf_hd = io.BytesIO()
                        PILImage.fromarray(hires).save(buf_hd, format="PNG")
                        st.download_button("⬇️ Haute résolution", buf_hd.getvalue(),
                            "plan_simplifie_hd.png", "image/png", use_container_width=True)
                    with dl3:
                        if st.button("🗺️ Utiliser comme plan de surveillance", use_container_width=True):
                            b64 = base64.b64encode(buf_png.getvalue()).decode()
                            st.session_state.map_image = f"data:image/png;base64,{b64}"
                            st.session_state.map_image_type = "image"
                            st.session_state.active_tab = "plan"
                            st.success("✅ Plan chargé dans l'onglet Plan interactif !")
                            st.rerun()

                    st.markdown("""<div style="background:#111827;border:1px solid #1e2d45;border-radius:8px;padding:10px 14px;margin-top:8px;font-size:.72rem;color:#64748b">
                    💡 <b>Conseils</b> : Trop de bruit → réduire la sensibilité. Murs manquants → augmenter la sensibilité. Activez "Supprimer textes" pour enlever les annotations.
                    </div>""", unsafe_allow_html=True)
        else:
            st.markdown('''<div style="background:#111827;border:2px dashed #1e2d45;border-radius:12px;padding:48px;text-align:center;color:#64748b">
              <div style="font-size:2.5rem;margin-bottom:12px">✂️</div>
              <div style="font-size:.9rem;margin-bottom:8px;color:#e2e8f0">Uploadez votre plan en PNG ou JPG</div>
              <div style="font-size:.75rem">Pour un PDF : utilisez le convertisseur PDF→PNG ci-dessus, téléchargez le PNG, puis uploadez-le ici.</div>
            </div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
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
                    if st.button("🗑️", key=f"del_surv_{real_i}", help="Supprimer ce prélèvement"):
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

    subtab_seuils, subtab_mesures = st.tabs(["📏 Seuils par criticité", "📋 Mesures correctives par origine"])

    # ── SOUS-ONGLET 1 : SEUILS ────────────────────────────────────────────────
    with subtab_seuils:
        st.markdown("Configurez les seuils d'alerte et d'action **par niveau de criticité**. Ces valeurs s'appliquent automatiquement à tous les germes du niveau correspondant.")

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
            st.markdown(f"""<div style="background:#111827;border-left:4px solid {color};border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:4px">
              <div style="font-size:.85rem;font-weight:700;color:{color}">{title}</div>
              <div style="font-size:.65rem;color:#64748b;margin-top:2px">{germs_list[:150]}{'...' if len(germs_list)>150 else ''}</div>
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
            if st.button("💾 Sauvegarder les seuils", type="primary", use_container_width=True):
                st.session_state.thresholds = new_thresholds
                save_thresholds_and_measures(new_thresholds, st.session_state.measures)
                st.success("✅ Seuils sauvegardés !")
        with cr:
            if st.button("↩️ Réinitialiser les seuils", use_container_width=True):
                st.session_state.thresholds = {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}
                save_thresholds_and_measures(st.session_state.thresholds, st.session_state.measures)
                st.success("✅ Seuils réinitialisés.")
                st.rerun()

    # ── SOUS-ONGLET 2 : MESURES PAR ORIGINE ──────────────────────────────────
    with subtab_mesures:
        st.markdown("Gérez les **mesures correctives** applicables lors d'un dépassement de seuil. Chaque mesure peut s'appliquer à **toutes les origines** ou à une **origine spécifique** (4ème nœud du logigramme).")

        om = st.session_state.origin_measures

        # ── SCOPE OPTIONS ─────────────────────────────────────────────────
        scope_options = ["all"] + ALL_ORIGINS
        scope_labels = {"all": "🌐 Toutes les origines", "Air": "💨 Air",
            "Humidité": "💧 Humidité", "Flore fécale": "🦠 Flore fécale",
            "Oropharynx / Gouttelettes": "😷 Oropharynx / Gouttelettes",
            "Peau / Muqueuses": "🖐️ Peau / Muqueuses", "Peau / Muqueuse": "🖐️ Peau / Muqueuse",
            "Sol / Carton / Surface sèche": "📦 Sol / Carton / Surface sèche",
            "Sol / Carton / Surface sèche": "📦 Sol / Carton / Surface sèche",
            "Sol / Carton / Surface sèche": "📦 Sol / Carton / Surface sèche",
        }
        type_labels = {"alert": "⚠️ Alerte", "action": "🚨 Action", "both": "⚠️🚨 Alerte & Action"}
        type_colors = {"alert": "#f59e0b", "action": "#ef4444", "both": "#818cf8"}

        # ── FILTER BAR ────────────────────────────────────────────────────
        risk_labels_filter = {"all": "🌐 Toutes criticités", "1": "🟢 Criticité 1", "2": "🟢 Criticité 2", "3": "🟡 Criticité 3", "4": "🟠 Criticité 4", "5": "🔴 Criticité 5"}

        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1])
        with col_f1:
            filter_scope = st.selectbox("Filtrer par origine", ["Tout afficher"] + list(scope_labels.values()),
                key="filter_scope", label_visibility="collapsed")
        with col_f2:
            filter_risk_lbl = st.selectbox("Filtrer par criticité", list(risk_labels_filter.values()),
                key="filter_risk", label_visibility="collapsed")
            filter_risk_map = {v: k for k, v in risk_labels_filter.items()}
            active_risk_filter = filter_risk_map.get(filter_risk_lbl, "all")
        with col_f3:
            filter_type = st.selectbox("Filtrer par type", ["Alerte & Action", "⚠️ Alerte seulement", "🚨 Action seulement"],
                key="filter_type", label_visibility="collapsed")
        with col_f4:
            if st.button("➕ Nouvelle mesure", type="primary", use_container_width=True):
                st.session_state.show_new_measure = True

        # Map filter values back
        scope_filter_map = {v: k for k, v in scope_labels.items()}
        active_scope_filter = scope_filter_map.get(filter_scope, None)
        active_type_filter = None if filter_type == "Alerte & Action" else ("alert" if "Alerte" in filter_type else "action")

        st.divider()

        # ── NEW MEASURE FORM ──────────────────────────────────────────────
        if st.session_state.get("show_new_measure", False):
            with st.container(border=True):
                st.markdown("#### ➕ Nouvelle mesure corrective")
                nmc1, nmc2, nmc3, nmc4 = st.columns([3, 2, 1.5, 1.5])
                with nmc1:
                    nm_text = st.text_input("Texte de la mesure *", placeholder="Ex : Vérifier l'intégrité des filtres HEPA", key="nm_text")
                with nmc2:
                    nm_scope_label = st.selectbox("S'applique à (origine)", list(scope_labels.values()), key="nm_scope")
                    nm_scope = scope_filter_map.get(nm_scope_label, "all")
                with nmc3:
                    risk_opts_nm = {"all": "🌐 Toutes criticités","1":"🟢 Criticité 1","2":"🟢 Criticité 2","3":"🟡 Criticité 3","4":"🟠 Criticité 4","5":"🔴 Criticité 5","[3,4,5]":"🟡🟠🔴 3-4-5","[4,5]":"🟠🔴 4-5","[1,2,3]":"🟢🟢🟡 1-2-3"}
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
                    if st.button("✅ Ajouter la mesure", type="primary", use_container_width=True, key="nm_submit"):
                        if nm_text.strip():
                            new_id = f"m{len(om)+1:03d}_custom"
                            om.append({"id": new_id, "text": nm_text.strip(), "scope": nm_scope, "risk": nm_risk, "type": nm_type})
                            save_origin_measures(om)
                            st.session_state.origin_measures = om
                            st.session_state.show_new_measure = False
                            st.success(f"✅ Mesure ajoutée !")
                            st.rerun()
                        else:
                            st.error("Le texte est obligatoire.")
                with nb2:
                    if st.button("Annuler", use_container_width=True, key="nm_cancel"):
                        st.session_state.show_new_measure = False
                        st.rerun()

        # ── GROUP MEASURES BY SCOPE ───────────────────────────────────────
        # Filter
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

        # Group by scope
        from collections import OrderedDict
        groups = OrderedDict()
        for sc in (["all"] + ALL_ORIGINS):
            grp = [m for m in filtered_measures if m["scope"] == sc]
            if grp:
                groups[sc] = grp

        if not filtered_measures:
            st.info("Aucune mesure ne correspond aux filtres sélectionnés.")
        else:
            for scope_key, group_measures in groups.items():
                scope_lbl = scope_labels.get(scope_key, scope_key)
                st.markdown(f"""<div style="background:#111827;border-left:3px solid #38bdf8;border-radius:0 8px 8px 0;padding:8px 14px;margin:12px 0 6px 0">
                  <span style="font-size:.78rem;font-weight:700;color:#38bdf8">{scope_lbl}</span>
                  <span style="font-size:.62rem;color:#64748b;margin-left:8px">{len(group_measures)} mesure(s)</span>
                </div>""", unsafe_allow_html=True)

                for mi, m in enumerate(group_measures):
                    real_idx = om.index(m)
                    tcol = type_colors.get(m["type"], "#64748b")
                    tlbl = type_labels.get(m["type"], m["type"])

                    # Edit mode
                    if st.session_state.get(f"edit_m_{real_idx}", False):
                        with st.container(border=True):
                            ec1, ec2, ec3, ec4 = st.columns([3, 2, 1.5, 1.5])
                            with ec1:
                                edit_text = st.text_input("Texte", value=m["text"], key=f"et_{real_idx}")
                            with ec2:
                                cur_scope_lbl = scope_labels.get(m["scope"], m["scope"])
                                cur_scope_idx = list(scope_labels.values()).index(cur_scope_lbl) if cur_scope_lbl in scope_labels.values() else 0
                                edit_scope_lbl = st.selectbox("Origine", list(scope_labels.values()), index=cur_scope_idx, key=f"es_{real_idx}")
                                edit_scope = scope_filter_map.get(edit_scope_lbl, "all")
                            with ec3:
                                risk_opts_e = {"all":"🌐 Toutes","1":"🟢 1","2":"🟢 2","3":"🟡 3","4":"🟠 4","5":"🔴 5","[3,4,5]":"🟡🟠🔴 3-4-5","[4,5]":"🟠🔴 4-5","[1,2,3]":"🟢🟢🟡 1-2-3"}
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
                                if st.button("✅ Valider", type="primary", use_container_width=True, key=f"ev_{real_idx}"):
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
                        if mr == "all": risk_badge = "🌐 Toutes"
                        elif isinstance(mr, list):
                            rcols = {1:"#22c55e",2:"#84cc16",3:"#f59e0b",4:"#f97316",5:"#ef4444"}
                            risk_badge = " ".join(f'<span style="color:{rcols.get(r,"#64748b")};font-weight:700">{r}</span>' for r in mr)
                        else: risk_badge = str(mr)
                        row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([4.5, 1.2, 1.5, 0.8, 0.8])
                        with row_c1:
                            st.markdown(f'<div style="padding:6px 0;font-size:.8rem;color:#e2e8f0">• {m["text"]}</div>', unsafe_allow_html=True)
                        with row_c2:
                            st.markdown(f'<div style="padding:6px 0;font-size:.63rem;color:#64748b;text-align:center">Nv.{risk_badge}</div>', unsafe_allow_html=True)
                        with row_c3:
                            st.markdown(f'<div style="padding:6px 0;font-size:.65rem;color:{tcol};font-weight:600;text-align:center">{tlbl}</div>', unsafe_allow_html=True)
                        with row_c4:
                            if st.button("✏️", key=f"edit_btn_{real_idx}", help="Modifier"):
                                st.session_state[f"edit_m_{real_idx}"] = True
                                st.rerun()
                        with row_c5:
                            if st.button("🗑️", key=f"del_m_{real_idx}", help="Supprimer"):
                                om.pop(real_idx)
                                save_origin_measures(om)
                                st.session_state.origin_measures = om
                                st.rerun()

        st.divider()
        col_sr, col_def = st.columns(2)
        with col_sr:
            if st.button("💾 Sauvegarder les mesures", type="primary", use_container_width=True):
                save_origin_measures(om)
                st.success("✅ Mesures sauvegardées !")
        with col_def:
            if st.button("↩️ Réinitialiser les mesures par défaut", use_container_width=True):
                st.session_state.origin_measures = [dict(m) for m in DEFAULT_ORIGIN_MEASURES]
                save_origin_measures(st.session_state.origin_measures)
                st.success("✅ Mesures réinitialisées.")
                st.rerun()