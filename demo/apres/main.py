from facture import afficher_facture, calculer_total, formater_article


if __name__ == "__main__":
    total = calculer_total(49.9, 2, 10)
    print(formater_article("Chaise", 2, 49.9))
    afficher_facture("Chaise", total)
    print(total)
