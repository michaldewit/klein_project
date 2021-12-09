import pandas as pd
import math
dtf = pd.read_csv(r"C:\Users\arie\academy\projectmetsuus\uitslagen.csv", sep=";")
# print(dtf)
#print(dtf.columns)
#allecodes = dtf[['RegioCode', 'GeldigeStemmen']][5:12]

#allecodes.info()


# allecodes = dtf
# print(allecodes[3:4])
# print(allecodes)

# 1. Nu willen we een naam invoeren Bijvoorbeeld VVD en dan zien we in welke regiocodes hij stemmen heeft gehad Ook voor Volt.
#  Dus we komen zo te weten in hoeveel regiocodes een partij stemmen heeft gekregen

def partij_checker(): #checkt of partij bestaat, en indien bestaat geeft de partij als return
    # Nu willen we een naam invoeren Bijvoorbeeld VVD
    print("geef naam van partij op, om te stoppen zeg quit ")
    
    partij_namen = dtf.iloc[:, 10:46]
    mogelijke_naam_partij = list(partij_namen.columns)
    while True: #while functie om voor 
        input_info = input() #verwacht een naam van een partij
        if input_info in mogelijke_naam_partij:
            print("naam is correct, gaat door")
            return input_info 
            break
        elif input_info == "quit":
            print("programma is gestopt")
            break
        else:
            print(f"naam van partij was incorrect, kies een partij uit lijst {mogelijke_naam_partij}")
            print("\n geef naam van partij op, om te stoppen zeg quit ")
        #print("correct")#checken of naam inderdaad van een partij is

#print(f'dit is de partij die je hebt gekozen {partij_checker()}')

def regio_codes(partij): #dataframe maken waarbij regiocode en partij uit input staat.
    new_dtf_regiocodes = dtf.loc[:,["RegioNaam","RegioCode",partij]]
    print(new_dtf_regiocodes.dropna(0))
    print(f'aantal gemeentes met stemmen voor deze partij is {new_dtf_regiocodes[new_dtf_regiocodes.columns[2]].count()}')



# 2.  print top 3 partijen met aantal stemmen per gemeente. begin met 1 gemeente, veralgemeniseer
#beginnen met een functie die op row basis itereert

def gemeente_top(gemeente,nummer):
    gemeente_top_3 = dtf[dtf['RegioNaam'] == gemeente]
    gemeente_dtf = gemeente_top_3.iloc[:,10:46]
    gemeente_series = gemeente_dtf.squeeze()
    n_string = '\n'
    print(f'dit zijn de grootste {nummer} partijen in {gemeente} van groot naar klein:{n_string}{gemeente_series.sort_values(ascending=False).head(nummer)}')


def gemeente_checker(): #checkt of gemeente bestaat
    print("geef naam van gemeente op, om te stoppen zeg quit ")
    
    gemeente_namen = dtf.iloc[:, 0]
    mogelijke_naam_gemeente = list(gemeente_namen)
    while True: #while functie om voor 
         input_info = input() #verwacht een naam van een partij
         if input_info in mogelijke_naam_gemeente:
             print("naam is correct, gaat door naar volgende functie")
             return input_info 
             break
         elif input_info == "quit":
             print("programma is gestopt")
             break
         else:
             print(f"naam van gemeente was incorrect, kies een gemeente uit lijst {mogelijke_naam_gemeente}")
             print("\n geef naam van gemeente op, om te stoppen zeg quit ")
#print(gemeente_top_3(gemeente_checker()))


#print_stemmen()

# gemeente invoeren; welke partijen hebben 0 stemmen. Welke partijen hebben geen stemdata.

#gemeentechecker voor gemeenteinvoer

def gemeente_bottom(gemeente):
    gemeente_bottom = dtf[dtf['RegioNaam'] == gemeente]
    gemeente_dtf = gemeente_bottom.iloc[:,10:46]
    gemeente_series = gemeente_dtf.squeeze()
    #print(gemeente_series)
    for i, x in gemeente_series.iteritems():
        if x == 0:
            print(i)
        elif math.isnan(x) == True:
            print(i)
    #n_string = '\n'
    #print(f'dit zijn de grootste {nummer} partijen in {gemeente} van groot naar klein:{n_string}{gemeente_series.sort_values(ascending=False).head(nummer)}')



# 3. alle gemeente met (letter) waarbij de grootste partij genoemd wordt.
def gemeente_letter(): #checkt of gemeente bestaat
    print("geef letters waarmee de gemeente naam begint ")
    letter_invoer = input()
    letter = letter_invoer.capitalize()
    gemeente_namen = dtf.iloc[:, 0]
    mogelijke_naam_gemeente = list(gemeente_namen)
    lijstje_gemeente = [i for i in mogelijke_naam_gemeente if i.startswith(letter)]
    for i in range(len(lijstje_gemeente)):
        print(gemeente_top(lijstje_gemeente[i],1))

def start():
    while True:
        print("typ 1 om te zien in welke gemeente een ingevoerde partij stemmen heeft gehad \ntyp 2 om top 3 partijen met aantal stemmen per ingevoerde gemeente te zien\nTyp 3 om alle gemeente met [letters] waarbij de grootste partij genoemd wordt.")
        print("Typ 4 om een gemeente in te voeren en daarbij de partijen te laten zien die 0 of geen stem data hebben")
        print("typ quit om te stoppen")
        invoer=input()
        if invoer == "1":
            print(f'{regio_codes(partij_checker())}')
        elif invoer == "2":
            print(gemeente_top(gemeente_checker(),3))
        elif invoer == "3":
            gemeente_letter()
        elif invoer == "4":
            gemeente_bottom(gemeente_checker())
        elif invoer == 'quit':
            print('programma gestopt')
            break
        else:
            print("je hebt een fout gemaakt!")

start()


# 4. een overzicht per OudeRegioNaam met op STEDEN GESORTEERD met alleen de naam van de GROOTSTE PARTIJ per regionaam GEGROEPEERD op winnaar
# 5. hoeveel procent een partij van de geldige stemmen in een regio gehaald heeft
# 6. hoeveel procent de coalitie in handen heeft per stad
# 7. het gemiddelde aantal kiesgerechtigde in steden die een d in de naam hebben
