import textwrap

def pad(s, cols):
    return s + ' ' * max(0, cols - len(s))

def ctr(s, cols, pre='', post=''):
    l = (cols - len(s)) // 2; r = cols - len(s) - l
    return ' ' * max(l, 0) + pre + s + post + ' ' * max(r, 0)

def wrap(text, width=30, indent=' '):
    return '\\n'.join(indent + l for l in textwrap.wrap(text, width))

def card(title, specs, body, tcols=32, kw=9):
    lines = [ctr(title, tcols, '{~f06}', '{~f0F}').rstrip() + ' ']
    for k, v in specs:
        if not k: lines.append(' ' * (kw + 2) + v); continue
        lines.append(' ' * max(0, kw - len(k)) + '{~f04}' + k + ':{~f0F} ' + v)
    lines[-1] += '{~f0E} '
    lines.append('DATA:{~f0F} ')
    return '\\n'.join(lines) + '\\n' + wrap(body)

def sign(text, width=26):
    """Quoted notice text (signs, plaques)."""
    return '\\n'.join(textwrap.wrap('"' + text + '"', width))

def lbl(a, b):
    """Two-line label: 'A\\n  B'."""
    return a + '\\n  ' + b
