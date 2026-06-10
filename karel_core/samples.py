# -*- coding: utf-8 -*-
"""Karel core – ukážkové programy."""

EXAMPLES={
"Prázdny/Empty":"""\
# Karel 2010 – program
# Slovak: zaciatok/koniec, dopredu, vlavo, vpravo, dozadu
#   poloz=pred seba, zdvihni=z pred seba, oznac=pod seba
#   opakuj N krat ... koniec
#   kym podmienka rob ... koniec
#   ak podmienka potom ... inak ... koniec
zaciatok
  dopredu
  dopredu
  vlavo
  dopredu
koniec
""",
"Štvorec/Square":"""\
prikaz Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
""",
"Stavanie múru/Build wall":"""\
# Karel stavia múr z tehál pred sebou
zaciatok
  opakuj 4 krat
    poloz
    dopredu
  koniec
koniec
""",
"Zbieranie tehál/Collect":"""\
prikaz ZdvihniVsetko
zaciatok
  kym tehla rob zdvihni koniec
koniec

zaciatok
  kym nie stena rob
    ZdvihniVsetko
    dopredu
  koniec
koniec
""",
"Samba":"""\
prikaz Samba
zaciatok
  vlavo dopredu vpravo dozadu dopredu vpravo
  opakuj 2 krat dopredu vlavo vpravo koniec
  vlavo dozadu dopredu vlavo dopredu vpravo
  Samba
koniec
Zaciatok Samba Koniec
""",
"Valčík/Waltz":"""\
prikaz Valcik
zaciatok
  opakuj 4 krat
    opakuj 2 krat dopredu koniec
    vlavo
  koniec
koniec
zaciatok opakuj 6 krat Valcik koniec koniec
""",
"Označenie trate/Mark path":"""\
zaciatok
  kym nie stena rob oznac dopredu koniec
  oznac
koniec
""",
"Bludisko/Maze":"""\
prikaz Krok
zaciatok
  ak stena potom vlavo inak dopredu koniec
koniec
zaciatok opakuj 80 krat Krok koniec koniec
""",
}


