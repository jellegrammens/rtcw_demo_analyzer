weapons_enum = {}

#real weapons
weapons_enum['knife'] = [12, 14]
weapons_enum['colt'] = [16]
weapons_enum['luger'] = [15]
weapons_enum['mp40'] = [17]
weapons_enum['thompson'] = [18]
weapons_enum['sten'] = [19]
weapons_enum['grenade'] = [4, 5]
weapons_enum['panzerfaust'] = [6, 7]
weapons_enum['sniper'] = [20, 21]
weapons_enum['flamethrower'] = [34]
weapons_enum['dynamite'] = [45]
weapons_enum['support_fire'] = [0, 46]
weapons_enum['artillery'] = [49]
weapons_enum['venom'] = [32]
weapons_enum['mg42'] = [3]

#killed by world: bAttacker will be 254
weapons_enum['barbed_wire'] = [40, 58]
weapons_enum['mortar'] = [41]
weapons_enum['drowned'] = [50]
weapons_enum['crushed'] = [53]
weapons_enum['fall_to_death'] = [55]

#selfkill / join spec
weapons_enum['selfkill'] = [56]
weapons_enum['joined_spectator'] = [74]

#putting similar weapons together to filter easier on frags
weapons_enum['pistol'] = [15, 16]
weapons_enum['smg'] = [17, 18, 19]
weapons_enum['pistol_and_smg'] = [15, 16, 17, 18, 19]
weapons_enum['merlinator'] = [0, 46, 49]
weapons_enum['world_kills'] = [40, 58, 41, 50, 53, 55]