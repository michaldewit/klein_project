import pandas as pd

dtf = pd.read_csv("Uitslagen.csv", sep=";")
# print(dtf)
# print(dtf.columns)
#allecodes = dtf[['RegioCode', 'GeldigeStemmen']][5:12]

#allecodes.info()


# allecodes = dtf
# print(allecodes[3:4])
# print(allecodes)
class print_stemmen():
    # Nu willen we een naam invoeren Bijvoorbeeld VVD
    # en dan zien we in welke regiocodes hij stemmen heeft gehad
    print("geef naam van partij op")
    input_info = input() #verwacht een naam van een partij
    allecodes = dtf.iloc[:, 10:46]
    mogelijke_naam_partij = list(allecodes.columns)
    if input_info in mogelijke_naam_partij:
        print("Naam partij correct")
    elif input_info = "exit":
        print("gestopt")
    else:
        print("naam was verkeerd, hier heb je een lijst van mogelijke keuzes "+ mogelijke_naam_partij)
    #checken of naam inderdaad van een partij is



#print_stemmen()
