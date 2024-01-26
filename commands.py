from sqlalchemy import create_engine, ForeignKey, String, Integer, CHAR, Column
from sqlalchemy.orm import sessionmaker
import constants
import users
import requests
import re

ranks = {"Iron": 0, "Bronze": 400, "Silver": 800, "Gold": 1200, "Platinum": 1600, "Emerald": 2000, "Diamond": 2400}
divisions = {"I": 300, "II": 200, "III": 100, "IV": 0}

engine = create_engine("sqlite:///database.db", echo = False)
users.Base.metadata.create_all(bind = engine)

Session = sessionmaker(bind = engine)
session = Session()

session.commit()

def register(discordId, serverId, username, tag, rank, division, lp):
    if (session.query(users.User).filter_by(discordId = discordId, serverId = serverId).first()) is not None:
        raise Exception("You have already registered in this server.")
    
    # Check that LP is valid (between 0 and 100)
    if lp > 100 or lp < 0:
        raise Exception("Please enter a valid LP between 0 and 100")
    
    # Check that tag is correct format
    if re.match(r"^[a-zA-Z0-9]{3,5}$", tag) is None:
        raise Exception("Entered tag format is incorrect")
    
    puuid = getPuuid(username, tag)
    summonerId, accountId = getIDs(puuid)

    value = getRankValue(rank, division, lp)
    registerUser(discordId, serverId, username, tag, puuid, summonerId, accountId, rank, division, lp, value, True)
    registerUser(discordId, serverId, username, tag, puuid, summonerId, accountId, rank, division, lp, value, False)

def getPuuid(username, tag):
    response = requests.get(f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tag}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Invalid Riot Games name and/or tag")
    response = response.json()
    return response["puuid"]

def getIDs(puuid):
    response = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting account and summoner id from Riot Games")
    response = response.json()
    return response["id"], response["accountId"]

def getRankValue(rank, division, lp):
    if rank not in ["Master", "Grandmaster", "Challenger"]:
        return ranks[rank] + divisions[division] + lp
    else:
        return lp + 2800

def registerUser(discordId, serverId, username, tag, puuid,
                 summonerId, accountId, rank, division, lp, value, currRank):
    newUser = users.User(discordId, serverId, username, tag, puuid, summonerId,
                         accountId, rank, division, lp, value, currRank)
    session.add(newUser)
    session.commit()

