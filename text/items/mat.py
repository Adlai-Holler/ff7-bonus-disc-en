from gen import *
DATA.setdefault(3, [])
P = DATA[3]
EA = ['Str -1, Mag +1', 'HP -2%, MP +2%']
EB = ['Str -2, Vit -1', 'Mag +2, MDef +1', 'HP -5%, MP +5%']
def ap(levels):
    out = []; cur = []
    for k, v in enumerate(levels, 2):
        cur.append('Lv%d %s' % (k, v))
        if len(cur) == 2: out.append('  '.join(cur)); cur = []
    if cur: out.append('  '.join(cur))
    return out
def M(name, desc, eff, elem, pr, maxsell, levels, found):
    nb = lambda x: x.replace(' ', '\u00a0')
    L = ['{g}' + name, '{w}' + desc]
    # each original pair stays on one line, written compactly like the JP ("HP-2%")
    effs = [nb(e.replace(' -', '-').replace(' +', '+')) for part in eff for e in part.split(', ')]
    L += found_lines('Effect', [' '.join(effs)])        # wraps under the value column
    L += found_lines('Element', [elem]) + found_lines('Price', [price(pr)]) + found_lines('Max sell', ['%s gil' % maxsell])
    L += found_lines('AP', [' '.join(nb('Lv%d %s' % (k, v)) for k, v in enumerate(levels, 2))] if levels else ['None'])
    L += ['{g}Found', '{w}' + ', '.join(found)]                        # heading, then full-width text (as in the JP)
    return '\n'.join(L)
