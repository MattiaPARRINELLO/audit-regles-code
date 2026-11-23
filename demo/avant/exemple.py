# def ancien_calcul(x):
#     return x * 1.196

import datetime


def f(d, q, p, r, t):
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
                x = round(x, 2)
                print("Article :", d)
                print("Total :", x)
                return x
            else:
                return 0
        else:
            return 0
    else:
        return 0


def valide_q(q):
    if 1 <= q <= 99:
        return True
    else:
        return False


def valide_p(p):
    if p > 0:
        return True
    else:
        return False


def afficher_article(d, q, p):
    a = d
    b = q
    c = p
    return f"{a} x{b} a {c} euros et ce texte est vraiment beaucoup trop long pour la limite de colonnes"


def afficher_article_bis(d, q, p):
    a = d
    b = q
    c = p
    return f"{a} x{b} a {c} euros et ce texte est vraiment beaucoup trop long pour la limite de colonnes"


def vieux_format(x):
    y = x  # noqa
    return y


if __name__ == "__main__":
    print(f("Chaise", 2, 49.9, 10, True))
