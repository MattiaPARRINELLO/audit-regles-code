# Règles de code à faire respecter

Ces règles viennent d'un cadre pédagogique strict. Elles s'appliquent à tout
fichier de code du dépôt audité, quel que soit le langage. Chaque règle indique
comment la détecter et ce qui compte comme violation.

## 1. Prédicats en gardes successives

Un prédicat nommé `*_valide`, `est_*`, `tous_*`, `*_complete` s'écrit avec une
garde par règle : chaque `if` teste une seule condition et renvoie `False`, et
la fonction finit par `return True`.

```python
def pseudo_valide(pseudo):
    if len(pseudo) > 40:
        return False
    if len(pseudo) < 3:
        return False
    return True
```

Violation : un `and` qui regroupe plusieurs règles dans le dernier `return`,
une expression booléenne condensée, ou un `else` après un `return`.

## 2. Absence d'invalidation

On teste d'abord le cas invalide et on sort. Pas de validation imbriquée dans
un `else`, pas de `if` dans un `if` quand une garde suffit.

## 3. Pas de `else` après un `return`

Dès qu'un `if` renvoie, le `else` est inutile : on désindente la suite.

```python
if condition:
    return valeur
return autre_valeur
```

Détection : `scripts/audit_regles.py`, règle `else_apres_return`.

## 4. Pas de directives de suppression

Aucune directive qui fait taire un linter. Selon l'écosystème :

| Langage | À refuser |
|---|---|
| Python | `# noqa`, `# type: ignore`, `# pylint: disable` |
| JavaScript, TypeScript | `// eslint-disable`, `// @ts-ignore`, `// @ts-expect-error` |
| Go | `//nolint` |
| Ruby | `# rubocop:disable` |
| Swift | `// swiftlint:disable` |
| Tout langage | `// prettier-ignore` |

Quand une règle de linter contredit le style imposé, on désactive la règle dans
la configuration du linter, pas ligne par ligne.

Détection : règle `suppression_linter`.

## 5. Pas de comparaisons enchaînées

`3 <= len(x) <= 40` est interdit, même quand c'est correct en Python. On écrit
deux conditions séparées, ou deux gardes.

Détection : règle `comparaison_enchainee`.

## 6. Une fonction se décrit en une phrase sans « et »

Chaque fonction doit avoir une seule responsabilité. Si la description a besoin
d'un « et », il faut découper.

Violation typique : une fonction qui valide, affiche et enregistre.

## 7. Dix lignes utiles maximum

Le corps d'une fonction ne dépasse pas 10 lignes utiles, hors signature, lignes
vides et commentaires. Au-delà, on extrait des étapes nommées.

Détection : règle `fonction_trop_longue`.

## 8. Nommage

| Préfixe ou suffixe | Signification |
|---|---|
| `afficher_` | affiche, ne renvoie rien d'utile |
| `demander_` | obtient une saisie déjà valide |
| `*_valide` | prédicat qui renvoie un booléen |
| `compter_`, `tirer_`, `creer_`, `copier_`, `calculer_` | action explicite |

Ce tableau vient d'un cadre francophone. Dans un autre dépôt, appliquer les
conventions équivalentes du projet (verbe à l'infinitif, préfixe métier,
prédicat nommé `is_` ou `has_`).

Règles associées :

- Pas de valeur en dur quand une constante existe.
- Noms en français, explicites, sans abréviation.
- Une fonction qui renvoie autre chose qu'un booléen ne s'appelle pas `*_valide`.

Détection : règle `predicat_non_booleen` pour le dernier point, relecture pour le
reste.

## 9. Réutilisation

Dès qu'un motif apparaît deux fois, on l'extrait : copie d'objet, construction
d'un prompt, message répété, formatage commun.

Violation : deux blocs identiques à quelques mots près, ou une constante
dupliquée en chaîne de caractères.

## 10. Ordre des fonctions

- Fichiers de logique : du plus simple au plus composé. Les briques en haut, les
  fonctions qui les assemblent en bas.
- Fichier d'orchestration : dans l'ordre du déroulement (entrée en haut).

Violation : une fonction utilitaire définie après celle qui l'appelle, ou des
thèmes mélangés (affichage entrecoupé de logique).

## 11. Architecture

- Un fichier, une responsabilité.
- Aucun cycle d'import.
- Les données statiques sont séparées du code.
- La couche d'accès aux données n'affiche rien et renvoie des données.
- Seul le module de base de données importe le client de base de données.
- Le menu est piloté par un dictionnaire, pas par une chaîne de `if`.

Détection : règle `cycle_import` et relecture.

## 12. Commentaires

- Un commentaire dit **pourquoi**, jamais **quoi**.
- Pas de commentaire qui paraphrase la ligne suivante.
- Pas de code commenté.
- Peu de commentaires, uniquement sur la logique non évidente.

Détection : règle `code_commente`, relecture pour le reste.

## 13. Pas de code mort

Aucune fonction sans appelant, aucun bloc inutilisé, aucun import orphelin.

Détection : règle `fonction_morte` et les linters du projet.

## 14. Style et outillage

- Largeur de ligne alignée sur la configuration du projet (79 colonnes dans les
  projets de ce cadre, souvent 80, 100 ou 120 ailleurs).
- Aucun `print` de débogage oublié.
- Les linters et le vérificateur de types du projet doivent passer sans erreur
  avant chaque commit.
- Aucun tiret cadratin (U+2014) dans le code, les commentaires ou les messages
  de commit.

## 15. Tests et vérifications

- Une correction n'est jamais validée sans exécuter les linters du projet.
- Si le projet a des tests, ils doivent passer après chaque correction.
- Si le projet n'a pas de tests, exécuter le point d'entrée et vérifier un
  scénario manuel ou un script de simulation.
- Ne jamais modifier un test pour le faire passer.

## 16. Git

- Conventional Commits, sujet à l'impératif, en français pour ce cadre.
- Un commit par correction, jamais un commit fourre-tout.
- Jamais de `git push` sans accord explicite.
- Jamais de `git reset --hard`, `git clean -fd` ni de réécriture d'historique
  sans confirmation.

## 17. Détection par langage

| Langage | Méthode du script | Fiabilité |
|---|---|---|
| Python | AST | exacte |
| JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, PHP, Swift, Kotlin, Scala, Shell | accolades | heuristique |
| Ruby, Lua | blocs `end` | heuristique |

Les règles qui ne se mesurent pas automatiquement (nommage, ordre des fonctions,
duplication, qualité des commentaires, responsabilité unique) se vérifient à la
lecture du code, pas par le script. Une violation heuristique se confirme avant
d'être corrigée.
