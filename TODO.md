
start here: get `generate_outfits` to generate the permutations of outfits including useful artifice combinations
- change outfit to store the int/long of the armor that it includes
- make armor list a dict of int/long of instance id to the armor piece?
- split armor slots into exotic and non-exotic groupings, iterate separately over them
- instead of excluding class items, include them, but pick one to represent, if there is an artifice use it, otherwise don't

identify `pinnacle_outfits`, outfits with a peak tier stat combo that no other outfit exceeds
opposite could be `redundant_outfits` that don't have a peak tier stat.  

what about outfits that are equivalent?

triple-100 optimizer?  Pick 3 stats and show where you're weakest getting to that stat
- maybe some scatter/bar graph showing how many outfits get to a particular level?
- or, pick all 3-stat combos (ex: mob/res/dis) and plot the highest tier for each


- stat priority as part of algorithm? (default to res, dis, reco, str, int, mob?)
- allow minimum stat along with priority (so maybe a map with minimum tier?)


----

Some rules about how armor works in Destiny 2:
- A character can have at most one piece of armor equipped per slot (ex: only one Helmet)
- Armor is specific to a `d2_class`, a `Hunter` can only equip `Hunter` armor.  This is true for `Warlock` and `Titan` too.
- if a piece of armor `is_artifice`, then it can put +3 points on a single stat (mobility, resilience, recovery, discipline, intellect, strength)
- every slot must have a piece of armor equipped
- stats across all equipped armor are totaled up to determine the point total for that stat.  Ex: having 10 mobility on each of Helmet, Gauntlets, Chest Armor, Leg Armor, and Class Item would give a total of 50 mobility
- total stats have a "tier".  every tier is 10 points of that stat (ex: 10 mobility is `T1` (tier 1), 20 mobility is `T2` (tier 2), 100 mobility is `T10` (tier 10))
Users of armor can attach a mod that gives +5 points to that piece of armor, so it is also possible to have a `.5` tier. So mobility of 14 is still T1, but 15-19 is `T1.5`.  
- the maximum tier for a stat is 10, so T10 (100 points) is the highest it can go.  Points above 100 are wasted points

