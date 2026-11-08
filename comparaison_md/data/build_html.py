import json, glob, os, re, sys, html, datetime
from urllib.parse import quote

SCRATCH = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRATCH, "rapport.html")
NOTICE_PDF = "notice/Notice_ATTITUDE_ArtMony_V1.2.pdf"
# correspondance chemin d'origine dans l'archive DOE -> copie publiée (DOE/<lot>/<fichier>)
_map_file = os.path.join(SCRATCH, "doe_map.json")
DOE_MAP = {}  # pièces du DOE non publiées : citées par leur chemin, sans lien

CHAPITRES = {
    "1": "1. Caractéristiques techniques générales de l'immeuble",
    "2": "2. Locaux privatifs et leurs équipements",
    "3": "3. Annexes privatives",
    "4": "4. Parties communes intérieures",
    "5": "5. Équipements généraux de l'immeuble",
    "6": "6. Parties communes extérieures",
    "7": "7. Organigramme des clés",
    "8": "8. Information des habitants",
}
VERDICTS = {
    "rouge": ("Inférieure", "Prestation manifestement inférieure"),
    "orange": ("Doute", "Cas en doute ou non documenté"),
    "bleu": ("Conforme", "Notice respectée à la lettre"),
    "vert": ("Supérieure", "Prestation manifestement supérieure"),
}
ORDER = ["rouge", "orange", "bleu", "vert"]

def e(s):
    return html.escape(str(s or ""), quote=True)

def art_key(a):
    nums = re.findall(r"\d+", str(a or "99"))
    return [int(n) for n in nums] or [99]

def doe_link(path):
    p = (path or "").replace("\\", "/")
    # les archives imbriquées ont été extraites dans un dossier <nom>_unzipped
    shown = re.sub(r"_unzipped/", ".zip ▸ ", p)
    pub = DOE_MAP.get(p)
    if not pub:
        return f'<span class="path">{e(shown)}</span>'
    href = "/".join(quote(x) for x in pub.split("/"))
    return f'<a class="path" href="{e(href)}" target="_blank" rel="noopener" title="Chemin dans l\'archive DOE : {e(shown)}">{e(shown)}</a>'

def notice_page_link(text):
    def rep(m):
        n = m.group(2)
        return f'<a href="{e(quote(NOTICE_PDF))}#page={n}" target="_blank" rel="noopener">{m.group(1)}{n}</a>'
    return re.sub(r"(p\.\s?)(\d{1,2})", rep, text)

items, observations = [], []
for f in sorted(glob.glob(os.path.join(SCRATCH, "results", "*.json"))):
    with open(f, encoding="utf-8") as fh:
        d = json.load(fh)
    for it in d.get("items", []):
        it["_agent"] = d.get("perimetre", d.get("agent", ""))
        v = str(it.get("verdict", "orange")).lower().strip()
        it["verdict"] = v if v in VERDICTS else "orange"
        items.append(it)
    if d.get("observations"):
        observations.append((d.get("perimetre", d.get("agent", "")), d["observations"]))

items.sort(key=lambda it: (art_key(it.get("article")), str(it.get("titre", ""))))
counts = {k: sum(1 for it in items if it["verdict"] == k) for k in ORDER}
total = len(items)
web_count = sum(len(it.get("sources_web") or []) for it in items)

