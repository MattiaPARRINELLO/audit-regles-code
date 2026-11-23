# Audit des règles

Dépôt : `/home/mattia/Documents/dev/audit-regles-code/demo/avant`
Fichiers analysés : 3
Langages : python
Violations : 19

| Règle | Nombre | Gravité |
|---|---|---|
| fonction_trop_longue | 1 | moyenne |
| else_apres_return | 1 | basse |
| comparaison_enchainee | 1 | basse |
| suppression_linter | 1 | moyenne |
| nommage_afficher | 1 | basse |
| responsabilite_multiple | 1 | moyenne |
| fonction_morte | 6 | moyenne |
| duplication | 1 | moyenne |
| code_commente | 2 | basse |
| ligne_trop_longue | 4 | basse |

## fonction_trop_longue (1)

- `gestion.py:7` [python] f : 33 lignes utiles (max 10)

## else_apres_return (1)

- `gestion.py:44` [python] else inutile après un return

## comparaison_enchainee (1)

- `gestion.py:21` [python] comparaison enchaînée

## suppression_linter (1)

- `gestion.py:55` [python] directive de suppression interdite

## nommage_afficher (1)

- `gestion.py:50` [python] afficher_total renvoie une valeur, un affichage ne devrait pas

## responsabilite_multiple (1)

- `gestion.py:7` [python] f renvoie une valeur et produit un affichage

## fonction_morte (6)

- `gestion.py:43` [python] est_dispo n'est jamais appelée, à vérifier
- `gestion.py:50` [python] afficher_total n'est jamais appelée, à vérifier
- `gestion.py:54` [python] aide n'est jamais appelée, à vérifier
- `gestion.py:59` [python] vieux_tri n'est jamais appelée, à vérifier
- `gestion.py:63` [python] formater_livre n'est jamais appelée, à vérifier
- `gestion.py:70` [python] formater_livre_bis n'est jamais appelée, à vérifier

## duplication (1)

- `gestion.py:64` [?] bloc de 4 lignes répété 2 fois, par exemple en gestion.py:71

## code_commente (2)

- `gestion.py:1` [python] ligne de code commentée, à vérifier
- `gestion.py:2` [python] ligne de code commentée, à vérifier

## ligne_trop_longue (4)

- `donnees.py:2` [python] 93 colonnes (max 79)
- `donnees.py:3` [python] 82 colonnes (max 79)
- `donnees.py:4` [python] 82 colonnes (max 79)
- `gestion.py:34` [python] 96 colonnes (max 79)

