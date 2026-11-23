"""Même exemple après application des règles."""


def calculer_total(prix, quantite, remise):
    total = round(prix * quantite - remise + 3.5, 2)
    if total < 0:
        return 0
    return total * 1.2 + 2


def prix_valide(prix):
    if prix <= 0:
        return False
    return True


def quantite_valide(quantite):
    if quantite < 1:
        return False
    if quantite > 10:
        return False
    return True


def formater_total(total):
    return f"Total : {total}"


if __name__ == "__main__":
    print(prix_valide(12))
    print(quantite_valide(3))
    print(formater_total(calculer_total(10, 2, 1)))
