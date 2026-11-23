# Recettes de correction

Une recette par type de violation. Toujours dans cet ordre : lire le contexte
autour de la ligne, corriger, exécuter la vérification, commiter.

## fonction_trop_longue

1. Identifier les étapes de la fonction, en une phrase chacune.
2. Extraire chaque étape dans une fonction nommée par un verbe explicite.
3. Garder la fonction d'origine comme orchestration courte.
4. Ne pas tricher en supprimant des lignes vides ou des sauts de ligne.

Avant :

```python
def afficher_round(perso, opposant, degats):
    table = Table(title="Round")
    table.add_column("Combattant")
    table.add_column("Dégâts")
    table.add_column("HP")
    for combattant in (perso, opposant):
        table.add_row(...)
    console.print(...)
    if not est_vivant(opposant):
        console.print(...)
```

Après :

```python
def afficher_round(perso, opposant, degats):
    table = construire_table_round(perso, opposant, degats)
    console.print(Panel(table))
    afficher_vaincus(perso, opposant)
```

Commit : `refactor(<portée>): découper <nom> en fonctions dédiées`.

## else_apres_return

1. Supprimer le `else`.
2. Désindenter son contenu d'un niveau.
3. Vérifier que la logique est identique.

Avant :

```python
if condition:
    return True
else:
    return False
```

Après :

```python
if condition:
    return True
return False
```

Commit : `refactor(<portée>): supprimer le else après return dans <nom>`.

## comparaison_enchainee

1. Séparer en deux comparaisons reliées par `and`, ou deux gardes.
2. Ne pas changer la borne ni l'ordre.

Avant :

```python
if 3 <= len(pseudo) <= 40:
```

Après :

```python
if len(pseudo) < 3:
    return False
if len(pseudo) > 40:
    return False
```

Commit : `refactor(<portée>): séparer la comparaison enchaînée dans <nom>`.

## noqa

1. Identifier la règle visée.
2. Réécrire le code pour la satisfaire, ou désactiver la règle dans la
   configuration du linter si elle contredit une consigne explicite.
3. Ne jamais laisser un `noqa`, ne jamais utiliser `--fix --unsafe-fixes` à
   l'aveugle.

Commit : `refactor(<portée>): supprimer la directive noqa dans <nom>`.

## predicat_non_booleen

1. Si la fonction est un prédicat, elle doit renvoyer uniquement des booléens.
2. Si l'appelant a besoin d'un message, sortir le message dans une seconde
   fonction au nom différent (`message_*`, `valider_*`).

Avant :

```python
def equipe_valide(equipe):
    if len(equipe) == TAILLE_EQUIPE:
        return True
    return "Choisis exactement 3 personnages"
```

Après :

```python
def equipe_complete(equipe):
    if len(equipe) != TAILLE_EQUIPE:
        return False
    return True


def valider_equipe(equipe):
    if equipe_complete(equipe):
        return True
    return f"Choisis exactement {TAILLE_EQUIPE} personnages"
```

Commit : `refactor(<portée>): séparer le prédicat et le message dans <nom>`.

## code_commente

1. Vérifier si le code commenté correspond à une version antérieure utile.
2. S'il est mort, supprimer.
3. S'il documente un choix, le transformer en commentaire de « pourquoi ».
4. Ne jamais le laisser en place.

Commit : `refactor(<portée>): supprimer le code commenté`.

## fonction_morte

1. Confirmer l'absence d'appel (recherche du nom dans tout le dépôt, y compris
   les chaînes et les dictionnaires d'actions).
2. Supprimer la fonction, puis les imports devenus inutiles.
3. Vérifier que le point d'entrée fonctionne toujours.

Commit : `refactor(<portée>): supprimer la fonction inutilisée <nom>`.

## cycle_import

1. Identifier le prédicat ou la donnée partagée.
2. Le déplacer dans un module neutre qui ne dépend de rien.
3. Importer ce module des deux côtés.
4. Vérifier qu'il ne reste qu'un seul sens de dépendance.

Commit : `refactor(<portée>): casser le cycle d'import entre <a> et <b>`.

## ligne_trop_longue

1. Couper au bon endroit : arguments sur plusieurs lignes, f-string concaténée,
   commentaire scindé.
2. Ne pas réduire la lisibilité pour gagner une colonne.
3. Ne pas changer la configuration du linter pour faire disparaître l'erreur.

Commit : `style(<portée>): couper les lignes trop longues dans <fichier>`.

## Duplication

1. Repérer les deux occurrences exactes.
2. Extraire une fonction nommée par l'intention, pas par la forme.
3. Remplacer les deux appels.
4. Vérifier que le comportement est identique.

Commit : `refactor(<portée>): mutualiser <intention>`.

## Ordre des fonctions

1. Définir la règle du fichier (plus simple au plus composé, ou ordre du flux).
2. Déplacer les blocs entiers, sans modifier une seule ligne de code.
3. Vérifier que le diff est symétrique (autant d'ajouts que de suppressions).

Commit : `refactor(<portée>): ordonner les fonctions de <fichier>`.
