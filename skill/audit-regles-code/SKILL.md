---
name: audit-regles-code
description: Audite tout le code d'un dépôt, quel que soit le langage, contre des règles de style strictes (prédicats en gardes successives, pas de else après return, pas de directives de suppression, pas de comparaisons enchaînées, 10 lignes utiles maximum par fonction, nommage explicite, réutilisation, ordre des fonctions, modules sans cycle d'import, commentaires qui disent pourquoi), puis corrige chaque violation en détail, avec un commit par correction et une note avant/après écrite hors du dépôt. Python est analysé par AST, les autres langages par heuristiques et linters locaux. Deux modes, audit seul et correction. Utiliser quand l'utilisateur dit « vérifie que le code respecte les règles », « audit des règles », « corrige les violations de style », « passe le repo au propre », « applique les consignes du prof », ou lance /audit-regles-code. Use when the user asks to audit or fix strict code style rules in a repository, in any language.
---

# Audit des règles de code

Ce skill lit l'intégralité d'un dépôt, compare chaque fichier de code à un jeu
de règles strictes, corrige les écarts un par un, et documente le avant/après.

Python est analysé par AST, donc avec précision. Les autres langages sont
analysés par heuristiques (longueur des blocs, lignes, directives de
suppression, code commenté) et par les linters locaux. Les règles qui ne se
mesurent pas automatiquement (nommage, ordre, duplication, commentaires) sont
vérifiées en lisant le code.

## Ce qu'il fait

- Mode **audit** : analyse seule, rapport, aucune modification.
- Mode **correction** : analyse, corrections appliquées une par une, un commit
  par correction, note avant/après.
- **Configuration par dépôt** : un fichier `.audit-regles.json` fixe la largeur,
  la taille maximale, les exclusions, les règles désactivées et les seuils.
- **Baseline** : geler les violations existantes pour ne signaler que les
  nouvelles.
- **Intégration continue** : `--check` renvoie 1 si des violations restent, et
  `--format sarif` s'importe dans GitHub.
- **Issues** : en mode audit, il peut ouvrir une issue de synthèse et une
  sous-issue par règle, après confirmation.
- Dans les deux modes, il pose des questions quand une règle est ambiguë ou
  qu'une correction changerait le comportement.

## Important

- Ne jamais inventer une violation pour remplir le rapport. Une violation doit
  être citée avec fichier, ligne et règle.
- Ne jamais compter les violations à l'œil sur une sortie affichée : les longs
  rapports sont souvent tronqués en haut. Le nombre officiel vient de
  `--summary` ou du JSON, jamais d'une lecture partielle.
- Ne jamais modifier un test pour le faire passer.
- Ne jamais changer le comportement du programme pendant une correction de
  style. Si la correction implique un changement de comportement, poser la
  question et attendre.
- Ne jamais pousser (`git push`), ni réécrire l'historique.
- Ne jamais reformater un fichier entier : les diffs restent localisés.
- Ne jamais toucher aux dépendances, sauf si l'utilisateur le demande.

## Étape 0 : cadrer avec des questions

Utiliser l'outil de question s'il existe, sinon poser les questions en texte et
attendre les réponses. Trois questions au maximum, avec une option recommandée :

1. **Mode** : audit seul, ou correction avec commits.
2. **Périmètre** : tout le dépôt, ou un dossier précis.
3. **Exceptions** : des règles à ignorer pour cette passe, ou des fichiers
   générés à exclure.

Si le mode est correction, confirmer une fois : « j'applique les corrections et
je fais un commit par correction, sans push ». Ne pas recommencer à demander à
chaque fichier.

## Étape 1 : inventaire du dépôt

1. Détecter les langages présents (extensions de fichiers) et les lister. Le
   script couvre Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust,
   Ruby, PHP, Swift, Kotlin, Scala, Shell et Lua.
2. Repérer la configuration existante : `pyproject.toml`, `ruff.toml`,
   `eslint.config.js`, `.eslintrc`, `tsconfig.json`, `go.mod`, `Cargo.toml`,
   `Gemfile`, `composer.json`, `package.json`.
3. Lire `AGENTS.md`, `CONTRIBUTING.md` et tout fichier de consignes présent :
   elles priment sur les règles génériques.
4. Lire `references/regles.md` pour la liste complète.
5. Compter les fichiers et les fonctions pour dimensionner le travail.

## Configuration du dépôt

Créer `.audit-regles.json` à la racine si le dépôt a des besoins propres. Le
script le lit automatiquement.

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
commande. Ne pas créer ce fichier sans demander si le dépôt n'en a pas : c'est
une décision de projet.

## Étape 2 : audit automatique

Le script du skill fait les détections déterministes. Le dossier du skill est
fourni avec le skill ; utiliser son chemin absolu.

