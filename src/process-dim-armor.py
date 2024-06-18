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

armor_csv_path = args.file
ignored_armor_path = f"{Path(__file__).parent.parent}/data/ignored-armor.json"

if not os.path.exists(armor_csv_path):
    print(f"Could not find {armor_csv_path}")
else:
	with open(armor_csv_path) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		ignored = []
		for row in csv_reader:
			if row[3] == "infuse" or row[3] == "junk" or re.search("#ignore", row[33]):
				ignored.append(dict( instance_id = int(row[2].strip('"')), 
									 name = row[0], 
									 tag = ("#ignore" if re.search("#ignore", row[33]) else row[3])))

		with open(ignored_armor_path, 'w', encoding="utf-8") as f:
			json.dump(ignored, f, indent = 2)

		print(f"wrote {len(ignored)} items to {ignored_armor_path}")
