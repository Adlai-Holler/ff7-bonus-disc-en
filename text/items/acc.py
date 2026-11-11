from gen import *
DATA.setdefault(2, [])
P = DATA[2]
def C(name, pr, eff, found=None, shops=None, note=None):
    return G(name, [('Price', price(pr)), ('Effect', eff)], found, shops, note)
P += [
 C('Power Wrist',7500,['Strength +10'],['Rocket Town','Defeat Bottomswell']),
 C('Protect Vest',3500,['Vitality +10'],['Rocket Town','Defeat Rufus']),
 C('Earring',7500,['Magic +10'],['Rocket Town']),
 C('Talisman',4000,['Spirit +10'],['Rocket Town','Gongaga','Defeat Sample: H0512']),
]
P += [
 C('Choco Feather',10000,['Dexterity +10'],['Wutai']),
 C('Amulet',10000,['Luck +10'],['Mideel']),
 C('Champion Belt',0,['Strength +30','Vitality +30'],['Battle Square prize']),
 C('Poison Ring',0,['Absorbs Poison;','prevents Poison'],['Whirlwind Maze']),
 C('Tough Ring',0,['Vitality +50','Spirit +50']),
 C('Circlet',0,['Magic +30','Spirit +30']),
 C('Star Pendant',4000,['Prevents Poison'],['Gongaga','Shinra HQ','Mt. Corel','Cosmo Canyon','Defeat Motor Ball']),
 C('Silver Glasses',3000,['Prevents Darkness'],['Lower Junon','Gongaga']),
 C('Headband',3000,['Prevents Sleep'],['Lower Junon','Gongaga']),
]
P += [
 C('Fairy Ring',7000,['Prevents Poison','and Darkness'],['Cave of the Gi','Mideel']),
 C('Jem Ring',7500,['Prevents Paralysis,','Petrify, Slow-numb'],['Nibelheim','Mideel','Defeat Materia Keeper']),
 C('White Cape',5000,['Prevents Frog','and Small'],['Gongaga','Mideel','Defeat Jenova-BIRTH']),
 C('Sprint Shoes',0,['Auto-Haste in battle'],['Chocobo race prize']),
 C('Peace Ring',7500,['Prevents Confuse,','Berserk, Fury, Sadness'],['Rocket Town (after Meteor)','Condor Fort','Defeat Rapps']),
 C('Ribbon',0,['Prevents all ailments'],['Ancient Temple',"Gaea's Cliff"]),
 C('Fire Ring',8000,['Nullifies Fire'],['Costa del Sol','Mideel']),
 C('Ice Ring',8000,['Nullifies Ice'],['Mideel','Defeat Schizo']),
 C('Bolt Ring',8000,['Nullifies Lightning'],["Old man's hut",'Mideel shop']),
]
P += [
 C('Tetra Elemental',0,['Absorbs Fire, Ice,','Lightning and Earth'],['Northern Cave']),
 C('Safety Bit',7500,['Prevents Death, Petrify,','Slow-numb, D. Sentence'],['Rocket Town (after Meteor)','Great Glacier']),
 C('Fury Ring',5000,['Auto-Berserk in battle'],['Gongaga']),
 C('Curse Ring',0,['Str +35, Mag +25','Dex +15, Vit +15','Spr +15, Luck +10'],['Mideel'],note='Auto Death Sentence in battle'),
 C('Protect Ring',0,['Auto Barrier and','MBarrier in battle']),
 C('Cat\'s Bell',0,['Restores HP as you walk'],['Chocobo race prize']),
 C('Reflect Ring',0,['Auto-Reflect in battle'],["Gaea's Cliff",'Defeat Jenova-DEATH']),
 C('Water Ring',0,['Absorbs Water'],['Coral Valley']),
 C('Sneak Glove',129000,['Higher Steal rate'],['Wall Market (after Meteor)']),
]
P += [
 C('HypnoCrown',0,['Higher Manipulate rate'],['Coral Valley']),
]
