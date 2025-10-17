# shelly-energy-diverter
Shelly 3EM Pro and Shelly Plug S in Photovoltaic systems

Script de automatizare realizat in Python pentru monitorizarea consumului electric si controlul dispozitivelor externe in functie de parametri monitorizati. 
Testat intr-o retea monofazica cu Shelly 3EM Pro instalat la intrarea in BMP, scriptul obtine valoarea de Active Energy printr-un request tip REST-API. Avand in vedere ca Shelly 3EM poate masura si energia injectata in retea, se defineste un threshold pentru aceasta valoare (ex. -50Wh) si tot prin intermediul unui request REST-API se porneste/opreste priza Shelly Plug S cu unul sau mai multi consumatori. 
