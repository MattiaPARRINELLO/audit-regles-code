"""Calcul des amendes de retard."""

from constantes import (
    JOURS_PLEIN_TARIF,
    PLAFOND_AMENDE,
    TARIF_COURT,
    TARIF_LONG,
)


def calculer_amende(jours):
    if jours <= JOURS_PLEIN_TARIF:
        return jours * TARIF_COURT
    jours_tardifs = jours - JOURS_PLEIN_TARIF
    return JOURS_PLEIN_TARIF * TARIF_COURT + jours_tardifs * TARIF_LONG


def plafonner(amende):
    if amende > PLAFOND_AMENDE:
        return PLAFOND_AMENDE
    return amende


def amende_de(emprunt):
    return round(plafonner(calculer_amende(emprunt["jours"])), 2)
