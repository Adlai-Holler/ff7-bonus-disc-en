# FF7 Bonus Disc (Perfect Guide) — English Translation
The first-ever (as far as I know) English translation of this gem. Adds in an optional sparkle on clickable items so you don't have to spend all day clicking every inch of the screen. Runs on real PS1s! Part slop -- I used AI but I put a ton of personal work in, too.

## What's in FF7 Perfect Guide?
Look it up, but basically a ton of exclusive environmental detail images, flavor text, and *CG renders of every item and piece of equipment.* High-def inspectable models of all the vehicles in the game including the snowboard. Videos from FF7 pre-production builds. The timeline of Midgar/Shinra/AVALANCHE leading up to the game's opening. CG cutscenes.

| Hype Image | Hype Image |
|:-:|:-:|
| ![10](https://github.com/user-attachments/assets/06536b17-e807-4b0b-8454-4d9bb134a6c9) | ![20](https://github.com/user-attachments/assets/54cea97c-6741-41a3-9f89-a23fafa21702) |
| ![30](https://github.com/user-attachments/assets/67916af1-4764-42d7-b860-88ac7bec12fb) | ![31](https://github.com/user-attachments/assets/85d02658-9e1a-414f-9d1c-4b544a40793e) |
| ![32](https://github.com/user-attachments/assets/370bd536-8398-4ed7-92d5-f8a8bca60ab6) | ![40](https://github.com/user-attachments/assets/7cbe26f6-84d3-4cf3-b019-d7d057246527) |
| ![50](https://github.com/user-attachments/assets/cee8959d-1f5b-4377-8c6e-c93c1941f3cf) | ![60](https://github.com/user-attachments/assets/6cac2c41-b948-41e2-9403-824d5083009e) |
| ![70](https://github.com/user-attachments/assets/fb9e8343-e00f-41dc-9e07-96bf0671429f) | ![80](https://github.com/user-attachments/assets/9b87c811-6885-4d3e-a6e7-c3411d5bce83) |
| ![90](https://github.com/user-attachments/assets/649fb49d-b182-44e5-8a1e-b8d3f46ea607) | ![100](https://github.com/user-attachments/assets/3761eb6c-4ded-4912-9659-a0d53f0547c0) |
| ![110](https://github.com/user-attachments/assets/80a5256e-8fb0-4719-9357-1fe156e88e68) | ![120](https://github.com/user-attachments/assets/6e2c00c3-30a9-4831-ae75-7907427a6029) |
| ![130](https://github.com/user-attachments/assets/83976741-2f59-4677-8e17-0748d88a6d6c) | ![140](https://github.com/user-attachments/assets/e51f1173-17f2-41c5-a0a1-e28fe8c9d026) |
| ![145](https://github.com/user-attachments/assets/93659c11-d4dc-4149-8919-1337c7a1310f) | ![150](https://github.com/user-attachments/assets/3a45c271-336e-442a-aaba-10e9ea328c2c) |
| ![145](https://github.com/user-attachments/assets/7e4ea9cb-b0e2-44f4-8191-cee42990fa2b) | ![150](https://github.com/user-attachments/assets/db81519e-c32a-4ed3-9737-ef1b0045829c) |

## What's translated
- EVERYTHING.
- Menus, labels, and the item, materia, weapon, armor and shop pages
- World map and field screens, including object labels, close-up ("hotspot") image captions
- Characters, summons, vehicles, bestiary

## Extras
- **△** on item pages and field close-ups shows English notes and tooltips.
- **Select** on field screens makes the clickable objects sparkle periodically. Otherwise you get no visual indication or feedback on them.

## Using the patch

1. You need your own copy of the original disc as a BIN/CUE rip.
2. Download `FF7PG_English_Patcher.exe` from the [Releases](../../releases) page.
3. Run the patcher and pick your `.cue` (or Track 1 `.bin`).
4. It writes `Final Fantasy VII International (Perfect Guide) [English].bin/.cue` next to the original. Your files are not modified.

The patcher checks the MD5 of the source and of the result, so a bad or different rip isn't touched.

## Repository layout

| Path | What it is |
|---|---|
| `text/exe_strings.tsv` | Main program text, keyed by EXE offset. Short Japanese strings (names, labels, menu items) are included as-is. Longer passages are given as a CRC32 of the Japanese bytes; the tools check it against your own disc and read the Japanese from there. Run `python3 tools/fill_jp.py <your SLPS_010.60>` to get a copy with every Japanese line filled in, for reviewing the translation side by side. |
| `text/mlist_strings.tsv` | Monster, summon and character data text. |
| `text/items.json`, `text/items/` | Item, materia, weapon and armor page text. |
| `text/tips.json`, `text/items_tips.json` | △ overlay text and field tooltips. |
| `text/captions/` | Text for the redrawn close-up caption bars and scene captions. |
| `tools/` | Python build tools: EXE string insertion, the overlay/hook builder (`overlay2.py`), MLIST (data file) tools, image/caption builders, MIPS disassembler/emulator. |
| `patcher/` | Go source for the patch format (`ffpatch`), `mkpatch` and the Windows patcher. |
| `build/` | Example mkpsxiso project and batch files used to build a test disc. |

## Building from source (outline)

1. Extract the disc with mkpsxiso's `dumpsxiso` to get the original files and the project XML.
2. Insert the program text:
   ```
   LBUDGET=1.01 python3 tools/exe_tool.py insert <original SLPS_010.60> text/exe_strings.tsv SLPS_010.60_alpha 1
   ```
3. Add the overlay, hooks and fixes:
   ```
   python3 tools/overlay2.py SLPS_010.60_alpha SLPS_010.60_ov text/items_tips.json
   ```
4. Build the data files:
   - MLIST: `tools/mlist_tool.py`, then `mlist_sort.py`, `summon_wrap.py` and `hero_fix.py`.
   - FF_TTOWN.NPK: `detail_build.py`, `train_build.py` and `caption_build.py`.
5. Rebuild the disc with mkpsxiso (see `build/`).
6. Make the patch:
   ```
   go run ./patcher/cmd/mkpatch <original.cue> <built.bin> <built.cue> out.ffpatch
   ```

The scripts still contain paths from the development machine; adjust them before running.

## Legal

This is an unofficial fan project. It is not affiliated with or endorsed by Square Enix. Final Fantasy VII and all related names are trademarks of Square Enix. You need your own legally obtained copy of the disc.
