"""Affichage du rapport de bibliothèque."""

from amendes import amende_de
from livres import libelle_disponibilite


def formater_livre(livre):
    return (
        f"{livre['titre']} ({livre['auteur']}, {livre['annee']}) : "
        f"{libelle_disponibilite(livre)}"
    )


def formater_emprunt(emprunt):
    amende = amende_de(emprunt)
    return (
        f"{emprunt['emprunteur']} a emprunté {emprunt['titre']} "
        f"depuis {emprunt['jours']} jours, amende : {amende:.2f} €"
    )


def afficher_livres(livres):
    print("=== Livres ===")
    for livre in livres:
        print(formater_livre(livre))


def afficher_emprunts(emprunts):
    print()
    print("=== Emprunts ===")
    for emprunt in emprunts:
        print(formater_emprunt(emprunt))
