from collections import defaultdict
from dataclasses import dataclass, field
from src.armor import Armor, ProfileOutfits


# holds the stat combination (ex: mob, or mob/res/str) and whether it is unique for this armor piece or not
@dataclass
class PinnacleStats:
    stat_combination: str = None
    is_unique: bool = True

    def __hash__(self):
        return hash(self.stat_combination)

    def __eq__(self, other):
        # when adding to a set, we just want to compare the stat_combination and not uniqueness
        return self.stat_combination == other.stat_combination

    def __str__(self):
        if self.is_unique:
            return f"{self.stat_combination}"
        else:
            return f"~{self.stat_combination}~"  # wrap in ~ to indicate that it is not unique


# Holds a piece of armor, and a set of exotic and stat combinations that are in pinnacle outfits
@dataclass
class ArmorPinnacleStats:
    armor: Armor

    # a dict of the exotic armor name to a set of PinnacleStats combinations that were in pinnacle outfits
    exotic_to_pinnacle_stats: dict = field(default_factory=lambda: {})

    @property
    def item_name(self):
        return self.armor.item_name

    @property
    def d2_class(self):
        return self.armor.d2_class

    @property
    def pinnacle_exotic_count(self):
        return len(self.exotic_to_pinnacle_stats)

    @property
    def total_pinnacle_outfits(self):
        return sum(
            [
                len(stat_combinations)
                for stat_combinations in self.exotic_to_pinnacle_stats.values()
            ]
        )

    @property
    def unique_pinnacle_outfits(self):
        return sum(
            [
                len(
                    [
                        stat_combination
                        for stat_combination in stat_combinations
                        if stat_combination.is_unique
                    ]
                )
                for stat_combinations in self.exotic_to_pinnacle_stats.values()
            ]
        )

    @property
    def is_exotic(self):
        return self.armor.is_exotic

    def __hash__(self):
        return hash(self.armor.instance_id)

    def __str__(self):
        armor = self.armor
        string = f"""id:{armor.instance_id} -- {armor.item_name} -- {armor.slot} -- m:{armor.mobility} r:{armor.resilience} r:{armor.recovery} d:{armor.discipline} i:{armor.intellect} s:{armor.strength} Σ:{armor.total_stats} α:{"T" if armor.is_artifice else "F"}-- total pinnacle outfits: {self.total_pinnacle_outfits} -- unique pinnacle outfits: {self.unique_pinnacle_outfits}"""
        for exotic, stat_combinations in sorted(
            self.exotic_to_pinnacle_stats.items(), key=lambda x: -len(x[1])
        ):
            # sort on the stat_combination field so that the output is deterministic
            joined_stat_combinations = "  ".join(
                sorted(
                    [str(stat_combination) for stat_combination in stat_combinations]
                )
            )

            unique_stat_combinations = len(
                [
                    stat_combination
                    for stat_combination in stat_combinations
                    if stat_combination.is_unique
                ]
            )
            string += f"\n\t {exotic} - {unique_stat_combinations} - {joined_stat_combinations}"

        return string


def find_field_ordinal(field_name, df):
    for i, name in enumerate(df.columns):
        if name == field_name:
            return i
    return None


# Returns a dictionary that maps the weighted column name to a tuple of
# the weighted column ordinal and the max column ordinal
def find_weighted_max_column_pairs(df):
    weighted_max_pairs = {}
    for i, name in enumerate(df.columns):
        if name.startswith("weighted_"):
            max_name = name + "_max"
            # strip weighted_ from the name
            stripped_name = name[9:]
            # shorten each part to the first three characters
            stripped_name = "/".join([part[:3] for part in stripped_name.split("_")])
            if max_name in df.columns:
                weighted_max_pairs[stripped_name] = (
                    i,
                    find_field_ordinal(max_name, df),
                )
    return weighted_max_pairs