def mg(spell): return 'Use %s magic' % spell
S7, S5, WM, FC, CS, MD = 'Sector 7', 'Sector 5', 'Wall Market', 'Fort Condor', 'Costa del Sol', 'Mideel'
UJ, LJ, GG, KL = 'Upper Junon', 'Lower Junon', 'Gongaga', 'Kalm'
ELEM = [S7, S5, WM, FC, LJ, CS, MD]
P += [
 M('Restore', mg('Restore'), EA, 'None', 750, 52500, [2500, 17000, 25000, 40000], [S7, S5, WM, FC, CS, MD, 'Reactor No. 1']),
 M('Heal', mg('Heal'), EA, 'None', 1500, 105000, [12000, 52000, 60000], [KL, UJ, CS, GG]),
 M('Revive', mg('Revive'), EB, 'None', 3000, 105000, [45000, 55000], [UJ, CS, GG]),
 M('Fire', mg('Fire'), EA, 'Fire', 600, 42000, [2000, 18000, 35000], ELEM + ["Red XIII's starting gear"]),
 M('Ice', mg('Ice'), EA, 'Ice', 600, 42000, [2000, 18000, 35000], ELEM + ["Cloud's starting gear"]),
 M('Lightning', mg('Lightning'), EA, 'Lightning', 600, 42000, [2000, 18000, 35000], ELEM + ["Cloud's starting gear"]),
 M('Earth', mg('Earth'), EA, 'Earth', 1500, 105000, [6000, 22000, 40000], [KL, LJ, CS + ' (after Meteor)']),
 M('Poison', mg('Poison'), EA, 'Poison', 1500, 105000, [5000, 20000, 38000], [LJ, CS + ' (after Meteor)', 'Shinra Building']),
 M('Gravity', mg('Gravity'), EA, 'Gravity', 8000, 560000, [10000, 20000, 40000], [CS + ' (after Meteor)', MD, 'Defeat Gi Nattak']),
 M('Seal', mg('Seal'), EA, 'None', 3000, 210000, [10000, 20000], [UJ, CS]),
 M('Mystify', mg('Mystify'), EA, 'None', 6000, 420000, [12000, 25000], [GG, 'Cosmo Canyon']),
 M('Transform', mg('Transform'), EA, 'None', 5000, 350000, [8000, 24000], ['North Corel', GG, 'Cosmo Canyon', MD, 'Mt. Corel', "Cait Sith's starting gear"]),
 M('Time', mg('Time'), EB, 'None', 6000, 420000, [8000, 20000, 42000], [GG, 'Rocket Town']),
 M('Barrier', mg('Barrier'), EB, 'None', 10000, 700000, [5000, 15000, 30000, 45000], ['Rocket Town']),
 M('Destruct', mg('Destruct'), EB, 'None', 9000, 630000, [6000, 10000, 45000], [FC + ' (after Meteor)', MD, 'Shinra Mansion']),
 M('Comet', mg('Comet'), EB, 'None', 0, 1400000, [12000, 60000], ['Forgotten Capital']),
 M('Contain', mg('Contain'), ['Str -4, Vit -2', 'Mag +4, MDef +2', 'HP -10%, MP +10%'], 'None', 0, 1,
   [5000, 10000, 15000, 60000], ["Mideel's white chocobo"]),
 M('Exit', mg('Exit'), EA, 'None', 10000, 700000, [10000, 30000], ['Rocket Town']),
]
EC = ['Str -4, Vit -2', 'Mag +4, MDef +2', 'HP -10%, MP +10%']
P += [
 M('Full Cure', 'Use Full Cure', EC, 'None', 0, 1, [3000, 100000], ['Cosmo Canyon (after Meteor)']),
 M('Shield', 'Use Shield', EC, 'None', 0, 1, [10000, 100000], ['Northern Crater']),
 M('Ultima', 'Use Ultima', EC, 'None', 0, 1, [5000, 100000], ['North Corel coal train']),
 M('Master Magic', 'Use all Magic', ['None'], 'None', 0, 1, None, ['Cosmo Canyon observatory']),
]
NONE = ['None']
def S(name, desc, pr, maxsell, levels, found): return M(name, desc, NONE, 'None', pr, maxsell, levels, found)
P += [
 S('All', 'Spreads paired Magic to all targets', 20000, 1400000, [1500, 6000, 18000, 35000],
   [S7, 'Shinra Building', 'Cargo ship', "Red XIII's starting gear"]),
 S('Elemental', "Adds paired Materia's element to weapon or armor", 0, 1, [10000, 40000, 80000],
   ['Nibel Mountains', 'Shinra Building', 'Nibelheim']),
 S('Added Effect', "Adds paired Materia's status to weapon or armor", 0, 1, [100000], ['Cave of the Gi']),
 S('HP Absorb', 'Recovers HP when paired Materia deals damage', 0, 1, [100000], ['Wutai']),
 S('MP Absorb', 'Recovers MP when paired Materia deals damage', 0, 1, [100000], ['Wutai']),
 S('MP Turbo', 'Paired Magic costs more MP but hits harder', 0, 1, [10000, 30000, 60000, 120000], ['Whirlwind Maze']),
 S('Added Cut', 'Also attacks after using paired Materia', 0, 1, [200000], ['Great Glacier']),
 S('Steal as well', 'Also steals after using paired Materia', 0, 1, [200000], ['Wutai']),
 S('Sneak Attack', 'Paired Materia activates at battle start', 0, 1, [20000, 60000, 100000, 150000], ['Chocobo race prize']),
 S('Quadra Magic', 'Casts paired Magic or Summon four times', 0, 1, [40000, 80000, 120000, 200000], ['Materia Cave']),
 S('Magic Counter', 'Casts paired Magic when attacked', 0, 1, [20000, 40000, 80000, 300000], ['Chocobo race prize']),
 S('Command Counter', 'Uses paired Command when attacked', 0, 1, [20000, 40000, 60000, 100000], ['Northern Crater']),
 S('Final Attack', 'Paired Materia activates right after KO', 0, 1, [20000, 40000, 80000, 160000], ['Battle Square special battle prize']),
]
def C(name, desc, eff, pr, maxsell, levels, found): return M(name, desc, eff, 'None', pr, maxsell, levels, found)
P += [
 C('Steal', 'Use the Steal command', ['Dex +2'], 1200, 84000, [40000, 50000], [KL, 'Underground sewers']),
 C('Sense', 'Use the Sense command', NONE, 1000, 70000, [40000], [KL, 'Sector 6', "Red XIII's starting gear"]),
 C('Throw', 'Use the Throw command', ['Vit +1'], 10000, 700000, [45000, 60000],
   [FC + ' (after Meteor)', 'Rocket Town (after Meteor)', "Yuffie's starting gear"]),
 C('Morph', 'Use the Morph command', NONE, 0, 1, [100000], ['Ancient Temple']),
 C('Deathblow', 'Use the Deathblow command', ['Luck +1'], 10000, 700000, [40000],
   [FC + ' (after Meteor)', 'Rocket Town (after Meteor)', GG]),
 C('Manipulate', 'Use the Manipulate command', NONE, 10000, 700000, [40000],
   [FC + ' (after Meteor)', 'Rocket Town (after Meteor)', "Cait Sith's starting gear"]),
 C('Mime', 'Use the Mime command', NONE, 0, 1, [100000], ['Materia Cave']),
 C('Enemy Skill', 'Use learned enemy skills', NONE, 0, 1, None,
   [UJ, 'Forgotten Capital', "Chocobo Sage's house", 'Shinra Building']),
 C('Slash-All', 'Attack hits all enemies', NONE, 0, 1, [130000, 150000], ['Ancient Forest']),
 C('Double Cut', 'Attack strikes several times', ['Dex +2'], 0, 1, [100000, 150000], ['Gelnika (sunken plane)']),
 C('W-Magic', 'Cast Magic twice in one turn', NONE, 0, 1, [250000], ['Battle Square prize']),
 C('W-Summon', 'Summon twice in one turn', NONE, 0, 1, [250000], ['Battle Square prize']),
 C('W-Item', 'Use two items in one turn', NONE, 0, 1, [250000], ['Sector 8 (after the cannon)']),
 C('Master Command', 'Use all Commands', NONE, 0, 1, None, ['Cosmo Canyon observatory']),
]
def I(name, desc, eff, pr, maxsell, levels, found): return M(name, desc, eff, 'None', pr, maxsell, levels, found)
BS = 'Battle Square prize'
CR = 'Chocobo race prize'
P += [
 I('HP Plus', 'Raises max HP', NONE, 8000, 560000, [10000, 20000, 30000, 50000], ['Cosmo Canyon', MD, 'Junon Harbor']),
 I('MP Plus', 'Raises max MP', NONE, 8000, 560000, [10000, 20000, 30000, 50000], ['Cosmo Canyon', MD]),
 I('HP<->MP', 'Swaps max HP and max MP', NONE, 0, 1, [80000], ['Materia Cave']),
 I('Speed Plus', 'Raises Dexterity', NONE, 0, 1400000, [15000, 30000, 60000, 100000], [BS]),
 I('Magic Plus', 'Raises Magic', NONE, 0, 1400000, [10000, 20000, 30000, 50000], ['Coral Valley']),
 I('Luck Plus', 'Raises Luck', NONE, 0, 1050000, [15000, 30000, 60000, 100000], ['Ancient Temple']),
 I('Gil Plus', 'More gil after battle', ['Luck +1'], 0, 1, [80000, 150000], ['Gold Saucer']),
 I('Exp Plus', 'More EXP after battle', ['Luck +1'], 0, 1, [60000, 150000], ['Gold Saucer']),
 I('Long Range', 'Full damage from the back row', NONE, 0, 1, [80000], ['Mythril Mine']),
 I('Pre-Emptive', 'Raises first-strike chance', ['Dex +2'], 0, 1, [8000, 20000, 40000, 80000], [BS]),
 I('Enemy Away', 'Fewer random battles', ['Luck +1'], 0, 1, [10000, 50000], [CR]),
 I('Enemy Lure', 'More random battles', ['Luck -1'], 0, 1, [10000, 50000], [BS]),
 I('Chocobo Lure', 'Lets you meet chocobos', ['Luck +1'], 2000, 1, [3000, 10000, 30000], ['Chocobo Farm']),
 I('Cover', 'Protects allies from attacks', ['Vit +1'], 1000, 70000, [2000, 10000, 25000, 40000], [WM, "Aeris's house flower bed"]),
 I('Counter Attack', 'Counterattacks when damaged', NONE, 0, 1, [10000, 20000, 50000, 100000], ['Nibel Mountains', CR]),
 I('Mega All', 'Attack, Magic and Commands hit all', NONE, 0, 1, [20000, 40000, 80000, 160000], ['Northern Crater']),
]
def SM(name, attack, eff, elem, levels, found): return M(name, 'Summons ' + attack, eff, elem, 0, 1, levels, found)
E1 = ['Mag +1', 'HP -2%, MP +2%']
E2 = ['Mag +1, MDef +1', 'HP -5%, MP +5%']
E3 = ['Mag +2, MDef +2', 'HP -10%, MP +10%']
E4 = ['Mag +4, MDef +4', 'HP -10%, MP +15%']
P += [
 SM('Choco/Mog', 'Deathblow!! / Fat Chocobo', E1, 'None', [2000, 14000, 25000, 35000], ['Chocobo Farm chocobo']),
 SM('Shiva', 'Diamond Dust', E1, 'Ice', [4000, 15000, 30000, 50000], ['Defeat Bottomswell']),
 SM('Ifrit', 'Hellfire', E1, 'Fire', [5000, 20000, 35000, 60000], ['Defeat Jenova-BIRTH']),
 SM('Ramuh', 'Judgment Bolt', E1, 'Lightning', [10000, 25000, 50000, 70000], ['Gold Saucer chocobo jockeys\' room']),
 SM('Titan', 'Anger of the Land', E1, 'Earth', [15000, 30000, 60000, 80000], ['Gongaga Reactor']),
 SM('Odin', 'Steel Bladed Sword / Gunge Lance', E2, 'None', [16000, 32000, 65000, 90000], ['Shinra Mansion 2F safe']),
 SM('Leviathan', 'Tidal Wave', E2, 'Water', [18000, 38000, 70000, 100000], ['Wutai Pagoda']),
 SM('Bahamut', 'Mega Flare', E2, 'None', [20000, 50000, 80000, 120000], ['Ancient Temple mural room']),
 SM('Kujata', 'Tetra-Disaster', E2, 'None', [22000, 60000, 90000, 140000], ['Sleeping Forest']),
 SM('Alexander', 'Judgment', ['Mag +1, MDef +1', 'HP -5%, MP +5%'], 'Holy', [25000, 65000, 100000, 150000], ['Great Glacier, Snow Woman\'s valley']),
 SM('Phoenix', 'Phoenix Flame', E3, 'Fire', [28000, 70000, 120000, 180000], [FC]),
 SM('Neo Bahamut', 'Giga Flare', E3, 'None', [30000, 80000, 140000, 200000], ['Whirlwind Maze']),
 SM('Hades', 'Black Cauldron', E4, 'None', [35000, 120000, 150000, 250000], ['Gelnika (sunken plane)']),
 SM('Typhon', 'Disintegration', E4, 'None', [35000, 120000, 150000, 250000], ['Ancient Forest']),
 SM('Bahamut ZERO', 'Tera Flare', E4, 'None', [35000, 120000, 120000, 250000], ['Cosmo Canyon observatory']),
 SM('Knights of Round', 'Ultimate End', ['Mag +8, MDef +8', 'HP -10%, MP +20%'], 'None', [50000, 200000, 300000, 500000], ['Round Island Materia Cave']),
 G('Master Summon', [('Element', 'None'), ('Price', 'Not sold'), ('Max sell', '1 gil')],
   note='Lets you use all Summons. Master every Summon Materia and bring them to the Huge Materia at Cosmo Canyon.'),
]
