# functions to parse the profile data and create the Dict of Armor the user has on all characters and in the vault
from dataclasses import dataclass, field
import random

from itertools import product
from collections import defaultdict

import polars as pl
from polars import col
from itertools import combinations

random.seed(42)


def random_64_int():
    return random.randint(0, 9223372036854775807)


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
    random_exotic_perks: tuple = field(default_factory=tuple)

    @property
    def is_exotic(self):
        return self.rarity == "Exotic"

    @property
    def total_stats(self):
        return (
            self.mobility
            + self.resilience
            + self.recovery
            + self.discipline
            + self.intellect
            + self.strength
        )

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

    CLASS_MAP = {0: "Titan", 1: "Hunter", 2: "Warlock"}

    ARMOR_ITEM_TYPE = 2

    def __init__(self, profile, item_definitions, stat_definitions):
        self.profile = profile
        self.item_definitions = item_definitions
        self.stat_definitions = stat_definitions

    # spin through the profile data and find all inventory items on the character and in character equipment
    # example for item instance: {'itemHash': 2244604734, 'itemInstanceId': '6917529860806551003', 'quantity': 1, 'bindStatus': 0, 'location': 2, 'bucketHash': 138197802, 'transferStatus': 0, 'lockable': True, 'state': 5, 'dismantlePermission': 2, 'isWrapper': False, 'tooltipNotificationIndexes': [], 'versionNumber': 0 }
    def __get_inventory_items(self, profile):
        items = {}
        for character_id in profile["profile"]["data"]["characterIds"]:
            for item in profile["characterEquipment"]["data"][character_id]["items"]:
                instance_id = int(item.get("itemInstanceId", item["itemHash"]))
                items[instance_id] = item
            for item in profile["characterInventories"]["data"][character_id]["items"]:
                instance_id = int(item.get("itemInstanceId", item["itemHash"]))
                items[instance_id] = item

        for item in profile["profileInventory"]["data"]["items"]:
            instance_id = int(item.get("itemInstanceId", item["itemHash"]))
            items[instance_id] = item

        return items

    # example for instance: {'damageType': 0, 'primaryStat': {'statHash': 3897883278, 'value': 1810}, 'itemLevel': 181, 'quality': 0, 'isEquipped': False, 'canEquip': False, 'equipRequiredLevel': 50, 'unlockHashesRequiredToEquip': [1368285237], 'cannotEquipReason': 16, 'energy': {'energyTypeHash': 4069572561, 'energyType': 3, 'energyCapacity': 10, 'energyUsed': 0, 'energyUnused': 10}
    def __get_item_component_instances(self, profile):
        item_component_instances = {}
        for instance_id, instance in profile["itemComponents"]["instances"][
            "data"
        ].items():
            item_component_instances[int(instance_id)] = instance

        return item_component_instances

    # example sockets for instance: sockets': [{'plugHash': 1980618587, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3820147479, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3820147479, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3820147479, 'isEnabled': True, 'isVisible': True}, {'plugHash': 4248210736, 'isEnabled': True, 'isVisible': True}, {'plugHash': 902052880, 'isEnabled': True, 'isVisible': True}, {'plugHash': 1390278942, 'isEnabled': True, 'isVisible': False}, {'plugHash': 3581342943, 'isEnabled': True, 'isVisible': False}, {'plugHash': 166910052, 'isEnabled': True, 'isVisible': False}, {'plugHash': 2807591295, 'isEnabled': True, 'isVisible': False}, {'plugHash': 702981643, 'isEnabled': True, 'isVisible': True}, {'plugHash': 4173924323, 'isEnabled': True, 'isVisible': True}, {'plugHash': 3727270518, 'isEnabled': True, 'isVisible': True}]
    def __get_item_component_sockets(self, profile):
        item_component_sockets = {}
        for instance_id, sockets in profile["itemComponents"]["sockets"][
            "data"
        ].items():
            item_component_sockets[int(instance_id)] = sockets["sockets"]

        return item_component_sockets

    # returns a dictionary of all items in the profile, keyed by the instance_id and joined with itemComponents and sockets
    def get_all_inventory_items(self):
        inventory_items = self.__get_inventory_items(self.profile)
        item_component_instances = self.__get_item_component_instances(self.profile)
        item_component_sockets = self.__get_item_component_sockets(self.profile)

        # join the instances and sockets to the inventory items when present
        for instance_id, item in inventory_items.items():
            item["itemComponents"] = item_component_instances.get(instance_id, None)
            item["sockets"] = item_component_sockets.get(instance_id, None)

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

        if item is None or "itemHash" not in item or "itemInstanceId" not in item:
            return None

        instance_id = int(item["itemInstanceId"])
        item_hash = int(item["itemHash"])
        item_definition = self.item_definitions[str(item_hash)]
        item_type = item_definition["itemType"]

        if item_type == self.ARMOR_ITEM_TYPE:
            mobility = 0
            resilience = 0
            recovery = 0
            discipline = 0
            intellect = 0
            strength = 0
            is_artifice = False

            item_name = item_definition["displayProperties"]["name"]

            if instance_id is None:
                print(f"No instance ID for item {item_hash} - {item_definition}")
                return None

            item_components = item.get("itemComponents", None)
            if item_components is None:
                print(f"No itemComponents for item {item_hash} - {item_definition}")
                return None

            sockets = item.get("sockets", None)

            if sockets is None:
                print(f"No sockets for item {item_hash} - {item_definition}")
                return None

            intrinsic_stats = item_definition.get("investmentStats", None)
            if intrinsic_stats is not None:
                for stat in intrinsic_stats:
                    stat_hash = str(stat["statTypeHash"])
                    stat_value = stat["value"]

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
                        print(
                            f"Unknown stat hash {stat_hash} in intrinsic stats of item {item_hash}"
                        )

            rarity = item_definition["inventory"]["tierTypeName"]
            slot = item_definition.get("itemTypeDisplayName", "Unknown")
            power = item_components["primaryStat"]["value"]

            # there's a way to determine this with sockets/plugs, but it is gross, I think checking for energy of 10 cleaner on armor
            is_masterworked = item_components["energy"]["energyCapacity"] == 10

            if slot == "Warlock Bond" or slot == "Titan Mark" or slot == "Hunter Cloak":
                slot = "Class Item"

            d2_class = self.CLASS_MAP.get(item_definition["classType"], "Unknown")

            random_exotic_perks = list()

            for socket in sockets:
                # if it doesn't have a `plugHash` we don't care about it
                if "plugHash" not in socket:
                    continue

                plug_hash = str(socket["plugHash"])

                plug_definition = self.item_definitions[plug_hash]

                if plug_definition is None:
                    print(f"No plug definition for plug {plug_hash}")
                    continue

                plug_name = plug_definition["displayProperties"]["name"]

                if plug_name == "Artifice Armor":
                    is_artifice = True
                    continue

                if rarity == "Exotic" and slot == "Class Item":
                    if (
                        plug_definition["itemTypeAndTierDisplayName"]
                        == "Exotic Intrinsic"
                    ):
                        random_exotic_perks.append(
                            plug_definition["displayProperties"]["name"]
                        )

                investment_stats = plug_definition.get("investmentStats", None)

                # we're looking for the 4 plugs that have 3 investment stats each
                # these are in groups of Mob/Res/Rec and Dis/Int/Str
                # there's another possible slot here if it is masterworked
                # or it has a stat mod on it where the length can be 7, we don't want that
                if investment_stats is None:
                    continue
                elif (
                    len(investment_stats) != 3
                ):  # masterworked/stat modded armor has 7 stats
                    # print(json.dumps(plug_definition, indent=4))
                    continue

                for stat in investment_stats:
                    stat_hash = str(stat["statTypeHash"])
                    stat_value = stat["value"]

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
                        print(f"Unknown stat hash {stat_hash} for plug {plug_hash}")

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
                d2_class=d2_class,
                random_exotic_perks=tuple(random_exotic_perks),
            )
            return armor


