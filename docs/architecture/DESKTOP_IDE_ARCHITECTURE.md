# ChromaPlex Desktop IDE Architecture Map

## Runtime truth model

Den samlede sandhed er en stream af runtime-events plus canonical snapshots.

Kilder:
- CPL source
- CPA bytecode
- VM program counter, registers, call stack
- Canonical voxel coordinates
- Sparse crystal channel state
- Simulated laser position, power and wavelength telemetry
- Renderer snapshots
- Source-to-voxel trace records

## Dataflow

```text
CPL Source
   ↓ compiler
CPA Assembly / Bytecode
   ↓ VM instrumentation
RuntimeEvent stream
   ├── SparseCrystalState
   ├── SourceToVoxelTrace
   ├── HardwareTelemetrySim
   └── RendererSnapshot / RendererDiff
```

## Isolation rule

Renderer, simulation og fysisk hardware er separate lag:

```text
compiler ──> assembler ──> vm ──> storage
                           │
                           ├── eventbus ──> desktop_ide
                           │              ├── renderer
                           │              ├── trace panel
                           │              └── telemetry panel
                           │
                           └── hardware abstraction
                                  ├── simulated telemetry
                                  └── physical driver gate
```

## Contract-first policy

Enhver ny funktion til Desktop IDE skal først definere:
1. Input contract
2. Output event/snapshot contract
3. Ownership
4. Test expectations
5. Failure behavior
