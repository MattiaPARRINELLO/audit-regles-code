"""Tests du détecteur d'audit des règles."""

import json
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "skill" / "audit-regles-code" / "scripts" / "audit_regles.py"


def lancer(dossier, *arguments):
    commande = [sys.executable, str(SCRIPT), str(dossier), *arguments]
    return subprocess.run(
        commande, capture_output=True, text=True, check=False
    )


def regles(dossier, *arguments):
    resultat = lancer(dossier, "--format", "json", *arguments)
    return [
        violation["regle"]
        for violation in json.loads(resultat.stdout)["violations"]
    ]


def ecrire(dossier, nom, contenu):
    chemin = dossier / nom
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


PYTHON_MAL = '''"""Exemple non conforme."""

# def ancienne():
#     return 1


def calculer(a):
    total = a
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    total += 1
    return total


def garde(x):
    if x > 0:
        return True
    else:
        return False


def plage(x):
    if 1 < x < 10:
        return True
    return False


def inutile(x):
    y = x  # noqa: F841
    return y


if __name__ == "__main__":
    print(calculer(1))
    print(garde(1))
    print(plage(1))
    print(inutile(1))
'''

PYTHON_PROPRE = '''"""Exemple conforme."""


def calculer(a):
    total = a + 1
    if total < 0:
        return 0
    return total


if __name__ == "__main__":
    print(calculer(1))
'''


def test_python_detecte_toutes_les_regles(tmp_path):
    ecrire(tmp_path, "mauvais.py", PYTHON_MAL)
    trouvees = regles(tmp_path)
    for attendue in (
        "fonction_trop_longue",
        "else_apres_return",
        "comparaison_enchainee",
        "suppression_linter",
        "code_commente",
    ):
        assert attendue in trouvees


def test_python_propre_ne_remonte_rien(tmp_path):
    ecrire(tmp_path, "propre.py", PYTHON_PROPRE)
    assert regles(tmp_path) == []


def test_predicat_non_booleen(tmp_path):
    ecrire(
        tmp_path,
        "p.py",
        """def equipe_valide(equipe):
    if len(equipe) == 3:
        return True
    return "trop de joueurs"
""",
    )
    assert "predicat_non_booleen" in regles(tmp_path)


def test_nommage_afficher(tmp_path):
    ecrire(
        tmp_path,
        "p.py",
        """def afficher_total(total):
    return f"Total : {total}"
""",
    )
    assert "nommage_afficher" in regles(tmp_path)


def test_srp_retour_et_affichage(tmp_path):
    ecrire(
        tmp_path,
        "p.py",
        """def calculer(x):
    print("calcul")
    return x + 1
""",
    )
    assert "responsabilite_multiple" in regles(tmp_path)


def test_duplication(tmp_path):
    bloc = (
        "def a():\n    x = 1\n    y = 2\n    z = 3\n    return x + y + z\n\n\n"
    )
    contenu = bloc.replace("a()", "a()") + bloc.replace("a()", "b()")
    ecrire(tmp_path, "p.py", contenu)
    assert "duplication" in regles(tmp_path)


def test_javascript(tmp_path):
    ecrire(
        tmp_path,
        "app.js",
        """// function ancienne() {
//   return 1;
// }

function calculer(a) {
  let total = a;
  total += 1;
  total += 1;
  total += 1;
  total += 1;
  total += 1;
  total += 1;
  total += 1;
  total += 1;
  return total;
}

// eslint-disable-next-line no-console
console.log(calculer(1));
""",
    )
    trouvees = regles(tmp_path)
    assert "fonction_trop_longue" in trouvees
    assert "suppression_linter" in trouvees
    assert "code_commente" in trouvees


def test_go(tmp_path):
    ecrire(
        tmp_path,
        "main.go",
        """package main

func calculer(a int) int {
	total := a
	total += 1
	total += 1
	total += 1
	total += 1
	total += 1
	total += 1
	total += 1
	total += 1
	return total
}
""",
    )
    assert "fonction_trop_longue" in regles(tmp_path)


def test_ruby(tmp_path):
    ecrire(
        tmp_path,
        "style.rb",
        """def calculer(a)
  total = a
  total += 1
  total += 1
  total += 1
  total += 1
  total += 1
  total += 1
  total += 1
  total += 1
  total += 1
  total
end
""",
    )
    assert "fonction_trop_longue" in regles(tmp_path)


def test_configuration_du_depot(tmp_path):
    ecrire(
        tmp_path,
        "p.py",
        """def f(a):
    x = a
    x += 1
    return x


if __name__ == "__main__":
    print(f(1))
""",
    )
    assert regles(tmp_path) == []
    ecrire(tmp_path, ".audit-regles.json", '{"max_lignes": 2}')
    assert "fonction_trop_longue" in regles(tmp_path)


def test_baseline(tmp_path):
    ecrire(tmp_path, "p.py", PYTHON_MAL)
    ecrire(tmp_path, "baseline.json", '{"empreintes": []}')
    resultat = lancer(tmp_path, "--ecrire-baseline", "baseline.json")
    assert resultat.returncode == 0
    restantes = regles(tmp_path, "--baseline", "baseline.json")
    assert restantes == []


def test_check_code_de_sortie(tmp_path):
    ecrire(tmp_path, "p.py", PYTHON_MAL)
    assert lancer(tmp_path, "--check").returncode == 1
    ecrire(tmp_path, "p.py", PYTHON_PROPRE)
    assert lancer(tmp_path, "--check").returncode == 0


def test_sortie_sarif(tmp_path):
    ecrire(tmp_path, "p.py", PYTHON_MAL)
    resultat = lancer(tmp_path, "--format", "sarif")
    rapport = json.loads(resultat.stdout)
    assert rapport["version"] == "2.1.0"
    assert rapport["runs"][0]["results"]


def test_ordre_des_fonctions(tmp_path):
    ecrire(
        tmp_path,
        "p.py",
        """def appelante():
    return utilitaire()


def utilitaire():
    return 1
""",
    )
    assert "ordre_fonctions" not in regles(tmp_path)
    assert "ordre_fonctions" in regles(tmp_path, "--ordre")


def test_desactiver_une_regle(tmp_path):
    ecrire(tmp_path, "p.py", PYTHON_MAL)
    trouvees = regles(tmp_path, "--desactiver", "ligne_trop_longue")
    assert "ligne_trop_longue" not in trouvees
