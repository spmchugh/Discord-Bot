from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import users
import re
import requests
import constants
import discord
import matplotlib.pyplot as plt
import champions

engine = create_engine("sqlite:///database.db", echo = False)
users.Base.metadata.create_all(bind = engine)

Session = sessionmaker(bind = engine)
session = Session()

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
        for entry in response:
            if entry["queueType"] == "RANKED_SOLO_5x5":
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

def displayInfo(user, server):
    discID = int(re.search(r"[0-9]+", user).group())
    player = session.query(users.User).filter_by(discordId = discID, serverId = server).first()

    response = requests.get(f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{player.summonerID}?api_key={constants.RIOT_KEY}")
    icon = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{player.puuID}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200 or icon.status_code != 200:
        raise Exception("Error getting user information from Riot Games API")
    
    response = response.json()
    icon = icon.json()["profileIconId"]

    for entry in response:
        if entry["queueType"] == "RANKED_SOLO_5x5":
            wins = entry["wins"]
            losses = entry["losses"]
            winrate = wins / (wins + losses)

            data = [wins, losses]
            colors = ["#3469d1", "#d13434"]

            fig1, ax = plt.subplots()
            ax.pie(data, colors = colors, startangle = 90)

            center_circle = plt.Circle((0, 0), 0.8, fc = "#2b2d31")
            fig = plt.gcf()
            fig.gca().add_artist(center_circle)

            ax.text(0, 0, (format(wins/(wins + losses), ".0%")), ha = "center", va = "center", color = "white", fontsize = 16)
            ax.axis("equal")
            fig.patch.set_facecolor("#2b2d31")
            fig.set_size_inches(1.5, 1.5)
            plt.tight_layout()
            plt.savefig("wr.png")

            championList = champions.getBestChampions(player.puuID)
            embed = discord.Embed(title = f"{player.username}",
                                  description = f"{player.currRank} {player.currDivision} {player.currLP} LP\nWins: {wins}" +
                                   f" | Losses: {losses}\n\n**Most Played Champions:**\n" +
                                   f"1. {championList[0]}\n2. {championList[1]}\n3. {championList[2]}",
                                  color = discord.Color.from_str("#101539"))
            # embed.set_thumbnail(url = "https://i.imgur.com/0QKRQ5V.png")
            embed.set_thumbnail(url = f"https://ddragon.leagueoflegends.com/cdn/14.2.1/img/profileicon/{icon}.png")
            file = discord.File("./wr.png", filename = "wr.png")
            embed.set_image(url = "attachment://wr.png")

            return embed, file