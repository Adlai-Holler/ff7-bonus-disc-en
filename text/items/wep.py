from gen import *
P = DATA[0]
P += [
 W('Buster Sword','Cloud',18,'Magic +2',96,'o-o','Normal',0,0,0,'Cut',["Cloud's starting gear"]),
 W('Mythril Saber','Cloud',23,'Magic +4',98,'o-o o','Normal',1,1000,1,'Cut',None,['Kalm','Lower Junon']),
 W('Hardedge','Cloud',32,'Magic +6',98,'o-o o o','Normal',1,1500,1,'Cut',None,['Upper Junon','Gongaga']),
 W('Butterfly Edge','Cloud',39,'Magic +8',100,'o-o o-o','Normal',1,2800,1,'Cut',None,['Cosmo Canyon']),
 W('Enhance Sword','Cloud',43,'Magic +16',107,'o-o o-o o-o o-o','Normal',1,12000,1,'Cut',["Gaea's Cliff"],['Upper Junon (after Meteor)']),
 W('Organics','Cloud',62,'Magic +15',103,'o-o o-o o o','Normal',1,12000,1,'Cut',None,['Icicle Inn']),
 W('Crystal Sword','Cloud',76,'Magic +19',105,'o-o o-o o-o','Normal',1,18000,1,'Cut',None,['Mideel']),
 W('Force Stealer','Cloud',36,'Magic +7',100,'o o o','Double',1,2200,1,'Cut',['Junon Harbor'],['North Corel']),
 W('Rune Blade','Cloud',40,'Magic +9',108,'o o o o','Double',1,3800,1,'Cut',['Nibel Mountains'],['Upper Junon (after Meteor)']),
]
P += [
 W('Murasame','Cloud',51,'Magic +12',100,'o-o o-o o','Normal',1,6500,1,'Cut',None,['Wutai']),
 W('Nail Bat','Cloud',70,None,100,'',None,1,2800,1,'Cut',['Ancient Temple'],['Upper Junon (after Meteor)']),
 W('Yoshiyuki','Cloud',56,'Magic +9',100,'o o','Normal',1,0,1,'Cut',['Rocket Town'],note='Stronger as allies fall'),
 W('Apocalypse','Cloud',88,['Magic +43','Mag. Def +16'],110,'o o o','Triple',1,0,1,'Cut',['Ancient Forest']),
 W("Heaven's Cloud",'Cloud',93,'Magic +31',100,'o o o o o o','Normal',1,0,1,'Cut',['Gelnika (sunken plane)']),
 W('Ragnarok','Cloud',97,['Magic +43','Mag. Def +35'],105,'o-o o-o o-o','Normal',1,0,1,'Cut',['Defeat Proud Clod']),
 W('Ultima Weapon','Cloud',100,['Magic +51','Mag. Def +24'],110,'o-o o-o o-o o-o','None',1,0,1,'Cut',['Defeat Ultima Weapon'],note='Damage scales with HP'),
 W('Leather Glove','Tifa',13,None,99,'o','Normal',1,0,0,'Punch',["Tifa's starting gear"]),
 W('Metal Knuckle','Tifa',18,'Magic +1',102,'o-o','Normal',1,320,0,'Punch',None,['Wall Market']),
]
P += [
 W('Mythril Claw','Tifa',24,'Magic +3',106,'o-o o','Normal',1,750,0,'Stab',None,['Kalm','Lower Junon']),
 W('Grand Glove','Tifa',31,'Magic +6',110,'o-o o o','Normal',1,1200,0,'Punch',None,['Upper Junon','Gongaga','Lower Junon (after Meteor)']),
 W('Tiger Fang','Tifa',38,'Magic +8',110,'o-o o-o','Normal',1,2500,0,'Stab',None,['Cosmo Canyon']),
 W('Diamond Knuckle','Tifa',51,'Magic +10',112,'o-o o-o o','Normal',1,5800,0,'Punch',None,['Wutai']),
 W('Dragon Claw','Tifa',62,'Magic +13',114,'o-o o-o o o','Normal',1,10000,0,'Stab',None,['Icicle Inn']),
 W('Crystal Glove','Tifa',75,'Magic +16',115,'o-o o-o o-o','Normal',1,16000,0,'Punch',None,['Mideel']),
 W('Motor Drive','Tifa',27,'Magic +6',106,'o o o','Double',1,0,0,'Punch',['Costa del Sol']),
 W('Platinum Fist','Tifa',30,'Magic +7',108,'o o o o','Double',1,2700,0,'Punch',['Nibelheim'],['Upper Junon (after Meteor)']),
 W('Kaiser Knuckle','Tifa',44,'Magic +13',110,'o-o o o o o o o','Normal',1,15000,0,'Punch',['Whirlwind Maze'],['Upper Junon (after Meteor)']),
]
P += [
 W('Work Glove','Tifa',68,None,114,'',None,1,2200,0,'Punch',['Ancient Temple'],['Lower Junon (after Meteor)'],note='Higher critical rate'),
 W('Powersoul','Tifa',28,'Magic +7',106,'o o o o','Double',1,4200,0,'Punch',['Nibel Mountains'],['Lower Junon (after Meteor)'],note='Up in Near-death or D. Sentence'),
 W('Master Fist','Tifa',38,None,108,'o o o o o o','Normal',1,0,0,'Punch',['Shinra HQ (after the cannon)'],note='Stronger the more ailments Tifa has'),
 W("God's Hand",'Tifa',86,'Magic +34',255,'o-o o-o','Normal',1,0,0,'Punch',['Defeat Carry Armor']),
 W('Premium Heart','Tifa',99,'Magic +32',112,'o-o o-o o-o o-o','None',1,0,0,'Punch',['Wall Market (after the cannon)'],note='Power set by the Limit gauge'),
 W('Gatling Gun','Barret',14,None,97,'o','Normal',0,0,0,'Shoot',["Barret's starting gear"],note='Long range: full power from the back row'),
 W('Assault Gun','Barret',17,'Magic +1',98,'o-o','Normal',1,350,1,'Shoot',['Defeat Guard Scorpion'],['Sector 7','Wall Market'],note='Long range'),
 W('Cannon Ball','Barret',23,'Magic +2',98,'o-o o','Normal',1,950,1,'Punch',None,['Kalm','Lower Junon']),
 W('Atomic Scissors','Barret',32,'Magic +4',99,'o-o o o','Normal',1,1400,1,'Stab',None,['Upper Junon','Gongaga','Lower Junon (after Meteor)']),
]
LR = 'Long range'
P += [
 W('Heavy Vulcan','Barret',39,'Magic +8',100,'o-o o-o','Normal',1,2700,1,'Shoot',None,['Cosmo Canyon'],note=LR),
 W('Chainsaw','Barret',52,'Magic +10',100,'o-o o-o o','Normal',1,6300,1,'Cut',None,['Wutai']),
 W('Microlaser','Barret',63,'Magic +13',101,'o-o o-o o o','Normal',1,12000,1,'Shoot',None,['Icicle Inn'],note=LR),
 W('A-M Cannon','Barret',77,'Magic +16',103,'o-o o-o o-o','Normal',1,18000,1,'Shoot',None,['Mideel'],note=LR),
 W('W Machine Gun','Barret',30,'Magic +3',100,'o o o','Double',1,2000,1,'Shoot',['Mt. Corel'],['Upper Junon (after Meteor)'],note=LR),
 W('Drill Arm','Barret',37,None,97,'o o o o','Double',1,3300,1,'Stab',['Rocket Town'],['Upper Junon (after Meteor)']),
 W('Solid Bazooka','Barret',61,'Magic +15',100,'o-o o-o o-o o-o','Normal',1,16000,1,'Shoot',None,['Costa del Sol (after Meteor)'],note=LR),
 W('Rocket Punch','Barret',62,None,110,'',None,1,3200,1,'Punch',['Ancient Temple'],['Lower Junon (after Meteor)']),
 W('Enemy Launcher','Barret',35,'Magic +7',100,'o-o o o o o','Normal',1,3300,1,'Shoot',['Shinra Mansion'],['Lower Junon (after Meteor)'],note=LR),
]
P += [
 W('Pile Banger','Barret',90,None,80,'o-o o-o o-o','None',1,0,1,'Stab',['Shinra HQ (after the cannon)']),
 W('Max Ray','Barret',97,'Magic +30',98,'o-o o-o o-o','Normal',1,0,1,'Shoot',['Sector 8 (after the cannon)'],note=LR),
 W('Missing Score','Barret',98,'Magic +49',108,'o-o o-o o-o o-o','None',1,0,1,'Shoot',['Sector 8 (after the cannon)'],note='Power from slotted Materia AP; long range'),
 W('Mythril Clip','Red XIII',24,'Magic +6',100,'o-o o','Normal',1,800,0,'Punch',["Red XIII's starting gear"],['Lower Junon']),
 W('Diamond Pin','Red XIII',33,'Magic +8',102,'o-o o o','Normal',1,1300,0,'Punch',None,['Upper Junon','Gongaga','Lower Junon (after Meteor)']),
 W('Silver Barrette','Red XIII',40,'Magic +10',110,'o-o o-o','Normal',0,2500,0,'Punch',None,['Cosmo Canyon']),
 W('Gold Barrette','Red XIII',50,'Magic +13',104,'o-o o-o o','Normal',1,6000,0,'Punch',None,['Wutai']),
 W('Adaman Clip','Red XIII',60,'Magic +15',106,'o-o o-o o o','Normal',1,11000,0,'Punch',None,['Icicle Inn']),
 W('Crystal Comb','Red XIII',76,'Magic +20',108,'o-o o-o o-o','Normal',1,17000,0,'Punch',None,['Mideel']),
]
P += [
 W('Magic Comb','Red XIII',37,'Magic +4',100,'o o o','Double',1,2000,0,'Punch',['Condor Fort'],['Upper Junon (after Meteor)']),
 W('Plus Barrette','Red XIII',39,'Magic +12',104,'o o o o','Double',1,3500,0,'Punch',['Nibel Mountains'],['Upper Junon (after Meteor)']),
 W('Centclip','Red XIII',58,'Magic +22',108,'o o o o o o o o','Normal',1,14000,0,'Punch',None,['Costa del Sol (after Meteor)']),
 W('Hairpin','Red XIII',57,'Magic +15',120,'',None,1,6000,0,'Shoot',['Wutai'],['Lower Junon (after Meteor)'],note=LR),
 W('Seraph Comb','Red XIII',68,'Magic +14',110,'o o o o','Normal',0,0,0,'Punch',['Cosmo Canyon'],note="His father's keepsake"),
 W('Behemoth Horn','Red XIII',91,['Magic +26','Defense +35','Mag. Def +18'],75,'o o o o o o','Normal',1,0,0,'Punch',['Shinra HQ (after the cannon)']),
 W('Spring Gun Clip','Red XIII',87,'Magic +55',100,'o-o o-o o-o','Normal',1,0,0,'Punch',['Ancient Forest']),
 W('Limited Moon','Red XIII',93,'Magic +31',114,'o-o o-o o-o o-o','None',1,0,0,'Punch',['Cosmo Canyon'],note='Power based on MP'),
 W('Guard Stick','Aeris',12,['Magic +2','Defense +1','Mag. Def +4'],99,'o','Normal',1,0,1,'Punch',["Aeris's starting gear"]),
]
P += [
 W('Mythril Rod','Aeris',16,'Magic +3',100,'o-o','Normal',1,370,1,'Punch',None,['Wall Market']),
 W('Full Metal Staff','Aeris',22,'Magic +4',100,'o-o o','Normal',1,800,1,'Punch',None,['Kalm','Lower Junon']),
 W('Striking Staff','Aeris',32,'Magic +7',100,'o-o o o','Normal',1,1300,1,'Punch',None,['Upper Junon','Gongaga','Lower Junon (after Meteor)']),
 W('Prism Staff','Aeris',40,'Magic +10',105,'o-o o-o','Normal',1,2600,1,'Punch',None,['Cosmo Canyon']),
 W('Aurora Rod','Aeris',51,'Magic +14',110,'o-o o-o o','Normal',1,5800,1,'Punch',None,['Wutai']),
 W('Wizard Staff','Aeris',28,'Magic +6',100,'o o o','Double',1,1800,1,'Punch',['Mt. Corel'],['Upper Junon (after Meteor)']),
 W('Wizer Staff','Aeris',33,'Magic +7',100,'o o o o','Double',1,3200,1,'Punch',['Defeat Gi Nattak'],['Upper Junon (after Meteor)']),
 W('Fairy Tale','Aeris',37,'Magic +8',103,'o o o o o o o','Normal',1,2500,1,'Punch',['Defeat Reno (Gongaga)'],['Upper Junon (after Meteor)']),
 W('Umbrella','Aeris',58,['Defense +20','Magic +10'],118,'',None,1,0,1,'Punch',['Speed Square prize']),
]
P += [
 W('Princess Guard','Aeris',52,['Magic +22','Def +12','M.Def +20'],111,'o-o o-o o-o o o','Normal',1,0,1,'Punch',['Ancient Temple'],note='Stronger as allies fall'),
 W('Spear','Cid',44,'Magic +8',97,'o-o o-o','Normal',1,1200,1,'Stab',["Cid's starting gear"],['Lower Junon (after Meteor)']),
 W('Slash Lance','Cid',56,'Magic +10',98,'o-o o-o o o','Normal',1,6500,1,'Stab',None,['Wutai']),
 W('Trident','Cid',60,'Magic +12',105,'o o o o o o','Normal',1,7500,1,'Stab',['Ancient Temple'],['Lower Junon (after Meteor)']),
 W('Mast Ax','Cid',64,'Magic +15',99,'o-o o-o o o o','Normal',1,13000,1,'Stab',None,['Icicle Inn']),
 W('Partisan','Cid',78,'Magic +17',100,'o-o o-o o-o','Normal',1,19000,1,'Stab',None,['Mideel']),
 W('Viper Halberd','Cid',58,'Magic +13',102,'o o o o','Double',1,7000,1,'Stab',['Coral Valley'],['Upper Junon (after Meteor)']),
 W('Javelin','Cid',62,'Magic +12',104,'o-o o-o o','Double',1,0,1,'Stab',["Gaea's Cliff"]),
 W('Grow Lance','Cid',78,'Magic +31',102,'o-o o-o o-o','Normal',1,None,1,'Stab',['Shinra HQ (after the cannon)']),
]
P += [
 W('Mop','Cid',68,'Magic +3',118,'',None,1,3200,1,'Punch',None,['Lower Junon (after Meteor)']),
 W('Dragoon Lance','Cid',66,'Magic +7',100,'o o o o o o o o','Normal',1,6200,1,'Stab',['Da-chao Statue'],['Upper Junon (after Meteor)']),
 W('Scimitar','Cid',86,'Magic +20',102,'o-o','Triple',1,0,1,'Cut',['Underwater Reactor']),
 W('Flayer','Cid',100,'Magic +20',100,'o o o o o o','Normal',1,0,1,'Stab',['Speed Square prize']),
 W('Spirit Lance','Cid',92,['Magic +43','Mag. Def +20'],112,'o-o o-o','Normal',1,0,1,'Stab',['Gelnika (sunken plane)']),
 W('Venus Gospel','Cid',97,'Magic +42',103,'o-o o-o o-o o-o','None',1,0,1,'Stab',['Rocket Town'],note='Power based on MP'),
 W('4-point Shuriken','Yuffie',23,'Magic +6',100,'o-o o','Normal',1,0,1,'Shoot',["Yuffie's starting gear"],note=LR),
 W('Boomerang','Yuffie',30,'Magic +7',101,'o-o o o','Normal',1,1400,1,'Shoot',None,['Upper Junon','Gongaga','Lower Junon (after Meteor)'],note=LR),
 W('Pinwheel','Yuffie',37,'Magic +9',104,'o-o o-o','Normal',1,2600,1,'Shoot',None,['Cosmo Canyon'],note=LR),
]
P += [
 W('Razor Ring','Yuffie',49,'Magic +12',105,'o-o o-o o','Normal',1,6000,1,'Shoot',None,['Wutai'],note=LR),
 W('Hawkeye','Yuffie',61,'Magic +14',107,'o-o o-o o o','Normal',1,12000,1,'Shoot',None,['Icicle Inn'],note=LR),
 W('Crystal Cross','Yuffie',74,'Magic +18',110,'o-o o-o o-o','Normal',1,18000,1,'Shoot',None,['Mideel'],note=LR),
 W('Wind Slash','Yuffie',30,'Magic +7',103,'o o o','Double',1,2000,1,'Shoot',['Cargo ship'],['Upper Junon (after Meteor)'],note=LR),
 W('Twin Viper','Yuffie',36,'Magic +8',108,'o o o o','Double',1,3200,1,'Shoot',['Shinra Mansion'],['Upper Junon (after Meteor)'],note=LR),
 W('Spiral Shuriken','Yuffie',68,'Magic +18',110,'o-o o o o o o o','Normal',1,14000,1,'Shoot',None,['Costa del Sol (after Meteor)'],note=LR),
 W('Superball','Yuffie',68,'Magic +10',120,'',None,1,3000,1,'Shoot',['Condor Fort'],['Lower Junon (after Meteor)'],note=LR),
 W('Magic Shuriken','Yuffie',64,'Dexterity +10',113,'o o o','Normal',1,6000,1,'Shoot',['Wutai'],['Lower Junon (after Meteor)'],note=LR),
 W('Rising Sun','Yuffie',90,'Magic +38',116,'o-o o-o o o o o','Normal',1,0,1,'Shoot',['Da-chao Statue'],note=LR),
]
P += [
 W('Conformer','Yuffie',96,'Magic +42',112,'o-o o-o o-o o-o','None',1,0,1,'Shoot',['Gelnika (sunken plane)'],note="Power set by foe's level; long range"),
 W('Yellow M-phone','Cait Sith',36,'Magic +8',100,'o-o o o','Normal',1,500,1,'Punch',["Cait Sith's starting gear"],['Lower Junon (after Meteor)']),
 W('Green M-phone','Cait Sith',41,'Magic +9',100,'o-o o-o','Normal',1,2400,1,'Punch',None,['Cosmo Canyon']),
 W('Blue M-phone','Cait Sith',48,'Magic +10',100,'o-o o-o o','Normal',1,5500,1,'Punch',None,['Wutai']),
 W('Red M-phone','Cait Sith',60,'Magic +15',100,'o-o o-o o o','Normal',1,11000,1,'Punch',None,['Icicle Inn']),
 W('Crystal M-phone','Cait Sith',74,'Magic +20',100,'o-o o-o o-o','Normal',1,18000,1,'Punch',None,['Mideel']),
 W('White M-phone','Cait Sith',35,'Magic +8',102,'o o o','Double',1,2300,1,'Punch',['Gongaga'],['Lower Junon (after Meteor)']),
 W('Black M-phone','Cait Sith',31,'Magic +10',104,'o o o o','Double',1,2800,1,'Punch',['Cave of the Gi'],['Lower Junon (after Meteor)']),
 W('Silver M-phone','Cait Sith',28,'Magic +14',106,'o o o o o o o o','Normal',1,3300,1,'Punch',['Shinra Mansion'],['Lower Junon (after Meteor)']),
]
P += [
 W('Trumpet Shell','Cait Sith',68,'Magic +2',118,'',None,1,3000,1,'Punch',['Ancient Temple'],['Lower Junon (after Meteor)']),
 W('Gold M-phone','Cait Sith',58,'Magic +28',103,'o-o o-o o-o o-o','Normal',1,15000,1,'Punch',None,['Costa del Sol (after Meteor)']),
 W('Battle Trumpet','Cait Sith',95,None,95,'o-o o-o o-o','None',1,0,1,'Punch',['Underwater Reactor']),
 W('Starlight Phone','Cait Sith',88,['Magic +31','Defense +30'],102,'o-o o-o o-o o-o','Normal',1,0,1,'Punch',['Sector 8 (after the cannon)']),
 W('HP Shout','Cait Sith',95,'Magic +44',110,'o-o o-o o-o o-o','None',1,0,1,'Punch',['Shinra HQ (after the cannon)'],note='Power based on HP'),
 W('Quicksilver','Vincent',38,'Magic +10',110,'o-o o o','Normal',1,1000,1,'Shoot',["Vincent's starting gear"],['Upper Junon (after Meteor)'],note=LR),
 W('Shotgun','Vincent',48,'Magic +12',112,'o-o o-o','Normal',1,3100,1,'Shoot',None,['Rocket Town'],note=LR),
 W('Shortbarrel','Vincent',51,'Magic +14',118,'o-o o-o o','Normal',1,6400,1,'Shoot',None,['Wutai'],note=LR),
 W('Lariat','Vincent',64,'Magic +16',120,'o-o o-o o o','Normal',1,12000,1,'Shoot',None,['Icicle Inn'],note=LR),
]
P += [
 W('Winchester','Vincent',73,'Magic +18',120,'o-o o-o o-o','Normal',1,18000,1,'Shoot',None,['Mideel'],note=LR),
 W('Peacemaker','Vincent',38,'Magic +8',118,'o-o o','Double',1,3500,1,'Shoot',['Kalm'],['Upper Junon (after Meteor)'],note=LR),
 W('Buntline','Vincent',48,'Magic +18',124,'o-o o-o','Double',1,6800,1,'Shoot',['Bone Village'],['Upper Junon (after Meteor)'],note=LR),
 W('Long Barrel R','Vincent',66,'Magic +14',255,'o-o o-o o-o o-o','Normal',1,13000,1,'Shoot',None,['Costa del Sol (after Meteor)'],note=LR),
 W('Silver Rifle','Vincent',62,None,120,'',None,1,3000,1,'Shoot',['Ancient Temple'],['Lower Junon (after Meteor)'],note=LR),
 W('Sniper CR','Vincent',42,'Magic +7',255,'o-o o-o','Normal',1,3300,1,'Shoot',['Nibel Mountains'],['Lower Junon (after Meteor)'],note=LR),
 W('Supershot ST','Vincent',97,'Magic +52',120,'o-o o-o o-o','None',1,0,1,'Shoot',['Ancient Forest'],note=LR),
 W('Outsider','Vincent',80,'Magic +48',120,'o-o o-o o o o o','Normal',1,0,1,'Shoot',['Gelnika (sunken plane)'],note=LR),
 W('Death Penalty','Vincent',99,'Magic +34',115,'o-o o-o o-o o-o','None',1,0,1,'Shoot',["Lucrecia's Cave"],note='Power grows with foes killed; long range'),
 '\n'.join(['{g}Masamune','{g}Equip\t{w}Sephiroth','{g}Attack\t{w}99','{g}Hit\t{w}255','{g}Slots\t{w}'+slots('o-o o-o o-o'),
            '{g}Growth\t{w}None','{g}Price\t{w}Not sold','{g}Element\t{w}Cut']),
]
