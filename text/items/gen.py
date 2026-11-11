"""Builds the overlay text JSON from compact item records.
slots: groups separated by spaces, 'o-o' = linked pair, 'o' = single, '' = none"""
import json, sys
def slots(sp):
    if not sp: return 'None'
    return ' '.join('◯━◯' if g == 'o-o' else '◯' for g in sp.split())
def found_lines(label, items):
    out = []
    for i, f in enumerate(items):
        out.append(('{g}%s\t{w}' % label if i == 0 else '\t{w}') + f)
    return out
def W(name, equip, atk, bonus, hit, sl, growth, sell, price, throw, elem, found, shops=None, note=None):
    L = ['{g}' + name, '{g}Equip\t{w}' + equip, '{g}Attack\t{w}%s' % atk]
    if bonus:
        bl = bonus if isinstance(bonus, list) else [bonus]
        L += found_lines('Bonus', bl)
    L += ['{g}Hit\t{w}%s' % hit, '{g}Slots\t{w}' + slots(sl)] + (['{g}Growth\t{w}' + growth] if growth else []) + [
          '{g}Sell\t{w}' + ('Yes' if sell else 'No'), '{g}Price\t{w}' + ('-' if price is None else ('%s gil' % price) if price else 'Not sold'),
          '{g}Throw\t{w}' + ('Yes' if throw else 'No'), '{g}Element\t{w}' + elem]
    if shops: L += found_lines('Shops', shops)
    if found: L += found_lines('Found', found)
    if note: L += ['{g}Note: {w}' + note]          # full-width line, wraps at the left margin
    return '\n'.join(L)
DATA = {0: []}

def G(name, fields, found=None, shops=None, note=None):
    """generic page: fields = [(label, value | [values])]"""
    L = ['{g}' + name]
    for lab, val in fields:
        if val is None: continue
        L += found_lines(lab, val if isinstance(val, list) else [str(val)])
    if shops: L += found_lines('Shops', shops)
    if found: L += found_lines('Found', found)
    if note: L += ['{g}Note: {w}' + note]
    return '\n'.join(L)
def price(p): return '-' if p is None else ('%s gil' % p) if p else 'Not sold'
def yn(v): return 'Yes' if v else 'No'
