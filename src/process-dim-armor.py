import argparse
import csv
import os
import json
import re
from pathlib import Path

desc = "Process DIM armor exports to tell d2noteboooks what to ignore."
parser = argparse.ArgumentParser( description=desc )
parser.add_argument( '-f', '--file', default=f"{os.getenv('HOME')}/Downloads/destinyArmor.csv" )
args = parser.parse_args()

# DIM has shown a propensity to revise its CSV columns without notice
name_idx  = 0
id_idx    = 2
tag_idx   = 3
notes_idx = 32

armor_csv_path = args.file
ignored_armor_path = f"{Path(__file__).parent.parent}/data/ignored-armor.json"

if not os.path.exists(armor_csv_path):
    print(f"Could not find {armor_csv_path}")
else:
	with open(armor_csv_path) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		seen_header = False	
		ignored = []
		for row in csv_reader:
			if not seen_header:
				try:
					assert(row[name_idx] == "Name")
					assert(row[id_idx] == "Id")
					assert(row[tag_idx] == "Tag")
					assert(row[notes_idx] == "Notes")
				except AssertionError as e:
					print("ERROR: looks like DIM changed its CSV columns again. Can't proceed.")
					raise(e)
				seen_header = True
				
			if row[tag_idx] == "infuse" or row[tag_idx] == "junk" or re.search("#ignore", row[notes_idx]):
				ignored.append(dict( instance_id = int(row[id_idx].strip('"')), 
									 name = row[name_idx], 
									 tag = ("#ignore" if re.search("#ignore", row[notes_idx]) else row[tag_idx])))

		with open(ignored_armor_path, 'w', encoding="utf-8") as f:
			json.dump(ignored, f, indent = 2)

		print(f"wrote {len(ignored)} items to {ignored_armor_path}")
