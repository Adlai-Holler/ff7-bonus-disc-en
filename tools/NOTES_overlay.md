# Item-page overlay (Nov 4)
- Item viewer code: ~0x80024100-0x80026700. Current item per category: u32 table 0x8009EF38[cat]; cat = gp+3012 (u32).
  Item counts per category: 0x8009EF60[cat]. Pad edge word gp+3648 (0x1000/0x4000 = +/-2 rows, 0x8000/0x2000 = +/-1).
  On change it calls 0x800197a8 then 0x800194b0 (load/show page).
- Page TIM is decoded into a reused buffer (outbuf gp+3936 = 0x8017FE90 during item pages); buffer gets reused after VRAM upload,
  so text appended to the NPK item does NOT survive in RAM.
- RAM 0x800C8E39-0x800F8000 (~180 KB) zero in 6 dumps (world map, field note, 3 item pages, earlier freeze) and not referenced
  as a real address. Plan: extend SLPS_010.60 (t_size) so the EXE image covers ~0x800E9000+ and carries the item text table;
  loaded by BIOS with the EXE. TODO: confirm with dumps from Making Of video, monster viewer, character model screens.
- Next: find per-frame draw for the page screen + box/text draw routine (vehicle card renderer), check △ unused on page screen,
  find the existing "△" prompt graphic on character pages.
## Window library (text boxes) — table 0x8017EED0, 132-byte slots
- open(text) 0x80072738 -> id (s16); rect(id,x,y,w,h[stack+16]) 0x80072D3C (stores x-256,y-120);
  colour 0x80072F28(id,r,g,b,[sp+16]=8 or 4) (vehicle card bg uses (0,0,255,8)? card: 0,255,0 / 0,0,255) ; text rgb 0x80073038(id,191,191,191);
  show 0x80072D00(id) (flag2 |= 2); hide 0x80072CC4(id); close/free 0x80072B44(id); close all 0x80072C28(); 0x80073AD8(id,on) toggles 0x40000000.
- Vehicle card example: 0x80030D00.. (gated by pad bit 0x10 = TRIANGLE), strcpy(0x8017F2F0, cardstr) via BIOS A0:0x19 (0x8003B5C8).
- BIOS stubs: strcpy 0x8003B5C8, memset 0x8003B5F8(A0:2B), strtok-ish 0x8003B628.
- Item page input: jump table @0x80016E24 on mode; item case at 0x80026164: prev = pad&0x8004 (left/L1), next = pad&0x2008 (right/R1),
  calls 0x800194B0 to load page; TRIANGLE (0x10) unused on page screen -> hook here.
- Character page shows a pink "more" triangle + "01/02" counter; FF_SYS.LPK image 4 = "triangle MOVIE PUSH START" sprite.
## Working demo (Nov 4, ovtest12)
- Draw hook: scheduler 0x80059808 (jal 0x8003cd70 -> stubC) draws our window slot via 0x80074E10/0x80074824/0x800731B8 + tdraw(OBJ).
  Page screen does NOT run the Data File render (0x80025498); old stubB hook unused.
- Window layer slot+2 = 1 (draws above page sprite). No wbit(id,1) (that flag = translucent). wcol last arg 8 = blue scheme (4 = green).
- Private text descriptor copy at 0x800E9F00: cols 20, rows = line count (fixes dotted line), texture x=984 y=336 (arrow texture is at x960-984,y384-416).
- All loads followed by nop (R3000 load delay). BSS clear at 0x80018B9C patched to skip 0x800E9000..seg_end.
- Card font lacks + and %: write words. 20 chars/line max, label width 6.
- Build: python3 overlay.py <SLPS alpha3> <out> texts.json   (LAYERTEST/MARK env = debug)
