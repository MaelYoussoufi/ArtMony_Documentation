# Méthode, limites et régénération

## Méthode
1. Extraction du texte de la notice (pdftotext -layout) et découpage en articles numérotés.
2. Extraction du DOE (zip de 2 Go, plus 6 zip imbriqués), puis conversion des 1 146 PDF en texte (80 premières pages chacun). Les PDF scannés ont été lus en image.
3. Analyse confiée à 7 agents, un par groupe de lots du DOE : A_structure_enveloppe, B_menuiseries_ext_metallerie, C_menuiserie_interieure, D_revetements_peinture, E_plomberie_sanitaires, F_chauffage_ventilation, G_electricite_ascenseur. Pour chaque prestation de la notice, chaque agent relève ce que le DOE documente (marque, modèle, référence, caractéristiques). Quand le produit diffère, il fait des recherches web pour situer la gamme (caractéristiques techniques, certifications, garantie, prix public indicatif).
4. Verdict selon le code couleur décrit dans le [README](README.md). Règles appliquées : pas de rouge ni de vert sans preuve ; un point non documenté est classé orange, jamais bleu par défaut.
5. Agrégation dans le rapport HTML et dans cette base Markdown.

## Limites
- Le DOE est un **1er envoi** : un orange « non documenté » ne veut pas dire que la prestation est absente du chantier.
- Les vérifications du nombre de prises et des équipements par logement sont des **sondages** sur quelques logements types (voir le lot G), pas une vérification exhaustive.
- Le bâtiment A (bailleur I3F) n'est pas soumis à la notice ATTITUDE. Ses écarts sont signalés pour information.
- Les prix publics indicatifs sont ceux constatés sur le web à la date de l'analyse (2026-11-08).
- L'analyse porte sur les documents et non sur une visite : un produit peut être conforme sur fiche et mal posé, ou l'inverse.

## Régénérer
Scripts (dans le scratchpad de la session d'origine, reproduits ici pour mémoire) :
- `build_html.py <sortie.html>` : rapport HTML à partir de `data/*.json` (dossier `results/`).
- `build_md.py <dossier>` : la présente base Markdown.
Extraction du texte d'un PDF du DOE : `pdftotext -enc UTF-8 -layout fichier.pdf sortie.txt`. Les chemins de l'archive dépassent souvent 260 caractères sous Windows : copier d'abord le PDF vers un chemin court.
