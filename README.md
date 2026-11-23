# Audit des règles de code

Skill pour agent de code qui audite un dépôt, quel que soit le langage, contre
un jeu de règles de style strictes, puis corrige chaque violation en détail.

- **Mode audit** : analyse seule, rapport classé par règle, aucune modification.
- **Mode correction** : une correction à la fois, un commit par correction, sans
  jamais pousser.
- **Note avant/après** : écrite hors du dépôt, avec les compteurs, le détail, les
  vérifications et les écarts assumés.
- **Questions** : le skill demande au lieu de deviner quand une règle est
  ambiguë, quand une correction changerait le comportement ou quand deux règles
  se contredisent.

## Installation

Copier le dossier `skill/audit-regles-code` dans le dossier de skills de votre
agent :

```bash
cp -r skill/audit-regles-code ~/.config/opencode/skills/
```

Le skill est alors disponible sous le nom `audit-regles-code`.

## Utilisation

Demander simplement :

- « audit des règles sur ce dépôt »
- « corrige les violations de style »
- « passe le repo au propre »
- « applique les consignes du prof »

Ou appeler le skill par son nom.

## Démonstration avant / après

Le dossier `demo/` contient le même fichier dans deux états.

### Avant

Exemple en Python ; les mêmes règles s'appliquent aux autres langages.

[demo/avant/exemple.py](demo/avant/exemple.py)

```python
# def ancienne_version(x):
#     return x * 2


def calculer_total(prix, quantite, remise):
    total = prix * quantite
    total = total - remise
    ...


def prix_valide(prix):
    if prix > 0:
        return True
    else:
        return False


def quantite_valide(quantite):
    if 1 <= quantite <= 10:
        return True
    return False


def ancien_affichage(total):
    texte = f"Total : {total}"  # noqa: F841
    return texte
```

Rapport complet : [demo/rapport-avant.md](demo/rapport-avant.md)

```
fonction_trop_longue    1
else_apres_return       1
comparaison_enchainee   1
suppression_linter      1
fonction_morte          2
code_commente           2
```

### Après

[demo/apres/exemple.py](demo/apres/exemple.py)

```python
def calculer_total(prix, quantite, remise):
    total = round(prix * quantite - remise + 3.5, 2)
    if total < 0:
        return 0
    return total * 1.2 + 2


def prix_valide(prix):
    if prix <= 0:
        return False
    return True


def quantite_valide(quantite):
    if quantite < 1:
        return False
    if quantite > 10:
        return False
    return True


def formater_total(total):
    return f"Total : {total}"
```

Rapport complet : [demo/rapport-apres.md](demo/rapport-apres.md)

```
Aucune violation détectée.
```

### Ce qui a changé

| Règle | Avant | Après |
|---|---|---|
| Longueur | `calculer_total` faisait 11 lignes utiles | 5 lignes utiles |
| `else` après `return` | `prix_valide` | retour direct |
| Comparaison enchaînée | `1 <= quantite <= 10` | deux gardes séparées |
| `# noqa` | `ancien_affichage` | supprimé |
| Code commenté | `ancienne_version` | supprimé |
| Fonction morte | `calculer_total`, `ancien_affichage` | toutes appelées |

## Langages pris en charge

| Langage | Analyse |
|---|---|
| Python | AST, précise |
| JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, PHP, Swift, Kotlin, Scala, Shell | blocs par accolades, heuristique |
| Ruby, Lua | blocs `end`, heuristique |

Les règles structurelles (nommage, ordre, duplication, commentaires) se vérifient
à la lecture pour tous les langages. Les linters du projet complètent : ruff,
eslint, gofmt, cargo clippy, rubocop, php-cs-fixer, ktlint, swiftlint, shellcheck.

## Règles couvertes

1. Prédicats en gardes successives, un `if` par règle, `return True` à la fin.
2. Absence d'invalidation, pas de validation imbriquée.
3. Pas de `else` après un `return`.
4. Pas de `# noqa`.
5. Pas de comparaisons enchaînées.
6. Une fonction se décrit en une phrase sans « et ».
7. Dix lignes utiles maximum par fonction.
8. Nommage `afficher_`, `demander_`, `*_valide`, pas de valeur en dur.
9. Réutilisation dès qu'un motif apparaît deux fois.
10. Ordre des fonctions cohérent dans chaque fichier.
11. Un fichier, une responsabilité, aucun cycle d'import.
12. Commentaires qui disent pourquoi, jamais de code commenté.
13. Pas de code mort.
14. Style et outillage du projet au vert.
15. Tests et vérifications après chaque correction.
16. Commits conventionnels, un commit par correction, jamais de push.

## Structure

```
.
├── README.md
├── demo/
│   ├── avant/exemple.py
│   ├── apres/exemple.py
│   ├── rapport-avant.md
│   └── rapport-apres.md
└── skill/
    └── audit-regles-code/
        ├── SKILL.md
        ├── scripts/audit_regles.py
        └── references/
            ├── regles.md
            └── corrections.md
```

## Limites

- Python est le seul langage analysé par AST. Ailleurs, la longueur des fonctions
  est estimée par comptage d'accolades ou de `end`, et marquée « heuristique à
  vérifier ».
- `fonction_morte` n'est détectée qu'en Python.
- `code_commente` et `fonction_morte` sont des détections heuristiques, marquées
  « à vérifier » : une fonction peut être appelée par une chaîne ou un callback.
- Les corrections qui changent le comportement ne sont jamais appliquées sans
  validation humaine.
