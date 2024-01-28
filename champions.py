import os
import json
import requests
import constants

# Get the champion name from the champion ID and make a dictionarry
# for all champions where the key is champion id and value is champion name
championsByID = { }
for file in os.listdir("./champion"):
    f = open(f"./champion/{file}", encoding="utf8")
    champion = file.split(".")[0]
    data = json.load(f)
    id = (data["data"][champion]["key"])
    championsByID[id] = champion

def getBestChampions(puuID):
    """
    Gets the top three most played champions for a user

    Arguments:
    puuID - the user;s puuID, used for Riot Games API call the get champion information

    Returns:
    champions - a list of the top three most played champions as strings
    """
    # Calls the Riot Games API to get champion master ifnormation for the user. Converts the champion ID response
    # to champion name as a string and appends it to the list
    response = requests.get(f"https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuID}/top?count=3&api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting champion mastery from Riot Games")
    response = response.json()
    champions = []
    for entry in response:
        champions.append(championsByID[str(entry["championId"])])
    return champions
