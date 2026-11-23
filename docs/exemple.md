# L'exemple, en détail

Un petit projet de bibliothèque, écrit une première fois comme du code de
dernière minute, puis repris proprement. Les deux versions produisent
exactement la même sortie.

## Le scénario

Le programme affiche :

1. la liste des livres avec leur disponibilité ;
2. la liste des emprunts avec l'amende de retard ;
3. le total des amendes, le nombre de retards et le livre le plus ancien.

Règles métier :

- 0,20 € par jour jusqu'à 7 jours ;
- 0,50 € par jour au-delà de 7 jours ;
- plafond de 15 € par emprunt.

## Arborescence

```
demo/
├── avant/
│   ├── donnees.py
│   ├── gestion.py
│   └── main.py
└── apres/
    ├── constantes.py
    ├── donnees.py
    ├── amendes.py
    ├── livres.py
    ├── emprunts.py
    ├── rapport.py
    └── main.py
```

Trois fichiers avant, sept après.

## Avant

### `donnees.py`

```python
LIVRES = [
    {"titre": "Le Petit Prince", "auteur": "Saint-Exupéry", "annee": 1943, "exemplaires": 2},
    {"titre": "1984", "auteur": "George Orwell", "annee": 1949, "exemplaires": 1},
    {"titre": "Dune", "auteur": "Frank Herbert", "annee": 1965, "exemplaires": 0},
]

EMPRUNTS = [
    {"titre": "1984", "emprunteur": "Alice", "jours": 3},
    {"titre": "Le Petit Prince", "emprunteur": "Bob", "jours": 12},
    {"titre": "Dune", "emprunteur": "Chloé", "jours": 40},
]
```

Quatre lignes dépassent 79 colonnes.

### `gestion.py`, la fonction qui fait tout

```python
def f(l, e):
    print("=== Livres ===")
    for x in l:
        if x["exemplaires"] > 0:
            s = "disponible"
        else:
            s = "indisponible"
        print(f"{x['titre']} ({x['auteur']}, {x['annee']}) : {s}")
    print()
    print("=== Emprunts ===")
    tot = 0
    ret = 0
    for y in e:
        j = y["jours"]
        if 1 <= j <= 7:
            a = j*0.2
        else:
            if j > 7:
                a = 7*0.2 + (j-7)*0.5
            else:
                a = 0
        if a > 15:
            a = 15
        a = round(a, 2)
        if j > 7:
            ret = ret + 1
        tot = tot + a
        print(f"{y['emprunteur']} a emprunté {y['titre']} depuis {j} jours, amende : {a:.2f} €")
    print()
    v = l[0]
    for x in l:
        if x["annee"] < v["annee"]:
            v = x
    return round(tot, 2), ret, v["titre"]
```

Ce que l'audit reproche à cette seule fonction :

- 24 lignes utiles, au-delà de la limite de 10 ;
- elle affiche et renvoie trois valeurs, donc plusieurs responsabilités ;
- `1 <= j <= 7` est une comparaison enchaînée ;
- `0.2`, `0.5`, `7` et `15` sont des constantes magiques ;
- `l`, `e`, `x`, `y`, `j`, `a`, `tot`, `ret`, `v` sont des noms opaques.

### `gestion.py`, le reste

```python
def est_dispo(x):
    if x["exemplaires"] > 0:
        return True
    else:
        return False


def afficher_total(t):
    return f"Total : {t:.2f} €"


def aide():
    z = 1  # noqa
    return z


def vieux_tri(l):
    return sorted(l, key=lambda x: x["annee"])


def formater_livre(x):
    a = x["titre"]
    b = x["auteur"]
    c = x["annee"]
    return f"{a} ({b}, {c})"


def formater_livre_bis(x):
    a = x["titre"]
    b = x["auteur"]
    c = x["annee"]
    return f"{a} ({b}, {c})"
```

- `est_dispo` : `else` après `return`.
- `afficher_total` : une fonction d'affichage qui renvoie une valeur, et qui n'est
  appelée nulle part.
- `aide` : directive `# noqa` et fonction morte.
- `vieux_tri`, `formater_livre`, `formater_livre_bis` : jamais appelées.
- `formater_livre` et `formater_livre_bis` sont identiques.

Le fichier contient aussi du code commenté et un import `datetime` inutile.

### Rapport d'audit

```
Violations : 19

fonction_trop_longue     1
else_apres_return        1
comparaison_enchainee    1
suppression_linter       1
nommage_afficher         1
responsabilite_multiple  1
fonction_morte           6
duplication              1
code_commente            2
ligne_trop_longue        4
```

## Après

### `constantes.py`

```python
TARIF_COURT = 0.20
TARIF_LONG = 0.50
JOURS_PLEIN_TARIF = 7
PLAFOND_AMENDE = 15.00
```

### `donnees.py`

Mêmes données, une clé par ligne, pour rester sous 79 colonnes.

```python
LIVRES = [
    {
        "titre": "Le Petit Prince",
        "auteur": "Saint-Exupéry",
        "annee": 1943,
        "exemplaires": 2,
    },
    ...
]
```

### `amendes.py`

