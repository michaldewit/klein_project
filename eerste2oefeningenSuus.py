#1. Nu willen we een naam invoeren Bijvoorbeeld VVD
# en dan zien we in welke regiocodes hij stemmen heeft gehad Ook voor Volt.
# Dus we komen zo te weten in hoeveel regiocodes een partij stemmen heeft gekregen

import pandas as pd
df = pd.read_csv(r'C:\Users\suzan\Documents\traineeship\data\Uitslag_alle_gemeenten_TK20210317.csv', sep=';')

partij_namen = list(df.iloc[:, 10:46])

def partij_checker():
    print('Geef de naam de een partij op')
    while True:
        invoer = input()
        if invoer in partij_namen:
            return invoer
        elif invoer == 'stop':
                print('programma stopt ermee doei')
                break
        else:
            print('Deze partij ken ik niet, kies een van de volgende partijen: ')
            print(', '.join(partij_namen))   # print lijst als string met komma en spatie tussen de items

def partij_welstemmen_aantalregios(invoer):
    regiolijst = list(df['RegioNaam'])
    regiocodelijst = list(df['RegioCode'])
    partij_invoer = list(df[invoer])
    df2 = pd.DataFrame(data={'Regio Naam': regiolijst, 'Regio Code': regiocodelijst, 'Partij '+invoer: partij_invoer})

    df3 = df2['Partij '+invoer].isna()
    z=0
    for i, x in df3.iteritems():
        if x == False:
            z += 1
    tekst1 = 'De gekozen partij '+invoer +' heeft stemmen gekregen in ' +str(z) +' regiocodes.'
    return tekst1



#2 gemeente invoeren, top3 partijen met stemmen terugkrijgen

def gemeente_checker():
    print('Geef de naam van de gemeente:')
    gemeente_namen = list(df.iloc[:,0])    # lijst met gemeentes
    while True:
        invoer2 = input()
        if invoer2 in gemeente_namen:
            return invoer2
        elif invoer2 == 'stop':
            print('programma stopt')
            break
        else:
            print('Deze gemeente ken ik niet, kies een van de volgende gemeenten: ')
            print(', '.join(gemeente_namen))


def top3_partijen_pergemeente(invoer2):
    zoek_gemeente = (df[df['RegioNaam'] == invoer2])  #waar invoer gelijk is aan een veld in kolom regionaam
    zoek_gemeente2 = zoek_gemeente.iloc[:,10:]
    serie = zoek_gemeente2.squeeze()   #.squeeze maakt er een series van
    df6 = serie.sort_values(ascending=False)
    newline = '\n'
    tekst2 = f'De top 3 partijen in gemeente {invoer2} zijn, met aantal stemmen: {newline}{df6.head(3)}'
    return tekst2


# voer een letter in, gemeentes die hiermee beginnen weergeven met de partij die het grootste is.

def grootstepartij_pergemeente_letter():
    print('Voer begin letter van een gemeente in:')
    letter_input = input()
    letter = letter_input.capitalize()
    gemeente_namen = list(df.iloc[:, 0])
    for i in gemeente_namen:
        if i.startswith(letter):
            print('De grootste partij in gemeente '+ i + ' is, met aantal stemmen:')
            zoek_gemeente = (df[df['RegioNaam'] == i])
            zoek_gemeente2 = zoek_gemeente.iloc[:, 10:]
            serie = zoek_gemeente2.squeeze()
            df6 = serie.sort_values(ascending=False)
            print(df6.head(1))
            print(' ')

# gemeente invoeren; welke partijen hebben 0 stemmen. Welke partijen hebben geen stemdata.

def nul_en_null_partijen_pergemeente(invoer2):
    zoek_gemeente = (df[df['RegioNaam'] == invoer2])  #waar invoer gelijk is aan een veld in kolom regionaam
    zoek_gemeente2 = zoek_gemeente.iloc[:,10:]
    serie = zoek_gemeente2.squeeze()   #.squeeze maakt er een series van
    print('Deze partijen hebben nul stemmen gekregen in ' +invoer2+ ':')
    for i, x in serie.iteritems():
        if x == 0:
            print(i)
    serie2 = serie.isna()
    print('\nDeze partijen hebben geen stemdata in ' +invoer2+ ':')
    for i, x in serie2.iteritems():
        if x == True:
            print(i)





keuze_menu = ('\nKies 0 om te stoppen'
          '\nKies 1 om een partij in te voeren en te zien in hoeveel regiocodes deze partij stemmen heeft gehad'
          '\nKies 2 om een gemeente in te voeren en de top 3 partijen te zien'
          '\nKies 3 om een begin letter van een gemeente in te voeren en de grootste partij in die gemeenten te zien'
          '\nKies 4 om een gemeente in te voeren en te zien welke partijen hier 0 stemmen hebben '
              'en welke partijen hier geen stemdata hebben')

def start():
    print('Hier volgt een keuze menu' + keuze_menu)
    while True:
        keuze = int(input())
        if keuze == 1:
            print(partij_welstemmen_aantalregios(partij_checker()))
        elif keuze == 2:
            print(top3_partijen_pergemeente(gemeente_checker()))
        elif keuze == 0:
            print('programma sluit af')
            break
        elif keuze == 3:
            print(grootstepartij_pergemeente_letter())
        elif keuze == 4:
            print(nul_en_null_partijen_pergemeente(gemeente_checker()))
        else:
            print('maak een andere keuze'+keuze_menu)
start()