def card(i, it):
    v = it["verdict"]
    label = VERDICTS[v][0]
    eq = ' <span class="eq">équivalent démontré</span>' if v == "bleu" and it.get("equivalence") else ""
    src_doe = "".join(
        f'<li>{doe_link(s.get("fichier"))}'
        + (f' <span class="pg">{e(s.get("pages"))}</span>' if s.get("pages") else "")
        + (f' <span class="muted">— {e(s.get("note"))}</span>' if s.get("note") else "")
        + "</li>"
        for s in (it.get("sources_doe") or []))
    src_web = "".join(
        f'<li><a href="{e(s.get("url"))}" target="_blank" rel="noopener">{e(s.get("titre") or s.get("url"))}</a>'
        + (f' <span class="muted">— {e(s.get("apport"))}</span>' if s.get("apport") else "")
        + "</li>"
        for s in (it.get("sources_web") or []))
    sources = ""
    if src_doe:
        sources += f'<div class="src"><h4>Pièces du DOE consultées</h4><ul>{src_doe}</ul></div>'
    if src_web:
        sources += f'<div class="src"><h4>Sources web</h4><ul>{src_web}</ul></div>'
    search = e(" ".join(str(it.get(k, "")) for k in ("article", "titre", "notice", "doe", "justification")).lower())
    return f'''
<article class="card v-{v}" data-v="{v}" data-s="{search}" id="it{i}">
  <header>
    <span class="art">Art. {e(it.get("article"))}</span>
    <h3>{e(it.get("titre"))}</h3>
    <span class="badge">{label}</span>{eq}
  </header>
  <div class="body">
    <div class="cmp">
      <div><h4>Notice descriptive</h4><p>{notice_page_link(e(it.get("notice")))}</p></div>
      <div><h4>DOE (ouvrage exécuté)</h4><p>{e(it.get("doe"))}</p></div>
    </div>
    <div class="just"><h4>Analyse</h4><p>{e(it.get("justification"))}</p></div>
    {sources}
  </div>
</article>'''

sections, current, buf = [], None, []
for i, it in enumerate(items):
    ch = str(art_key(it.get("article"))[0])
    if ch != current:
        if buf:
            sections.append((current, buf))
        current, buf = ch, []
    buf.append(card(i, it))
if buf:
    sections.append((current, buf))

body_sections = "".join(
    f'<section class="chap"><h2>{e(CHAPITRES.get(ch, "Autres"))}</h2>{"".join(cards)}</section>'
    for ch, cards in sections)

# tableau de synthèse
rows = "".join(
    f'<tr class="v-{it["verdict"]}" data-v="{it["verdict"]}"><td>{e(it.get("article"))}</td>'
    f'<td><a href="#it{i}">{e(it.get("titre"))}</a></td>'
    f'<td><span class="dot"></span>{VERDICTS[it["verdict"]][0]}</td></tr>'
    for i, it in enumerate(items))

obs_html = "".join(f"<div class='obs'><h4>{e(p)}</h4><p>{e(o)}</p></div>" for p, o in observations)

stat = "".join(
    f'<button class="stat v-{k}" data-filter="{k}" aria-pressed="false"><b>{counts[k]}</b><span>{VERDICTS[k][1]}</span></button>'
    for k in ORDER)

today = datetime.date.today().strftime("%d/%m/%Y")

page = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conformité DOE Art'Mony</title>
<style>
:root {{
  --bg:#f6f7f9; --surface:#ffffff; --text:#1c2230; --muted:#5d6678; --line:#dde1e8;
  --rouge:#c62828; --rouge-bg:#fdecec; --vert:#2e7d32; --vert-bg:#e9f5ea;
  --bleu:#1565c0; --bleu-bg:#e8f0fc; --orange:#e07b00; --orange-bg:#fff3e2;
  --link:#1554b0;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#12151b; --surface:#1b2029; --text:#e5e8ee; --muted:#9aa3b5; --line:#2d3441;
  --rouge:#ef5350; --rouge-bg:#3a1d1f; --vert:#66bb6a; --vert-bg:#1b3121;
  --bleu:#64a8f0; --bleu-bg:#172a42; --orange:#ffa726; --orange-bg:#3a2a14; --link:#8ab8ff;
}} }}
:root[data-theme="dark"] {{
  --bg:#12151b; --surface:#1b2029; --text:#e5e8ee; --muted:#9aa3b5; --line:#2d3441;
  --rouge:#ef5350; --rouge-bg:#3a1d1f; --vert:#66bb6a; --vert-bg:#1b3121;
  --bleu:#64a8f0; --bleu-bg:#172a42; --orange:#ffa726; --orange-bg:#3a2a14; --link:#8ab8ff;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
a {{ color:var(--link); }}
.wrap {{ max-width:1100px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:1.6rem; margin:0 0 4px; }}
.sub {{ color:var(--muted); margin:0 0 20px; }}
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:16px 0; }}
.stat {{ font:inherit; text-align:left; cursor:pointer; border:1px solid var(--line); border-left:6px solid; border-radius:8px; background:var(--surface); color:var(--text); padding:10px 12px; }}
.stat b {{ display:block; font-size:1.6rem; line-height:1.1; }}
.stat span {{ font-size:.85rem; color:var(--muted); }}
.stat[aria-pressed="true"] {{ outline:2px solid currentColor; }}
.stat.v-rouge {{ border-left-color:var(--rouge); }} .stat.v-rouge b {{ color:var(--rouge); }}
.stat.v-vert {{ border-left-color:var(--vert); }} .stat.v-vert b {{ color:var(--vert); }}
.stat.v-bleu {{ border-left-color:var(--bleu); }} .stat.v-bleu b {{ color:var(--bleu); }}
.stat.v-orange {{ border-left-color:var(--orange); }} .stat.v-orange b {{ color:var(--orange); }}
.tools {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:12px; }}
.tools input {{ flex:1; min-width:200px; padding:8px 10px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--text); font:inherit; }}
.tools button {{ font:inherit; padding:8px 12px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--text); cursor:pointer; }}
.box {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px 16px; margin:14px 0; }}
.box h2 {{ margin-top:0; font-size:1.1rem; }}
details.box summary {{ cursor:pointer; font-weight:600; }}
table {{ width:100%; border-collapse:collapse; font-size:.9rem; }}
td,th {{ text-align:left; padding:5px 8px; border-bottom:1px solid var(--line); vertical-align:top; }}
td:first-child {{ white-space:nowrap; color:var(--muted); }}
.dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle; }}
tr.v-rouge .dot {{ background:var(--rouge); }} tr.v-vert .dot {{ background:var(--vert); }}
tr.v-bleu .dot {{ background:var(--bleu); }} tr.v-orange .dot {{ background:var(--orange); }}
.chap h2 {{ font-size:1.2rem; margin:32px 0 10px; padding-bottom:6px; border-bottom:2px solid var(--line); }}
.card {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; margin:12px 0; overflow:hidden; }}
.card header {{ display:flex; flex-wrap:wrap; align-items:center; gap:6px 12px; padding:10px 14px; color:#fff; }}
.card.v-rouge header {{ background:var(--rouge); }} .card.v-vert header {{ background:var(--vert); }}
.card.v-bleu header {{ background:var(--bleu); }} .card.v-orange header {{ background:var(--orange); }}
:root[data-theme="dark"] .card header, :root:not([data-theme="light"]) .card header {{ }}
.card header h3 {{ margin:0; font-size:1.02rem; flex:1; min-width:180px; }}
.art {{ font-size:.82rem; opacity:.9; font-variant-numeric:tabular-nums; }}
.badge {{ background:rgba(255,255,255,.22); border:1px solid rgba(255,255,255,.5); padding:1px 9px; border-radius:20px; font-size:.82rem; font-weight:600; }}
.eq {{ font-size:.78rem; background:rgba(0,0,0,.18); padding:1px 8px; border-radius:20px; }}
.body {{ padding:12px 14px; }}
.cmp {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.cmp > div {{ border-radius:6px; padding:8px 10px; background:var(--bg); }}
.card.v-rouge .cmp > div:last-child {{ background:var(--rouge-bg); }}
.card.v-vert .cmp > div:last-child {{ background:var(--vert-bg); }}
.card.v-bleu .cmp > div:last-child {{ background:var(--bleu-bg); }}
.card.v-orange .cmp > div:last-child {{ background:var(--orange-bg); }}
h4 {{ margin:0 0 4px; font-size:.78rem; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }}
.body p {{ margin:0; white-space:pre-line; }}
.just {{ margin-top:10px; }}
.src {{ margin-top:10px; font-size:.86rem; }}
.src ul {{ margin:0; padding-left:18px; }}
.src li {{ margin:2px 0; overflow-wrap:anywhere; }}
.path {{ font-family:ui-monospace,Consolas,monospace; font-size:.8rem; }}
.pg {{ font-weight:600; }}
.muted {{ color:var(--muted); }}
.obs {{ margin:10px 0; }} .obs p {{ margin:0; white-space:pre-line; }}
.legend {{ display:flex; flex-wrap:wrap; gap:8px 18px; font-size:.9rem; }}
.legend span::before {{ content:""; display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:6px; vertical-align:-1px; background:var(--c); }}
.hidden {{ display:none !important; }}
@media (max-width:720px) {{ .stats {{ grid-template-columns:1fr 1fr; }} .cmp {{ grid-template-columns:1fr; }} }}
@media print {{ .tools,.stat {{ cursor:auto; }} .card {{ break-inside:avoid; }} details.box {{ display:block; }} }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Conformité du DOE à la notice descriptive</h1>
  <p class="sub">Résidence « ART'MONY », 112 logements, rue d'Italie / rue du Luxembourg, 94320 Thiais. Notice ATTITUDE LVT V1.2 (déc. 2024) comparée au DOE « 1er envoi ». Rapport généré le {today} : {total} prestations comparées, {web_count} sources web citées.</p>

  <div class="stats">{stat}</div>

  <div class="box">
    <div class="legend">
      <span style="--c:var(--rouge)"><b>Rouge</b> : manifestement inférieure (ou absente)</span>
      <span style="--c:var(--vert)"><b>Vert</b> : manifestement supérieure</span>
      <span style="--c:var(--bleu)"><b>Bleu</b> : respectée à la lettre (modèle cité, ou équivalent démontré, signalé par un libellé)</span>
      <span style="--c:var(--orange)"><b>Orange</b> : cas en doute ou non documenté dans le DOE</span>
    </div>
    <p class="muted" style="margin:8px 0 0;font-size:.86rem">Les liens « p.N » ouvrent la <a href="{e(quote(NOTICE_PDF))}" target="_blank" rel="noopener">notice descriptive</a> à la page citée. Les pièces du DOE (documents des entreprises) ne sont pas publiées : elles sont citées par leur chemin dans l'archive <code>1er envoi DOE.zip</code>, avec les pages concernées. La <a href="comparaison_md/README.md">version Markdown</a> du rapport contient les mêmes données. Le DOE étant un premier envoi, une prestation « non documentée » n'est pas forcément absente du chantier : il s'agit d'un point à réclamer au promoteur.</p>
  </div>

  <div class="tools">
    <input type="search" id="q" placeholder="Rechercher (ex. receveur, Hansgrohe, 2.6.2.7)…">
    <button id="reset">Tout afficher</button>
  </div>

  <details class="box"><summary>Tableau de synthèse ({total} lignes)</summary>
    <table><thead><tr><th>Article</th><th>Prestation</th><th>Verdict</th></tr></thead><tbody>{rows}</tbody></table>
  </details>

  {body_sections}

  <section class="chap"><h2>Observations générales par lot</h2>{obs_html}</section>
</div>
<script>
(function(){{
  var active=null, q=document.getElementById('q');
  var cards=[].slice.call(document.querySelectorAll('.card')), rows=[].slice.call(document.querySelectorAll('tbody tr'));
  var btns=[].slice.call(document.querySelectorAll('.stat'));
  function apply(){{
    var t=(q.value||'').toLowerCase().trim();
    cards.forEach(function(c){{ var ok=(!active||c.dataset.v===active)&&(!t||c.dataset.s.indexOf(t)>=0); c.classList.toggle('hidden',!ok); }});
    rows.forEach(function(r){{ r.classList.toggle('hidden', !!active && r.dataset.v!==active); }});
    document.querySelectorAll('.chap').forEach(function(s){{ var cs=s.querySelectorAll('.card'); if(!cs.length) return; s.classList.toggle('hidden', ![].some.call(cs,function(c){{return !c.classList.contains('hidden');}})); }});
    btns.forEach(function(b){{ b.setAttribute('aria-pressed', b.dataset.filter===active?'true':'false'); }});
  }}
  btns.forEach(function(b){{ b.addEventListener('click',function(){{ active = active===b.dataset.filter?null:b.dataset.filter; apply(); }}); }});
  q.addEventListener('input',apply);
  document.getElementById('reset').addEventListener('click',function(){{ active=null; q.value=''; apply(); }});
}})();
</script>
</body>
</html>'''

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(page)
print(f"{OUT}: {total} items {counts}, {web_count} web sources")
