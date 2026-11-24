#!/usr/bin/env python3
"""Audit multi-langage d'un dépôt contre les règles de style du projet.

Python est analysé par AST (précis). Les autres langages sont analysés par
heuristiques : longueur des blocs, lignes, directives de suppression, code
commenté, responsabilités multiples, duplication. Les règles structurelles non
mesurables (nommage applicatif, ordre, qualité des commentaires) restent à la
lecture de l'agent.

Options principales : configuration par dépôt, baseline, code de sortie CI,
sortie SARIF, heuristique SRP, détection de duplication.
"""

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

EXCLUSIONS = {
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
REGEX_DECLARATION = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:public\s+|private\s+|protected\s+|"
    r"static\s+|async\s+|final\s+|override\s+)*"
    r"(?:func|fn|function|def)\s+(?P<nom>[A-Za-z_$][\w$]*)\s*"
    r"\([^)]*\)[^{;]*\{?\s*$"
)
REGEX_METHODE = re.compile(
    r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+|"
    r"final\s+|override\s+)*"
    r"(?P<nom>[A-Za-z_$][\w$]*)\s*\([^)]*\)\s*(?::[^{;]*)?\{?\s*$"
)
REGEX_FLECHE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<nom>[A-Za-z_$][\w$]*)\s*=\s*"
    r"(?:async\s*)?\([^)]*\)\s*(?::[^=]*)?=>"
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
EFFETS = re.compile(
    r"(\bprint\(|\bconsole\.|\bfmt\.Print|\bputs\b|\bSystem\.out|"
    r"\becho\b|\blogger\.|\bprintln!|\bputs\()"
)

CONFIG_DEFAUT = {
    "max_lignes": 10,
    "max_colonnes": 79,
    "langues": [],
    "exclure": [],
    "regles_desactivees": [],
    "srp": True,
    "duplication": {"seuil_lignes": 4, "min_occurrences": 2},
    "ordre": False,
    "baseline": None,
}

NOM_FICHIER_CONFIG = ".audit-regles.json"


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


def lire_config(racine, chemin):
    """Fusionne les valeurs par défaut, le fichier du dépôt et les options."""
    config = json.loads(json.dumps(CONFIG_DEFAUT))
    candidat = Path(chemin) if chemin else racine / NOM_FICHIER_CONFIG
    if candidat.is_file():
        charge = json.loads(candidat.read_text(encoding="utf-8"))
        config.update(charge)
    return config


def fusionner_options(config, arguments):
    """Les options de ligne de commande écrasent la configuration."""
    for nom, attribut in (
        ("max_lignes", "max_lignes"),
        ("max_colonnes", "max_colonnes"),
        ("baseline", "baseline"),
    ):
        valeur = getattr(arguments, attribut)
        if valeur is not None:
            config[nom] = valeur
    if arguments.langues:
        config["langues"] = [
            langue.strip() for langue in arguments.langues.split(",") if langue.strip()
        ]
    if arguments.exclure:
        config["exclure"] = list(config["exclure"]) + list(arguments.exclure)
    if arguments.desactiver:
        config["regles_desactivees"] = list(config["regles_desactivees"]) + [
            regle.strip() for regle in arguments.desactiver.split(",") if regle.strip()
        ]
    if arguments.srp is not None:
        config["srp"] = arguments.srp
    if arguments.duplication is not None:
        config["duplication"]["active"] = arguments.duplication
    if arguments.ordre is not None:
        config["ordre"] = arguments.ordre
    return config


# --------------------------------------------------------------------------
# Parcours des fichiers
# --------------------------------------------------------------------------


def fichiers(racine, config):
    exclusions = EXCLUSIONS | set(config["exclure"])
    langues = set(config["langues"])
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
    retenues = []
    for ligne in lignes[debut:fin]:
        nue = ligne.strip()
        if not nue:
            continue
        if nue.startswith(("#", "//", "/*", "*")):
            continue
        retenues.append(ligne)
    return retenues


