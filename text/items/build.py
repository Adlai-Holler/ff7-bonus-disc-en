import json, sys
sys.path.insert(0, '.')
from gen import DATA
import wep, arm, acc, etc, mat
print({k: len(v) for k, v in DATA.items()})
json.dump({str(k): v for k, v in DATA.items()}, open('items.json', 'w'), ensure_ascii=False, indent=0)
