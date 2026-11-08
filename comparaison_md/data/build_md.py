"""Génère la base de connaissances Markdown à partir de results/*.json.
Usage : python -I build_md.py <dossier_sortie>"""
import json, glob, os, re, sys, shutil, datetime
from collections import defaultdict, Counter
from urllib.parse import quote
DOE_MAP = {}  # les pièces du DOE ne sont pas publiées : elles sont citées par leur chemin, sans lien

def doe_href(rel, base):
    pub = DOE_MAP.get(rel.replace(chr(92), '/'))
    return (base + '../' + quote(pub)) if pub else None

SCRATCH = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
V = {"rouge": "🔴 Inférieure", "orange": "🟠 Doute", "bleu": "🔵 Conforme", "vert": "🟢 Supérieure"}
ORDER = ["rouge", "orange", "bleu", "vert"]
CHAP = {
    "1": "Caractéristiques techniques générales de l'immeuble",
    "2": "Locaux privatifs et leurs équipements",
    "3": "Annexes privatives",
    "4": "Parties communes intérieures",
    "5": "Équipements généraux de l'immeuble",
    "6": "Parties communes extérieures",
    "7": "Organigramme des clés",
    "8": "Information des habitants",
}

def akey(a):
    n = re.findall(r"\d+", str(a or "99"))
    return [int(x) for x in n] or [99]

def slug(s):
    s = re.sub(r"[^\w\- ]", "", s, flags=re.U).strip().replace(" ", "_")
    return s[:60]

def cell(s):
    return str(s or "").replace("|", "/").replace("\n", " ")

