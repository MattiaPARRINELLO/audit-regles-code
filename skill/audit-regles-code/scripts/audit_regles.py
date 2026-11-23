#!/usr/bin/env python3
"""Audit multi-langage d'un dépôt contre les règles de style du projet.

Python est analysé par AST (précis). Les autres langages sont analysés par
heuristiques : longueur des blocs, lignes trop longues, directives de
suppression, code commenté. Les règles structurelles non mesurables (nommage,
ordre, duplication, commentaires) restent à la lecture de l'agent.

Sortie : Markdown sur stdout, ou fichier avec --sortie, ou JSON avec
--format json.
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

EXCLUS_PAR_DEFAUT = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "build",
    "dist",
    ".tox",
    "site-packages",
    "target",
    "vendor",
    ".next",
    "coverage",
}

LANGAGES = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".lua": "lua",
}

REGEX_NOQA = re.compile(r"#\s*noqa")
REGEX_SUPPRESSION = re.compile(
    r"(#\s*noqa|#\s*type:\s*ignore|#\s*pylint:\s*disable|"
    r"#\s*rubocop:disable|//\s*eslint-disable|/\*\s*eslint-disable|"
    r"//\s*@ts-ignore|//\s*@ts-expect-error|//\s*nolint|"
    r"//\s*swiftlint:disable|//\s*prettier-ignore)"
)
REGEX_CODE_COMMENTE = re.compile(
    r"^\s*(?:#|//|/\*+|\*)\s*"
    r"(def |class |return |if |elif |else|for |while |import |from |"
    r"function |const |let |var |public |private |protected |static |"
    r"print\(|console\.|[A-Za-z_$][\w$]*\s*[=:(])"
)
REGEX_DEBUT_FONCTION = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:public\s+|private\s+|protected\s+|"
    r"static\s+|async\s+|final\s+|override\s+|func\s+|fn\s+|function\s+|"
    r"def\s+)*"
    r"(?P<nom>[A-Za-z_$][\w$]*)\s*\([^;]*\)\s*(?:[:\-][^{;]*)?\{?\s*$"
)
MOTS_CLES = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "else",
    "do",
    "try",
    "with",
    "sizeof",
    "typeof",
    "new",
    "delete",
    "throw",
}


def fichiers(racine, exclusions, langues):
    for chemin in sorted(racine.rglob("*")):
        if not chemin.is_file():
            continue
        if set(chemin.parts) & exclusions:
            continue
        langue = LANGAGES.get(chemin.suffix.lower())
        if langue is None:
            continue
        if langues and langue not in langues:
            continue
        yield chemin, langue


def lignes_utiles(lignes, debut, fin):
    """Lignes du corps hors signature, lignes vides et commentaires seuls."""
    corps = lignes[debut:fin]
    retenues = []
    for ligne in corps:
        nue = ligne.strip()
        if not nue:
            continue
        if nue.startswith(("#", "//", "/*", "*")):
            continue
        retenues.append(ligne)
    return retenues


def est_bool(node):
    if isinstance(node, ast.Constant):
        return isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, (ast.Compare, ast.BoolOp, ast.Call)):
        return True
    return False


def analyser_python(chemin, relatif, max_lignes, max_colonnes):
    violations = []
    texte = chemin.read_text(encoding="utf-8", errors="replace")
    lignes = texte.splitlines()
    try:
        tree = ast.parse(texte)
    except SyntaxError as erreur:
        return [
            {
                "regle": "syntaxe",
                "fichier": relatif,
                "ligne": erreur.lineno or 0,
                "langue": "python",
                "detail": f"fichier non analysable : {erreur.msg}",
            }
        ], None

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            utiles = lignes_utiles(lignes, node.lineno, node.end_lineno)
            if len(utiles) > max_lignes:
                violations.append(
                    {
                        "regle": "fonction_trop_longue",
                        "fichier": relatif,
                        "ligne": node.lineno,
                        "langue": "python",
                        "detail": (
                            f"{node.name} : {len(utiles)} lignes utiles "
                            f"(max {max_lignes})"
                        ),
                    }
                )
            if node.name.endswith("_valide"):
                for sous in ast.walk(node):
                    if isinstance(sous, ast.Return) and sous.value is not None:
                        if not est_bool(sous.value):
                            violations.append(
                                {
                                    "regle": "predicat_non_booleen",
                                    "fichier": relatif,
                                    "ligne": sous.lineno,
                                    "langue": "python",
                                    "detail": (
                                        f"{node.name} renvoie une valeur "
                                        "non booléenne"
                                    ),
                                }
                            )
                            break
        if isinstance(node, ast.If) and node.orelse:
            if node.body and isinstance(node.body[-1], ast.Return):
                violations.append(
                    {
                        "regle": "else_apres_return",
                        "fichier": relatif,
                        "ligne": node.lineno,
                        "langue": "python",
                        "detail": "else inutile après un return",
                    }
                )
        if isinstance(node, ast.Compare) and len(node.ops) > 1:
            violations.append(
                {
                    "regle": "comparaison_enchainee",
                    "fichier": relatif,
                    "ligne": node.lineno,
                    "langue": "python",
                    "detail": "comparaison enchaînée",
                }
            )
    return violations, tree


def retirer_chaines_et_commentaires(ligne):
    resultat = []
    guillemet = None
    i = 0
    while i < len(ligne):
        caractere = ligne[i]
        if guillemet:
            if caractere == guillemet and ligne[i - 1] != "\\":
                guillemet = None
            continue
        if caractere in "\"'`":
            guillemet = caractere
            continue
        if ligne[i : i + 2] in ("//", "/*"):
            break
        resultat.append(caractere)
        i += 1
    return "".join(resultat)


def blocs_non_python(lignes):
    blocs = []
    i = 0
    while i < len(lignes):
        correspondance = REGEX_DEBUT_FONCTION.match(lignes[i])
        if not correspondance or correspondance.group("nom") in MOTS_CLES:
            i += 1
            continue
        j = i
        while j < len(lignes) and "{" not in lignes[j]:
            if ";" in lignes[j]:
                break
            j += 1
        if j >= len(lignes) or "{" not in lignes[j]:
            i += 1
            continue
        profondeur = 0
        ouvert = False
        k = j
        while k < len(lignes):
            code = retirer_chaines_et_commentaires(lignes[k])
            if "{" in code:
                ouvert = True
            profondeur += code.count("{") - code.count("}")
            if ouvert and profondeur <= 0:
                break
            k += 1
        blocs.append((correspondance.group("nom"), i + 1, k + 1))
        i = k + 1
    return blocs


def blocs_end(lignes):
    """Blocs délimités par end (Ruby, Lua), par heuristique d'imbrication."""
    ouvertures = re.compile(
        r"^\s*(def|if|unless|while|until|for|case|begin|class|module|do|"
        r"function)\b"
    )
    blocs = []
    i = 0
    while i < len(lignes):
        correspondance = re.match(
            r"^\s*def\s+(?P<nom>[A-Za-z_]\w*[?!]?)", lignes[i]
        )
        if not correspondance:
            i += 1
            continue
        profondeur = 0
        k = i
        while k < len(lignes):
            code = retirer_chaines_et_commentaires(lignes[k])
            if ouvertures.match(code):
                profondeur += 1
            profondeur -= len(re.findall(r"\bend\b", code))
            if profondeur <= 0 and k > i:
                break
            k += 1
        blocs.append((correspondance.group("nom"), i + 1, k + 1))
        i = k + 1
    return blocs