class ProfileOutfits:
    # masterworking helmet, gauntlets, chest armor, leg armor, and class item gives a +10 bonus to each stat in an outfit
    FULL_MASTERWORK_STAT_BONUS = 10

    NO_EXOTIC_HASH = -1

    def __init__(self, armor_dict):
        self.armor_dict = armor_dict
        self.artifice_permutations = {
            i: self.generate_artifice_permutations(i) for i in range(6)
        }

    # we want to generate outfits for a given class
    # The high-level algorithm is:

    # 1. filter armor to only include armor for the given class, also filter out class items
    # 2. segregate the armor by whether it is exotic or not
    # 3. group the exotic and non-exotic armor by slot
    def filter_and_group_armor(
        self,
        d2_class,
        slots=["Helmet", "Gauntlets", "Chest Armor", "Leg Armor", "Class Item"],
        include_ignored_armor = True
    ):
        exotic_armor = defaultdict(list)
        non_exotic_armor = defaultdict(list)
        for armor in self.armor_dict.values():
            if armor.d2_class == d2_class and armor.slot in slots:
                if armor.is_exotic:
                    if include_ignored_armor == True or armor.ignored == False:
                        exotic_armor[armor.slot].append(armor)
                else:
                    if include_ignored_armor == True or armor.ignored == False:
                        non_exotic_armor[armor.slot].append(armor)

        if "Class Item" in non_exotic_armor:
            # class items all have the same stats, the only option is if one is artifice.  Pick one and remove the rest
            for armor in non_exotic_armor["Class Item"]:
                if armor.is_artifice:
                    non_exotic_armor["Class Item"] = [armor]
                    break

            if len(non_exotic_armor["Class Item"]) > 1:
                non_exotic_armor["Class Item"] = [non_exotic_armor["Class Item"][0]]

        return exotic_armor, non_exotic_armor

    # 4. generate all possible outfits using non-exotic armor
    # 5. add in all possible outfits using a single piece of exotic armor
    def generate_class_outfits(self, d2_class, include_ignored_armor):
        outfits = []

        # filter armor to only include armor for the given class and slots
        exotic_armor, non_exotic_armor = self.filter_and_group_armor(
            d2_class, ["Helmet", "Gauntlets", "Chest Armor", "Leg Armor", "Class Item"], include_ignored_armor
        )

        # append all possible non-exotic armor combinations

        # do we care about non-exotic armor?
        self.append_outfit_permutations(
            outfits,
            non_exotic_armor["Helmet"],
            non_exotic_armor["Gauntlets"],
            non_exotic_armor["Chest Armor"],
            non_exotic_armor["Leg Armor"],
            non_exotic_armor["Class Item"],
        )

        # we can only have exotic armor in a single slot, add all outfits with a single slot of exotic armor
        self.append_outfit_permutations(
            outfits,
            exotic_armor["Helmet"],
            non_exotic_armor["Gauntlets"],
            non_exotic_armor["Chest Armor"],
            non_exotic_armor["Leg Armor"],
            non_exotic_armor["Class Item"],
        )
        self.append_outfit_permutations(
            outfits,
            non_exotic_armor["Helmet"],
            exotic_armor["Gauntlets"],
            non_exotic_armor["Chest Armor"],
            non_exotic_armor["Leg Armor"],
            non_exotic_armor["Class Item"],
        )
        self.append_outfit_permutations(
            outfits,
            non_exotic_armor["Helmet"],
            non_exotic_armor["Gauntlets"],
            exotic_armor["Chest Armor"],
            non_exotic_armor["Leg Armor"],
            non_exotic_armor["Class Item"],
        )
        self.append_outfit_permutations(
            outfits,
            non_exotic_armor["Helmet"],
            non_exotic_armor["Gauntlets"],
            non_exotic_armor["Chest Armor"],
            exotic_armor["Leg Armor"],
            non_exotic_armor["Class Item"],
        )

        # as of right now, there is no exotic class item.  there will be in TFS, but unless it has stats better than a legendary class item, we don't care
        # append_outfit_permutations(outfits, non_exotic_armor["Helmet"], non_exotic_armor["Gauntlets"], non_exotic_armor["Chest Armor"], non_exotic_armor["Leg Armor"], exotic_armor["Class Item"])

        return outfits

    def generate_artifice_permutations(self, num_artifice):
        # Generate all permutations artifice mods that could be assigned to each stat
        all_permutations = product(range(0, num_artifice + 1), repeat=6)

        # Filter the permutations to only include ones with that have the right number of artifice applied
        valid_permutations = [
            perm for perm in all_permutations if sum(perm) == num_artifice
        ]

        # for each artifice in a slot, it applies a +3 bonus to that stat
        return [tuple(i * 3 for i in perm) for perm in valid_permutations]

    def round_to_useful_tier(self, stat):
        # stats above 100 aren't useful.  T10 is the highest tier
        if stat > 100:
            return 100

        # half tiers can be useful as there are 5 point mods, so we want to round down to the nearest 5
        # return stat - (stat % 5)

        # EXPERMIENTAL: round to the nearest 10 and ignore half tiers
        return stat - (stat % 10)

    def append_outfit_permutations(
        self, outfits, helmets, gauntlets, chest_armors, leg_armors, class_items
    ):
        for helmet, gauntlet, chest_armor, leg_armor, class_item in product(
            helmets, gauntlets, chest_armors, leg_armors, class_items
        ):
            # we want to add the masterwork stat bonus
            # armor pieces have base stats, without any mods or masterworking
            base_mobility = (
                self.FULL_MASTERWORK_STAT_BONUS
                + helmet.mobility
                + gauntlet.mobility
                + chest_armor.mobility
                + leg_armor.mobility
                + class_item.mobility
            )
            base_resilience = (
                self.FULL_MASTERWORK_STAT_BONUS
                + helmet.resilience
                + gauntlet.resilience
                + chest_armor.resilience
                + leg_armor.resilience
                + class_item.resilience
            )
            base_recovery = (
                self.FULL_MASTERWORK_STAT_BONUS
                + helmet.recovery
                + gauntlet.recovery
                + chest_armor.recovery
                + leg_armor.recovery
                + class_item.recovery
            )
            base_discipline = (
                self.FULL_MASTERWORK_STAT_BONUS
                + helmet.discipline
                + gauntlet.discipline
                + chest_armor.discipline
                + leg_armor.discipline
                + class_item.discipline
            )
            base_intellect = (
                self.FULL_MASTERWORK_STAT_BONUS
                + helmet.intellect
                + gauntlet.intellect
                + chest_armor.intellect
                + leg_armor.intellect
                + class_item.intellect
            )
            base_strength = (
                self.FULL_MASTERWORK_STAT_BONUS
                + helmet.strength
                + gauntlet.strength
                + chest_armor.strength
                + leg_armor.strength
                + class_item.strength
            )

            num_artifice = (
                helmet.is_artifice
                + gauntlet.is_artifice
                + chest_armor.is_artifice
                + leg_armor.is_artifice
                + class_item.is_artifice
            )

            # should be at most one exotic armor piece in an outfit
            exotic_hash = self.NO_EXOTIC_HASH
            for armor in [helmet, gauntlet, chest_armor, leg_armor, class_item]:
                if armor.is_exotic:
                    exotic_hash = armor.item_hash
                    break

            self.append_outfit_permutation(
                outfits,
                base_mobility,
                base_resilience,
                base_recovery,
                base_discipline,
                base_intellect,
                base_strength,
                helmet.instance_id,
                gauntlet.instance_id,
                chest_armor.instance_id,
                leg_armor.instance_id,
                class_item.instance_id,
                exotic_hash,
                num_artifice,
            )

    # recursively apply any artifice to the outfit
    def append_outfit_permutation(
        self,
        outfits,
        mobility,
        resilience,
        recovery,
        discipline,
        intellect,
        strength,
        helmet,
        gauntlets,
        chest_armor,
        leg_armor,
        class_item,
        exotic_hash,
        num_artifice,
    ):
        if num_artifice == 0:
            outfits.append(
                (
                    self.round_to_useful_tier(mobility),
                    self.round_to_useful_tier(resilience),
                    self.round_to_useful_tier(recovery),
                    self.round_to_useful_tier(discipline),
                    self.round_to_useful_tier(intellect),
                    self.round_to_useful_tier(strength),
                    helmet,
                    gauntlets,
                    chest_armor,
                    leg_armor,
                    class_item,
                    exotic_hash,
                    num_artifice,
                )
            )
        else:
            # create a set of stats that we can use to only build outfits with a unique set of stats, some combinations don't create unique useful tiers
            # ex: if mobility is 27 adding +3 is the same as adding +6, they both round to 30
            useful_stats_permutations = set()

            for artifice_bonus in self.artifice_permutations[num_artifice]:
                useful_stats_permutations.add(
                    (
                        self.round_to_useful_tier(mobility + artifice_bonus[0]),
                        self.round_to_useful_tier(resilience + artifice_bonus[1]),
                        self.round_to_useful_tier(recovery + artifice_bonus[2]),
                        self.round_to_useful_tier(discipline + artifice_bonus[3]),
                        self.round_to_useful_tier(intellect + artifice_bonus[4]),
                        self.round_to_useful_tier(strength + artifice_bonus[5]),
                    )
                )
            for useful_stats in useful_stats_permutations:
                outfits.append(
                    (
                        useful_stats[0],
                        useful_stats[1],
                        useful_stats[2],
                        useful_stats[3],
                        useful_stats[4],
                        useful_stats[5],
                        helmet,
                        gauntlets,
                        chest_armor,
                        leg_armor,
                        class_item,
                        exotic_hash,
                        num_artifice,
                    )
                )

    # identify all non-class item armor that has the same or worse stats than another piece of armor of the same rarity and type
    def find_eclipsed_armor(self):
        eclipsed_armor = []
        armor_list = list(self.armor_dict.values())

        # sort by power level, low to high
        armor_list.sort(key=lambda x: x.power)

        for i, armor in enumerate(armor_list):
            if armor.slot == "Class Item":
                continue
            for other_armor in armor_list[i + 1 :]:
                if armor.rarity != other_armor.rarity:
                    continue
                # only compare exotic armor pieces that are the same item
                if (
                    armor.rarity == "Exotic"
                    and armor.item_hash != other_armor.item_hash
                ):
                    continue
                if (
                    armor.class_slot == other_armor.class_slot
                    and armor.instance_id != other_armor.instance_id
                ):
                    if (
                        armor.mobility <= other_armor.mobility
                        and armor.resilience <= other_armor.resilience
                        and armor.recovery <= other_armor.recovery
                        and armor.discipline <= other_armor.discipline
                        and armor.intellect <= other_armor.intellect
                        and armor.strength <= other_armor.strength
                    ):
                        eclipsed_armor.append((armor, other_armor))
                    elif (
                        other_armor.mobility <= armor.mobility
                        and other_armor.resilience <= armor.resilience
                        and other_armor.recovery <= armor.recovery
                        and other_armor.discipline <= armor.discipline
                        and other_armor.intellect <= armor.intellect
                        and other_armor.strength <= armor.strength
                    ):
                        eclipsed_armor.append((other_armor, armor))
        return eclipsed_armor


