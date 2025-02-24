# Data

Initial data setup with eddb dumps
```bash
wget -O - https://www.edsm.net/dump/systemsPopulated.json.gz | gunzip -c > ./workspace/systemsPopulated.json
jq -r '.[] 
| [.id, .name, .coords.x, .coords.y, .coords.z, .population, .government, .allegiance, .security, .economy, .controllingFaction.id, .controllingFaction.name] 
| @csv' workspace/systemsPopulated.json > db/data/systems.csv
```
