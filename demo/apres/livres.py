"""Consultation des livres."""


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
