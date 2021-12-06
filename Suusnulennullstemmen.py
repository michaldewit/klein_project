import pandas as pd
df = pd.read_csv(r'C:\Users\suzan\Documents\traineeship\data\Uitslag_alle_gemeenten_TK20210317.csv', sep=';')

# print(df.loc[4, 'VVD':'De Groenen'])

df2 = df[['RegioNaam', 'VVD', 'D66', 'PVV (Partij voor de Vrijheid)', 'CDA', 'SP (Socialistische Partij)',
          'Partij van de Arbeid (P.v.d.A.)', 'GROENLINKS', 'Forum voor Democratie', 'Partij voor de Dieren',
          'ChristenUnie', 'Volt', 'JA21', 'Staatkundig Gereformeerde Partij (SGP)', 'DENK', '50PLUS', 'BBB',
          'BIJ1', 'CODE ORANJE', 'NIDA', 'Splinter', 'Piratenpartij', 'JONG', 'Trots op Nederland (TROTS)',
          'Lijst Henk Krol', 'NLBeter', 'Blanco (Zeven, A.J.L.B.)', 'LP (Libertaire Partij)', 'OPRECHT', 'JEZUS LEEFT',
          'DE FEESTPARTIJ (DFP)', 'U-Buntu Connected Front', 'Vrij en Sociaal Nederland', 'Partij van de Eenheid',
          'Wij zijn Nederland', 'Partij voor de Republiek', 'Modern Nederland', 'De Groenen']]  # dit is een dataframe

# print(df2)

invoer = int(input())  # je moet nu een getal invullen als invoer

regionaam_invoer = df2.loc[invoer, 'RegioNaam']  # de regio die bij het ingevoerde nummer hoort
print('Regionaam: ' + regionaam_invoer)

df3 = df2.loc[invoer, 'VVD':'De Groenen']
# dit is nu een series, geeft de partijen en het aantal stemmen van deze regio
# print(df3)

print('\nDeze partijen hebben 0 stemmen gekregen in '+regionaam_invoer + ':')
for i, x in df3.iteritems():
    if x == 0:
        print(i)
# i is hier de index(partijen) van de series en x zijn de items(aantal stemmen)

series1 = df3.isna()

print('\nDeze partijen hebben geen steminformatie in '+regionaam_invoer + ':')
for i, x in series1.iteritems():
    if x == True:
        print(i)