# for each piece of armor, find the outfits where it is in a pinnacle outfit and identify the exotic and stat combinations that was pinnacle
def create_armor_pinnacle_stats_list(d2_class, armor_dict, outfits_df_max):
    armor_hash_to_name = {
        armor.item_hash: armor.item_name
        for armor in armor_dict.values()
        if armor.d2_class == d2_class
    }
    armor_to_exotic_to_set = {
        armor: defaultdict(set)
        for armor in armor_dict.values()
        if armor.d2_class == d2_class
    }

    helmet_ordinal = find_field_ordinal("helmet", outfits_df_max)
    gauntlets_ordinal = find_field_ordinal("gauntlets", outfits_df_max)
    chest_ordinal = find_field_ordinal("chest_armor", outfits_df_max)
    leg_ordinal = find_field_ordinal("leg_armor", outfits_df_max)
    class_item_ordinal = find_field_ordinal("class_item", outfits_df_max)
    exotic_hash_ordinal = find_field_ordinal("exotic_hash", outfits_df_max)

    weighted_max_pairs_dict = find_weighted_max_column_pairs(outfits_df_max)

    # create a dictionary that is a hash where the key is Armor and the value is
    # another hash of `exotic_name` to a set of stat combinations where this armor is pinnacle
    for row in outfits_df_max.iter_rows():
        helmet_id = row[helmet_ordinal]
        gauntlets_id = row[gauntlets_ordinal]
        chest_id = row[chest_ordinal]
        leg_id = row[leg_ordinal]
        class_item_id = row[class_item_ordinal]
        exotic_hash = row[exotic_hash_ordinal]

        exotic_name = "No Exotic"

        if exotic_hash != ProfileOutfits.NO_EXOTIC_HASH:
            exotic_name = armor_hash_to_name[exotic_hash]

        for key, value in weighted_max_pairs_dict.items():
            if row[value[0]] == row[value[1]]:
                armor_to_exotic_to_set[armor_dict[helmet_id]][exotic_name].add(
                    PinnacleStats(key)
                )
                armor_to_exotic_to_set[armor_dict[gauntlets_id]][exotic_name].add(
                    PinnacleStats(key)
                )
                armor_to_exotic_to_set[armor_dict[chest_id]][exotic_name].add(
                    PinnacleStats(key)
                )
                armor_to_exotic_to_set[armor_dict[leg_id]][exotic_name].add(
                    PinnacleStats(key)
                )
                armor_to_exotic_to_set[armor_dict[class_item_id]][exotic_name].add(
                    PinnacleStats(key)
                )

    # turn the armor_to_exotic_set into a list of ArmorPinnacleStats, turn the defaultdict(set) into a dict
    armor_pinnacle_stats_list = [
        ArmorPinnacleStats(armor, dict(exotic_to_set))
        for armor, exotic_to_set in armor_to_exotic_to_set.items()
    ]

    for armor_pinnacle_stats in armor_pinnacle_stats_list:
        armor = armor_pinnacle_stats.armor
        exotic_to_pinnacle_stats = armor_pinnacle_stats.exotic_to_pinnacle_stats

        for exotic, pinnacle_stat_combinations in exotic_to_pinnacle_stats.items():
            for other_armor_pinnacle_stats in armor_pinnacle_stats_list:
                if (
                    other_armor_pinnacle_stats.armor.slot != armor.slot
                ):  # if it is in another slot, it isn't fungible
                    continue
                if other_armor_pinnacle_stats.armor == armor:  # same armor piece
                    continue

                # only compare an exotic to another instance of the same exotic
                if (
                    other_armor_pinnacle_stats.armor.is_exotic
                    and other_armor_pinnacle_stats.armor.item_name != exotic
                ):
                    continue

                if exotic in other_armor_pinnacle_stats.exotic_to_pinnacle_stats:
                    for pinnacle_stat in pinnacle_stat_combinations:
                        # if we still think it is unique, but find that the other armor has this same pinnacle stat, mark it as not unique
                        if (
                            pinnacle_stat
                            in other_armor_pinnacle_stats.exotic_to_pinnacle_stats[
                                exotic
                            ]
                        ):
                            pinnacle_stat.is_unique = False

    return armor_pinnacle_stats_list


# prints out the legendary armor pieces and the exotic and stat combinations where this armor piece was in a pinnacle outfit
def legendary_armor_to_pinnacle_outfits_report(
    d2_class, armor_dict, pinnacle_outfits_df
):
    armor_pinnacle_stats_list = create_armor_pinnacle_stats_list(
        d2_class, armor_dict, pinnacle_outfits_df
    )

    num = 0
    for armor_pinnacle_stats in sorted(
        armor_pinnacle_stats_list,
        key=lambda x: (x.unique_pinnacle_outfits, x.total_pinnacle_outfits),
        reverse=True,
    ):
        if armor_pinnacle_stats.is_exotic:
            continue
        num += 1
        print(armor_pinnacle_stats)
    print(f"Total pieces: {num}")


# prints out the exotic armor pieces and the stat combinations where this armor piece was in a pinnacle outfit
# sorts by exotic name and then by the number of pinnacle outfits
def exotic_armor_to_pinnacle_outfits_report(d2_class, armor_dict, pinnacle_outfits_df):
    armor_pinnacle_stats_list = create_armor_pinnacle_stats_list(
        d2_class, armor_dict, pinnacle_outfits_df
    )

    num = 0
    for armor_pinnacle_stats in sorted(
        armor_pinnacle_stats_list,
        key=lambda x: (
            x.item_name,
            -x.unique_pinnacle_outfits,
            -x.total_pinnacle_outfits,
        ),
    ):
        if not armor_pinnacle_stats.is_exotic:
            continue
        num += 1
        print(armor_pinnacle_stats)
    print(f"Total pieces: {num}")
