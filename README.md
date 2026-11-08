# ArtMony Documentation

Documentation de la résidence **ART'MONY** (112 logements, rue d'Italie / rue du Luxembourg, 94320 Thiais, Bouygues Immobilier, collection ATTITUDE) : comparaison du DOE (Dossier des Ouvrages Exécutés, « 1er envoi ») avec la notice descriptive remise aux acquéreurs.

## Contenu

| Chemin | Contenu |
|---|---|
| [`index.html`](index.html) | Rapport interactif : 218 prestations comparées, en-têtes de couleur, filtres, sources DOE et web. C'est la page d'accueil du site statique. |
| [`comparaison_md/`](comparaison_md/README.md) | Même analyse en Markdown : synthèse, écarts à réclamer, détail par chapitre de la notice et par lot, sources web, inventaire du DOE, données JSON et scripts de génération. |
| [`notice/`](notice/) | Notice descriptive ATTITUDE LVT V1.2 (déc. 2024). |

Les pièces du DOE sont des documents des entreprises (fiches produits, plans, PV, attestations). Elles **ne sont pas publiées** dans ce dépôt : le rapport les cite par leur chemin dans l'archive `1er envoi DOE.zip`, avec les pages concernées.

## Code couleur

- 🔴 **Rouge** : prestation manifestement inférieure à la notice
- 🟢 **Vert** : prestation manifestement supérieure
- 🔵 **Bleu** : notice respectée à la lettre (ou équivalent démontré)
- 🟠 **Orange** : cas en doute ou non documenté dans le DOE

## Fichiers volumineux (Git LFS)

Les PDF (aujourd'hui, uniquement la notice), archives, images et tableurs sont stockés avec **Git LFS** (règles dans [`.gitattributes`](.gitattributes)). Pour cloner le dépôt avec les fichiers réels :

```bash
git lfs install
git clone <url-du-depot>
```

Sans Git LFS, ces fichiers ne sont que des pointeurs texte de quelques octets.

## Publication en site statique (GitHub Pages)

La publication classique de GitHub Pages (« Deploy from a branch ») **ne sert pas les fichiers LFS** : les liens vers les PDF afficheraient les pointeurs. Le workflow [`.github/workflows/pages.yml`](.github/workflows/pages.yml) récupère les fichiers LFS avant de publier le site. Pour l'activer :

1. Pousser le dépôt sur GitHub.
2. Dans *Settings → Pages → Build and deployment*, choisir **Source : GitHub Actions**.
3. Le site se publie à chaque push sur `main`.

À noter : avec un compte gratuit, GitHub Pages exige un dépôt **public**. Le rapport cite des noms d'entreprises et de produits, et la notice est jointe.
