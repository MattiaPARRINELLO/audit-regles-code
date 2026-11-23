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
- **Configuration** : `.audit-regles.json` par dépôt.
- **Baseline** : geler les violations existantes, ne signaler que les nouvelles.
- **CI** : `--check` pour le code de sortie, `--format sarif` pour GitHub.
- **Issues** : en mode audit, issue de synthèse et une sous-issue par règle,
  après confirmation.

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

## Configuration

Créer `.audit-regles.json` à la racine du dépôt audité :

```json
{
  "max_lignes": 10,
  "max_colonnes": 79,
  "langues": ["python", "javascript"],
  "exclure": ["demo/avant", "migrations"],
  "regles_desactivees": ["duplication"],
  "srp": true,
  "duplication": { "seuil_lignes": 4, "min_occurrences": 2 },
  "ordre": false
}
```

Priorité : valeurs par défaut, puis ce fichier, puis les options de la ligne de
commande.

## Compter sans se tromper

Un rapport long peut être tronqué à l'affichage, et un total lu à l'œil est
souvent faux. Le compte officiel tient en une ligne :

```bash
audit-regles . --summary
# violations=18 fichiers=2 langues=python
```

Le JSON (`--format json`) reste la source de vérité pour un traitement
automatique.

## Baseline et CI

Geler l'existant, puis bloquer seulement les nouvelles violations :

```bash
audit-regles . --ecrire-baseline .audit-baseline.json
audit-regles . --baseline .audit-baseline.json --check
```

`--check` renvoie 1 s'il reste une violation non gelée. Sortie SARIF pour
GitHub :

```bash
audit-regles . --format sarif --sortie audit.sarif --check
```

## Mode audit et issues

Après un audit, le skill propose d'ouvrir une issue GitHub : une synthèse avec le
tableau des règles, puis une sous-issue par règle rattachée à la synthèse. Rien
n'est créé sans confirmation, et jamais dans un dépôt qui n'est pas le remote du
dossier.

## Tests

```bash
python -m pytest -q tests
```

La suite couvre Python, JavaScript, Go et Ruby, la configuration, la baseline,
le code de sortie, SARIF, l'heuristique SRP, la duplication et l'ordre des
fonctions.

## Démonstration avant / après

Un petit programme de facturation sur deux fichiers, `facture.py` et `main.py`,
volontairement illisible, puis le même comportement en lisible. Les deux
versions affichent exactement la même chose.

### Avant

[demo/avant/facture.py](demo/avant/facture.py)

```python
def calculer(d, q, p, r, t):
    if d != None:
        if q > 0:
            if p > 0:
                x = p*q
                x = x - (x*r/100)
                if t == True:
                    x = x*1.2
                x = x + 5
                if x > 100:
                    x = x - 10
                return round(x, 2)
            else:
                return 0
        else:
            return 0
    else:
        return 0
```

Rapport complet : [demo/rapport-avant.md](demo/rapport-avant.md)

```
fonction_trop_longue     1
else_apres_return        3
comparaison_enchainee    1
suppression_linter       1
nommage_afficher         1
responsabilite_multiple  1
fonction_morte           4
duplication              2
code_commente            2
ligne_trop_longue        2
```

18 violations sur 2 fichiers.

### Après

[demo/apres/facture.py](demo/apres/facture.py)

```python
TVA = 1.2
FRAIS_FIXES = 5
SEUIL_REMISE = 100
REMISE_GRANDE_COMMANDE = 10


def calculer_total(prix, quantite, remise):
    if not quantite_valide(quantite):
        return 0
    if not prix_valide(prix):
        return 0
    total = calculer_brut(prix, quantite, remise)
    total = appliquer_tva(total)
    total = appliquer_frais(total)
    return round(total, 2)
```

Rapport complet : [demo/rapport-apres.md](demo/rapport-apres.md)

```
Aucune violation détectée.
```

### Ce qui a changé

| Règle | Avant | Après |
|---|---|---|
| Responsabilité | `calculer` valide, calcule et renvoie | `calculer_total` appelle cinq fonctions nommées |
| Validation imbriquée | trois `else` après `return` | gardes successives |
| Comparaison enchaînée | `1 <= q <= 99` | deux gardes séparées |
| Directive de suppression | `# noqa` | une constante et un paramètre nommés |
| Nommage | `f`, `x`, `t`, `d` | `calculer_total`, `total`, `designation` |
| Fonction d'affichage qui renvoie | `afficher_facture` | affichage sans valeur de retour |
| Constantes magiques | `1.2`, `5`, `100`, `10` | `TVA`, `FRAIS_FIXES`, `SEUIL_REMISE`, `REMISE_GRANDE_COMMANDE` |
| Fonctions mortes | 4 | toutes utilisées |
| Duplication | deux fonctions identiques | une seule fonction |
| Code commenté | `ancien_total` | supprimé |
| Lignes longues | deux lignes de 105 colonnes | f-string découpée |

Les deux versions produisent :

```
Chaise x2 a 49.9 euros et un texte beaucoup trop long pour la limite de colonnes
Article : Chaise
Total : 102.78
102.78
```

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
├── pyproject.toml
├── .github/workflows/ci.yml
├── tests/test_audit.py
├── demo/
│   ├── avant/
│   │   ├── facture.py
│   │   └── main.py
│   ├── apres/
│   │   ├── facture.py
│   │   └── main.py
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

## Auto-audit du dépôt

`demo/avant` est volontairement non conforme, c'est le sujet de la démonstration.
Pour auditer le reste :

```bash
python3 skill/audit-regles-code/scripts/audit_regles.py skill
python3 skill/audit-regles-code/scripts/audit_regles.py demo/apres
```

## Limites

- Python est le seul langage analysé par AST. Ailleurs, la longueur des fonctions
  est estimée par comptage d'accolades ou de `end`, et marquée « heuristique à
  vérifier ».
- `fonction_morte` n'est détectée qu'en Python.
- `code_commente`, `fonction_morte`, `responsabilite_multiple`, `duplication` et
  `ordre_fonctions` sont des détections heuristiques, marquées « à vérifier » :
  une fonction peut être appelée par une chaîne ou un callback, et une
  duplication peut être volontaire.
- Le script d'analyse est un outil de diagnostic : ses propres fonctions
  dépassent la limite de 10 lignes, car il privilégie la lisibilité de l'analyse.
  Les règles de taille visent le code applicatif, pas l'outillage.
- Les corrections qui changent le comportement ne sont jamais appliquées sans
  validation humaine.
