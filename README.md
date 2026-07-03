# ChromaPlex OS Compiler Toolchain

Velkommen til maskinrummet for fremtidens optiske datalagring. Dette repository indeholder den fuldt eksekverbare software-stack for ChromaPlex OS – et sprog bygget til 5D-datalagring i glaskrystaller (*fused silica*). 

Her finder du den komplette virtuelle maskine (VM), CPA-assembleren (ChromaPlex Assembly) og CPL-compileren. Det er her, de teoretiske principper om massiv parallelitet, eksponentiel datakomprimering og vinkelmultipleksing bliver omsat til reel, testbar kode.

🔗 **[Hovedprojekt: Se selve ChromaPlex programmeringssproget og kildekoden her](https://github.com/Janus5G/chromaplex-os)**

👉 **[Forstå fysikken og arkitekturen: Læs den fulde ChromaPlex v2.0 specifikation her](https://github.com/Janus5G/ChromaPlex-v2.0-Specification-Architecture-Documentation)**

🎮 **[Prøv 3D Simulatoren direkte i browseren her](https://Janus5G.github.io/chromaplex-os-compiler/)**

## ℹ️ **[Er du fra pressen? Læs vores FAQ her for hurtige svar.](FAQ.md)**

---
### Installation og test
For at trække projektet ned og køre det lokalt:

```bash
git clone [https://github.com/Janus5G/chromaplex-os-compiler.git](https://github.com/Janus5G/chromaplex-os-compiler.git)
cd chromaplex-os-compiler
pip install -e .
# ChromaPlex OS

ChromaPlex OS er et domænespecifikt sprog (DSL) designet til at styre laser-baseret læsning/skrivning i 3D-krystaller (fused silica).

## Funktioner

- **5 laserbølgelængder**: 350nm (UV), 405nm (Violet), 473nm (Blå), 532nm (Grøn), 650nm (Rød)
- **Eksponentiel datakomprimering**: Tal gemmes som 2^e + rest
- **3D voxel-adressering**: Præcis (x,y,z) positionering i krystallen
- **To sprog**: CPA (Assembly) og CPL (Højniveau)

## Installation

Kræver Python 3.9+.

```
pip install -e .
```

## Brug

```
chromaplex compile program.cpl -o program.bin
chromaplex run program.bin
chromaplex run --source program.cpl
```

## Projektstruktur

```
chromaplex_os/
    __init__.py          - Pakkeinitiering
    spec.py              - Specifikationer og konstanter
    assembler.py         - CPA assembler
    compiler.py          - CPL compiler
    vm.py                - Virtual Machine
    storage.py           - Krystalsimulering
    hardware.py          - Laserhardware-simulering
    cli.py               - Kommandolinjeinterface
    visual_demo.py       - Visualiseringsværktøj
    visualization_viewer.py - Visualisering af krystaldata
examples/
    hello.cpl            - Simpelt CPL program
    fibonacci.cpl        - Fibonacci demonstration
    generate_visualization.cpl - Visualiseringsdatagenerator
tests/
    test_assembler.py    - Assembler tests
setup.py                 - Installationsscript
```
