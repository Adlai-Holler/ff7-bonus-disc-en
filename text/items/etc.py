from gen import *
DATA.setdefault(4, [])
P = DATA[4]
TGT = {'1': 'One', 'A': 'All', 'P': 'Party'}
def I(name, pr, tgt, battle, menu, eff, found=None, note=None):
    return G(name, [('Price', price(pr)), ('Target', TGT.get(tgt, tgt)), ('Battle', yn(battle)), ('Menu', yn(menu)),
                    ('Effect', eff)], found, None, note)
P += [
 I('Potion',50,'1',1,1,['Restores 100 HP']),
 I('Hi-Potion',300,'1',1,1,['Restores 500 HP']),
 I('X-Potion',0,'1',1,1,['Fully restores HP']),
 I('Ether',1500,'1',1,1,['Restores 100 MP']),
 I('Turbo Ether',0,'1',1,1,['Fully restores MP']),
 I('Elixir',0,'1',1,1,['Fully restores HP/MP']),
 I('Megalixir',0,'A',1,1,['Fully restores HP/MP','of the whole party']),
 I('Phoenix Down',300,'1',1,1,['Revives from KO']),
]
P += [
 I('Antidote',80,'1',1,0,['Cures Poison']),
 I('Soft',150,'1',1,0,['Cures Petrify and','Slow-numb']),
 I("Maiden's Kiss",150,'1',1,0,['Cures Frog']),
 I('Cornucopia',150,'1',1,0,['Cures Small']),
 I('Echo Screen',100,'1',1,0,['Cures Silence']),
 I('Hyper',100,'1',1,1,['Cures Sadness']),
 I('Tranquilizer',100,'1',1,1,['Cures Fury']),
 I('Remedy',1000,'1',1,0,['Cures all ailments']),
 I('Smoke Bomb',300,'A',1,0,['Guarantees escape']),
 I('Speed Drink',1000,'1',1,0,['Same as Haste']),
 I('Hero Drink',0,'1',1,0,['Raises Str, Dex, Vit,','Mag, Spr and Luck','for the battle']),
 I('Vaccine',0,'1',1,0,['Prevents ailments','for the battle']),
 I('Grenade',80,'1',1,0,['About 150 physical','damage to one foe']),
 I('Shrapnel',0,'A',1,0,['About 400 physical','damage to all foes']),
 I('Right arm',0,'A',1,0,['About 1500 physical','damage to all foes']),
]
P += [
 I('Hourglass',0,'A',1,0,['Same as Stop']),
 I('Kiss of Death',0,'A',1,0,['Same as Death']),
 I('Spider Web',0,'A',1,0,['Same as Slow']),
 I('Dream Powder',0,'A',1,0,['Same as Sleepel']),
 I('Mute Mask',0,'A',1,0,['Same as Silence']),
 I('War Gong',0,'A',1,0,['Same as Berserk']),
 I('Loco weed',0,'A',1,0,['Same as Confu']),
 I('Fire Fang',0,'A',1,0,['Same as Fire2;','about 1000 damage']),
 I('Fire Veil',800,'A',1,0,['Same as Fire3;','about 1200 damage']),
 I('Antarctic Wind',0,'A',1,0,['Same as Ice2;','about 1200 damage']),
 I('Ice Crystal',0,'A',1,0,['Same as Ice3;','about 2000 damage']),
 I('Bolt Plume',0,'A',1,0,['Same as Bolt2;','about 400 damage']),
 I('Swift Bolt',800,'A',1,0,['Same as Bolt3;','about 1200 damage']),
 I('Earth Drum',0,'A',1,0,['Same as Quake2;','about 600 damage']),
 I('Earth Mallet',0,'A',1,0,['Same as Quake3;','about 2500 damage']),
]
P += [
 I('Deadly Waste',0,'A',1,0,['Same as Bio2;','about 100 damage']),
 I('M-Tentacles',0,'A',1,0,['Same as Bio3;','about 1000 damage']),
 I('Stardust',0,'A',1,0,['Same as Comet2;','about 1000 damage']),
 I('Vampire Fang',0,'1',1,0,['Drains about 200 HP','from a foe']),
 I('Ghost Hand',0,'1',1,0,['Drains about 30 MP','from a foe']),
 I('Vagyrisk Claw',0,'1',1,0,['Same as Break']),
 I('Light Curtain',0,'A',1,0,['Same as Barrier']),
 I('Lunar Curtain',0,'A',1,0,['Same as MBarrier']),
 I('Mirror',0,'A',1,0,['Same as Reflect']),
 I('Holy Torch',0,'A',1,0,['Same as DeSpell']),
 I('Bird Wing',0,'A',1,0,['Wind; about 1000 dmg']),
 I('Dragon Scales',0,'A',1,0,['Water; about 3800 dmg']),
 I('Impaler',500,'1',1,0,['Turns foe into a frog']),
 I('Shrivel',500,'1',1,0,['Same as Mini']),
 I('Eye drop',50,'1',1,0,['Cures Darkness']),
]
VEG = ['Chocobo feed. Use in','battle and the chocobo','will not run away']
P += [
 I('Molotov',400,'1',1,0,['Fire; about 400 damage']),
 I('S-mine',1000,'1',1,0,['Explosive; about','1500 damage']),
 I('8-inch Cannon',0,'1',1,0,['Explosive; about','3000 damage']),
 I('Graviball',0,'1',1,0,['Same as Demi']),
 I('T/S Bomb',0,'1',1,0,['Same as Demi2']),
 I('Ink',0,'1',1,0,['Inflicts Darkness']),
 I('Dazers',0,'1',1,0,['Inflicts Paralysis']),
 I('Dragon Fang',0,'A',1,0,['Lightning; about','3000 damage']),
 I('Cauldron',0,'1',1,0,['Inflicts Poison, Confuse,','Sleep, Silence,','Small and Frog']),
 I('Sylkis Greens',5000,'1',1,0,VEG),
 I('Reagan Greens',3000,'1',1,0,VEG),
 I('Mimett Greens',1500,'1',1,0,VEG),
 I('Curiel Greens',1000,'1',1,0,VEG),
 I('Pahsana Greens',800,'1',1,0,VEG),
 I('Tantal Greens',400,'1',1,0,VEG),
]
NUT = 'Used when breeding chocobos'
def N(name, pr): return G(name, [('Price', price(pr))], note=NUT)
def SRC(name, stat): return I(name, 500, '1', 0, 1, ['Raises max ' + stat])
P += [
 I('Krakka Greens',250,'1',1,0,VEG),
 I('Gysahl Greens',100,'1',1,0,VEG),
 I('Tent',500,'A',0,1,['Fully restores HP/MP','and cures ailments']),
 SRC('Power Source','Strength'), SRC('Guard Source','Vitality'), SRC('Magic Source','Magic'),
 SRC('Mind Source','Spirit'), SRC('Speed Source','Dexterity'), SRC('Luck Source','Luck'),
 N('Zeio Nut',0), N('Carob Nut',0), N('Porov Nut',2000), N('Pram Nut',1500), N('Lasan Nut',600), N('Saraha Nut',400),
]
def LM(name, who, limit): return G(name, [], note="Teaches %s's final Limit Break, %s" % (who, limit))
def NOTE(name, note, pr='x'): return G(name, [('Price', price(pr))] if pr != 'x' else [], note=note)
P += [
 N('Luchile Nut',200), N('Pepio Nut',100),
 G('Battery',[('Price','3 for 300 gil')],note='Used at the cut-away Plate'),
 NOTE('Pocket Tissue','Battle Square participation prize',0),
 LM('Omnislash','Cloud','Omnislash'), LM('Catastrophe','Barret','Catastrophe'), LM('Final Heaven','Tifa','Final Heaven'),
 LM('Great Gospel','Aeris','Great Gospel'), LM('Cosmo Memory','Red XIII','Cosmo Memory'), LM('All Creation','Yuffie','All Creation'),
 LM('Chaos','Vincent','Chaos'), LM('Highwind','Cid','Highwind'),
 NOTE('1/35 soldier','Shinra grenadier figures: "Assault" set of 12'),
 NOTE('Super Sweeper','Latest mech guarding the reactor! Fires missiles from both arms!'),
 NOTE('Masamune Blade','Replica of Sephiroth\'s sword. Feel like a SOLDIER!'),
]
KEEP = 'Cannot be thrown away'
P += [
 NOTE('Save Crystal','Lets you make a save point, only inside the Northern Cave. ' + KEEP),
 NOTE('Combat Diary',"Hot-blooded Dio's combat diary. " + KEEP),
 NOTE('Autograph',"Superhuman Dio's signed autograph. " + KEEP),
 NOTE('Gambler',"Invincible Dio's combat diary, Part 2: The Gold Saucer. " + KEEP),
 NOTE('Cotton Dress','A dress woven from cotton.'),
 NOTE('Satin Dress','A dress woven from satin.'),
 NOTE('Silk Dress','A dress woven from silk.'),
 NOTE('Wig','A wig with frizzy hair.'),
 NOTE('Dyed Wig','A wig with brown hair.'),
 NOTE('Blonde Wig','A wig with blonde hair.'),
 NOTE('Glass Tiara','A tiara made of glass.'),
 NOTE('Ruby Tiara','A tiara set with rubies.'),
 NOTE('Diamond Tiara','A tiara set with diamonds.'),
 NOTE('Cologne','Cheap perfume.'),
 NOTE('Flower Cologne','Perfume with a floral scent.'),
]
SWAP = 'Obtained by trading in the Pharmacy Coupon.'
P += [
 NOTE('Sexy Cologne','Perfume with a sexy scent.'),
 NOTE('Member\'s Card','Honey Bee Inn membership card.'),
 NOTE('Lingerie','Underwear with a lovely scent.'),
 NOTE('Bikini briefs','Daringly cut briefs.'),
 NOTE('Pharmacy Coupon','Trade it for a prize at the pharmacy.'),
 NOTE('Disinfectant','Disinfectant. ' + SWAP),
 NOTE('Deodorant','Deodorant. ' + SWAP),
 NOTE('Digestive','Digestive aid. ' + SWAP),
 NOTE('Keycard 60','Keycard for Shinra HQ floors 60, 62, 65, 66 and 68.'),
 NOTE('Midgar parts','A part for the model of Midgar.'),
 G('',[],note='Lets you call party members who are elsewhere.'),
 NOTE('Gold Ticket','Unlimited-entry pass to the Gold Saucer.'),
 NOTE('Keystone','The key to the Temple of the Ancients.'),
 NOTE('Leviathan Scales','Scales holding the power of water.'),
 NOTE('Glacier Map','A map for the Great Glacier.'),
 NOTE('Coupon A / Coupon B\\n/ Coupon C','Each can be traded for an item.'),
]
HUGE = 'Huge Materia'
BASE = 'Key to the Shinra Mansion basement.'
P += [
 NOTE('Black Materia','A black Materia.'),
 NOTE('Mythril','Might be useful as material for something...'),
 NOTE('Snowboard','Lets you travel across snow.'),
 NOTE(HUGE+' (Command)','Huge Materia obtained at the Fort Condor reactor.'),
 NOTE(HUGE+' (Magic)','Huge Materia obtained at the Corel reactor.'),
 NOTE(HUGE+' (Summon)','Huge Materia obtained on the sea floor.'),
 NOTE(HUGE+' (Support)','Huge Materia obtained from the rocket.'),
 NOTE('Key to Ancients','An old key found in the sea.'),
 NOTE('Lunar Harp','An instrument that wakes the Sleeping Forest.'),
 NOTE('Basement Key',BASE),
 NOTE('Key to Sector 5','Key that opens the Sector 5 gate in Midgar.'),
 NOTE('Basement Key',BASE),
 NOTE('Key to Ancients','An old key found in the sea.'),
 NOTE('Lunar Harp','An instrument that wakes the Sleeping Forest.'),
 NOTE('Basement Key',BASE),
 NOTE('Basement Key',BASE),
]
