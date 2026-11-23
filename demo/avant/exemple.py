"""Exemple volontairement non conforme, pour la démonstration."""

# def ancienne_version(x):
#     return x * 2


def calculer_total(prix, quantite, remise):
    total = prix * quantite
    total = total - remise
    total = total + 2.5
    total = total + 1.0
    total = round(total, 2)
    if total < 0:
        return 0
    total = total * 1.2
    total = total + 3
    total = total - 1
    return total


def prix_valide(prix):
    if prix > 0:
        return True
    else:
        return False


def quantite_valide(quantite):
    if 1 <= quantite <= 10:
        return True
    return False


def ancien_affichage(total):
    texte = f"Total : {total}"  # noqa: F841
    return texte


if __name__ == "__main__":
    print(prix_valide(12))
    print(quantite_valide(3))
