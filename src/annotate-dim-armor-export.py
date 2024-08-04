#!/usr/bin/env python

import argparse
import csv
import os
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

desc = "Process DIM armor exports to add UPO notes"
parser = argparse.ArgumentParser( description=desc )
parser.add_argument( '-a', '--armor-file', default=f"{Path(__file__).parent.parent}/data/destinyArmor.csv" )
parser.add_argument( '-o', '--output-file', default=f"{Path(__file__).parent.parent}/data/destinyArmor-annotated.csv" )
parser.add_argument( '-j', '--json-report-dir', default=f"{Path(__file__).parent.parent}/data" )
args = parser.parse_args()

# DIM has shown a propensity to revise its CSV columns without notice
name_idx  = 0
id_idx    = 2
tag_idx   = 3
notes_idx = 32

@dataclass
class ArmorItem:
	row: list
	name: str = ""
	armor_id: str = ""
	notes: str = ""
	
	def __post_init__(self):
		self.name = self.row[name_idx]
		self.armor_id = self.row[id_idx].strip('"')
		self.notes = self.row[notes_idx]

	def ignored(self):
		if re.search("#ignore", self.notes):
			return True
		else:
			return False

	def add_upo_note(self, upo_count):
		original = self.notes

		# clear any existing "#upo-X-y" notes
		modified = re.sub("#UPO-[A-Z]-[\d]+", "", self.notes).strip()
		if modified != self.notes:
			self.notes = modified

		# append the new UPO count
		self.notes = f"{self.notes} {upo_count}".strip()

		if self.notes != original:
			# update the underlying `row` iterable used to write to CSV
			self.row[notes_idx] = self.notes
			# announce the difference
			print(f"id:{self.armor_id}, {self.name}")
			print(f"was: '{original}'")
			print(f"is : '{self.notes}'\n")

@dataclass
class ArmorProcessor:
	armor_csv_path: str
	json_report_dir: str
	output_path: str
	history: list = field(default_factory=lambda: {})

	def __post_init__(self):
		self.validate_files()
		self.process_armor()		

	def validate_files(self):
		should_exit = False
		if not os.path.exists(self.armor_csv_path):
			print(f"Could not find armor path '{self.armor_csv_path}'")
			should_exit = True
		if not os.path.exists(self.json_report_dir):
			print(f"Could not find base directory for json reports at '{self.json_report_dir}'")
			should_exit = True
		if should_exit:
			sys.exit(1)

	def add_to_history(self, letter_grade, armor, upo_count, d2_class):
		if letter_grade not in self.history:
			self.history[letter_grade] = list()
		self.history[letter_grade].append(f"UPO {upo_count}, {d2_class.title()}, {armor.name} (id:{armor.armor_id})")

	def process_armor(self):
		for d2_class in ["warlock", "hunter", "titan"]:
			report_path = f"{self.json_report_dir}/armor-report-{d2_class}.json"
			if not os.path.exists(report_path):
				print(f"No report found at {report_path}")
			else:			
				with open(report_path, 'r', encoding="utf-8") as f:
					parsed = json.load(f)
					# extract a mapping of instance IDs to UPO counts
					mapping = dict([(str(x['id']), x['unique_pinnacle_outfit_count']) for x in parsed])

				with open(self.armor_csv_path) as csv_file:
					csv_reader = csv.reader(csv_file, delimiter=',')				

					with open(self.output_path, 'w', newline='', encoding="utf-8") as csv_outfile:
						csv_writer = csv.writer(csv_outfile, delimiter=",")

						header = True
						for row in csv_reader:
							if header:
								try:
									assert(row[name_idx] == "Name")
									assert(row[id_idx] == "Id")
									assert(row[notes_idx] == "Notes")
								except AssertionError as e:
									print("ERROR: looks like DIM changed its CSV columns again. Can't proceed.")
									raise(e)	
								csv_writer.writerow(row)
								header = False
								continue

							armor = ArmorItem(row)
							if armor.armor_id in mapping:
								upo_count = mapping[armor.armor_id]
								if armor.ignored():
									pass
								elif upo_count == 0:
									self.add_to_history("F", armor, upo_count, d2_class)
									armor.add_upo_note("#UPO-F-0")
								elif upo_count < 5:
									self.add_to_history("D", armor, upo_count, d2_class)
									armor.add_upo_note(f"#UPO-D-{upo_count}")
								elif upo_count < 11:
									self.add_to_history("C", armor, upo_count, d2_class)
									armor.add_upo_note(f"#UPO-C-{upo_count}")
								elif upo_count < 31:
									self.add_to_history("B", armor, upo_count, d2_class)
									armor.add_upo_note(f"#UPO-B-{upo_count}")
								elif upo_count < 50:
									self.add_to_history("A", armor, upo_count, d2_class)
									armor.add_upo_note(f"#UPO-A-{upo_count}")
								elif upo_count >= 50:
									self.add_to_history("S", armor, upo_count, d2_class)
									armor.add_upo_note(f"#UPO-S-{upo_count}")
							csv_writer.writerow(armor.row)
		
		for letter_grade in ["F", "D", "C", "B", "A", "S"]:
			if letter_grade in self.history:
				armors = sorted(self.history[letter_grade], key=lambda x: int(re.search("UPO (\d+)", x)[1]), reverse=True)
				print(f"grade {letter_grade}:")
				for armor in armors:
					print(f"  {armor}")
					
processor = ArmorProcessor(args.armor_file, args.json_report_dir, args.output_file)
