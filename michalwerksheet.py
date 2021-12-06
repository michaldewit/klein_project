import pandas as pd

dtf = pd.read_csv(r"C:\Users\arie\academy\projectmetsuus\uitslagen.csv", sep=";")
# print(dtf)
# print(dtf.columns)
#allecodes = dtf[['RegioCode', 'GeldigeStemmen']][5:12]

#allecodes.info()


# allecodes = dtf
# print(allecodes[3:4])
# print(allecodes)
def partij_checker(): #checkt of partij bestaat, en indien bestaat geeft de partij als return
    # Nu willen we een naam invoeren Bijvoorbeeld VVD
    print("geef naam van partij op, om te stoppen zeg quit ")
    
    partij_namen = dtf.iloc[:, 10:46]
    mogelijke_naam_partij = list(partij_namen.columns)
    while True: #while functie om voor 
        input_info = input() #verwacht een naam van een partij
        if input_info in mogelijke_naam_partij:
            print("naam is correct, gaat door")
            partij_return = input_info
            return partij_return 
            break
        elif input_info == "quit":
            print("programma is gestopt")
            break
        else:
            print(f"naam van partij was incorrect, kies een partij uit lijst {mogelijke_naam_partij}")
            print("\n geef naam van partij op, om te stoppen zeg quit ")
        #print("correct")#checken of naam inderdaad van een partij is

print(f'dit is de partij die je hebt gekozen {partij_checker()}')


# 1. Nu willen we een naam invoeren Bijvoorbeeld VVD en dan zien we in welke regiocodes hij stemmen heeft gehad Ook voor Volt.
#  Dus we komen zo te weten in hoeveel regiocodes een partij stemmen heeft gekregen
# 2.  print top 3 partijen met aantal stemmen per gemeente. begin met 1 gemeente, veralgemeniseer
# 3. alle gemeente met (letter) waarbij de partij die het grootste als eerst genoemd wordt 
# 4. een overzicht per OudeRegioNaam met op STEDEN GESORTEERD met alleen de naam van de GROOTSTE PARTIJ per regionaam GEGROEPEERD op winnaar
# 5. hoeveel procent een partij van de geldige stemmen in een regio gehaald heeft
# 6. hoeveel procent de coalitie in handen heeft per stad
# 7. het gemiddelde aantal kiesgerechtigde in steden die een d in de naam hebben

#print_stemmen()
