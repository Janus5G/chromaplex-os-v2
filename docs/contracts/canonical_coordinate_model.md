# Contract: Canonical Coordinate Model

## Formål

Alle lag bruger samme koordinatmodel, så VM, storage, hardware telemetry og renderer ikke divergerer.

## Canonical voxel coordinate

```json
{
  "x": 0,
  "y": 0,
  "z": 0,
  "unit": "voxel",
  "space": "crystal.logical",
  "bounds": {
    "x": [0, 1023],
    "y": [0, 1023],
    "z": [0, 1023]
  }
}
```

## Physical coordinate extension

```json
{
  "x_um": 0.0,
  "y_um": 0.0,
  "z_um": 0.0,
  "space": "crystal.physical",
  "calibration_id": "sim-default"
}
```

## Rules

- Logical coordinates are integer voxels.
- Physical coordinates are calibration-dependent and must not replace logical coordinates.
- Renderer may transform coordinates for camera/view only.
- Hardware drivers must accept canonical logical coordinate plus calibration, never arbitrary UI coordinates.
- Storage keys must use `(x, y, z)` plus wavelength/channel.

## Specialist handoff

- Storage specialist validates sparse key format.
- Hardware specialist defines calibration transforms.
- Renderer specialist defines view-space transforms separately.
