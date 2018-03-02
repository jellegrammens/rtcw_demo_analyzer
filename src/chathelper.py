DocsStolen = []
DocsStolen.append('Axis have stolen Allied Documents!')
DocsStolen.append('Allies have stolen The UFO Documents!')
DocsStolen.append('Allies have stolen the Radio Codes Booklet!')
DocsStolen.append('Allies have stolen the War Documents!')
DocsStolen.append('Allies have stolen the Sacred Obelisk!')
DocsStolen.append('Allies have stolen the Gold!')

DocsReturned = []
DocsReturned.append('Axis have returned The UFO Documents!')
DocsReturned.append('Axis have returned the objective!')
DocsReturned.append('Axis have returned the Radio Codes Booklet!')
DocsReturned.append('Axis have returned the Sacred Obelisk!')
DocsReturned.append('Axis have returned the War Documents!')
DocsReturned.append('Axis have returned the Gold!')
DocsReturned.append('Allies have returned the objective!')
DocsReturned.append('Allies have returned Allied Documents!')

DocsTransmitted = []
DocsTransmitted.append('Allies transmitted the documents!')
DocsTransmitted.append('Axis transmitted the documents!')
DocsTransmitted.append('The Allies have escaped with the Obelisk!')
DocsTransmitted.append('Allies Transmitted the UFO Documents!')
DocsTransmitted.append('The Allies have escaped with the Gold!')
DocsTransmitted.append('Allies have transmitted the Top Secret Documents!')

DocsAll = []
DocsAll.append(DocsStolen)
DocsAll.append(DocsReturned)
DocsAll.append(DocsTransmitted)
DocsAll = [item for sublist in DocsAll for item in sublist]

DynamitePlanted = []
DynamitePlanted.append('Dynamite planted near the Axis Submarine!')
DynamitePlanted.append('Dynamite planted near the South Radar [02]!')
DynamitePlanted.append('Dynamite planted near the North Radar [01]!')
DynamitePlanted.append('Dynamite planted near The Communications Tower!')

DynamiteDefused = []
DynamiteDefused.append('Axis engineer disarmed the Dynamite!')
DynamiteDefused.append('Allied engineer disarmed the Dynamite!')

DynamiteExploded = []
DynamiteExploded.append('Allied team has destoryed the Axis Submarine!')
DynamiteExploded.append('Allied team has destroyed the Axis Submarine!')
DynamiteExploded.append('Axis team destroyed the Communications Tower!')
DynamiteExploded.append('Allied team has disabled the South Radar!')
DynamiteExploded.append('Allied team has disabled the North Radar!')

DynamiteAll = []
DynamiteAll.append(DynamitePlanted)
DynamiteAll.append(DynamiteDefused)
DynamiteAll.append(DynamiteExploded)
DynamiteAll = [item for sublist in DynamiteAll for item in sublist]