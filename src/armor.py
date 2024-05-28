# functions to parse the profile data and create the Dict of Armor the user has on all characters and in the vault
from dataclasses import dataclass, field
from typing import Dict
import random

random.seed(42)

def random_64_int():
    return random.randint(0,9223372036854775807)

# the stats on the armor are the base values, they do not include masterworking or other mods
@dataclass
class Armor:
    item_name: str = "Generic Armor"
    item_hash: int = field(default_factory=random_64_int)
    instance_id: int = field(default_factory=random_64_int)
    rarity: str = "Legendary"
    slot: str = "Helmet"
    power: int = 0 
    mobility: int = 0
    resilience: int = 0
    recovery: int = 0
    discipline: int = 0
    intellect: int = 0
    strength: int = 0
    is_artifice: bool = False
    is_masterworked: bool = False
    d2_class: str = "Warlock"

    @property
    def is_exotic(self):
        return self.rarity == "Exotic"

    @property
    def total_stats(self):
        return self.mobility + self.resilience + self.recovery + self.discipline + self.intellect + self.strength

    @property
    def class_slot(self):
        return f"{self.d2_class} {self.slot}"

    def __hash__(self):
        return hash(self.instance_id)

class ProfileArmor:
    # hard coding some magic numbers, these are in DestinyStatDefinition.json
    MOBILITY_ID = "2996146975"
    RESILIENCE_ID = "392767087"
    RECOVERY_ID = "1943323491"
    DISCIPLINE_ID = "1735777505"
    INTELLECT_ID = "144602215"
    STRENGTH_ID = "4244567218"

    CLASS_MAP = {0: 'Titan', 1: 'Hunter', 2: 'Warlock'}

    ARMOR_ITEM_TYPE = 2

    def __init__(self, profile, item_definitions, stat_definitions):
        self.profile = profile
        self.item_definitions = item_definitions
        self.stat_definitions = stat_definitions

    # spin through the profile data and find all inventory items on the character and in character equipment
    # example for item instance: {'itemHash': 2244604734, 'itemInstanceId': '6917529860806551003', 'quantity': 1, 'bindStatus': 0, 'location': 2, 'bucketHash': 138197802, 'transferStatus': 0, 'lockable': True, 'state': 5, 'dismantlePermission': 2, 'isWrapper': False, 'tooltipNotificationIndexes': [], 'versionNumber': 0 }
    def __get_inventory_items(self, profile):
        items = {}
        for character_id in profile['profile']['data']['characterIds']:
            for item in profile['characterEquipment']['data'][character_id]['items']:
                instance_id = int(item.get('itemInstanceId', item['itemHash']))
                items[instance_id] = item
            for item in profile['characterInventories']['data'][character_id]['items']:
                instance_id = int(item.get('itemInstanceId', item['itemHash']))
                items[instance_id] = item

        for item in profile['profileInventory']['data']['items']:
            instance_id = int(item.get('itemInstanceId', item['itemHash']))
            items[instance_id] = item

        return items

    # example for instance: {'damageType': 0, 'primaryStat': {'statHash': 3897883278, 'value': 1810}, 'itemLevel': 181, 'quality': 0, 'isEquipped': False, 'canEquip': False, 'equipRequiredLevel': 50, 'unlockHashesRequiredToEquip': [1368285237], 'cannotEquipReason': 16, 'energy': {'energyTypeHash': 4069572561, 'energyType': 3, 'energyCapacity': 10, 'energyUsed': 0, 'energyUnused': 10}
    def __get_item_component_instances(self, profile):
        item_component_instances = {}
        for instance_id, instance in profile['itemComponents']['instances']['data'].items():
            item_component_instances[int(instance_id)] = instance
        
        return item_component_instances

    # example sockets for instance: sockets': [{'plugHash': 1980618587, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3820147479, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3820147479, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3820147479, 'isEnabled': True, 'isVisible': True}, {'plugHash': 4248210736, 'isEnabled': True, 'isVisible': True}, {'plugHash': 902052880, 'isEnabled': True, 'isVisible': True}, {'plugHash': 1390278942, 'isEnabled': True, 'isVisible': False}, {'plugHash': 3581342943, 'isEnabled': True, 'isVisible': False}, {'plugHash': 166910052, 'isEnabled': True, 'isVisible': False}, {'plugHash': 2807591295, 'isEnabled': True, 'isVisible': False}, {'plugHash': 702981643, 'isEnabled': True, 'isVisible': True}, {'plugHash': 4173924323, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3727270518, 'isEnabled': True, 'isVisible': True}]
    def __get_item_component_sockets(self, profile):
        item_component_sockets = {}
        for instance_id, sockets in profile['itemComponents']['sockets']['data'].items():
            item_component_sockets[int(instance_id)] = sockets['sockets']
        
        return item_component_sockets

    # returns a dictionary of all items in the profile, keyed by the instance_id and joined with itemComponents and sockets
    def get_all_inventory_items(self):
        inventory_items = self.__get_inventory_items(self.profile)
        item_component_instances = self.__get_item_component_instances(self.profile)
        item_component_sockets = self.__get_item_component_sockets(self.profile)

        # join the instances and sockets to the inventory items when present
        for instance_id, item in inventory_items.items():
            item['itemComponents'] = item_component_instances.get(instance_id, None)
            item['sockets'] = item_component_sockets.get(instance_id, None)

        return inventory_items

    # expects the output of `get_all_inventory_items` and returns a list of all armor items
    def get_armor_dict(self, all_items=None): 
        if all_items is None:
            all_items = self.get_all_inventory_items()

        armor_items = {}

        for item in all_items.values():
            armor = self.convert_to_armor(item)
            if armor is not None:
                armor_items[armor.instance_id] = armor

        return armor_items

    # given an item from `get_all_inventory_items` turn it into an Armor object joined with information from other manifests
    # yeah... this is a mess.  if there is a better way to do this, I'd love to hear it
    # bungie's API has plugs for armor stats, 4 per armor piece and they each have 3 of the stats on them
    # also, if the armor is artifice, we have to parse that out as a separate socket by name as well
    def convert_to_armor(self, item):

        # print(json.dumps(item, indent=4))

        if item is None or 'itemHash' not in item or 'itemInstanceId' not in item:
            return None

        instance_id = int(item['itemInstanceId'])
        item_hash = int(item['itemHash'])
        item_definition = self.item_definitions[str(item_hash)]
        item_type = item_definition['itemType']

        if item_type == self.ARMOR_ITEM_TYPE:
            mobility = 0
            resilience = 0
            recovery = 0
            discipline = 0
            intellect = 0
            strength = 0
            is_artifice = False

            item_name = item_definition['displayProperties']['name']

            if instance_id is None:
                print(f'No instance ID for item {item_hash} - {item_definition}')
                return None

            item_components = item.get('itemComponents', None)
            if item_components is None:
                print(f'No itemComponents for item {item_hash} - {item_definition}')
                return None

            sockets = item.get('sockets', None)

            if sockets is None:
                print(f'No sockets for item {item_hash} - {item_definition}')
                return None

            for socket in sockets:
                # if it doesn't have a `plugHash` we don't care about it
                if 'plugHash' not in socket:
                    continue

                plug_hash = str(socket['plugHash'])

                plug_definition = self.item_definitions[plug_hash]

                if plug_definition is None:
                    print(f'No plug definition for plug {plug_hash}')
                    continue

                # print(json.dumps(plug_definition, indent=4))

                plug_name = plug_definition['displayProperties']['name']

                if plug_name == "Artifice Armor":
                    is_artifice = True
                    continue

                investment_stats = plug_definition.get('investmentStats', None)

                # we're looking for the 4 plugs that have 3 investment stats each
                # these are in groups of Mob/Res/Rec and Dis/Int/Str
                # there's another possible slot here if it is masterworked
                # or it has a stat mod on it where the length can be 7, we don't want that
                if investment_stats is None:
                    continue
                elif len(investment_stats) != 3: # masterworked/stat modded armor has 7 stats
                    # print(json.dumps(plug_definition, indent=4))
                    continue

                for stat in investment_stats:
                    stat_hash = str(stat['statTypeHash'])
                    stat_value = stat['value']

                    if stat_value == 0:
                        continue
                    elif stat_hash == self.MOBILITY_ID:
                        mobility += stat_value
                    elif stat_hash == self.RESILIENCE_ID:
                        resilience += stat_value
                    elif stat_hash == self.RECOVERY_ID:
                        recovery += stat_value
                    elif stat_hash == self.DISCIPLINE_ID:
                        discipline += stat_value
                    elif stat_hash == self.INTELLECT_ID:
                        intellect += stat_value
                    elif stat_hash == self.STRENGTH_ID:
                        strength += stat_value
                    else:
                        print(f'Unknown stat hash {stat_hash} for plug {plug_hash}')

    
            rarity = item_definition['inventory']['tierTypeName']
            slot = item_definition.get('itemTypeDisplayName', 'Unknown')
            power = item_components['primaryStat']['value']

            # there's a way to determine this with sockets/plugs, but it is gross, I think checking for energy of 10 cleaner on armor
            is_masterworked = item_components['energy']['energyCapacity'] == 10

            if slot == "Warlock Bond" or slot == "Titan Mark" or slot == "Hunter Cloak":
                slot = "Class Item"

            d2_class = self.CLASS_MAP.get(item_definition['classType'], 'Unknown')

            armor = Armor(
                item_name=item_name,
                item_hash=item_hash,
                instance_id=instance_id,
                rarity=rarity,
                slot=slot,
                power=power,
                mobility=mobility,
                resilience=resilience,
                recovery=recovery,
                discipline=discipline,
                intellect=intellect,
                strength=strength,
                is_artifice=is_artifice,
                is_masterworked=is_masterworked,
                d2_class=d2_class
            )
            return armor
