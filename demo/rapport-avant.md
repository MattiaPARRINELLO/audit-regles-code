# Audit des règles

Dépôt : `/home/mattia/Documents/dev/audit-regles-code/demo/avant`
Fichiers analysés : 1
Langages : python
Violations : 20

| Règle | Nombre | Gravité |
|---|---|---|
| fonction_trop_longue | 1 | moyenne |
| else_apres_return | 3 | basse |
| comparaison_enchainee | 1 | basse |
| suppression_linter | 1 | moyenne |
| nommage_afficher | 2 | basse |
| responsabilite_multiple | 1 | moyenne |
| fonction_morte | 5 | moyenne |
| duplication | 2 | moyenne |
| code_commente | 2 | basse |
| ligne_trop_longue | 2 | basse |

## fonction_trop_longue (1)

- `exemple.py:7` [python] f : 20 lignes utiles (max 10)

## else_apres_return (3)

- `exemple.py:31` [python] else inutile après un return
- `exemple.py:38` [python] else inutile après un return
- `exemple.py:10` [python] else inutile après un return

## comparaison_enchainee (1)

- `exemple.py:31` [python] comparaison enchaînée

## suppression_linter (1)

- `exemple.py:59` [python] directive de suppression interdite

## nommage_afficher (2)

- `exemple.py:44` [python] afficher_article renvoie une valeur, un affichage ne devrait pas
- `exemple.py:51` [python] afficher_article_bis renvoie une valeur, un affichage ne devrait pas

## responsabilite_multiple (1)

- `exemple.py:7` [python] f renvoie une valeur et produit un affichage

## fonction_morte (5)

- `exemple.py:30` [python] valide_q n'est jamais appelée, à vérifier
- `exemple.py:37` [python] valide_p n'est jamais appelée, à vérifier
- `exemple.py:44` [python] afficher_article n'est jamais appelée, à vérifier
- `exemple.py:51` [python] afficher_article_bis n'est jamais appelée, à vérifier
- `exemple.py:58` [python] vieux_format n'est jamais appelée, à vérifier

## duplication (2)

- `exemple.py:22` [?] bloc de 4 lignes répété 2 fois, par exemple en exemple.py:24
- `exemple.py:45` [?] bloc de 4 lignes répété 2 fois, par exemple en exemple.py:52

## code_commente (2)

- `exemple.py:1` [python] ligne de code commentée, à vérifier
- `exemple.py:2` [python] ligne de code commentée, à vérifier

## ligne_trop_longue (2)

- `exemple.py:48` [python] 105 colonnes (max 79)
- `exemple.py:55` [python] 105 colonnes (max 79)

