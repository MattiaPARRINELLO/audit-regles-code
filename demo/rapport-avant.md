# Audit des règles

Dépôt : `/home/mattia/Documents/dev/audit-regles-code/demo/avant`
Fichiers Python analysés : 1
Violations : 8

## fonction_trop_longue (1)

- `exemple.py:7` calculer_total : 11 lignes utiles (max 10)

## else_apres_return (1)

- `exemple.py:22` else inutile après un return

## comparaison_enchainee (1)

- `exemple.py:29` comparaison enchaînée

## noqa (1)

- `exemple.py:35` directive noqa interdite

## fonction_morte (2)

- `exemple.py:7` calculer_total n'est jamais appelée, à vérifier
- `exemple.py:34` ancien_affichage n'est jamais appelée, à vérifier

## code_commente (2)

- `exemple.py:3` ligne de code commentée, à vérifier
- `exemple.py:4` ligne de code commentée, à vérifier