def analyser_autre(chemin, relatif, langue, max_lignes, max_colonnes):
    violations = []
    lignes = chemin.read_text(encoding="utf-8", errors="replace").splitlines()
    if langue in ("ruby", "lua"):
        blocs = blocs_end(lignes)
    else:
        blocs = blocs_non_python(lignes)
    for nom, debut, fin in blocs:
        utiles = lignes_utiles(lignes, debut, fin)
        if len(utiles) > max_lignes:
            violations.append(
                {
                    "regle": "fonction_trop_longue",
                    "fichier": relatif,
                    "ligne": debut,
                    "langue": langue,
                    "detail": (
                        f"{nom} : {len(utiles)} lignes utiles "
                        f"(max {max_lignes}, heuristique à vérifier)"
                    ),
                }
            )
    return violations


def analyser_lignes(chemin, relatif, langue, max_colonnes):
    violations = []
    lignes = chemin.read_text(encoding="utf-8", errors="replace").splitlines()
    for numero, ligne in enumerate(lignes, start=1):
        if len(ligne) > max_colonnes:
            violations.append(
                {
                    "regle": "ligne_trop_longue",
                    "fichier": relatif,
                    "ligne": numero,
                    "langue": langue,
                    "detail": f"{len(ligne)} colonnes (max {max_colonnes})",
                }
            )
        if REGEX_NOQA.search(ligne) or REGEX_SUPPRESSION.search(ligne):
            violations.append(
                {
                    "regle": "suppression_linter",
                    "fichier": relatif,
                    "ligne": numero,
                    "langue": langue,
                    "detail": "directive de suppression interdite",
                }
            )
        if REGEX_CODE_COMMENTE.match(ligne):
            violations.append(
                {
                    "regle": "code_commente",
                    "fichier": relatif,
                    "ligne": numero,
                    "langue": langue,
                    "detail": "ligne de code commentée, à vérifier",
                }
            )
    return violations


def modules_python(racine, exclusions):
    modules = {}
    for chemin, langue in fichiers(racine, exclusions, {"python"}):
        nom = chemin.stem
        modules.setdefault(nom, set())
        try:
            tree = ast.parse(
                chemin.read_text(encoding="utf-8", errors="replace")
            )
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules[nom].add(alias.name.split(".")[0])
            if isinstance(node, ast.ImportFrom) and node.module:
                modules[nom].add(node.module.split(".")[0])
    return {
        n: {d for d in deps if d in modules} for n, deps in modules.items()
    }


