from sqlalchemy import ForeignKey, String, Integer, CHAR, Column, Boolean
import sqlalchemy.orm
import requests
import constants

Base = sqlalchemy.orm.declarative_base() # Base to be used for SQLAlchemy

# Rank and Division keys and values for calculating ranked value
ranks = {"IRON": 0, "BRONZE": 400, "SILVER": 800, "GOLD": 1200, "PLATINUM": 1600, "EMERALD": 2000, "DIAMOND": 2400}
divisions = {"I": 300, "II": 200, "III": 100, "IV": 0}

# Class to be used to store the user's information in the database using SQLAlchemy
class User(Base):
    __tablename__ = "users"

    # Discord identifying information
    discordId = Column("discordId", Integer, primary_key = True)
    serverId = Column("serverId", Integer, primary_key = True)
    
    # Riot Games identifying information
    username = Column("username", String)
    tag = Column("tag", String)
    puuID = Column("puuID", String)
    summonerID = Column("summonerID", String)
    accountID = Column("accountID", String)

    # Start rank info
    startRank = Column("startRank", String)
    startDivision = Column("startDivision", String)
    startLP = Column("startLP", Integer)
    startValue = Column("startValue", Integer)
    
    currRank = Column("currRank", String)
    currDivision = Column("currDivision", String)
    currLP = Column("currLP", Integer)
    currValue = Column("currValue", Integer)

    valueChange = Column("valueChange", Integer)
        
    def __init__(self, discordId, serverId, username, tag, startRank, startDivision, startLP):
        self.discordId = discordId
        self.serverId = serverId
        
        self.username = username
        self.tag = tag
        self.puuID = getPuuID(username, tag)
        self.summonerID = getSummonerID(self.puuID)
        self.accountID = getAccountID(self.puuID)

        self.startRank = startRank
        self.startDivision = startDivision
        self.startLP = startLP
        self.startValue = getRankValue(startRank, startDivision, startLP)

        self.currRank, self.currDivision, self.currLP = getCurrRank(self.summonerID)
        self.currValue = getRankValue(self.currRank, self.currDivision, self.currLP)

        self.valueChange = self.currValue - self.startValue

    def __repr__(self):
        if self.currValue > 0:
            return f"{self.username} {self.currRank} {self.currDivision} {self.currLP} (+{self.valueChange} lp)"
        else:
            return f"**{self.username}** {self.currRank} {self.currDivision} {self.currLP} (-{self.valueChange} lp)"
        
def getPuuID(username, tag):
    """
    Get the Riot Games puuID for the user

    Arguments:
    username - username to be used in API call
    tag - unique identifier used in API call
    """
    response = requests.get(f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tag}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Invalid Riot Games name and/or tag")
    response = response.json()
    return response["puuid"]

def getSummonerID(puuid):
    """
    Gets the Riot Games summoner ID for the user

    Arguments:
    puuid - the user's puuid to be used in API call to get the summoner ID
    """
    response = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting account and summoner id from Riot Games")
    response = response.json()
    return response["id"]

def getAccountID(puuid):
    """
    Gets the Riot Games account ID for the user

    Arguments:
    puuid - the user's puuid to be used in API call to get the account ID
    """
    response = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting account and summoner id from Riot Games")
    response = response.json()
    return response["accountId"]

def getRankValue(rank, division, lp):
    """
    Calculate the rank value for the user

    Arguments:
    rank - the user's rank
    division - the user's division
    lp - the user's lp
    """
    if rank not in ["Master", "Grandmaster", "Challenger"]:
        return ranks[rank] + divisions[division] + lp
    else:
        return lp + 2800

def getCurrRank(summonerID):
    """
    Gets the current rank for the user by calling Riot Games API

    Arguments:
    summonerID - user's unique League of Legends ID to be used to get rank
    """
    response = requests.get(f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting current rank from Riot Games")
    response = response.json()

    # Finds the entry for Solo/Duo ranked to get the user's rank information in that mode
    for entry in response:
        if entry["queueType"] == "RANKED_SOLO_5x5":
            return response[0]["tier"], response[0]["rank"], response[0]["leaguePoints"]
    raise Exception("User is not ranked in Solo/Duo queue.")