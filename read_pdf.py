from unicodedata import category
import pdfplumber
import numpy as np
import re
import io
import json

category_regex = "Strategy|2 Player|Card & Dice|Classic|Light Strategy|Co-op|Trivia|Adventure/Heavy|Family and Kids|Over 18|Party"
check_after = []
game_list= []

with pdfplumber.open("d20.pdf") as document:
    pages = document.pages
    for page in pages:
        lines = page.extract_text().split("\n")
        check_after.append(lines[0])
        check_after.append(lines[1])
        check_after.append(lines[2])
        check_after.append(lines[-1])

        lines = lines[4:-1]

        for line in lines:
            num_matches = len(re.findall(category_regex, line))
            if num_matches == 0:
                print(line)
                line = input("fix this (or leave empty): ")
                num_matches = len(re.findall(category_regex, line))
                if num_matches == 0:
                    check_after.append(line)
                    continue

            category_regex_start = 0
            category_regex_end = 0
            first_match_section = ""
            second_match_section = line
            while num_matches > 0:
                match_obj = re.search(category_regex, second_match_section)
                category_regex_start = len(first_match_section) + match_obj.start()
                category_regex_end = len(first_match_section) + match_obj.end()
                first_match_section = first_match_section + second_match_section[:category_regex_end]
                second_match_section = second_match_section[category_regex_end:]
                num_matches -= 1

            game_name = line[0:category_regex_start].strip()
            game_category = line[category_regex_start:category_regex_end].strip()
            game_numbers = line[category_regex_end:].strip().split(" ")
            game_min_age = game_numbers.pop(-1)
            game_avg_playtime = game_numbers.pop(-1)

            expansion = "Base Game"
            shelf = "Unknown"

            next_add = game_numbers.pop(0)
            if re.search("[0-9]{1,2}[a-zA-Z]", next_add): 
                shelf = next_add
            else:
                expansion = next_add
                shelf = game_numbers.pop(0)

            num_players = "".join(game_numbers)

            game_list.append({
                "name" : game_name,
                "category" : game_category,
                "expansion" : expansion,
                "shelf" : shelf,
                "players" : num_players,
                "playtime" : game_avg_playtime,
                "age+" : game_min_age
            })

with io.open("pdf_data", "w", encoding="utf8") as output_file:
    output_file.write(json.dumps(game_list, indent=4, ensure_ascii=False))

print("Remaining Problems:")
print("")
for line in check_after:
    if re.search(r"Directory of Board Game Library", line): continue
    if re.search(r"Game Category EXP", line): continue
    if re.search(r"20-Aug-2021", line): continue
    if re.search(r"Key to expansions \(EXP\)", line): continue
    print(line)
    if line.strip() == "": continue

    print(line)