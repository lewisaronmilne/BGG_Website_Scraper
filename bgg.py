import requests 
import xml.etree.ElementTree as et
import xml.dom.minidom as minidom
import json
import time
import io
import numpy as np

xml_saving = True
last_api_request_time = 0
min_time_btw_calls =  1
sleep_btw_throttles = 5

def load_json_file(file_loc):
    try:
        with io.open(file_loc, "r", encoding="utf8") as input_file:
            return json.load(input_file)
    except:
        return {}
    

def save_json_file(data, file_loc):
    with io.open(file_loc, "w", encoding="utf8") as output_file:
        output_file.write(json.dumps(data, indent=4, ensure_ascii=False))

def bgg_query_api(query_string):
    while(True):
        global last_api_request_time
        sleep_time = last_api_request_time + min_time_btw_calls - time.time()
        if sleep_time > 0: 
            time.sleep(sleep_time)
        last_api_request_time = time.time()

        response = requests.get("https://boardgamegeek.com/xmlapi2/" + query_string)

        if response.status_code == 200:
            break

        time.sleep(sleep_btw_throttles)

    xml_string = response.content
    root = et.fromstring(xml_string)

    if xml_saving:
        formatted_xml_lines = minidom.parseString(xml_string).toprettyxml(indent="\t").splitlines()
        output_xml_lines = []
        for line in formatted_xml_lines:
            if len(line.strip()) > 0:
                output_xml_lines.append(line)
        with open("last_api_response.xml", "w", encoding="utf8") as output_file:
            output_file.write("\n".join(output_xml_lines))

    return root

def bgg_get_game_data(bgg_id):
    search_string = "thing?id={}&stats=1".format(bgg_id)
    root = bgg_query_api(search_string)

    game_root = root.find(".//item")
    game_data = {}

    game_data["real_data"] = "True"
    game_data["id"] = int(game_root.attrib["id"])
    game_data["name"] = game_root.find(".//name[@type='primary']").attrib["value"]
    game_data["type"] = game_root.attrib["type"]
    game_data["rating"] = game_root.find(".//statistics/ratings/average").attrib["value"]
    game_data["weight"] = game_root.find(".//statistics/ratings/averageweight").attrib["value"]
    game_data["description"] = game_root.find(".//description").text

    # player_polls_total_votes = int(game_root.find(".//poll[@name='suggested_numplayers']").attrib["totalvotes"])
    # game_data["player_polls_total_votes"] = player_polls_total_votes

    # if player_polls_total_votes > 0:
    #     game_data["player_polls"] = []
    #     player_polls = game_root.findall(".//poll[@name='suggested_numplayers']/results")
    #     for poll in player_polls:
    #         game_data["player_polls"].append({
    #             "players" : poll.attrib["numplayers"],
    #             "best" : poll[0].attrib["numvotes"],
    #             "recommended" : poll[1].attrib["numvotes"],
    #             "not recommended" : poll[2].attrib["numvotes"]
    #         })

    return game_data
    
def bgg_search(game_name):
    search_string = "search?query={}&type=boardgame,boardgameexpansion".format("+".join(game_name.split(" ")), type)
    root = bgg_query_api(search_string)

    search_results = root.findall(".//item")

    results_data = {
        "searched_for" : game_name,
        "search_string" : search_string,
        "exact" : [],
        "non-exact" : []
    }
    
    for result in search_results:
        formatted_result = {}
        formatted_result["id"] = int(result.attrib["id"])
        formatted_result["name"] = result.find(".//name").attrib["value"]
        formatted_result["type"] = result.attrib["type"]
        formatted_result["url"] = "https://boardgamegeek.com/" + formatted_result["type"] + "/" + str(formatted_result["id"])

        if game_name.lower() == formatted_result["name"].lower():
            results_data["exact"].append(formatted_result)
        else:
            results_data["non-exact"].append(formatted_result)

    return results_data

# run one of these functions
def search_game_matches():
    games_db_file = "games_db.json"
    games_db = load_json_file(games_db_file)

    for i in range(0, len(games_db)):
        game = games_db[i]
        search_for = game["bgg"]["name"]

        if "real_data" not in game["bgg"]:
            print(game)

        if ("real_data" in game["bgg"]) and (game["bgg"]["real_data"] == "True"):
            continue

        progress_info_string = "[" + str(i+1) + "/" + str(len(games_db)) + "]"
        search_info_string = "Searched: [" + search_for + "]"

        search_results = bgg_search(search_for)
        exact_results = len(search_results["exact"])
        non_exact_results = len(search_results["non-exact"])

        results_info_string = "[exact: " + str(exact_results) + ", non-exact: " + str(non_exact_results) +"]"

        game["try_id"] = -1
        matches_db_file = ""
        populated_results = []

        if (exact_results == 1) or (exact_results == 2 and search_results["exact"][0]["id"] == search_results["exact"][1]["id"]):
            matches_db_file = "matches_probable.json"
            game["try_id"] = search_results["exact"][0]["id"]
        elif exact_results > 1:
            matches_db_file = "matches_uncertain_exact.json"
        elif non_exact_results > 0:
            matches_db_file = "matches_uncertain_non_exact.json"
        else:
            matches_db_file = "matches_none.json"

        for result in np.concatenate((search_results["exact"], search_results["non-exact"])):
            if len(populated_results) < 10:
                populated_results.append(bgg_get_game_data(result["id"]))
            else:
                break

        matches_db = load_json_file(matches_db_file)
        matches_db[str(i)] = { "game": game, "results": populated_results }
        save_json_file(matches_db, matches_db_file)
        print("[" + matches_db_file + "] " + progress_info_string + " " + search_info_string + " " + results_info_string)

def populate_games_db():
    games_db_file = "games_db.json"
    games_db = load_json_file(games_db_file)

    matches_files = [
        "matches_probable.json",
        "matches_uncertain_exact.json",
        "matches_uncertain_non_exact.json",
        "matches_none.json"
    ]

    for matches_file in matches_files:
        matches = load_json_file(matches_file)
        for i, match_and_results in enumerate(matches):
            match = match_and_results[0]
            if match["try_id"] > 0:
                game_data = bgg_get_game_data(match["try_id"])
                match["bgg"] = game_data
                games_db[match["d20_num"]]["bgg"] = game_data
                save_json_file(matches, matches_file)
                save_json_file(games_db, games_db_file)
                print("[" + matches_file + "] [" + str(i+1) + "/" + str(len(matches)) + "] " + match["bgg"]["name"])

search_game_matches()