class PinnacleOutfits:
    def __init__(self, outfits):
        self.outfits = outfits
        weighted_outfits_df = self.__generate_weighted_outfits_df(outfits)
        self.weighted_outfits_max_df = self.__weighted_outfits_max(weighted_outfits_df)
        self.weighted_outfits_df = self.__joined_outfits_max(
            weighted_outfits_df, self.weighted_outfits_max_df
        )
        self.pinnacle_outfits_df = self.__pinnacle_outfits_df(self.weighted_outfits_df)

    # Create weighted columns for stat combinations, this weight is used to determine how much that stat is worth in that combination
    # adding that stat to all other stats to determine the outfits worth for that combo
    # this lets us compare two outfits and allow the spike in one stat to offset some lesser stats in others we don't care about for that combo
    # we can then search through and find the maximum values for each combo and keep those and reject outfits/armor pieces that aren't at a max
    #
    # `stat_count` is the number of stats we want to combine in a weighted sum.
    # a value of `3` (the default) would give us all 3 stat combos: mob/res/rec, mob/res/dis, mob/res/int, ...
    # `weight` is how much we want to value the stats associated with the weighted column over unweighted stats
    def __generate_weighted_outfits_df(self, outfits, stat_count=3, weight=2):
        column_names = [
            "mobility",
            "resilience",
            "recovery",
            "discipline",
            "intellect",
            "strength",
            "helmet",
            "gauntlets",
            "chest_armor",
            "leg_armor",
            "class_item",
            "exotic_hash",
            "num_artifice",
        ]

        schema = {}

        for column_name in column_names:
            schema[column_name] = pl.Int64

        outfits_df = pl.DataFrame(outfits, schema=schema)

        # the stats that can be weighted
        stats = [
            "mobility",
            "resilience",
            "recovery",
            "discipline",
            "intellect",
            "strength",
        ]

        # Generate the weighted columns for each combination
        weighted_columns = []

        combos = list(combinations(stats, stat_count))

        for combo in combos:
            # Create a list of the column expressions for the weighted sum
            column_exprs = [
                (col(stat) * weight if stat in combo else col(stat)) for stat in stats
            ]

            # Create the alias for the weighted column
            alias = "weighted_" + "_".join(combo)

            # Add the weighted column to the list
            weighted_columns.append(sum(column_exprs).alias(alias))

        return outfits_df.with_columns(*weighted_columns)

    # find the max for each weighted column, group by exotic hash so we find the best outfit for each exotic armor piece
    def __weighted_outfits_max(self, outfits_df):
        return outfits_df.group_by("exotic_hash").max()

    def __joined_outfits_max(self, weighted_outfits_df, weighted_outfits_max_df):
        return weighted_outfits_df.join(
            weighted_outfits_max_df, on="exotic_hash", suffix="_max"
        )

    def __pinnacle_outfits_df(self, joined_outfits_df):
        # filter the original DataFrame to only include rows where it has any `weighted_*` column that matches the max value for that exotic_hash

        # Get the column names starting with 'weighted_' and don't end in '_max'
        weighted_columns = [
            col
            for col in joined_outfits_df.columns
            if (col.startswith("weighted_") and not col.endswith("_max"))
        ]

        # check if the weighted column for this outfit is the same as the max/best outfit for this exotic
        conditions = [
            pl.col(name) == pl.col(f"{name}_max") for name in weighted_columns
        ]

        # Create a combined condition that is True if any of the conditions is True
        combined_condition = conditions[0]
        for condition in conditions[1:]:
            combined_condition = combined_condition | condition

        # filter rows where the outfit has at least one column that is the max value for that exotic
        pinnacle_outfits_df = joined_outfits_df.filter(combined_condition)
        # eclipsed_outfits_df = joined_outfits_df.filter(~combined_condition)

        # add a total_stats column to the dataframe that sums mobility, resilience, recovery, discipline, intellect, and strength
        pinnacle_outfits_df = pinnacle_outfits_df.with_columns(
            (
                col("mobility")
                + col("resilience")
                + col("recovery")
                + col("discipline")
                + col("intellect")
                + col("strength")
            ).alias("total_stats")
        )

        return pinnacle_outfits_df