# --------------------------------------------------------------------------
# Analyse Python
# --------------------------------------------------------------------------


def est_bool(node):
    if isinstance(node, ast.Constant):
        return isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, (ast.Compare, ast.BoolOp, ast.Call)):
        return True
    return False


def renvoie_une_valeur(node):
    for sous in ast.walk(node):
        if isinstance(sous, ast.Return) and sous.value is not None:
            return True
    return False


def a_un_effet_de_bord(node):
    for sous in ast.walk(node):
        if not isinstance(sous, ast.Call):
            continue
        nom = ""
        if isinstance(sous.func, ast.Name):
            nom = sous.func.id
        elif isinstance(sous.func, ast.Attribute):
            nom = sous.func.attr
        if nom in {"print", "input", "write", "insert_one"}:
            return True
        if nom.startswith(("enregistrer_", "logger")):
            return True
    return False


def regle_longueur(node, lignes, relatif, config):
    utiles = lignes_utiles(lignes, node.lineno, node.end_lineno)
    if len(utiles) <= config["max_lignes"]:
        return []
    return [
        {
            "regle": "fonction_trop_longue",
            "fichier": relatif,
            "ligne": node.lineno,
            "langue": "python",
            "detail": (
                f"{node.name} : {len(utiles)} lignes utiles "
                f"(max {config['max_lignes']})"
            ),
        }
    ]


def regle_predicat(node, relatif):
    if not node.name.endswith("_valide"):
        return []
    for sous in ast.walk(node):
        if isinstance(sous, ast.Return) and sous.value is not None:
            if not est_bool(sous.value):
                return [
                    {
                        "regle": "predicat_non_booleen",
                        "fichier": relatif,
                        "ligne": sous.lineno,
                        "langue": "python",
                        "detail": f"{node.name} renvoie une valeur non booléenne",
                    }
                ]
    return []


def regle_nommage_afficher(node, relatif):
    if not node.name.startswith("afficher_"):
        return []
    if not renvoie_une_valeur(node):
        return []
    return [
        {
            "regle": "nommage_afficher",
            "fichier": relatif,
            "ligne": node.lineno,
            "langue": "python",
            "detail": f"{node.name} renvoie une valeur, un affichage ne devrait pas",
        }
    ]


def regle_srp_python(node, relatif, config):
    if not config["srp"]:
        return []
    if not renvoie_une_valeur(node) or not a_un_effet_de_bord(node):
        return []
    return [
        {
            "regle": "responsabilite_multiple",
            "fichier": relatif,
            "ligne": node.lineno,
            "langue": "python",
            "detail": f"{node.name} renvoie une valeur et produit un affichage",
        }
    ]


def regles_structure_python(tree, relatif):
    violations = []
    for node in ast.walk(tree):
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
    return violations


def analyser_python(chemin, relatif, config):
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

    violations.extend(regles_structure_python(tree, relatif))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        violations.extend(regle_longueur(node, lignes, relatif, config))
        violations.extend(regle_predicat(node, relatif))
        violations.extend(regle_nommage_afficher(node, relatif))
        violations.extend(regle_srp_python(node, relatif, config))
    return violations, tree


# --------------------------------------------------------------------------
# Analyse générique (tous les autres langages)
# --------------------------------------------------------------------------


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


def blocs_accolades(lignes):
    """Blocs délimités par des accolades, par heuristique."""
    blocs = []
    i = 0
    while i < len(lignes):
        correspondance = (
            REGEX_DECLARATION.match(lignes[i])
            or REGEX_METHODE.match(lignes[i])
            or REGEX_FLECHE.match(lignes[i])
        )
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
        correspondance = re.match(r"^\s*def\s+(?P<nom>[A-Za-z_]\w*[?!]?)", lignes[i])
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


def blocs_de(langue, lignes):
    if langue in ("ruby", "lua"):
        return blocs_end(lignes)
    return blocs_accolades(lignes)


def regle_srp_bloc(corps):
    texte = "\n".join(corps)
    if not EFFETS.search(texte):
        return False
    if not re.search(r"\breturn\s+\S", texte):
        return False
    return True