```bash
python3 "<dossier-du-skill>/scripts/audit_regles.py" <racine> \
  --max-lignes 10 --max-colonnes 79 \
  --sortie /tmp/audit-regles-<repo>-<AAAAMMJJ-HHMM>.md
```

Puis, pour un rapport lisible directement :

```bash
python3 "<dossier-du-skill>/scripts/audit_regles.py" <racine> --format md
```

Le compte officiel, à utiliser dans la note, se lit ainsi et jamais autrement :

```bash
python3 "<dossier-du-skill>/scripts/audit_regles.py" <racine> --summary
# violations=18 fichiers=2 langues=python
```

ou en JSON, qui reste la source de vérité :

```bash
python3 "<dossier-du-skill>/scripts/audit_regles.py" <racine> \
  --format json --sortie /tmp/audit.json
python3 -c "import json; print(len(json.load(open('/tmp/audit.json'))['violations']))"
```

Le script détecte : fonction trop longue, `else` après `return`, comparaison
enchaînée, directive de suppression, code commenté, prédicat non booléen,
fonction morte, cycle d'import, ligne trop longue, erreur de syntaxe.

En Python, l'analyse est exacte. Ailleurs, `fonction_trop_longue` est
heuristique (comptage d'accolades ou de `end`) et porte la mention « à
vérifier » : confirmer en lisant le bloc avant de corriger.

Compléter avec l'outillage du projet. Selon les langages détectés :

| Langage | Outils |
|---|---|
| Python | `ruff check .`, `python3 -m pycodestyle .`, `pyright .` |
| JavaScript, TypeScript | `npx eslint .`, `npx tsc --noEmit`, `npx prettier --check .` |
| Go | `gofmt -l .`, `go vet ./...`, `golangci-lint run` |
| Rust | `cargo fmt --check`, `cargo clippy` |
| Ruby | `rubocop` |
| PHP | `php-cs-fixer fix --dry-run --diff`, `phpstan analyse` |
| Java, Kotlin | `./gradlew check`, `ktlint` |
| C#, .NET | `dotnet format --verify-no-changes` |
| Swift | `swiftlint` |
| Shell | `shellcheck` |

Ne lancer que les outils réellement installés et configurés par le projet.

## Baseline et intégration continue

Sur un dépôt existant, geler l'état avant de corriger.

```bash
python3 "<dossier-du-skill>/scripts/audit_regles.py" . \
  --ecrire-baseline .audit-baseline.json

python3 "<dossier-du-skill>/scripts/audit_regles.py" . \
  --baseline .audit-baseline.json --check
```

La baseline compare des empreintes (règle, fichier, détail), pas les numéros de
ligne, donc elle résiste aux décalages. `--check` renvoie 1 s'il reste une
violation non gelée.

Pour GitHub :

```bash
python3 "<dossier-du-skill>/scripts/audit_regles.py" . \
  --format sarif --sortie audit.sarif --check
```

Puis l'upload avec `github/codeql-action/upload-sarif`. Ne pas activer `--check`
sur un dépôt sans baseline : la CI échouerait dès le premier commit.

Enfin, ouvrir les fichiers signalés et lire le contexte autour de chaque ligne.
Le script signale des candidats, pas des verdicts : `fonction_morte` et
`code_commente` portent la mention « à vérifier », il faut confirmer avant de
corriger.

## Étape 3 : noter l'état AVANT

Écrire la note hors du dépôt, jamais dedans. Chemin :
`/tmp/audit-regles-<repo>-<AAAAMMJJ-HHMM>.md`, ou `$TMPDIR` si `/tmp` n'existe
pas.

Format attendu :

```markdown
# Audit des règles, avant correction

- Dépôt : <chemin>
- Date : <date>
- Commit de départ : <sha court>
- Fichiers analysés : <n>
- Violations : <n, lu avec --summary ou le JSON>
- Note : ce nombre est mesuré avant toute modification, pas après une première passe

## Violations par règle

| Règle | Nombre | Gravité |
|---|---|---|
| ... | ... | ... |

## Détail

- `<fichier>:<ligne>` règle, description courte, décision prévue

## Vérifications de départ

- linters du projet : <état>
- tests : <état>
```

Si le mode est audit seul, s'arrêter ici, présenter la note et le tableau.

## Étape 4 : corriger

Ordre de traitement, du plus grave au plus cosmétique :

1. Erreurs de syntaxe et imports cassés.
2. Cycles d'import et fonctions mortes.
3. Fonctions trop longues, prédicats non booléens, `else` après `return`.
4. Comparaisons enchaînées, directives de suppression.
5. Nommage, duplication, ordre des fonctions.
6. Lignes trop longues, code commenté, commentaires.

Pour chaque violation, suivre la recette correspondante dans
`references/corrections.md`.

Après chaque correction :

1. Relancer le linter du projet.
2. Relancer les tests, ou le point d'entrée avec un scénario court.
3. Vérifier que le diff ne touche que la violation visée.
4. Commiter, un commit par correction :

```bash
git add <fichiers>
git commit -m "refactor(<portée>): <description à l'impératif>"
```

Types autorisés : `refactor`, `style`, `fix`, `chore`, `docs`, `test`.

Si une correction échoue ou casse un test, annuler la modification
(`git restore <fichier>`), la signaler dans la note, et demander à
l'utilisateur au lieu d'insister.

## Étape 5 : noter l'état APRÈS

Mettre à jour le même fichier de note avec une section finale :

```markdown
# Après correction

- Violations restantes : <n>
- Commits créés : <sha court> <sujet>

## Avant / après

| Règle | Avant | Après |
|---|---|---|
| ... | ... | ... |

## Vérifications finales

- linters du projet : <état>
- tests : <état>

## Écarts assumés

- <fichier:ligne> : <pourquoi la règle n'a pas été appliquée>
```

## Étape 6 : rendre compte

Répondre avec :

- le chemin de la note ;
- le tableau avant/après ;
- la liste des commits ;
- les points laissés en suspens et la raison ;
- une question si un choix reste à trancher.

## Mode audit : ouvrir une issue

Ne jamais créer d'issue sans confirmation explicite. Demander avec trois
options : aucune, une issue de synthèse, une issue de synthèse plus une
sous-issue par règle.

Avant de créer :

```bash
gh auth status
gh repo view --json nameWithOwner -q .nameWithOwner
```

Si `gh` est absent ou non authentifié, le dire et fournir le corps de l'issue à
coller manuellement.

### Issue de synthèse

Titre : `Audit des règles : <n> violations`.

Corps : tableau règle / nombre / gravité, liste des fichiers concernés, lien
vers la note avant/après, et mention des sous-issues.

```bash
gh issue create --title "..." --body-file /tmp/issue-audit.md
```

### Sous-issues

Une par règle, titre `Audit : <règle> (<n>)`, corps avec les `fichier:ligne` et
le rappel de la recette dans `references/corrections.md`.

```bash
gh issue create --title "..." --body-file /tmp/issue-<regle>.md
gh issue view <numero> --json id -q .id
```

Puis rattacher à l'issue parente :

```bash
gh api -X POST repos/<owner>/<repo>/issues/<parent>/sub_issues \
  -F sub_issue_id=<id>
```

Si l'API répond 404 ou 422 (fonctionnalité indisponible), ajouter dans l'issue
parente une liste de tâches avec les liens des issues créées, au lieu
d'insister.

### Règles à respecter

- Ne jamais créer d'issue dans un dépôt qui n'est pas le remote du dossier.
- Ne jamais créer d'issue si le dépôt est privé sans confirmation explicite.
- Ne jamais modifier le code en mode audit.
- Ne jamais fermer, assigner ou étiqueter une issue sans demande.

## Questions à poser en cours de route

Poser une question, sans continuer, dans ces cas :

- **Règle ambiguë** : deux corrections possibles, ou la règle du cadre
  contredit la configuration du linter. Exemple : `SIM103` contre les gardes
  imposées.
- **Changement de comportement** : la correction modifie un résultat, un message
  ou un ordre d'affichage.
- **Conflit entre deux règles** : par exemple « une seule fonction partagée »
  contre « pas de branchement dans une fonction ».
- **Fichier généré** : migration, fichier vendu, code tiers. Proposer de
  l'exclure.
- **Fonction morte suspecte** : peut servir de point d'entrée, de callback ou
  être appelée par une chaîne.

Formuler la question avec les options concrètes, pas une question ouverte.

## Dépannage

- **Le script ne trouve rien alors que le linter râle** : le linter a des règles
  non couvertes (imports, types). Traiter ces erreurs à part et le dire.
- **Trop de violations** : proposer de commencer par un dossier, ou par les
  règles de gravité haute, et le noter.
- **Faux positif de fonction morte** : vérifier les références par chaîne, les
  entrées `if __name__ == "__main__"` et les dictionnaires d'actions.
- **Dépôt sans linter** : compiler ou vérifier la syntaxe avec l'outil du
  langage (`python3 -m py_compile`, `node --check`, `go build`, `cargo check`),
  puis exécuter le point d'entrée.
- **Dépôt sans tests** : construire un scénario court (entrées, sortie
  attendue) et le documenter dans la note.
- **Langage non couvert** : le script ignore l'extension. Appliquer les règles
  à la lecture et utiliser le linter du langage. Le signaler dans la note.

## Fichiers du skill

- `scripts/audit_regles.py` : détection multi-langage, sortie Markdown ou JSON.
- `references/regles.md` : les 16 règles, avec exemples et méthode de détection.
- `references/corrections.md` : une recette par type de violation, avec avant,
  après et message de commit.