def chercher_cycles(graphe):
    cycles = []
    etat = {}

    def visiter(noeud, pile):
        etat[noeud] = 1
        pile.append(noeud)
        for voisin in graphe.get(noeud, ()):
            if etat.get(voisin) == 1:
                debut = pile.index(voisin)
                cycles.append(pile[debut:] + [voisin])
            elif etat.get(voisin) is None:
                visiter(voisin, pile)
        pile.pop()
        etat[noeud] = 2

    for noeud in graphe:
        if etat.get(noeud) is None:
            visiter(noeud, [])
    vus = set()
    uniques = []
    for cycle in cycles:
        cle = tuple(sorted(set(cycle)))
        if cle not in vus:
            vus.add(cle)
            uniques.append(cycle)
    return uniques


def fonctions_mortes(racine, arbres):
    appels = set()
    definitions = []
    for chemin, tree in arbres.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                appels.add(node.id)
            if isinstance(node, ast.Attribute):
                appels.add(node.attr)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                definitions.append((chemin, node))
    mortes = []
    for chemin, node in definitions:
        if node.name.startswith("__") or node.name in ("main",):
            continue
        if node.name.startswith("test_"):
            continue
        if node.name not in appels:
            mortes.append(
                {
                    "regle": "fonction_morte",
                    "fichier": str(chemin.relative_to(racine)),
                    "ligne": node.lineno,
                    "langue": "python",
                    "detail": f"{node.name} n'est jamais appelée, à vérifier",
                }
            )
    return mortes


def rapport_markdown(racine, violations, cycles, total, langues):
    par_regle = {}
    for violation in violations:
        par_regle.setdefault(violation["regle"], []).append(violation)
    ordre = [
        "syntaxe",
        "fonction_trop_longue",
        "else_apres_return",
        "comparaison_enchainee",
        "suppression_linter",
        "noqa",
        "predicat_non_booleen",
        "fonction_morte",
        "code_commente",
        "ligne_trop_longue",
        "cycle_import",
    ]
    lignes = [
        "# Audit des règles",
        "",
        f"Dépôt : `{racine}`",
        f"Fichiers analysés : {total}",
        "Langages : " + ", ".join(sorted(langues))
        if langues
        else "Langages : aucun",
        f"Violations : {len(violations)}",
        "",
    ]
    for regle in ordre:
        groupe = par_regle.get(regle)
        if not groupe:
            continue
        lignes.append(f"## {regle} ({len(groupe)})")
        lignes.append("")
        for violation in groupe:
            lignes.append(
                f"- `{violation['fichier']}:{violation['ligne']}` "
                f"[{violation.get('langue', '?')}] {violation['detail']}"
            )
        lignes.append("")
    if cycles:
        lignes.append(f"## cycle_import ({len(cycles)})")
        lignes.append("")
        for cycle in cycles:
            lignes.append("- " + " -> ".join(cycle))
        lignes.append("")
    if not violations and not cycles:
        lignes.append("Aucune violation détectée.")
    return "\n".join(lignes)


def main():
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("racine", nargs="?", default=".")
    parseur.add_argument("--max-lignes", type=int, default=10)
    parseur.add_argument("--max-colonnes", type=int, default=79)
    parseur.add_argument("--format", choices=("md", "json"), default="md")
    parseur.add_argument("--sortie")
    parseur.add_argument("--langues", default="")
    parseur.add_argument("--exclure", nargs="*", default=[])
    arguments = parseur.parse_args()

    racine = Path(arguments.racine).resolve()
    exclusions = EXCLUS_PAR_DEFAUT | set(arguments.exclure)
    filtre = {
        langue.strip()
        for langue in arguments.langues.split(",")
        if langue.strip()
    } or None

    violations = []
    arbres = {}
    langues_vues = set()
    total = 0
    for chemin, langue in fichiers(racine, exclusions, filtre):
        total += 1
        langues_vues.add(langue)
        relatif = str(chemin.relative_to(racine))
        if langue == "python":
            trouvees, tree = analyser_python(
                chemin, relatif, arguments.max_lignes, arguments.max_colonnes
            )
            violations.extend(trouvees)
            if tree is not None:
                arbres[chemin] = tree
        else:
            violations.extend(
                analyser_autre(
                    chemin,
                    relatif,
                    langue,
                    arguments.max_lignes,
                    arguments.max_colonnes,
                )
            )
        violations.extend(
            analyser_lignes(chemin, relatif, langue, arguments.max_colonnes)
        )

    violations.extend(fonctions_mortes(racine, arbres))
    cycles = chercher_cycles(modules_python(racine, exclusions))

    if arguments.format == "json":
        contenu = json.dumps(
            {
                "racine": str(racine),
                "fichiers": total,
                "langues": sorted(langues_vues),
                "violations": violations,
                "cycles": cycles,
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        contenu = rapport_markdown(
            racine, violations, cycles, total, langues_vues
        )

    if arguments.sortie:
        Path(arguments.sortie).write_text(contenu, encoding="utf-8")
        print(f"Rapport écrit dans {arguments.sortie}")
    else:
        print(contenu)
    return 0


if __name__ == "__main__":
    sys.exit(main())
