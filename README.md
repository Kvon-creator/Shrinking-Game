# Shrink Spire

A wall-jumping, shrinking platformer. A little fox climbs a spire through four
zones (Ruined Spire, Industrial Forest, Ice & Frost Cliffs, Crystal Cavern).

Open `index.html` in a browser (it loads `assets/atlas.png` and `assets/walls.jpg`).

| Action | Keys | Touch |
| --- | --- | --- |
| Move | ← → / A D | ◀ ▶ |
| Jump, wall-jump | Space / W / ↑ | JUMP |
| Shrink | hold Shift / S / ↓ | TINY (toggle) |
| Respawn, pause, mute | R, P / Esc, M | |

Three hearts per checkpoint; lose them all and the fox faints and wakes at the last flag.

## Art

All character, hazard and wall art comes from the Game Asset Design Document,
whose figures are in `design/`. `tools/build_assets.py` cuts the sprites out of
those figures, packs `assets/atlas.png` and `assets/walls.jpg`, and writes the
sprite index into `index.html`:

```bash
pip install pillow numpy scipy
python3 tools/build_assets.py
```
