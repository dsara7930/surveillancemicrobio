import streamlit as st
import json

st.set_page_config(
    page_title="Logigramme Germes",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp, [data-testid="stAppViewContainer"] { background: #0a0e1a; }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.page-title { font-size:1.1rem; font-weight:800; letter-spacing:0.15em; text-transform:uppercase; color:#38bdf8; margin-bottom:4px; }
.legend { display:flex; gap:14px; flex-wrap:wrap; margin-top:4px; margin-bottom:8px; }
.leg { font-size:0.65rem; font-family:'DM Mono',monospace; color:#64748b; }
.risk-badge { display:inline-flex; align-items:center; gap:5px; font-size:0.7rem; font-family:'DM Mono',monospace; font-weight:500; padding:3px 10px; border-radius:20px; border:1px solid; }
.risk-1 { color:#22c55e; background:rgba(34,197,94,0.08); border-color:#22c55e55; }
.risk-2 { color:#84cc16; background:rgba(132,204,22,0.08); border-color:#84cc1655; }
.risk-3 { color:#f59e0b; background:rgba(245,158,11,0.08); border-color:#f59e0b55; }
.risk-4 { color:#f97316; background:rgba(249,115,22,0.08); border-color:#f9731655; }
.risk-5 { color:#ef4444; background:rgba(239,68,68,0.08); border-color:#ef444455; }
.risk-dot { width:8px; height:8px; border-radius:50%; background:currentColor; display:inline-block; }
.panel { background:#111827; border:1px solid #1e2d45; border-radius:12px; overflow:hidden; }
.panel-head { background:rgba(56,189,248,0.04); border-bottom:1px solid #1e2d45; padding:18px; }
.panel-germ { font-size:1rem; font-weight:700; font-style:italic; color:#e2e8f0; margin-bottom:8px; line-height:1.3; }
.panel-body { padding:18px; }
.info-lbl { font-size:0.58rem; letter-spacing:0.15em; text-transform:uppercase; font-family:'DM Mono',monospace; color:#64748b; margin-bottom:4px; }
.info-val { font-size:0.82rem; color:#e2e8f0; line-height:1.5; margin-bottom:14px; }
.sens-bar { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:8px; border:1px solid #1e2d45; background:rgba(255,255,255,0.02); margin-bottom:10px; font-family:'DM Mono',monospace; font-size:0.74rem; color:#e2e8f0; }
.ok   { color:#22c55e; font-weight:700; }
.warn { color:#f97316; font-weight:700; }
.crit { color:#ef4444; font-weight:700; }
.notes { padding:12px; border-radius:8px; background:rgba(56,189,248,0.04); border:1px solid rgba(56,189,248,0.1); font-size:0.76rem; line-height:1.6; color:#94a3b8; font-family:'DM Mono',monospace; }
.path-trail { font-size:0.68rem; font-family:'DM Mono',monospace; color:#38bdf8; opacity:0.8; margin-bottom:8px; }
.empty-panel { text-align:center; color:#2d3d52; font-family:'DM Mono',monospace; font-size:0.78rem; padding:60px 20px; line-height:2.2; }
</style>
""", unsafe_allow_html=True)

RISK_LABELS = {1:"Limité", 2:"Modéré", 3:"Important", 4:"Majeur", 5:"Critique"}
RISK_COLORS = {1:"#22c55e", 2:"#84cc16", 3:"#f59e0b", 4:"#f97316", 5:"#ef4444"}

GERMS = [
    dict(name="Staphylococcus spp.", path=["Germes","Bactéries","Humains","Peau / Muqueuses"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Corynebacterium spp.", path=["Germes","Bactéries","Humains","Peau / Muqueuses"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Cutibacterium acnes", path=["Germes","Bactéries","Humains","Peau / Muqueuses"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Micrococcus spp.", path=["Germes","Bactéries","Humains","Peau / Muqueuses"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Dermabacter hominis", path=["Germes","Bactéries","Humains","Peau / Muqueuses"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Brevibacterium epidermidis", path=["Germes","Bactéries","Humains","Peau / Muqueuses"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Streptococcus mitis/salivarius", path=["Germes","Bactéries","Humains","Oropharynx"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Streptococcus pyogenes/pneumoniae", path=["Germes","Bactéries","Humains","Oropharynx"], risk=3, pathotype="Pathogène primaire", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Escherichia coli", path=["Germes","Bactéries","Humains","Flore fécale"], risk=4, pathotype="Pathogène opportuniste multirésistant (O157:H7 = pathogène primaire)", surfa="Risque résistance (biofilm)", apa="Sensible", notes=None),
    dict(name="Enterococcus spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=4, pathotype="Pathogène opportuniste multirésistant", surfa="Risque résistance (biofilm)", apa="Sensible", notes=None),
    dict(name="Enterobacter spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène opportuniste multirésistant", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Citrobacter spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène opportuniste multirésistant", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Klebsiella pneumoniae", path=["Germes","Bactéries","Humains","Flore fécale"], risk=4, pathotype="Pathogène opportuniste multirésistant", surfa="Risque résistance (biofilm)", apa="Sensible", notes=None),
    dict(name="Proteus spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène opportuniste multirésistant", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Morganella spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène opportuniste multirésistant", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Providencia spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène opportuniste multirésistant", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Salmonella spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène primaire", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Shigella spp.", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène primaire", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Yersinia enterocolitica", path=["Germes","Bactéries","Humains","Flore fécale"], risk=3, pathotype="Pathogène primaire", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Pseudomonas spp.", path=["Germes","Bactéries","Environnemental","Humidité"], risk=4, pathotype="Pathogène opportuniste multirésistant", surfa="Risque résistance (biofilm)", apa="Sensible", notes=None),
    dict(name="Acinetobacter spp.", path=["Germes","Bactéries","Environnemental","Humidité"], risk=4, pathotype="Pathogène opportuniste multirésistant", surfa="Risque résistance (biofilm)", apa="Sensible", notes=None),
    dict(name="Paenibacillus spp. (SPORULÉS)", path=["Germes","Bactéries","Environnemental","Humidité"], risk=2, pathotype="Non pathogène", surfa="Risque résistance (spore)", apa="Risque résistance (spore)", notes="Sporulé — résistance accrue aux désinfectants."),
    dict(name="Hafnia alvei", path=["Germes","Bactéries","Environnemental","Humidité"], risk=2, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Sphingomonas paucimobilis", path=["Germes","Bactéries","Environnemental","Humidité"], risk=2, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Sphingobium spp.", path=["Germes","Bactéries","Environnemental","Humidité"], risk=2, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Methylobacterium spp.", path=["Germes","Bactéries","Environnemental","Humidité"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Caulobacter crescentus", path=["Germes","Bactéries","Environnemental","Humidité"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Mycobacterium non tuberculeux", path=["Germes","Bactéries","Environnemental","Humidité"], risk=5, pathotype="Pathogène opportuniste multirésistant", surfa="Risque résistance", apa="Risque résistance", notes=None),
    dict(name="Burkholderia cepacia", path=["Germes","Bactéries","Environnemental","Humidité"], risk=4, pathotype="Pathogène opportuniste multirésistant", surfa="Risque résistance (biofilm)", apa="Sensible", notes=None),
    dict(name="Massilia spp.", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Bacillus spp. (SPORULÉS)", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=2, pathotype="Non pathogène", surfa="Risque résistance (spore)", apa="Risque résistance (spore)", notes="Sporulé — cycle isolateur conçu pour détruire les spores avec l'APA."),
    dict(name="Clostridium spp. (SPORULÉS)", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=5, pathotype="Pathogène opportuniste", surfa="Risque résistance (spore)", apa="Risque résistance (spore)", notes="Sporulé — résistance très élevée aux désinfectants."),
    dict(name="Geobacillus stearothermophilus", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=5, pathotype="Pathogène opportuniste", surfa="Risque résistance (spore)", apa="Risque résistance (spore)", notes="Sporulé thermophile — indicateur biologique de stérilisation."),
    dict(name="Arthrobacter spp.", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Cellulomonas spp.", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Curtobacterium spp.", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Agrococcus spp.", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Microbacterium spp.", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Brevibacterium linens/casei", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=2, pathotype="Pathogène opportuniste", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Georgenia spp.", path=["Germes","Bactéries","Environnemental","Sol / Surface sèche"], risk=1, pathotype="Non pathogène", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Candida spp.", path=["Germes","Champignons","Humain","Peau / Muqueuse"], risk=3, pathotype="Pathogène opportuniste multirésistant", surfa="Sensible", apa="Sensible", notes=None),
    dict(name="Trichosporon spp.", path=["Germes","Champignons","Humain","Peau / Muqueuse"], risk=3, pathotype="Pathogène opportuniste résistant aux échinocandines", surfa="Sensible", apa="Sensible", notes="Levure — pas de production de spores."),
    dict(name="Rhodotorula spp.", path=["Germes","Champignons","Environnemental","Humidité"], risk=3, pathotype="Pathogène opportuniste résistant aux échinocandines", surfa="Sensible", apa="Sensible", notes="Levure — pas de production de spores."),
    dict(name="Fusarium spp.", path=["Germes","Champignons","Environnemental","Humidité"], risk=5, pathotype="Pathogène opportuniste multirésistant", surfa="Risque résistance", apa="Risque résistance", notes="Conidies (2–4 µm) → dissémination aérienne + résistance aux agents oxydants."),
    dict(name="Aureobasidium spp.", path=["Germes","Champignons","Environnemental","Humidité"], risk=4, pathotype="Pathogène opportuniste", surfa="Risque résistance", apa="Sensible", notes="Blastospores + biofilm. Moins résistant aux agents oxydants, pas de dissémination aérienne."),
    dict(name="Mucorales", path=["Germes","Champignons","Environnemental","Sol / Surface / Carton"], risk=5, pathotype="Pathogène opportuniste résistant aux échinocandines", surfa="Risque résistance", apa="Risque modéré résistance", notes="Sporangiospores — moins résistant aux agents oxydants que les conidies."),
    dict(name="Alternaria spp.", path=["Germes","Champignons","Environnemental","Air"], risk=5, pathotype="Pathogène opportuniste", surfa="Risque résistance", apa="Risque modéré résistance", notes="Conidies grandes, moins mélanisées que Fusarium → moins résistante à l'oxydation."),
    dict(name="Aspergillus spp.", path=["Germes","Champignons","Environnemental","Air"], risk=5, pathotype="Pathogène opportuniste", surfa="Risque résistance", apa="Risque résistance", notes="Conidies (2–4 µm) → dissémination aérienne + résistance aux agents oxydants."),
    dict(name="Cladosporium spp.", path=["Germes","Champignons","Environnemental","Air"], risk=4, pathotype="Très rarement pathogène", surfa="Risque résistance", apa="Risque modéré résistance", notes="Conidies grandes, moins mélanisées → moins résistante à l'oxydation."),
    dict(name="Penicillium spp.", path=["Germes","Champignons","Environnemental","Air"], risk=5, pathotype="Pathogène opportuniste", surfa="Risque résistance", apa="Risque modéré résistance", notes="Conidies moins déshydratées que Fusarium → moins résistante à l'oxydation."),
    dict(name="Wallemia sebi", path=["Germes","Champignons","Environnemental","Air"], risk=4, pathotype="Très rarement pathogène", surfa="Risque résistance", apa="Risque résistance", notes="Arthroconidies. Résistance à l'APA dépend de la concentration, humidité et diffusion."),
]

def get_sens(val):
    if not val: return "ok", "✓"
    v = val.lower()
    if "modéré" in v: return "warn", "⚠"
    if "risque" in v: return "crit", "✗"
    return "ok", "✓"

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "selected" not in st.session_state:
    st.session_state.selected = None

# ── HEADER ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([5, 1])
with c1:
    st.markdown('<p class="page-title">🦠 Logigramme Germes</p>', unsafe_allow_html=True)
    st.markdown("""<div class="legend">
      <span class="leg"><span style="color:#22c55e">●</span> 1 Limité</span>
      <span class="leg"><span style="color:#84cc16">●</span> 2 Modéré</span>
      <span class="leg"><span style="color:#f59e0b">●</span> 3 Important</span>
      <span class="leg"><span style="color:#f97316">●</span> 4 Majeur</span>
      <span class="leg"><span style="color:#ef4444">●</span> 5 Critique</span>
    </div>""", unsafe_allow_html=True)
with c2:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.selected = None
        st.rerun()

st.divider()

# ── LAYOUT ────────────────────────────────────────────────────────────────────
col_graph, col_panel = st.columns([3, 1.1])

# Build the interactive tree as an HTML component using vis.js
LEVEL_COLORS = ["#38bdf8", "#818cf8", "#fb923c", "#34d399"]

with col_graph:
    selected = st.session_state.selected
    sel_path = []
    if selected:
        g = next((x for x in GERMS if x["name"] == selected), None)
        if g:
            sel_path = g["path"]

    # Build vis.js nodes and edges data
    vis_nodes = []
    vis_edges = []
    seen = set()

    # All germ leaf nodes
    for g in GERMS:
        n = g["name"]
        c = RISK_COLORS[g["risk"]]
        is_sel = n == selected
        vis_nodes.append({
            "id": n,
            "label": n,
            "color": {"background": c+"44", "border": "#ffffff" if is_sel else c,
                      "highlight": {"background": c+"88", "border": "#ffffff"}},
            "font": {"color": "#e2e8f0", "size": 12, "face": "DM Mono"},
            "shape": "box",
            "borderWidth": 3 if is_sel else 1,
            "size": 20,
            "level": 4,
        })
        seen.add(n)

    # If selected: ancestor nodes + edges
    if sel_path:
        g = next((x for x in GERMS if x["name"] == selected), None)
        if g:
            for i, node_name in enumerate(sel_path):
                c = LEVEL_COLORS[i] if i < len(LEVEL_COLORS) else "#64748b"
                if node_name not in seen:
                    vis_nodes.append({
                        "id": node_name,
                        "label": node_name,
                        "color": {"background": c+"22", "border": c,
                                  "highlight": {"background": c+"44", "border": c}},
                        "font": {"color": c, "size": 14 if i == 0 else 12, "face": "Syne"},
                        "shape": "box",
                        "borderWidth": 2,
                        "level": i,
                    })
                    seen.add(node_name)
                if i < len(sel_path) - 1:
                    vis_edges.append({"from": sel_path[i], "to": sel_path[i+1],
                                       "color": {"color": c, "opacity": 0.9}, "width": 2})
            vis_edges.append({"from": sel_path[-1], "to": selected,
                               "color": {"color": RISK_COLORS[g["risk"]], "opacity": 1}, "width": 2})

    nodes_json = json.dumps(vis_nodes)
    edges_json = json.dumps(vis_edges)
    hierarchical = "true" if sel_path else "false"

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet">
<style>
  body {{ margin:0; background:#0a0e1a; overflow:hidden; }}
  #tree {{ width:100%; height:580px; background:#0a0e1a; border:1px solid #1e2d45; border-radius:10px; }}
  .vis-network canvas {{ border-radius:10px; }}
</style>
</head>
<body>
<div id="tree"></div>
<script>
  var nodes = new vis.DataSet({nodes_json});
  var edges = new vis.DataSet({edges_json});
  var options = {{
    layout: {{
      hierarchical: {{
        enabled: {hierarchical},
        direction: "UD",
        sortMethod: "directed",
        nodeSpacing: 140,
        levelSeparation: 100,
      }}
    }},
    physics: {{ enabled: {("false" if sel_path else "true")}, stabilization: {{ iterations: 200 }} }},
    interaction: {{ hover: true, tooltipDelay: 100 }},
    nodes: {{ margin: 8, widthConstraint: {{ maximum: 180 }} }},
    edges: {{ arrows: {{ to: {{ enabled: true, scaleFactor: 0.6 }} }}, smooth: {{ type: "cubicBezier" }} }},
  }};
  var network = new vis.Network(document.getElementById("tree"), {{nodes, edges}}, options);
  network.on("click", function(params) {{
    if (params.nodes.length > 0) {{
      var nodeId = params.nodes[0];
      // Send to Streamlit via query param trick
      window.parent.postMessage({{type: "streamlit:setComponentValue", value: nodeId}}, "*");
    }}
  }});
</script>
</body>
</html>
"""

    clicked = st.components.v1.html(html_code, height=590, scrolling=False)

    # Fallback: manual selection via selectbox
    st.markdown('<p style="color:#64748b;font-size:0.72rem;font-family:DM Mono,monospace;margin-top:8px;">👆 Ou sélectionnez un germe ici :</p>', unsafe_allow_html=True)
    germ_names = [""] + [g["name"] for g in GERMS]
    choice = st.selectbox("Germe", germ_names, index=0, label_visibility="collapsed")
    if choice and choice != st.session_state.selected:
        st.session_state.selected = choice
        st.rerun()
    elif not choice and st.session_state.selected:
        pass  # keep current selection

# ── SIDE PANEL ────────────────────────────────────────────────────────────────
with col_panel:
    if st.session_state.selected:
        g = next((x for x in GERMS if x["name"] == st.session_state.selected), None)
        if g:
            sc, si = get_sens(g["surfa"])
            ac, ai = get_sens(g["apa"])
            notes_html = f'<div style="margin-top:12px"><div class="info-lbl">Notes</div><div class="notes">{g["notes"]}</div></div>' if g["notes"] else ""
            st.markdown(f"""
            <div class="panel">
              <div class="panel-head">
                <div class="path-trail">{"  ›  ".join(g['path'])}</div>
                <div class="panel-germ">{g['name']}</div>
                <span class="risk-badge risk-{g['risk']}">
                  <span class="risk-dot"></span>Niveau {g['risk']} — {RISK_LABELS[g['risk']]}
                </span>
              </div>
              <div class="panel-body">
                <div class="info-lbl">Type de pathogène</div>
                <div class="info-val">{g['pathotype']}</div>
                <div class="info-lbl">Surfa'Safe</div>
                <div class="sens-bar"><span class="{sc}">{si}</span>&nbsp;{g['surfa']}</div>
                <div class="info-lbl">Acide Peracétique (APA)</div>
                <div class="sens-bar"><span class="{ac}">{ai}</span>&nbsp;{g['apa']}</div>
                {notes_html}
              </div>
            </div>""", unsafe_allow_html=True)
        if st.button("✕ Fermer", use_container_width=True):
            st.session_state.selected = None
            st.rerun()
    else:
        st.markdown("""<div class="panel"><div class="empty-panel">
            Sélectionnez<br>un germe<br>via la liste<br>ou le graphe ↙
        </div></div>""", unsafe_allow_html=True)