def write(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")

# ---------- chargement
lots, items = [], []
for f in sorted(glob.glob(os.path.join(SCRATCH, "results", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    lot = {"id": d.get("agent") or os.path.splitext(os.path.basename(f))[0],
           "perimetre": d.get("perimetre", ""), "observations": d.get("observations", ""), "items": []}
    for it in d.get("items", []):
        v = str(it.get("verdict", "orange")).lower().strip()
        it["verdict"] = v if v in V else "orange"
        it["_lot"] = lot["id"]
        lot["items"].append(it)
        items.append(it)
    lots.append(lot)
items.sort(key=lambda i: (akey(i.get("article")), str(i.get("titre"))))
for n, it in enumerate(items, 1):
    it["_id"] = f"P{n:03d}"
cnt = Counter(i["verdict"] for i in items)
today = datetime.date.today().isoformat()

def chap_of(it):
    return str(akey(it.get("article"))[0])

def chap_file(ch):
    return f"par_chapitre/{ch}_{slug(CHAP.get(ch, 'Autres'))}.md"

def lot_file(lot_id):
    return f"par_lot/{lot_id}.md"

def detail(it, h="###", base=""):
    eq = " (équivalent démontré)" if it["verdict"] == "bleu" and it.get("equivalence") else ""
    out = [f"{h} {it['_id']} · Art. {it.get('article')} · {it.get('titre')}",
           "",
           f"**Verdict : {V[it['verdict']]}{eq}** · lot d'analyse : [{it['_lot']}]({base}{lot_file(it['_lot'])})",
           "",
           f"- **Notice :** {it.get('notice')}",
           f"- **DOE :** {it.get('doe')}",
           f"- **Analyse :** {it.get('justification')}"]
    sd = it.get("sources_doe") or []
    if sd:
        out.append("- **Pièces DOE :**")
        for s in sd:
            extra = f" ({s['pages']})" if s.get("pages") else ""
            note = f" — {s['note']}" if s.get("note") else ""
            h = doe_href(s.get('fichier') or '', base)
            lk = f" [ouvrir]({h})" if h else ""
            out.append(f"  - `{s.get('fichier')}`{extra}{note}{lk}")
    sw = it.get("sources_web") or []
    if sw:
        out.append("- **Sources web :**")
        for s in sw:
            ap = f" — {s['apport']}" if s.get("apport") else ""
            out.append(f"  - [{s.get('titre') or s.get('url')}]({s.get('url')}){ap}")
    out.append("")
    return "\n".join(out)

def table(rows, base=""):
    t = ["| ID | Article | Prestation | Verdict | Lot |", "|---|---|---|---|---|"]
    for it in rows:
        ch = chap_of(it)
        anchor = f"{base}{chap_file(ch)}"
        t.append(f"| {it['_id']} | {cell(it.get('article'))} | [{cell(it.get('titre'))}]({anchor}) | {V[it['verdict']]} | {it['_lot']} |")
    return "\n".join(t)

# ---------- README
nb_web = sum(len(i.get("sources_web") or []) for i in items)
readme = f"""# Analyse de conformité DOE / notice descriptive — Résidence ART'MONY (Thiais)

Généré le {today}. Point d'entrée de la base de connaissances : commencer ici pour toute question future.

## Contexte
- **Programme :** « ART'MONY », 112 logements, 3 bâtiments (A, B, C) en R+5 sur un niveau de sous-sol, rue d'Italie / rue du Luxembourg, 94320 Thiais. Promoteur : Bouygues Immobilier, collection ATTITUDE.
- **Bâtiment A :** vendu en logement locatif intermédiaire à un bailleur institutionnel (I3F). Ses prestations suivent le descriptif du bailleur et **pas** la notice ATTITUDE. La notice vaut pour les bâtiments **B et C** (accession).
- **Engagements de la notice :** NF Habitat HQE, label E3C1, seuil 2025 de la RE2020, Biodivercity.
- **Documents comparés :**
  - Notice : [../notice/Notice_ATTITUDE_ArtMony_V1.2.pdf](../notice/Notice_ATTITUDE_ArtMony_V1.2.pdf) (ATTITUDE LVT V1.2, déc. 2024, 27 p. ; original : `241206 Notice Attitude.pdf.pdf`). Texte intégral : [notice_texte.md](notice_texte.md).
  - DOE : `C:\\Workspace\\Bouygue\\1er envoi DOE.zip` (2 Go, environ 900 fichiers dont 1 146 PDF une fois les zip imbriqués extraits). Il s'agit d'un **1er envoi**, donc certaines pièces manquent. Inventaire : [doe_inventaire.md](doe_inventaire.md).
- **Rapport visuel :** [../index.html](../index.html), généré à partir des mêmes données que les fichiers .md. Les pièces du DOE (documents des entreprises) ne sont pas publiées dans ce dépôt. Elles sont citées par leur chemin dans l'archive `1er envoi DOE.zip`, avec les pages concernées.

## Code couleur
| Verdict | Signification | Nombre |
|---|---|---|
| {V['rouge']} | Prestation manifestement inférieure, ou absente alors que la notice la prévoit | {cnt['rouge']} |
| {V['orange']} | Cas en doute : équivalence incertaine, contradiction entre pièces, ou point non documenté dans ce 1er envoi | {cnt['orange']} |
| {V['bleu']} | Notice respectée à la lettre (modèle cité, ou équivalent démontré, ce qui est signalé) | {cnt['bleu']} |
| {V['vert']} | Prestation manifestement supérieure | {cnt['vert']} |
| **Total** | | **{len(items)}** prestations, {nb_web} sources web citées |

## Navigation
- [synthese.md](synthese.md) : tableau de toutes les prestations triées par article de la notice.
- [ecarts_et_points_a_reclamer.md](ecarts_et_points_a_reclamer.md) : toutes les prestations rouges et orange, avec le détail. **C'est le fichier à utiliser pour un courrier au promoteur.**
- [conformes_et_superieurs.md](conformes_et_superieurs.md) : prestations bleues et vertes, avec le détail.
- **Par chapitre de la notice** (détail complet de chaque comparaison) :
{chr(10).join(f'  - [{ch}. {CHAP[ch]}]({chap_file(ch)}) ({sum(1 for i in items if chap_of(i)==ch)} prestations)' for ch in sorted({chap_of(i) for i in items}, key=int))}
- **Par lot d'analyse** (périmètre, observations de l'analyste, pièces manquantes, anomalies) :
{chr(10).join(f'  - [{l["id"]}]({lot_file(l["id"])}) : {l["perimetre"]} ({len(l["items"])} prestations)' for l in lots)}
- [sources_web.md](sources_web.md) : toutes les URL consultées, par prestation.
- [data/](data/) : données brutes JSON par lot (format : article, titre, notice, doe, verdict, equivalence, justification, sources_doe, sources_web).
- [methode.md](methode.md) : méthode suivie, limites, et comment régénérer.

## Comment répondre à une question future
1. Chercher l'article (ex. `2.6.2.7`) ou le produit (ex. `Hansgrohe`) avec grep dans `par_chapitre/` ou `data/*.json`.
2. Pour revenir à la source, les chemins `sources_doe` sont relatifs à la racine de l'archive `1er envoi DOE.zip`, qui n'est pas incluse dans ce dépôt. Un chemin contenant `_unzipped/` désigne un fichier situé dans un zip imbriqué de l'archive (`<nom>_unzipped/` correspond au contenu de `<nom>.zip`).
3. Pour une pièce non citée, extraire le zip et faire `pdftotext` (voir [methode.md](methode.md)).
"""
write("README.md", readme)

# ---------- synthèse
syn = [f"# Synthèse — toutes les prestations ({len(items)})", "",
       "Triées par article de la notice. Le détail de chaque ligne se trouve dans le fichier du chapitre (lien sur la prestation).", "",
       " · ".join(f"{V[k]} : {cnt[k]}" for k in ORDER), ""]
for ch in sorted({chap_of(i) for i in items}, key=int):
    rows = [i for i in items if chap_of(i) == ch]
    c = Counter(i["verdict"] for i in rows)
    syn += [f"## {ch}. {CHAP.get(ch, 'Autres')}", "", " · ".join(f"{V[k]} : {c[k]}" for k in ORDER if c[k]), "", table(rows), ""]
write("synthese.md", "\n".join(syn))

# ---------- écarts
ec = ["# Écarts et points à réclamer (rouge puis orange)", "",
      "Les prestations rouges sont des écarts établis. Les orange sont à faire préciser par le promoteur : une pièce manque au DOE, des documents se contredisent ou l'équivalence n'est pas démontrée.", ""]
for v in ("rouge", "orange"):
    rows = [i for i in items if i["verdict"] == v]
    ec += [f"## {V[v]} ({len(rows)})", "", table(rows), ""]
    for it in rows:
        ec.append(detail(it, "###"))
write("ecarts_et_points_a_reclamer.md", "\n".join(ec))

cs = ["# Prestations conformes et supérieures", ""]
for v in ("vert", "bleu"):
    rows = [i for i in items if i["verdict"] == v]
    cs += [f"## {V[v]} ({len(rows)})", "", table(rows), ""]
    for it in rows:
        cs.append(detail(it, "###"))
write("conformes_et_superieurs.md", "\n".join(cs))

# ---------- par chapitre
for ch in sorted({chap_of(i) for i in items}, key=int):
    rows = [i for i in items if chap_of(i) == ch]
    md = [f"# {ch}. {CHAP.get(ch, 'Autres')}", "", "[← README](../README.md)", "", table(rows, "../"), ""]
    sub = None
    for it in rows:
        a = akey(it.get("article"))
        s = ".".join(map(str, a[:2]))
        if s != sub:
            sub = s
            md.append(f"## Article {s}\n")
        md.append(detail(it, "###", "../"))
    write(chap_file(ch), "\n".join(md))

# ---------- par lot
for l in lots:
    c = Counter(i["verdict"] for i in l["items"])
    rows = sorted(l["items"], key=lambda i: akey(i.get("article")))
    md = [f"# Lot d'analyse {l['id']}", "", "[← README](../README.md)", "",
          f"**Périmètre :** {l['perimetre']}", "",
          " · ".join(f"{V[k]} : {c[k]}" for k in ORDER), "",
          "## Observations de l'analyste (pièces manquantes, anomalies, hors notice)", "", l["observations"] or "_Aucune._", "",
          "## Prestations", "", table(rows, "../"), ""]
    for it in rows:
        md.append(detail(it, "###", "../"))
    write(lot_file(l["id"]), "\n".join(md))

# ---------- sources web
sw = ["# Sources web consultées", "", "Classées par prestation. Chaque URL a été citée par l'agent d'analyse comme réellement consultée.", ""]
dom = Counter()
for it in items:
    if it.get("sources_web"):
        sw.append(f"## {it['_id']} · Art. {it.get('article')} · {it.get('titre')} ({V[it['verdict']]})")
        for s in it["sources_web"]:
            u = s.get("url", "")
            m = re.match(r"https?://([^/]+)", u)
            if m: dom[m.group(1)] += 1
            sw.append(f"- [{s.get('titre') or u}]({u})" + (f" — {s['apport']}" if s.get("apport") else ""))
        sw.append("")
sw += ["## Domaines les plus cités", "", "| Domaine | Citations |", "|---|---|"] + [f"| {d} | {n} |" for d, n in dom.most_common(40)]
write("sources_web.md", "\n".join(sw))

# ---------- données brutes
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
for f in glob.glob(os.path.join(SCRATCH, "results", "*.json")):
    shutil.copy(f, os.path.join(OUT, "data", os.path.basename(f)))

# ---------- notice
notice = open(os.path.join(SCRATCH, "notice.txt"), encoding="utf-8").read()
write("notice_texte.md", "# Notice descriptive ATTITUDE LVT V1.2 (déc. 2024) — texte intégral\n\n"
      "Extraction pdftotext -layout du PDF `241206 Notice Attitude.pdf.pdf`. Les numéros de page figurent en pied de page (« ATTITUDE LVT V1.2 - DECEMBRE 2024   N »).\n\n```text\n" + notice + "\n```")

# ---------- inventaire DOE + textes des pièces citées
idx = [l.rstrip("\n").split("\t", 1) for l in open(os.path.join(SCRATCH, "txt", "index.tsv"), encoding="utf-8")]
by_path = {p: n for n, p in idx}
lot_count = defaultdict(lambda: defaultdict(int))
for n, p in idx:
    parts = p.split("/")
    lot_count[parts[0]][parts[1] if len(parts) > 2 else "(racine)"] += 1
others = [l.strip() for l in open(os.path.join(SCRATCH, "txt", "autres_fichiers.txt"), encoding="utf-8") if l.strip()]
cited = defaultdict(list)
for it in items:
    for s in it.get("sources_doe") or []:
        cited[(s.get("fichier") or "").replace("\\", "/")].append(it["_id"])

inv = ["# Inventaire du DOE « 1er envoi »", "",
       f"{len(idx)} PDF (après extraction des zip imbriqués) et {len(others)} autres fichiers. Les chemins sont relatifs à la racine de l'archive. `_unzipped/` désigne un zip imbriqué qui a été extrait.", "",
       "## Répartition par lot et par entreprise (PDF)", ""]
for lot in sorted(lot_count):
    inv.append(f"### {lot}")
    for sub, n in sorted(lot_count[lot].items()):
        inv.append(f"- {sub} : {n} PDF")
    inv.append("")
inv += ["## Pièces du DOE citées dans l'analyse", "", "Pièces citées par leur chemin dans l'archive, non publiées dans ce dépôt.", "", "| Pièce | Prestations |", "|---|---|"]
for p in sorted(cited):
    inv.append(f"| `{p}` | {', '.join(sorted(set(cited[p])))} |")
inv += ["", "## Index complet des PDF", "", "| N° | Chemin |", "|---|---|"] + [f"| {n} | `{p}` |" for n, p in idx]
inv += ["", "## Autres fichiers (non PDF)", ""] + [f"- `{o}`" for o in others]
write("doe_inventaire.md", "\n".join(inv))

# ---------- méthode
write("methode.md", f"""# Méthode, limites et régénération

## Méthode
1. Extraction du texte de la notice (pdftotext -layout) et découpage en articles numérotés.
2. Extraction du DOE (zip de 2 Go, plus 6 zip imbriqués), puis conversion des 1 146 PDF en texte (80 premières pages chacun). Les PDF scannés ont été lus en image.
3. Analyse confiée à {len(lots)} agents, un par groupe de lots du DOE : {", ".join(l["id"] for l in lots)}. Pour chaque prestation de la notice, chaque agent relève ce que le DOE documente (marque, modèle, référence, caractéristiques). Quand le produit diffère, il fait des recherches web pour situer la gamme (caractéristiques techniques, certifications, garantie, prix public indicatif).
4. Verdict selon le code couleur décrit dans le [README](README.md). Règles appliquées : pas de rouge ni de vert sans preuve ; un point non documenté est classé orange, jamais bleu par défaut.
5. Agrégation dans le rapport HTML et dans cette base Markdown.

## Limites
- Le DOE est un **1er envoi** : un orange « non documenté » ne veut pas dire que la prestation est absente du chantier.
- Les vérifications du nombre de prises et des équipements par logement sont des **sondages** sur quelques logements types (voir le lot G), pas une vérification exhaustive.
- Le bâtiment A (bailleur I3F) n'est pas soumis à la notice ATTITUDE. Ses écarts sont signalés pour information.
- Les prix publics indicatifs sont ceux constatés sur le web à la date de l'analyse ({today}).
- L'analyse porte sur les documents et non sur une visite : un produit peut être conforme sur fiche et mal posé, ou l'inverse.

## Régénérer
Scripts (dans le scratchpad de la session d'origine, reproduits ici pour mémoire) :
- `build_html.py <sortie.html>` : rapport HTML à partir de `data/*.json` (dossier `results/`).
- `build_md.py <dossier>` : la présente base Markdown.
Extraction du texte d'un PDF du DOE : `pdftotext -enc UTF-8 -layout fichier.pdf sortie.txt`. Les chemins de l'archive dépassent souvent 260 caractères sous Windows : copier d'abord le PDF vers un chemin court.
""")
for s in ("build_html.py", "build_md.py"):
    shutil.copy(os.path.join(SCRATCH, s), os.path.join(OUT, "data", s))
print("OK", len(items), dict(cnt), "fichiers cités:", len(cited))