def analyser_blocs(chemin, relatif, langue, config):
    violations = []
    lignes = chemin.read_text(encoding="utf-8", errors="replace").splitlines()
    for nom, debut, fin in blocs_de(langue, lignes):
        corps = lignes[debut:fin]
        utiles = lignes_utiles(lignes, debut, fin)
        if len(utiles) > config["max_lignes"]:
            violations.append(
                {
                    "regle": "fonction_trop_longue",
                    "fichier": relatif,
                    "ligne": debut,
                    "langue": langue,
                    "detail": (
                        f"{nom} : {len(utiles)} lignes utiles "
                        f"(max {config['max_lignes']}, heuristique à vérifier)"
                    ),
                }
            )
        if config["srp"] and regle_srp_bloc(corps):
            violations.append(
                {
                    "regle": "responsabilite_multiple",
                    "fichier": relatif,
                    "ligne": debut,
                    "langue": langue,
                    "detail": f"{nom} renvoie une valeur et produit un affichage",
                }
            )
    return violations


def analyser_lignes(chemin, relatif, langue, config):
    violations = []
    lignes = chemin.read_text(encoding="utf-8", errors="replace").splitlines()
    for numero, ligne in enumerate(lignes, start=1):
        if len(ligne) > config["max_colonnes"]:
            violations.append(
                {
                    "regle": "ligne_trop_longue",
                    "fichier": relatif,
                    "ligne": numero,
                    "langue": langue,
                    "detail": f"{len(ligne)} colonnes (max {config['max_colonnes']})",
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


# --------------------------------------------------------------------------
# Graphe d'imports, fonctions mortes, ordre, duplication
# --------------------------------------------------------------------------


def modules_python(racine, config):
    modules = {}
    for chemin, langue in fichiers(racine, config):
        if langue != "python":
            continue
        nom = chemin.stem
        modules.setdefault(nom, set())
        try:
            tree = ast.parse(chemin.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules[nom].add(alias.name.split(".")[0])
            if isinstance(node, ast.ImportFrom) and node.module:
                modules[nom].add(node.module.split(".")[0])
    return {n: {d for d in deps if d in modules} for n, deps in modules.items()}


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
        if node.name.startswith("test_") or node.name in appels:
            continue
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


def ordre_fonctions(arbres, config, racine):
    violations = []
    if not config["ordre"]:
        return violations
    for chemin, tree in arbres.items():
        positions = {
            node.name: node.lineno
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            cible = appelle_plus_bas(node, positions)
            if cible is None:
                continue
            violations.append(
                {
                    "regle": "ordre_fonctions",
                    "fichier": str(chemin.relative_to(racine)),
                    "ligne": node.lineno,
                    "langue": "python",
                    "detail": f"{node.name} appelle {cible}, défini plus bas",
                }
            )
    return violations


def appelle_plus_bas(node, positions):
    for sous in ast.walk(node):
        if not isinstance(sous, ast.Call):
            continue
        if not isinstance(sous.func, ast.Name):
            continue
        cible = positions.get(sous.func.id)
        if cible is not None and cible > node.lineno:
            return sous.func.id
    return None


def normaliser_ligne(ligne):
    nue = ligne.strip()
    if not nue or nue.startswith(("#", "//", "/*", "*")):
        return ""
    return re.sub(r"\s+", " ", nue)


def chercher_duplication(textes, config):
    reglage = config["duplication"]
    if not reglage.get("active", True):
        return []
    taille = int(reglage.get("seuil_lignes", 4))
    minimum = int(reglage.get("min_occurrences", 2))
    occurrences = {}
    for relatif, lignes in textes.items():
        normalisees = [normaliser_ligne(ligne) for ligne in lignes]
        for debut in range(len(normalisees) - taille + 1):
            fenetre = normalisees[debut : debut + taille]
            if sum(1 for ligne in fenetre if ligne) < taille:
                continue
            if len(set(fenetre)) == 1:
                continue
            cle = hashlib.sha1("\n".join(fenetre).encode()).hexdigest()
            occurrences.setdefault(cle, []).append((relatif, debut + 1))
    violations = []
    deja_vus = set()
    for cle, lieux in occurrences.items():
        if len(lieux) < minimum or cle in deja_vus:
            continue
        deja_vus.add(cle)
        premier = lieux[0]
        violations.append(
            {
                "regle": "duplication",
                "fichier": premier[0],
                "ligne": premier[1],
                "langue": "?",
                "detail": (
                    f"bloc de {taille} lignes répété {len(lieux)} fois, "
                    f"par exemple en {lieux[1][0]}:{lieux[1][1]}"
                ),
            }
        )
    return violations


# --------------------------------------------------------------------------
# Baseline
# --------------------------------------------------------------------------


def empreinte(violation):
    return "|".join(
        (
            violation["regle"],
            violation["fichier"],
            violation["detail"],
        )
    )


def charger_baseline(chemin):
    if not chemin:
        return set()
    fichier = Path(chemin)
    if not fichier.is_file():
        return set()
    contenu = json.loads(fichier.read_text(encoding="utf-8"))
    return set(contenu.get("empreintes", []))


def ecrire_baseline(chemin, violations):
    Path(chemin).write_text(
        json.dumps(
            {
                "version": 1,
                "empreintes": sorted({empreinte(v) for v in violations}),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def filtrer_baseline(violations, baseline):
    return [v for v in violations if empreinte(v) not in baseline]


# --------------------------------------------------------------------------
# Rapports
# --------------------------------------------------------------------------

ORDRE_REGLES = [
    "syntaxe",
    "fonction_trop_longue",
    "else_apres_return",
    "comparaison_enchainee",
    "suppression_linter",
    "predicat_non_booleen",
    "nommage_afficher",
    "responsabilite_multiple",
    "fonction_morte",
    "ordre_fonctions",
    "duplication",
    "code_commente",
    "ligne_trop_longue",
    "cycle_import",
]

GRAVITES = {
    "syntaxe": "haute",
    "fonction_trop_longue": "moyenne",
    "else_apres_return": "basse",
    "comparaison_enchainee": "basse",
    "suppression_linter": "moyenne",
    "predicat_non_booleen": "moyenne",
    "nommage_afficher": "basse",
    "responsabilite_multiple": "moyenne",
    "fonction_morte": "moyenne",
    "ordre_fonctions": "basse",
    "duplication": "moyenne",
    "code_commente": "basse",
    "ligne_trop_longue": "basse",
    "cycle_import": "haute",
}


def rapport_markdown(racine, violations, cycles, total, langues):
    par_regle = {}
    for violation in violations:
        par_regle.setdefault(violation["regle"], []).append(violation)
    lignes = [
        "# Audit des règles",
        "",
        f"Dépôt : `{racine}`",
        f"Fichiers analysés : {total}",
        "Langages : " + (", ".join(sorted(langues)) or "aucun"),
        f"Violations : {len(violations)}",
        "",
        "| Règle | Nombre | Gravité |",
        "|---|---|---|",
    ]
    for regle in ORDRE_REGLES:
        if regle in par_regle:
            lignes.append(
                f"| {regle} | {len(par_regle[regle])} | "
                f"{GRAVITES.get(regle, 'basse')} |"
            )
    if cycles:
        lignes.append(f"| cycle_import | {len(cycles)} | haute |")
    lignes.append("")
    for regle in ORDRE_REGLES:
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


def rapport_sarif(racine, violations):
    regles = [
        {"id": regle, "shortDescription": {"text": regle}} for regle in ORDRE_REGLES
    ]
    resultats = []
    for violation in violations:
        resultats.append(
            {
                "ruleId": violation["regle"],
                "level": "warning",
                "message": {"text": violation["detail"]},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": violation["fichier"]},
                            "region": {"startLine": max(violation["ligne"], 1)},
                        },
                    }
                ],
            }
        )
    return json.dumps(
        {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "audit-regles-code",
                            "informationUri": str(racine),
                            "rules": regles,
                        }
                    },
                    "results": resultats,
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------


def collecter(racine, config, afficher_progression=False):
    violations = []
    arbres = {}
    textes = {}
    langues = set()
    total = 0
    liste = list(fichiers(racine, config))
    nombre_total = len(liste)
    for index, (chemin, langue) in enumerate(liste, 1):
        if afficher_progression:
            relatif_affichage = str(chemin.relative_to(racine))
            print(
                f"[{index}/{nombre_total}] {relatif_affichage}",
                file=sys.stderr,
                flush=True,
            )
        total += 1
        langues.add(langue)
        relatif = str(chemin.relative_to(racine))
        textes[relatif] = chemin.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
        if langue == "python":
            trouvees, tree = analyser_python(chemin, relatif, config)
            violations.extend(trouvees)
            if tree is not None:
                arbres[chemin] = tree
        else:
            violations.extend(analyser_blocs(chemin, relatif, langue, config))
        violations.extend(analyser_lignes(chemin, relatif, langue, config))
    violations.extend(fonctions_mortes(racine, arbres))
    violations.extend(ordre_fonctions(arbres, config, racine))
    violations.extend(chercher_duplication(textes, config))
    cycles = chercher_cycles(modules_python(racine, config))
    return violations, cycles, total, langues


def main():
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("racine", nargs="?", default=".")
    parseur.add_argument("--config")
    parseur.add_argument("--max-lignes", type=int)
    parseur.add_argument("--max-colonnes", type=int)
    parseur.add_argument("--langues")
    parseur.add_argument("--exclure", nargs="*", default=[])
    parseur.add_argument("--desactiver")
    parseur.add_argument("--srp", action=argparse.BooleanOptionalAction)
    parseur.add_argument("--duplication", action=argparse.BooleanOptionalAction)
    parseur.add_argument("--ordre", action=argparse.BooleanOptionalAction)
    parseur.add_argument("--baseline")
    parseur.add_argument("--ecrire-baseline")
    parseur.add_argument("--check", action="store_true")
    parseur.add_argument("--summary", action="store_true")
    parseur.add_argument("--format", choices=("md", "json", "sarif"), default="md")
    parseur.add_argument("--sortie")
    parseur.add_argument(
        "--quiet",
        "--no-progress",
        "--silent",
        action="store_true",
        dest="quiet",
        help="Désactive l'affichage de la progression sur stderr.",
    )
    arguments = parseur.parse_args()

    racine = Path(arguments.racine).resolve()
    config = fusionner_options(lire_config(racine, arguments.config), arguments)

    violations, cycles, total, langues = collecter(
        racine, config, afficher_progression=not arguments.quiet
    )
    desactivees = set(config["regles_desactivees"])
    violations = [v for v in violations if v["regle"] not in desactivees]

    if arguments.ecrire_baseline:
        ecrire_baseline(arguments.ecrire_baseline, violations)

    restantes = filtrer_baseline(violations, charger_baseline(config["baseline"]))

    if arguments.format == "json":
        contenu = json.dumps(
            {
                "racine": str(racine),
                "fichiers": total,
                "langues": sorted(langues),
                "violations": restantes,
                "cycles": cycles,
            },
            ensure_ascii=False,
            indent=2,
        )
    elif arguments.format == "sarif":
        contenu = rapport_sarif(racine, restantes)
    else:
        contenu = rapport_markdown(racine, restantes, cycles, total, langues)

    if arguments.sortie:
        Path(arguments.sortie).write_text(contenu, encoding="utf-8")
        print(f"Rapport écrit dans {arguments.sortie}")
    elif not arguments.summary:
        print(contenu)

    if arguments.summary:
        langues_texte = ",".join(sorted(langues)) or "-"
        print(f"violations={len(restantes)} fichiers={total} langues={langues_texte}")

    if arguments.check and (restantes or cycles):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
