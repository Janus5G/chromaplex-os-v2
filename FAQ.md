# FAQ: Presse & Tekniske Spørgsmål

Dette dokument er oprettet for at besvare de oftest stillede spørgsmål fra pressen, udviklere og tech-entusiaster. Da jeg i øjeblikket er dybt fokuseret på udviklingen af en ny local-first søgemaskine, er min tid til interviews og direkte kontakt desværre meget begrænset.

### Hvad er ChromaPlex OS helt præcist?
Det er et domænespecifikt programmeringssprog (DSL) og en komplet software-stack designet til at styre laser-baseret læsning og skrivning i 3D-krystaller (*fused silica*)[cite: 1]. Pakken indeholder en virtuel maskine, en CPL-compiler (højniveau) og en CPA-assembler (lavniveau)[cite: 1].

### Er dette et fysisk hardware-produkt?
Nej, dette er det software-mæssige fundament. Det er det "maskinrum", der beviser, at vi programmeringsmæssigt kan udnytte krystallernes potentiale gennem præcis voxel-adressering i 3D (x, y, z koordinater)[cite: 1]. Hardware-abstraktionen er simuleret via systemets `hardware.py` modul[cite: 1].

### Hvordan adskiller teknologien sig fra traditionel SSD-lagring?
Vi benytter 5 uafhængige laserbølgelængder (350nm UV, 405nm Violet, 473nm Blå, 532nm Grøn og 650nm Rød)[cite: 1]. Det betyder, at vi via vinkel- og bølgelængdemultipleksing kan gemme 5 forskellige datapunkter i præcis samme fysiske koordinat uden data-korruption[cite: 1].

### Hvordan fungerer datakomprimeringen?
Systemet benytter en algoritme til eksponentiel datakomprimering[cite: 1]. I stedet for at skrive massive rå data-strenge, kodes og gemmes tal matematisk som $2^e + \text{rest}$ i et 32-bit pakket format[cite: 1]. Dette reducerer den fysiske plads, der kræves per datablok markant.

### Hvordan opstod idéen til ChromaPlex og den eksponentielle kodning?
Konceptet med at bruge eksponentiel kodning (at opløfte i potens) på maskinsprogsniveau har været kendt i årevis, men det har hidtil manglet en reel praktisk anvendelse. Konventionelle lagringsmedier er strengt bundet til det binære system (0 og 1), hvor 8 bits udgør 1 byte (svarende til ét standard ASCII-tegn, mens specialtegn som æ, ø og å kræver 2-4 bytes). 

For at bryde disse binære lænker udfordrede jeg en avanceret AI til at co-udvikle et programmeringssprog, der kunne koble den matematiske komprimering direkte sammen med 5D optisk lagring. AI'en var indledningsvist meget skeptisk. Tidligere fysiske tests med krystallagring har nemlig kæmpet med problemer som massiv varmeudvikling, når data brændes ind i glasset. 

Gennembruddet – og fundamentet for ChromaPlex – opstod, da jeg foreslog et skift i den fysiske tilgang til problemet: I stedet for at bruge én enkelt, kraftig laserstråle (som i hidtidige eksperimenter), bruger vi lyset til at flytte dataene og anvender *flere* parallelle laserstråler til skrivningen. Denne fordeling af energien over flere bølgelængder løser problemet med varmeudvikling og åbner samtidig døren for den massive vinkelmultipleksing, som systemet benytter.

### Hvordan kan jeg som journalist eller udvikler teste det?
Du behøver ikke være programmør for at se systemet i aktion:
1. **For alle:** Du kan afprøve de teoretiske principper interaktivt via vores [live 3D-simulator i browseren](https://Janus5G.github.io/chromaplex-os-compiler/).
2. **For udviklere:** Hele systemet kan klones og installeres lokalt i miljøer med Python 3.9+ via kommandoen `pip install -e .`[cite: 1, 2].

### Hvorfor er projektet gjort open-source?
Formålet er at flytte 5D optisk datalagring fra abstrakt deep-tech teori til noget, som udviklermiljøet kan validere, eksperimentere med og bygge videre på. 

Det er desuden for dyrt at hyre eksperter til at videreudvikle teknologien udelukkende med profit for øje – især når et lagringsmedie som dette kan være så afgørende netop nu, hvor strømslugende datacentre skyder op overalt med enorme omkostninger for både miljøet og de globale strømpriser.

### Kan jeg få et interview eller en uddybende kommentar?
Som nævnt arbejder jeg i øjeblikket på fuld tid med arkitekturen til en ny dansk, local-first søgemaskine. Jeg lader kildekoden, dokumentationen og 3D-simulatoren tale for sig selv, og har derfor ikke mulighed for at stille op til telefoniske interviews.

Tekniske spørgsmål, der *ikke* er dækket af dokumentationen eller kildekoden, kan i særlige tilfælde rettes skriftligt, men forvent længere svartider.
