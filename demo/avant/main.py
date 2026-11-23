from facture import afficher_facture, calculer, formater


if __name__ == "__main__":
    total = calculer("Chaise", 2, 49.9, 10, True)
    print(formater("Chaise", 2, 49.9))
    afficher_facture("Chaise", total)
    print(total)
