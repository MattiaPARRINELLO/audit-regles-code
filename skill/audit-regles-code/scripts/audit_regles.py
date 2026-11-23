#!/usr/bin/env python3
"""Audit déterministe d'un dépôt Python contre les règles de style du projet.

Détecte les violations mesurables par AST ou par expression régulière :
longueur des fonctions, else après return, comparaisons enchaînées,
directives noqa, code commenté, prédicats non booléens, fonctions mortes,
cycles d'imports et lignes trop longues.

Sortie : rapport Markdown sur stdout, ou fichier avec --sortie, ou JSON
avec --format json.
"""

import argparse
import ast
import json
import os
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
}

REGEX_NOQA = re.compile(r"#\s*noqa")
REGEX_CODE_COMMENTE = re.compile(
    r"^\s*#\s*(def |class |return |if |elif |else:|for |while |import |from |"
    r"print\(|[A-Za-z_][A-Za-z0-9_]*\s*=)"
)


def fichiers_python(racine, exclusions):
    for chemin in sorted(Path(racine).rglob("*.py")):
        parties = set(chemin.parts)
        if parties & exclusions:
            continue
        yield chemin


def lignes_utiles(lignes, debut, fin):
    """Lignes du corps hors signature, lignes vides et commentaires seuls."""
    corps = lignes[debut:fin]
    return [
        ligne
        for ligne in corps
        if ligne.strip() and not ligne.strip().startswith("#")
    ]


def est_bool(node):
    if isinstance(node, ast.Constant):
        return isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, ast.Compare):
        return True
    if isinstance(node, ast.BoolOp):
        return all(est_bool(v) for v in node.values)
    if isinstance(node, ast.Call):
        return True
    return False


def analyser_fichier(chemin, racine, max_lignes, max_colonnes):
    violations = []
    texte = chemin.read_text(encoding="utf-8", errors="replace")
    lignes = texte.splitlines()
    relatif = str(chemin.relative_to(racine))

    try:
        tree = ast.parse(texte)
    except SyntaxError as erreur:
        violations.append(
            {
                "regle": "syntaxe",
                "fichier": relatif,
                "ligne": erreur.lineno or 0,
                "detail": f"fichier non analysable : {erreur.msg}",
            }
        )
        return violations, tree

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            utiles = lignes_utiles(lignes, node.lineno, node.end_lineno)
            if len(utiles) > max_lignes:
                violations.append(
                    {
                        "regle": "fonction_trop_longue",
                        "fichier": relatif,
                        "ligne": node.lineno,
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
                                    "detail": (
                                        f"{node.name} renvoie une valeur non "
                                        "booléenne"
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
                        "detail": "else inutile après un return",
                    }
                )

        if isinstance(node, ast.Compare) and len(node.ops) > 1:
            violations.append(
                {
                    "regle": "comparaison_enchainee",
                    "fichier": relatif,
                    "ligne": node.lineno,
                    "detail": "comparaison enchaînée",
                }
            )

    for numero, ligne in enumerate(lignes, start=1):
        if len(ligne) > max_colonnes:
            violations.append(
                {
                    "regle": "ligne_trop_longue",
                    "fichier": relatif,
                    "ligne": numero,
                    "detail": f"{len(ligne)} colonnes (max {max_colonnes})",
                }
            )
        if REGEX_NOQA.search(ligne):
            violations.append(
                {
                    "regle": "noqa",
                    "fichier": relatif,
                    "ligne": numero,
                    "detail": "directive noqa interdite",
                }
            )
        if REGEX_CODE_COMMENTE.match(ligne):
            violations.append(
                {
                    "regle": "code_commente",
                    "fichier": relatif,
                    "ligne": numero,
                    "detail": "ligne de code commentée, à vérifier",
                }
            )

    return violations, tree


def modules_locaux(racine):
    modules = {}
    for chemin in fichiers_python(racine, EXCLUS_PAR_DEFAUT):
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
    connus = {
        n: {d for d in deps if d in modules} for n, deps in modules.items()
    }
    return connus


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
                    "detail": f"{node.name} n'est jamais appelée, à vérifier",
                }
            )
    return mortes


def rapport_markdown(racine, violations, cycles, total_fichiers):
    par_regle = {}
    for violation in violations:
        par_regle.setdefault(violation["regle"], []).append(violation)
    ordre = [
        "syntaxe",
        "fonction_trop_longue",
        "else_apres_return",
        "comparaison_enchainee",
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
        f"Fichiers Python analysés : {total_fichiers}",
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
                f"{violation['detail']}"
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
    parseur.add_argument(
        "--exclure",
        nargs="*",
        default=[],
        help="dossiers supplémentaires à ignorer",
    )
    arguments = parseur.parse_args()

    racine = Path(arguments.racine).resolve()
    exclusions = EXCLUS_PAR_DEFAUT | set(arguments.exclure)

    violations = []
    arbres = {}
    fichiers = 0
    for chemin in fichiers_python(racine, exclusions):
        fichiers += 1
        trouves, tree = analyser_fichier(
            chemin, racine, arguments.max_lignes, arguments.max_colonnes
        )
        violations.extend(trouves)
        if tree is not None:
            arbres[chemin] = tree

    violations.extend(fonctions_mortes(racine, arbres))
    cycles = chercher_cycles(modules_locaux(racine))

    if arguments.format == "json":
        contenu = json.dumps(
            {
                "racine": str(racine),
                "fichiers": fichiers,
                "violations": violations,
                "cycles": cycles,
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        contenu = rapport_markdown(racine, violations, cycles, fichiers)

    if arguments.sortie:
        Path(arguments.sortie).write_text(contenu, encoding="utf-8")
        print(f"Rapport écrit dans {arguments.sortie}")
    else:
        print(contenu)

    return 0


if __name__ == "__main__":
    sys.exit(main())
