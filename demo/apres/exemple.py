"""Facturation d'une commande, version lisible."""

TVA = 1.2
FRAIS_FIXES = 5
SEUIL_REMISE = 100
REMISE_GRANDE_COMMANDE = 10
QUANTITE_MIN = 1
QUANTITE_MAX = 99


def quantite_valide(quantite):
    if quantite < QUANTITE_MIN:
        return False
    if quantite > QUANTITE_MAX:
        return False
    return True


def prix_valide(prix):
    if prix <= 0:
        return False
    return True


def calculer_brut(prix, quantite, remise):
    return prix * quantite * (1 - remise / 100)


def appliquer_tva(total):
    return total * TVA


def appliquer_frais(total):
    total = total + FRAIS_FIXES
    if total <= SEUIL_REMISE:
        return total
    return total - REMISE_GRANDE_COMMANDE


def calculer_total(prix, quantite, remise):
    if not quantite_valide(quantite):
        return 0
    if not prix_valide(prix):
        return 0
    total = calculer_brut(prix, quantite, remise)
    total = appliquer_tva(total)
    total = appliquer_frais(total)
    return round(total, 2)


def afficher_facture(designation, total):
    print("Article :", designation)
    print("Total :", total)


def main():
    total = calculer_total(49.9, 2, 10)
    afficher_facture("Chaise", total)
    print(total)


if __name__ == "__main__":
    main()
