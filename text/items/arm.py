from gen import *
DATA.setdefault(1, [])
P = DATA[1]
def A(name, user, pr, sell, sl, growth, eff, found=None, shops=None, note=None):
    return G(name, [('User', user), ('Price', price(pr)), ('Sell', yn(sell)), ('Slots', slots(sl)),
                    ('Growth', growth if sl else None), ('Effect', eff)], found, shops, note)
P += [
 A('Bronze Bangle','All',0,1,'',None,['Def +8'],["Cloud, Barret, Tifa and Aeris's starting gear"]),
 A('Iron Bangle','All',160,1,'o','Normal',['Def +10','M.Def +2'],None,['Sector 7']),
 A('Titan Bangle','All',280,1,'o o','Normal',['Def +14','M.Def +4','Def% +2'],['Defeat Guard Scorpion'],['Sector 5','Wall Market']),
 A('Mythril Armlet','All',350,1,'o-o','Normal',['Def +18','M.Def +8','Def% +3'],['Defeat Hell House'],['Wall Market','Kalm','Under Junon']),
 A('Carbon Bangle','All',800,1,'o-o o','Normal',['Def +27','M.Def +14','Def% +3'],None,['Costa del Sol','North Corel']),
 A('Silver Armlet','All',1300,1,'o-o o o','Normal',['Def +34','M.Def +22','Def% +4'],['Defeat Dyne'],['Cosmo Canyon']),
 A('Gold Armlet','All',2000,1,'o-o o-o','Normal',['Def +46','M.Def +28','Def% +4'],["Weapon maker's hut"],['Rocket Town']),
 A('Diamond Bangle','All',3200,1,'o-o o-o o','Normal',['Def +57','M.Def +37','Def% +6'],None,['Bone Village']),
 A('Crystal Bangle','All',4800,1,'o-o o-o o-o','Normal',['Def +70','M.Def +45','Def% +8','MDef% +1'],['Snowboard game prize'],['Mideel']),
]
P += [
 A('Platinum Bangle','All',1800,1,'o o','Double',['Def +20','M.Def +12'],['Costa del Sol'],['Junon (after Meteor)']),
 A('Rune Armlet','All',3700,1,'o o o o','Double',['Def +43','Def% +5','M.Def +24'],None,['Bone Village']),
 A('Edincoat','All',8000,1,'o o o o o o o','Normal',['Def +50','Magic +5','M.Def +33'],['Defeat Palmer'],['Rocket Town (after Meteor)']),
 A('Wizard Bracelet','All',12000,1,'o-o o-o o-o o-o','Normal',['Def +6','Magic +20','M.Def +85','Def% +3','MDef% +3'],['Defeat Jenova-LIFE'],['Mideel']),
 A('Adaman Bangle','All',0,1,'o-o','Normal',['Def +93','M.Def +23']),
 A('Gigas Armlet','All',0,1,'o-o o-o o o','None',['Attack +30','Def +59'],['Defeat Demons Gate']),
 A('Imperial Guard','All',0,1,'o-o o-o o-o','Normal',['Def +82','M.Def +74'],['Northern Cave','Defeat CMD. Grand Horn']),
 A('Aegis Armlet','All',0,1,'o-o o-o','Normal',['Def +55','M.Def +86','Def% +15','MDef% +50'],['Sector 8 (after the cannon)']),
 A('Fourth Bracelet','All',0,1,'o-o o-o o o','Normal',['Def +74','Magic +20','M.Def +100','Def% +3','MDef% +3'],['Rocket Town']),
]
P += [
 A('Warrior Bangle','All',0,1,'o-o o-o','None',['Attack +20','Def +96','M.Def +21']),
 A('Shinra Beta','All',0,1,'o-o o o','Normal',['Def +30'],['Defeat Shinra submarine crew']),
 A('Shinra Alpha','All',0,1,'o-o o-o o-o','Normal',['Def +77','M.Def +34']),
 A('Four Slots','All',1300,1,'o o o o','Normal',['Def +12','M.Def +10'],['Shinra HQ'],['Costa del Sol']),
 A('Fire Armlet','All',0,1,'o-o o-o','Normal',['Def +72','M.Def +52','Def% +8','MDef% +3'],["Gaea's Cliff"],note='Absorbs Fire attacks'),
 A('Aurora Armlet','All',0,1,'o-o o-o','Normal',['Def +76','M.Def +54','Def% +8','MDef% +3'],['Forgotten Capital'],note='Absorbs Ice attacks'),
 A('Bolt Armlet','All',0,1,'o-o o-o','Normal',['Def +74','M.Def +55','Def% +8','MDef% +3'],['Coral Valley'],note='Absorbs Lightning attacks'),
 A('Dragon Armlet','All',0,1,'o-o o-o o-o','Normal',['Def +58','M.Def +47','Def% +3','MDef% +2'],['Defeat Red Dragon or Blue Dragon'],note='Halves Fire, Ice and Lightning'),
 A('Minerva Band','Women',0,1,'o-o o-o o-o','Normal',['Def +60','M.Def +57','Def% +8'],['Ancient Forest'],note='Women only. Nullifies Fire, Ice, Gravity and Holy'),
]
P += [
 A('Escort Guard','Men',0,1,'o-o o-o o-o','Normal',['Def +62','M.Def +55','Def% +5'],['Gelnika (sunken plane)'],note='Men only. Nullifies Lightning, Earth, Water and Poison'),
 A('Mystile','All',0,1,'o-o o-o o-o','Normal',['Def +65','M.Def +72','Def% +50','MDef% +60'],['Sector 8 (after the cannon)','Northern Cave']),
 A('Ziedrich','All',0,1,'',None,['Attack +20','Def +100','Magic +20','M.Def +98','Def% +15','MDef% +18'],note='Halves all elemental attacks'),
 A('Precious Watch','All',0,1,'o o o o o o o o','Normal',None,['Chocobo race prize']),
 A('Chocobracelet','All',0,1,'o o o o','Normal',['Def +35','M.Def +38','Dex +30','Luck +20','Def% +10','MDef% +10'],['Chocobo race prize']),
]
