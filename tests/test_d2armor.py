import unittest
import random
from src.armor import Armor, ProfileOutfits, random_64_int

import json

random.seed(42)


class TestOutfits(unittest.TestCase):
    def armor_list_to_dict(self, armor_list):
        return {armor.instance_id: armor for armor in armor_list}

    def random_stat(self):
        return random.randint(1, 42)

    def random_armor(self, slot, rarity="Legendary", item_hash=None):
        if item_hash is None:
            item_hash = random_64_int()
        return Armor(
            slot=slot,
            rarity=rarity,
            item_hash=item_hash,
            mobility=self.random_stat(),
            resilience=self.random_stat(),
            recovery=self.random_stat(),
            discipline=self.random_stat(),
            intellect=self.random_stat(),
            strength=self.random_stat(),
        )

    def setUp(self):
        self.titan_helmet = Armor(
            slot="Helmet",
            mobility=6,
            resilience=6,
            recovery=6,
            discipline=6,
            intellect=6,
            strength=6,
            d2_class="Titan",
        )
        self.helmet = Armor(
            slot="Helmet",
            mobility=6,
            resilience=6,
            recovery=6,
            discipline=6,
            intellect=6,
            strength=6,
        )
        self.artifice_helmet = Armor(
            slot="Helmet",
            mobility=6,
            resilience=6,
            recovery=6,
            discipline=6,
            intellect=6,
            strength=6,
            is_artifice=True,
        )
        self.gauntlets = Armor(
            slot="Gauntlets",
            mobility=7,
            resilience=7,
            recovery=7,
            discipline=7,
            intellect=7,
            strength=7,
        )
        self.chest_armor = Armor(
            slot="Chest Armor",
            mobility=8,
            resilience=8,
            recovery=8,
            discipline=8,
            intellect=8,
            strength=8,
        )
        self.leg_armor = Armor(
            slot="Leg Armor",
            mobility=9,
            resilience=9,
            recovery=9,
            discipline=9,
            intellect=9,
            strength=9,
        )
        self.artifice_leg_armor = Armor(
            slot="Leg Armor",
            mobility=11,
            resilience=11,
            recovery=11,
            discipline=5,
            intellect=5,
            strength=20,
            is_artifice=True,
        )
        self.class_item = Armor(
            slot="Class Item",
            mobility=0,
            resilience=0,
            recovery=0,
            discipline=0,
            intellect=0,
            strength=0,
        )
        self.exotic_helmet = Armor(
            slot="Helmet",
            item_hash=200,
            rarity="Exotic",
            mobility=2,
            resilience=20,
            recovery=10,
            discipline=30,
            intellect=2,
            strength=2,
        )
        self.exotic_helmet2 = Armor(
            slot="Helmet",
            item_hash=300,
            rarity="Exotic",
            mobility=11,
            resilience=11,
            recovery=11,
            discipline=11,
            intellect=11,
            strength=11,
        )
        self.exotic_gauntlets = Armor(
            slot="Gauntlets",
            item_hash=400,
            rarity="Exotic",
            mobility=10,
            resilience=10,
            recovery=10,
            discipline=10,
            intellect=10,
            strength=10,
        )

        # all armor pieces in a dictionary keyed by instance_id
        self.armor_dict = self.armor_list_to_dict(
            [
                self.titan_helmet,
                self.helmet,
                self.artifice_helmet,
                self.gauntlets,
                self.chest_armor,
                self.leg_armor,
                self.artifice_leg_armor,
                self.class_item,
                self.exotic_helmet,
                self.exotic_helmet2,
                self.exotic_gauntlets,
            ]
        )

        # all unspecified stats are zero
        self.helmet_0 = Armor(slot="Helmet")
        self.gauntlets_0 = Armor(slot="Gauntlets")
        self.chest_armor_0 = Armor(slot="Chest Armor")
        self.leg_armor_0 = Armor(slot="Leg Armor")
        self.class_item_0 = Armor(slot="Class Item")

    def test_armor(self):
        armor = self.helmet
        self.assertEqual(armor.total_stats, 36)
        self.assertEqual(armor.class_slot, "Warlock Helmet")
        self.assertFalse(armor.is_exotic)

        exotic_armor = self.exotic_helmet
        self.assertTrue(exotic_armor.is_exotic)

    def test_filter_and_group_armor(self):
        profile_outfits = ProfileOutfits(self.armor_dict)
        exotic_armor, non_exotic_armor = profile_outfits.filter_and_group_armor(
            "Warlock"
        )

        self.assertIsNotNone(exotic_armor)
        self.assertEqual(len(exotic_armor), 2)
        self.assertEqual(
            exotic_armor["Helmet"], [self.exotic_helmet, self.exotic_helmet2]
        )
        self.assertEqual(exotic_armor["Gauntlets"], [self.exotic_gauntlets])
        self.assertIsNotNone(non_exotic_armor)
        self.assertEqual(len(non_exotic_armor), 5)
        self.assertEqual(
            non_exotic_armor["Helmet"], [self.helmet, self.artifice_helmet]
        )
        self.assertEqual(non_exotic_armor["Gauntlets"], [self.gauntlets])
        self.assertEqual(non_exotic_armor["Chest Armor"], [self.chest_armor])
        self.assertEqual(
            non_exotic_armor["Leg Armor"], [self.leg_armor, self.artifice_leg_armor]
        )
        self.assertEqual(non_exotic_armor["Class Item"], [self.class_item])

        exotic_armor, non_exotic_armor = profile_outfits.filter_and_group_armor("Titan")
        self.assertEqual(len(exotic_armor), 0)
        self.assertEqual(len(non_exotic_armor), 1)
        self.assertEqual(non_exotic_armor["Helmet"], [self.titan_helmet])

    def test_generate_class_outfits(self):
        armor_dict = self.armor_list_to_dict(
            [
                self.helmet,
                self.gauntlets,
                self.chest_armor,
                self.leg_armor,
                self.class_item,
                self.exotic_helmet,
                self.exotic_helmet2,
                self.exotic_gauntlets,
            ]
        )
        profile_outfits = ProfileOutfits(armor_dict)
        outfits = profile_outfits.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits), 4)

        # point totals would be 44 for each stat, but we round down to the nearest 10 for the tier
        self.assertEqual(
            outfits[0],
            (
                40,
                40,
                40,
                40,
                40,
                40,
                self.helmet.instance_id,
                self.gauntlets.instance_id,
                self.chest_armor.instance_id,
                self.leg_armor.instance_id,
                self.class_item.instance_id,
                -1,
                0,
            ),
        )
        self.assertEqual(
            outfits[1],
            (
                30,
                50,
                40,
                60,
                30,
                30,
                self.exotic_helmet.instance_id,
                self.gauntlets.instance_id,
                self.chest_armor.instance_id,
                self.leg_armor.instance_id,
                self.class_item.instance_id,
                self.exotic_helmet.item_hash,
                0,
            ),
        )
        self.assertEqual(
            outfits[2],
            (
                40,
                40,
                40,
                40,
                40,
                40,
                self.exotic_helmet2.instance_id,
                self.gauntlets.instance_id,
                self.chest_armor.instance_id,
                self.leg_armor.instance_id,
                self.class_item.instance_id,
                self.exotic_helmet2.item_hash,
                0,
            ),
        )
        self.assertEqual(
            outfits[3],
            (
                40,
                40,
                40,
                40,
                40,
                40,
                self.helmet.instance_id,
                self.exotic_gauntlets.instance_id,
                self.chest_armor.instance_id,
                self.leg_armor.instance_id,
                self.class_item.instance_id,
                400,
                0,
            ),
        )

    def test_generate_many_class_outfits(self):
        armor_list = []
        for i in range(10):
            armor_list.append(self.random_armor("Helmet"))
            armor_list.append(self.random_armor("Gauntlets"))
            armor_list.append(self.random_armor("Chest Armor"))
            armor_list.append(self.random_armor("Leg Armor"))
            armor_list.append(self.random_armor("Class Item"))

        armor_dict = self.armor_list_to_dict(armor_list)
        profile_outfits = ProfileOutfits(armor_dict)
        outfits = profile_outfits.generate_class_outfits("Warlock", True)
        # 4 slots with 20 pieces per slot, 10^4 = 10,000
        self.assertEqual(len(outfits), 10**4)

        for i in range(2):
            armor_list.append(self.random_armor("Helmet", "Exotic"))
            armor_list.append(self.random_armor("Gauntlets", "Exotic"))
            armor_list.append(self.random_armor("Leg Armor", "Exotic"))
            armor_list.append(self.random_armor("Chest Armor", "Exotic"))

        armor_dict = self.armor_list_to_dict(armor_list)
        profile_outfits = ProfileOutfits(armor_dict)
        outfits = profile_outfits.generate_class_outfits("Warlock", True)
        # same 4 slots with 10 legendary pieces per slot, but now 2 exotic pieces per slot that each need to be combined with 3 slots of 10 legendary pieces
        self.assertEqual(len(outfits), 10**4 + 8 * 10**3)

    def test_outfit_permutations_zero_artifice(self):
        no_artifice_armor_dict = self.armor_list_to_dict(
            [
                self.helmet_0,
                self.gauntlets_0,
                self.chest_armor_0,
                self.leg_armor_0,
                self.class_item_0,
            ]
        )

        profile_outfits = ProfileOutfits(no_artifice_armor_dict)
        outfits = profile_outfits.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits), 1)
        # stats in outfit are 10 as we're assuming all armor pieces are masterworked, even though they have all stats at zero
        self.assertEqual(
            outfits[0],
            (
                10,
                10,
                10,
                10,
                10,
                10,
                self.helmet_0.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                0,
            ),
        )

    def test_outfit_permutations_one_artifice_stats_zero(self):
        # if we have one piece of artifice armor, but the 3 points it gives doesn't increase a tier, we'll still only have 1 outfit
        artifice_helmet_0 = Armor(
            slot="Helmet", is_artifice=True
        )  # all stats still at zero
        one_artifice_armor_dict = self.armor_list_to_dict(
            [
                artifice_helmet_0,
                self.gauntlets_0,
                self.chest_armor_0,
                self.leg_armor_0,
                self.class_item_0,
            ]
        )

        profile_outfits = ProfileOutfits(one_artifice_armor_dict)
        outfits = profile_outfits.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits), 1)
        self.assertEqual(
            outfits[0],
            (
                10,
                10,
                10,
                10,
                10,
                10,
                artifice_helmet_0.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                1,
            ),
        )

    def test_outfit_permutations_one_artifice_stats_seven(self):
        # if we have one piece of artifice armor, but the 2 base points it has are enough to get it close enough to the next tier, we'll have 6 outfits, one for each stat bumped up
        artifice_helmet_7 = Armor(
            slot="Helmet",
            mobility=7,
            resilience=7,
            recovery=7,
            discipline=7,
            intellect=7,
            strength=7,
            is_artifice=True,
        )
        one_artifice_armor_dict = self.armor_list_to_dict(
            [
                artifice_helmet_7,
                self.gauntlets_0,
                self.chest_armor_0,
                self.leg_armor_0,
                self.class_item_0,
            ]
        )

        profile_outfits = ProfileOutfits(one_artifice_armor_dict)
        outfits = profile_outfits.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits), 6)
        self.assertIn(
            (
                20,
                10,
                10,
                10,
                10,
                10,
                artifice_helmet_7.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                1,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                20,
                10,
                10,
                10,
                10,
                artifice_helmet_7.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                1,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                20,
                10,
                10,
                10,
                artifice_helmet_7.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                1,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                10,
                20,
                10,
                10,
                artifice_helmet_7.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                1,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                10,
                10,
                20,
                10,
                artifice_helmet_7.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                1,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                10,
                10,
                10,
                20,
                artifice_helmet_7.instance_id,
                self.gauntlets_0.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                1,
            ),
            outfits,
        )

    def test_outfit_permutations_two_artifice_stats_four(self):
        # if we have two pieces of artifice armor, but we're starting with all stats ending in 4, we'll get 6 outfits as we can add 6 to each stat
        artifice_helmet_0 = Armor(
            slot="Helmet", is_artifice=True
        )  # all stats still at zero
        artifice_gauntlets_4 = Armor(
            slot="Gauntlets",
            mobility=4,
            resilience=4,
            recovery=4,
            discipline=4,
            intellect=4,
            strength=4,
            is_artifice=True,
        )

        two_artifice_armor_dict = self.armor_list_to_dict(
            [
                artifice_helmet_0,
                artifice_gauntlets_4,
                self.chest_armor_0,
                self.leg_armor_0,
                self.class_item_0,
            ]
        )

        profile_outfits = ProfileOutfits(two_artifice_armor_dict)
        outfits = profile_outfits.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits), 7)
        self.assertIn(
            (
                10,
                10,
                10,
                10,
                10,
                10,
                artifice_helmet_0.instance_id,
                artifice_gauntlets_4.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                2,
            ),
            outfits,
        )
        self.assertIn(
            (
                20,
                10,
                10,
                10,
                10,
                10,
                artifice_helmet_0.instance_id,
                artifice_gauntlets_4.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                2,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                20,
                10,
                10,
                10,
                10,
                artifice_helmet_0.instance_id,
                artifice_gauntlets_4.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                2,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                20,
                10,
                10,
                10,
                artifice_helmet_0.instance_id,
                artifice_gauntlets_4.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                2,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                10,
                20,
                10,
                10,
                artifice_helmet_0.instance_id,
                artifice_gauntlets_4.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                2,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                10,
                10,
                20,
                10,
                artifice_helmet_0.instance_id,
                artifice_gauntlets_4.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                2,
            ),
            outfits,
        )
        self.assertIn(
            (
                10,
                10,
                10,
                10,
                10,
                20,
                artifice_helmet_0.instance_id,
                artifice_gauntlets_4.instance_id,
                self.chest_armor_0.instance_id,
                self.leg_armor_0.instance_id,
                self.class_item_0.instance_id,
                -1,
                2,
            ),
            outfits,
        )

    def test_outfit_permutations_five_artifice_stats(self):
        # if we have five pieces of artifice armor, and we start with base stats of 0 in each stat
        # we'll get permutations we can add:
        # - 15 to one stat - 6 ways
        # - 12 to one stat and 3 to one stat - 30 ways
        # - 9 to one stat and 6 to one stat - 30 ways
        # - 9 to one stat and 3 to two stats - 60 ways
        # - 6 to two stats and 3 to one stat - 60 ways
        # - 6 to one stat and 3 to three stats - 60 ways
        # - 3 to five stats - 6 ways
        # but! some of those ways don't give us new stat combos because we only care about increments of 5 on a stat
        # if all stats end in 0, adding +3 ~ +0 and +9 ~ +6 - redundant combos can be removed
        # if all stats end in 1, adding +3 ~ +0 and +9 ~ +12
        # if all stats end in 2, adding +6 ~ +3 and +9 ~ +12
        # if all stats end in 3, adding +6 ~ +3 and +12 ~ +15
        # if all stats end in 4, adding +9 ~ +6 and +12 ~ +15
        # stats of 5 loop back to the same as 0

        artifice_helmet_0 = Armor(slot="Helmet", is_artifice=True)
        artifice_helmet_1 = Armor(
            slot="Helmet",
            mobility=1,
            resilience=1,
            recovery=1,
            discipline=1,
            intellect=1,
            strength=1,
            is_artifice=True,
        )
        artifice_helmet_2 = Armor(
            slot="Helmet",
            mobility=2,
            resilience=2,
            recovery=2,
            discipline=2,
            intellect=2,
            strength=2,
            is_artifice=True,
        )
        artifice_helmet_3 = Armor(
            slot="Helmet",
            mobility=3,
            resilience=3,
            recovery=3,
            discipline=3,
            intellect=3,
            strength=3,
            is_artifice=True,
        )
        artifice_helmet_4 = Armor(
            slot="Helmet",
            mobility=4,
            resilience=4,
            recovery=4,
            discipline=4,
            intellect=4,
            strength=4,
            is_artifice=True,
        )
        artifice_gauntlets_0 = Armor(slot="Gauntlets", is_artifice=True)
        artifice_chest_0 = Armor(slot="Chest Armor", is_artifice=True)
        artifice_legs_0 = Armor(slot="Leg Armor", is_artifice=True)
        artifice_class_0 = Armor(slot="Class Item", is_artifice=True)

        profile_outfits_0 = ProfileOutfits(
            self.armor_list_to_dict(
                [
                    artifice_helmet_0,
                    artifice_gauntlets_0,
                    artifice_chest_0,
                    artifice_legs_0,
                    artifice_class_0,
                ]
            )
        )
        outfits_0 = profile_outfits_0.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits_0), 7)

        profile_outfits_1 = ProfileOutfits(
            self.armor_list_to_dict(
                [
                    artifice_helmet_1,
                    artifice_gauntlets_0,
                    artifice_chest_0,
                    artifice_legs_0,
                    artifice_class_0,
                ]
            )
        )
        outfits_1 = profile_outfits_1.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits_1), 7)

        profile_outfits_2 = ProfileOutfits(
            self.armor_list_to_dict(
                [
                    artifice_helmet_2,
                    artifice_gauntlets_0,
                    artifice_chest_0,
                    artifice_legs_0,
                    artifice_class_0,
                ]
            )
        )
        outfits_2 = profile_outfits_2.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits_2), 7)

        profile_outfits_3 = ProfileOutfits(
            self.armor_list_to_dict(
                [
                    artifice_helmet_3,
                    artifice_gauntlets_0,
                    artifice_chest_0,
                    artifice_legs_0,
                    artifice_class_0,
                ]
            )
        )
        outfits_3 = profile_outfits_3.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits_3), 7)

        profile_outfits_4 = ProfileOutfits(
            self.armor_list_to_dict(
                [
                    artifice_helmet_4,
                    artifice_gauntlets_0,
                    artifice_chest_0,
                    artifice_legs_0,
                    artifice_class_0,
                ]
            )
        )
        outfits_4 = profile_outfits_4.generate_class_outfits("Warlock", True)
        self.assertEqual(len(outfits_4), 22)

        # print outfits_4 to a file in data as json
        with open("data/outfits_4.json", "w") as f:
            json.dump(outfits_4, f, indent=4)


if __name__ == "__main__":
    unittest.main(argv=[""], verbosity=2, exit=False)
