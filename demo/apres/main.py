"""Point d'entrée du rapport de bibliothèque."""

from donnees import EMPRUNTS, LIVRES
from emprunts import compter_retards, total_amendes
from livres import plus_ancien
from rapport import afficher_emprunts, afficher_livres


def main():
    afficher_livres(LIVRES)
    afficher_emprunts(EMPRUNTS)
    print()
    total = total_amendes(EMPRUNTS)
    print(f"Total : {total:.2f} €")
    print(f"Retards : {compter_retards(EMPRUNTS)}")
    print(f"Plus ancien : {plus_ancien(LIVRES)}")


if __name__ == "__main__":
    main()
