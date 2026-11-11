# FF7 Bonus Disc — English Translation

An English fan translation of the **Final Fantasy VII International "Perfect Guide"** — the Japan-only fourth disc (SLPS-01060).

The patch covers:
- the menus and labels
- the item, materia and shop pages
- the world map and field screens, including close-up captions and tooltips
- the monster, summon and character data files

## Using the patch

1. You need your own copy of the original disc as a BIN/CUE rip.
2. Download `FF7PG_English_Patcher.exe` from the [Releases](../../releases) page.
3. Run the patcher and pick your `.cue` (or Track 1 `.bin`).
4. It writes `Final Fantasy VII International (Perfect Guide) [English].bin/.cue` next to the original. Your files are not modified.

The patcher checks the MD5 of the source and of the result, so a bad or different rip is rejected rather than half-patched.

### Extras in the English version
- **Tooltips:** press △ on item pages and on field close-ups for English notes.
- **Sparkles:** press **Select** on field screens to make clickable objects sparkle.
- **Sorting:** the monster list sorts A–Z by English name, and areas are listed alphabetically.

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

No game files (EXE, archives, images, audio, video) are included. Everything is built from your own disc.

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
