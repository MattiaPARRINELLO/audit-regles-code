from donnees import EMPRUNTS, LIVRES
from gestion import f


if __name__ == "__main__":
    t, r, v = f(LIVRES, EMPRUNTS)
    print("Total :", f"{t:.2f} €")
    print("Retards :", r)
    print("Plus ancien :", v)
