# def ancien_total(x):
#     return x * 1.196

import datetime


def calculer(d, q, p, r, t):
    if d != None:
        if q > 0:
            if p > 0:
                x = p * q
                x = x - (x * r / 100)
                if t == True:
                    x = x * 1.2
                x = x + 5
                if x > 100:
                    x = x - 10
                return round(x, 2)
            else:
                return 0
        else:
            return 0
    else:
        return 0


def quantite_valide(q):
    if 1 <= q <= 99:
        return True
    else:
        return False


def prix_valide(p):
    if p > 0:
        return True
    else:
        return False


def formater(d, q, p):
    a = d
    b = q
    c = p
    return f"{a} x{b} a {c} euros et un texte beaucoup trop long pour la limite de colonnes"


def formater_bis(d, q, p):
    a = d
    b = q
    c = p
    return f"{a} x{b} a {c} euros et un texte beaucoup trop long pour la limite de colonnes"


def afficher_facture(d, x):
    print("Article :", d)
    print("Total :", x)
    return x


def vieux_format(x):
    y = x  # noqa
    return y
