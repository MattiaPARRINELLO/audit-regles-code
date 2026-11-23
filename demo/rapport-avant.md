# Audit des règles

Dépôt : `/home/mattia/Documents/dev/audit-regles-code/demo/avant`
Fichiers analysés : 2
Langages : python
Violations : 18

| Règle | Nombre | Gravité |
|---|---|---|
| fonction_trop_longue | 1 | moyenne |
| else_apres_return | 3 | basse |
| comparaison_enchainee | 1 | basse |
| suppression_linter | 1 | moyenne |
| nommage_afficher | 1 | basse |
| responsabilite_multiple | 1 | moyenne |
| fonction_morte | 4 | moyenne |
| duplication | 2 | moyenne |
| code_commente | 2 | basse |
| ligne_trop_longue | 2 | basse |

## fonction_trop_longue (1)

- `facture.py:7` [python] calculer : 17 lignes utiles (max 10)

## else_apres_return (3)

- `facture.py:28` [python] else inutile après un return
- `facture.py:35` [python] else inutile après un return
- `facture.py:10` [python] else inutile après un return

## comparaison_enchainee (1)

- `facture.py:28` [python] comparaison enchaînée

## suppression_linter (1)

- `facture.py:62` [python] directive de suppression interdite

## nommage_afficher (1)

- `facture.py:55` [python] afficher_facture renvoie une valeur, un affichage ne devrait pas

## responsabilite_multiple (1)

- `facture.py:55` [python] afficher_facture renvoie une valeur et produit un affichage

## fonction_morte (4)

- `facture.py:27` [python] quantite_valide n'est jamais appelée, à vérifier
- `facture.py:34` [python] prix_valide n'est jamais appelée, à vérifier
- `facture.py:48` [python] formater_bis n'est jamais appelée, à vérifier
- `facture.py:61` [python] vieux_format n'est jamais appelée, à vérifier

## duplication (2)

- `facture.py:19` [?] bloc de 4 lignes répété 2 fois, par exemple en facture.py:21
- `facture.py:42` [?] bloc de 4 lignes répété 2 fois, par exemple en facture.py:49

## code_commente (2)

- `facture.py:1` [python] ligne de code commentée, à vérifier
- `facture.py:2` [python] ligne de code commentée, à vérifier

## ligne_trop_longue (2)

- `facture.py:45` [python] 92 colonnes (max 79)
- `facture.py:52` [python] 92 colonnes (max 79)

