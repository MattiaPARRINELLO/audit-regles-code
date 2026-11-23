# Audit des règles

Dépôt : `/home/mattia/Documents/dev/audit-regles-code/demo/avant`
Fichiers analysés : 1
Langages : python
Violations : 8

## fonction_trop_longue (1)

- `exemple.py:7` [python] calculer_total : 11 lignes utiles (max 10)

## else_apres_return (1)

- `exemple.py:22` [python] else inutile après un return

## comparaison_enchainee (1)

- `exemple.py:29` [python] comparaison enchaînée

## suppression_linter (1)

- `exemple.py:35` [python] directive de suppression interdite

## fonction_morte (2)

- `exemple.py:7` [python] calculer_total n'est jamais appelée, à vérifier
- `exemple.py:34` [python] ancien_affichage n'est jamais appelée, à vérifier

## code_commente (2)

- `exemple.py:3` [python] ligne de code commentée, à vérifier
- `exemple.py:4` [python] ligne de code commentée, à vérifier

