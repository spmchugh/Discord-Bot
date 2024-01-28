import os
import json
import requests
import constants

championsByID = { }
for file in os.listdir("./champion"):
    f = open(f"./champion/{file}", encoding="utf8")
    champion = file.split(".")[0]
    data = json.load(f)
    id = (data["data"][champion]["key"])
    championsByID[id] = champion

def getBestChampions(puuID):
    response = requests.get(f"https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuID}/top?count=3&api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting champion mastery from Riot Games")
    response = response.json()
    champions = []
    for entry in response:
        champions.append(championsByID[str(entry["championId"])])
    return champions