```python
def calculer_amende(jours):
    if jours <= JOURS_PLEIN_TARIF:
        return jours * TARIF_COURT
    jours_tardifs = jours - JOURS_PLEIN_TARIF
    return JOURS_PLEIN_TARIF * TARIF_COURT + jours_tardifs * TARIF_LONG


def plafonner(amende):
    if amende > PLAFOND_AMENDE:
        return PLAFOND_AMENDE
    return amende


def amende_de(emprunt):
    return round(plafonner(calculer_amende(emprunt["jours"])), 2)
```

### `livres.py`

```python
def est_disponible(livre):
    if livre["exemplaires"] <= 0:
        return False
    return True


def libelle_disponibilite(livre):
    if est_disponible(livre):
        return "disponible"
    return "indisponible"


def plus_ancien(livres):
    ancien = livres[0]
    for livre in livres:
        if livre["annee"] < ancien["annee"]:
            ancien = livre
    return ancien["titre"]
```

### `emprunts.py`

```python
def est_en_retard(emprunt):
    if emprunt["jours"] <= JOURS_PLEIN_TARIF:
        return False
    return True


def total_amendes(emprunts):
    total = 0
    for emprunt in emprunts:
        total = total + amende_de(emprunt)
    return total


def compter_retards(emprunts):
    retards = 0
    for emprunt in emprunts:
        if est_en_retard(emprunt):
            retards = retards + 1
    return retards
```

### `rapport.py`

```python
def formater_livre(livre):
    return (
        f"{livre['titre']} ({livre['auteur']}, {livre['annee']}) : "
        f"{libelle_disponibilite(livre)}"
    )


def formater_emprunt(emprunt):
    amende = amende_de(emprunt)
    return (
        f"{emprunt['emprunteur']} a emprunté {emprunt['titre']} "
        f"depuis {emprunt['jours']} jours, amende : {amende:.2f} €"
    )


def afficher_livres(livres):
    print("=== Livres ===")
    for livre in livres:
        print(formater_livre(livre))


def afficher_emprunts(emprunts):
    print()
    print("=== Emprunts ===")
    for emprunt in emprunts:
        print(formater_emprunt(emprunt))
```

### `main.py`

```python
def main():
    afficher_livres(LIVRES)
    afficher_emprunts(EMPRUNTS)
    print()
    total = total_amendes(EMPRUNTS)
    print(f"Total : {total:.2f} €")
    print(f"Retards : {compter_retards(EMPRUNTS)}")
    print(f"Plus ancien : {plus_ancien(LIVRES)}")
```

## Preuve du comportement

Les deux versions doivent imprimer exactement la même chose :

```
=== Livres ===
Le Petit Prince (Saint-Exupéry, 1943) : disponible
1984 (George Orwell, 1949) : disponible
Dune (Frank Herbert, 1965) : indisponible

=== Emprunts ===
Alice a emprunté 1984 depuis 3 jours, amende : 0.60 €
Bob a emprunté Le Petit Prince depuis 12 jours, amende : 3.90 €
Chloé a emprunté Dune depuis 40 jours, amende : 15.00 €

Total : 19.50 €
Retards : 2
Plus ancien : Le Petit Prince
```

Vérification :

```bash
cd demo/avant && python3 main.py > /tmp/avant.txt
cd ../apres && python3 main.py > /tmp/apres.txt
diff /tmp/avant.txt /tmp/apres.txt
# aucune sortie : les fichiers sont identiques
```

## Correspondance règle par règle

| Règle | Avant | Après |
|---|---|---|
| Responsabilité unique | `f` affiche, calcule et renvoie trois valeurs | `main` orchestre, les modules calculent ou affichent |
| Dix lignes utiles | `f` en fait 24 | `calculer_amende` en fait 5, `main` en fait 8 |
| Gardes explicites | `est_dispo` avec `else` après `return` | `est_disponible` avec une garde |
| Comparaison non enchaînée | `1 <= j <= 7` | `jours <= JOURS_PLEIN_TARIF` |
| Pas de directive de suppression | `# noqa` dans `aide` | fonction supprimée |
| Nommage explicite | `l`, `e`, `x`, `y`, `j`, `a` | `livres`, `emprunts`, `livre`, `jours`, `amende` |
| Affichage sans valeur de retour | `afficher_total` renvoie une chaîne | `afficher_livres` et `afficher_emprunts` ne renvoient rien |
| Pas de constante magique | `0.2`, `0.5`, `7`, `15` | `TARIF_COURT`, `TARIF_LONG`, `JOURS_PLEIN_TARIF`, `PLAFOND_AMENDE` |
| Pas de code mort | six fonctions sans appelant | toutes utilisées |
| Pas de duplication | `formater_livre` et `formater_livre_bis` | une seule fonction de formatage |
| Pas de code commenté | `ancien_total` | supprimé |
| Lignes courtes | quatre lignes au-delà de 79 | aucune |

## Reproduire

```bash
# comportement
cd demo/avant && python3 main.py
cd ../apres && python3 main.py

# comptes officiels
python3 ../../skill/audit-regles-code/scripts/audit_regles.py . --summary
```

Depuis la racine du dépôt :

```bash
python3 skill/audit-regles-code/scripts/audit_regles.py demo/avant --summary
# violations=19 fichiers=3 langues=python

python3 skill/audit-regles-code/scripts/audit_regles.py demo/apres --summary
# violations=0 fichiers=7 langues=python
```
