from sqlalchemy import ForeignKey, String, Integer, CHAR, Column, Boolean
import sqlalchemy.orm
import requests
import constants

Base = sqlalchemy.orm.declarative_base()

ranks = {"IRON": 0, "BRONZE": 400, "SILVER": 800, "GOLD": 1200, "PLATINUM": 1600, "EMERALD": 2000, "DIAMOND": 2400}
divisions = {"I": 300, "II": 200, "III": 100, "IV": 0}

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
    response = requests.get(f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tag}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Invalid Riot Games name and/or tag")
    response = response.json()
    return response["puuid"]

def getSummonerID(puuid):
    response = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting account and summoner id from Riot Games")
    response = response.json()
    return response["id"]

def getAccountID(puuid):
    response = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting account and summoner id from Riot Games")
    response = response.json()
    return response["accountId"]

def getRankValue(rank, division, lp):
    if rank not in ["Master", "Grandmaster", "Challenger"]:
        return ranks[rank] + divisions[division] + lp
    else:
        return lp + 2800

def getCurrRank(summonerID):
    response = requests.get(f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200:
        raise Exception("Error getting current rank from Riot Games")
    if response == []:
        raise Exception("Player is unranked")
    response = response.json()
    return response[0]["tier"], response[0]["rank"], response[0]["leaguePoints"]
