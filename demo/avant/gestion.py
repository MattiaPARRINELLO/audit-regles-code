# def ancien_total(l, e):
#     return 0

import datetime


def f(l, e):
    print("=== Livres ===")
    for x in l:
        if x["exemplaires"] > 0:
            s = "disponible"
        else:
            s = "indisponible"
        print(f"{x['titre']} ({x['auteur']}, {x['annee']}) : {s}")
    print()
    print("=== Emprunts ===")
    tot = 0
    ret = 0
    for y in e:
        j = y["jours"]
        if 1 <= j <= 7:
            a = j*0.2
        else:
            if j > 7:
                a = 7*0.2 + (j-7)*0.5
            else:
                a = 0
        if a > 15:
            a = 15
        a = round(a, 2)
        if j > 7:
            ret = ret + 1
        tot = tot + a
        print(f"{y['emprunteur']} a emprunté {y['titre']} depuis {j} jours, amende : {a:.2f} €")
    print()
    v = l[0]
    for x in l:
        if x["annee"] < v["annee"]:
            v = x
    return round(tot, 2), ret, v["titre"]


def est_dispo(x):
    if x["exemplaires"] > 0:
        return True
    else:
        return False


def afficher_total(t):
    return f"Total : {t:.2f} €"


def aide():
    z = 1  # noqa
    return z


def vieux_tri(l):
    return sorted(l, key=lambda x: x["annee"])


def formater_livre(x):
    a = x["titre"]
    b = x["auteur"]
    c = x["annee"]
    return f"{a} ({b}, {c})"


def formater_livre_bis(x):
    a = x["titre"]
    b = x["auteur"]
    c = x["annee"]
    return f"{a} ({b}, {c})"
