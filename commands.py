from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import users
import re
import requests
import constants

engine = create_engine("sqlite:///database.db", echo = False)
users.Base.metadata.create_all(bind = engine)

Session = sessionmaker(bind = engine)
session = Session()

session.commit()

def register(discordId, serverId, username, tag, rank, division, lp):
    if (session.query(users.User).filter_by(discordId = discordId, serverId = serverId).first()) is not None:
        raise Exception("User already registered in this server")
    
    # Check that LP is valid (between 0 and 100)
    if lp > 99 or lp < 0:
        raise Exception("Please enter a valid LP between 0 and 99")
    
    # Check that tag is correct format
    if re.match(r"^[a-zA-Z0-9]{3,5}$", tag) is None:
        raise Exception("Entered tag format is incorrect")
    
    newUser = users.User(discordId, serverId, username, tag, rank, division, lp)
    session.add(newUser)
    session.commit()

def unregister(discId, servId):
    entries = session.query(users.User).filter_by(discordId = discId, serverId = servId).all()
    if len(entries) == 0:
        raise Exception("You are not registered in thsi server")
    else:
        for entry in entries:
            session.delete(entry)
        session.commit()

def updateRanks(server):
    players = session.query(users.User).filter_by(serverId = server).all()
    for player in players:
        response = requests.get(f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{player.summonerID}?api_key={constants.RIOT_KEY}")
        if response.status_code != 200:
            raise Exception("Error updating user ranks")
        response = response.json()
        player.currRank = response[0]["tier"]
        player.currDivision = response[0]["rank"]
        player.currLP = response[0]["leaguePoints"]
        player.currValue = users.getRankValue(player.currRank, player.currDivision, player.currLP)
        player.valueChange = player.currValue - player.startValue


def getImprovementLeaderboard(server):
    text = []
    place = 1
    players = session.query(users.User).filter_by(serverId = server).order_by(users.User.valueChange.desc()).all()
    for player in players:
        if player.valueChange > 0:
            text.append(f"**{place}. {player.username}** {player.currRank} {player.currDivision} {player.currLP} LP (+{player.valueChange} LP)")
        else:
            text.append(f"**{place}. {player.username}** {player.currRank} {player.currDivision} {player.currLP} LP ({player.valueChange} LP)")
        place += 1
    return text

def getRankLeaderboard(server):
    text = []
    place = 1
    players = session.query(users.User).filter_by(serverId = server).order_by(users.User.currValue.desc()).all()
    for player in players:
        text.append(f"**{place}. {player.username}** {player.currRank} {player.currDivision} {player.currLP} LP")
        place += 1
    return text