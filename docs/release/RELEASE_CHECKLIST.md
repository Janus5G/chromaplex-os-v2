# Release Checklist

## Package integrity

- [ ] JSON validates with `python -m json.tool chromaplex_os_desktop_ide_release_package.json`
- [ ] `python unpack_chromaplex.py chromaplex_os_desktop_ide_release_package.json chromaplex-os-desktop-ide-release` succeeds
- [ ] README, FAQ and release notes are present
- [ ] docs/contracts/ contains all required contracts
- [ ] docs/specialist_handoff/ contains routing and open questions
- [ ] No layer imports renderer from VM/storage/compiler
- [ ] No physical hardware implementation is mixed into simulation modules

## Architecture gates

- [ ] Eventbus API approved
- [ ] Coordinate model approved
- [ ] Sparse state API approved
- [ ] Renderer snapshot/diff schema approved
- [ ] VM instrumentation hook map approved
- [ ] Source-to-voxel trace schema approved
- [ ] Simulated telemetry schema approved
- [ ] Physics/material review completed
