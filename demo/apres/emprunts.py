"""Analyse des emprunts."""

from amendes import amende_de
from constantes import JOURS_PLEIN_TARIF


def est_en_retard(emprunt):
    if emprunt["jours"] <= JOURS_PLEIN_TARIF:
        return False
    return True


def total_amendes(emprunts):
    total = 0
    for emprunt in emprunts:
        total = total + amende_de(emprunt)
    return total


def compter_retards(emprunts):
    retards = 0
    for emprunt in emprunts:
        if est_en_retard(emprunt):
            retards = retards + 1
    return retards
