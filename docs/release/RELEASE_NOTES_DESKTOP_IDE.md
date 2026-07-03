# ChromaPlex OS Desktop IDE Release Notes

Version: 1.1.0-desktop-ide-planning
Dato: 2026-06-06
Release type: Technical planning/release handoff
Scope: Desktop IDE runtime-control architecture, not production implementation.

## Vision

ChromaPlex Desktop IDE skal være et runtime-kontrolsystem, hvor CPL-kode, VM-state,
laserposition, bølgelængdekanaler og 3D-krystalvisning er én samlet sandhed.

Dette release fastlåser arkitekturbeslutninger, grænseflader og specialist-ejerskab for
næste udviklingsfase.

## Prioriteret udviklingsrækkefølge

1. Eventbus og runtime events
2. Canonical coordinate model
3. Sparse crystal state
4. Live 3D renderer contract
5. VM instrumentation
6. Source-to-voxel trace
7. Simulated hardware telemetry
8. Physics/material review
9. Release documentation

## Lagdeling

Følgende lag må ikke blandes:

| Lag | Ansvar | Må afhænge af | Må ikke afhænge af |
|---|---|---|---|
| compiler | CPL parsing/CPA generation | spec, contracts | renderer, hardware |
| vm | bytecode execution, events | spec, runtime events, storage | renderer UI |
| storage | sparse voxel state | coordinate model | laser hardware |
| hardware_sim | simulated telemetry | events, coordinate model | physical hardware drivers |
| hardware_driver | fysisk laser/kamera/SLM adapter | safety contracts | renderer, compiler |
| renderer | 3D/static visualization | renderer contract, event snapshots | VM internals, hardware drivers |
| desktop_ide | orchestration and UI | public contracts only | private module state |

## Beslutninger

- Runtime state skal publiceres via eventbus, ikke læses direkte fra VM-private felter.
- Coordinate model er canonical og deles mellem VM, storage, telemetry og renderer.
- Crystal state skal være sparse/dictionary-baseret for IDE-runtime og store koordinatrum.
- Fysisk hardware må kun tilgås gennem et eksplicit driverlag med safety checks.
- Simuleret hardware telemetry er standard i Desktop IDE indtil fysisk hardware-gate er godkendt.
- Renderer må kun modtage immutable snapshots/diffs, aldrig mutere VM eller storage.
- Source-to-voxel trace er et førsteklasses debug-artefakt.

## Ikke-mål for denne release

- Ingen produktionskode til fysisk laserstyring.
- Ingen direkte hardware access fra VM, compiler eller renderer.
- Ingen endelig UI-implementation.
- Ingen materialefysiske claims uden særskilt physics/material review.

## Release exit-kriterier

- Alle contracts ligger i docs/contracts/.
- Alle specialist-spørgsmål ligger i docs/specialist_handoff/.
- Alle arkitekturbeslutninger er registreret i denne release note.
- Package JSON kan udpakkes med unpack_chromaplex.py uden manuel filoprettelse.
