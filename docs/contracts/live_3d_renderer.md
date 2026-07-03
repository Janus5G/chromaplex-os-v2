# Contract: Live 3D Renderer

## Formål

Renderer viser live 3D crystal state uden at eje runtime truth.

## Renderer input snapshot

```json
{
  "schema_version": "1.0",
  "runtime_id": "session-id",
  "sequence": 0,
  "bounds": {"x": [0, 1023], "y": [0, 1023], "z": [0, 1023]},
  "voxels": [
    {
      "x": 5,
      "y": 5,
      "z": 5,
      "channels": [
        {"name": "GREEN", "wavelength_nm": 532, "intensity": 0.7, "encoded_value": 1234567}
      ]
    }
  ],
  "laser": {
    "x": 5,
    "y": 5,
    "z": 5,
    "wavelength_nm": 532,
    "power": 50,
    "mode": "simulated"
  }
}
```

## Renderer output

Renderer may emit:
- renderer.snapshot.ready
- renderer.frame.rendered
- renderer.error

Renderer must not emit:
- crystal.voxel.written
- vm.step.completed
- hardware.write_pulse

## Performance target

- Accept event diffs for incremental update.
- Accept full snapshot for recovery/resync.
- Do not block VM execution loop.
