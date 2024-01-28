from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import users
import re
import requests
import constants
import discord
import matplotlib.pyplot as plt
import champions

# Create the database session for storing and accessing user information
engine = create_engine("sqlite:///database.db", echo = False)
users.Base.metadata.create_all(bind = engine)

Session = sessionmaker(bind = engine)
session = Session()


def register(discordId, serverId, username, tag, rank, division, lp):
    """
    Register a user to the bot by adding them to the database

    Arguments:
    discordId - the discord ID of the user
    serverId - the ID of the server where the user is registering
    username - the username for the user's Riot Games account
    tag - the unique identifier tag associated with the user's Riot Games account
    rank - the starting rank of the user
    division - the starting division of the user
    lp - starting LP of the user
    """
    # Check whether or not the user is already registered in the server. If yes raise an exception
    if (session.query(users.User).filter_by(discordId = discordId, serverId = serverId).first()) is not None:
        raise Exception("User already registered in this server")
    
    # Check that the entered tag is valid (3-5 alphanumeric characters)
    if re.match(r"^[a-zA-Z0-9]{3,5}$", tag) is None:
        raise Exception("Entered tag format is incorrect")
    
    # Check that the entered starting LP is valid (between 0 and 99 inclusive)
    if lp > 99 or lp < 0:
        raise Exception("Please enter a valid LP between 0 and 99")
    
    # If the input information is correct, create the user and add them to the databse
    newUser = users.User(discordId, serverId, username, tag, rank, division, lp)
    session.add(newUser)
    session.commit()

def unregister(discId, servId):
    """
    Unregisters the user from the bot and removes them from the database

    Arguments:
    discId - the discord ID of the user to be removed
    servId - the server ID of the server where the user is being removed.
    """
    # Query database to see if the user is registered. If the user is registered in the server,
    # remove them from the database. If not, raise and exception
    entries = session.query(users.User).filter_by(discordId = discId, serverId = servId).all()
    if len(entries) == 0:
        raise Exception("You are not registered in this server")
    else:
        for entry in entries:
            session.delete(entry)
        session.commit()

def updateRanks(server):
    """
    Iterate through all users in the server and update their current ranks by calling Riot Games API

    Arguments:
    server - The server ID of the server to get users in and update their ranks
    """
    # Get the list of User objects for players in this server
    players = session.query(users.User).filter_by(serverId = server).all()

    # For each player in the server, call Riot Games API to get their current rank information
    for player in players:
        response = requests.get(f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{player.summonerID}?api_key={constants.RIOT_KEY}")
        
        # Check that request response is valid. If not, raise an exception
        if response.status_code != 200:
            raise Exception("Error updating user ranks")
        
        # Get the response as a JSON object, then find and update their updated rank information.
        response = response.json()
        for entry in response:
            if entry["queueType"] == "RANKED_SOLO_5x5":
                player.currRank = response[0]["tier"]
                player.currDivision = response[0]["rank"]
                player.currLP = response[0]["leaguePoints"]
                player.currValue = users.getRankValue(player.currRank, player.currDivision, player.currLP)
                player.valueChange = player.currValue - player.startValue


def getImprovementLeaderboard(server):
    """
    Get the improvement leaderboard, where users are ranked by the amount of LP they have gained since registering

    Arguments:
    server - the server ID in which the leaderboard will be displayed in.

    Returns:
    text - the list of strings to be displayed as the leaderboard
    """
    # Get the list of User objects ordered by the change in LP and append their string representation
    # to the text list (with + or - lp depending on whether they have improved or not)
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
    """
    Get the rank leaderboard, where users are ranked by their current rank
    
    Arguments:
    server - the server ID in which the ranked leaderboard will be displayed

    Returns:
    text - the list of strings to be displayed as the leaderboard
    """
    # Get the list of User objects ordered by their rank and append their string representation to the
    # text list. Then return the text list
    text = []
    place = 1
    players = session.query(users.User).filter_by(serverId = server).order_by(users.User.currValue.desc()).all()
    for player in players:
        text.append(f"**{place}. {player.username}** {player.currRank} {player.currDivision} {player.currLP} LP")
        place += 1
    return text

def displayInfo(user, server):
    """
    Get the user's information (rank, wins, losses, winrate, most played champions, and profile picture) and
    create an embed for display and return the embed.

    Arguments:
    user - the user's discord ID of who to get the information of

    Returns:
    embed - the embed to be displayed in discord
    file - the piechart image file to be displayed in the embed
    """

    # Parse the discord ID and use it to query the database for the player's User object
    discID = int(re.search(r"[0-9]+", user).group())
    player = session.query(users.User).filter_by(discordId = discID, serverId = server).first()
    if player is None:
        raise Exception("User not registered in this server.")

    # Call the Riot Games APIs to get ranked information and account information. If either return
    # an unsuccessful response code, raise an exception. Then convert response and icon data to needed types.
    response = requests.get(f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{player.summonerID}?api_key={constants.RIOT_KEY}")
    icon = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{player.puuID}?api_key={constants.RIOT_KEY}")
    if response.status_code != 200 or icon.status_code != 200:
        raise Exception("Error getting user information from Riot Games API")
    
    response = response.json()
    icon = icon.json()["profileIconId"]

    # Loop through the data in response and find the information associated with ranked Solo/Duo
    for entry in response:
        if entry["queueType"] == "RANKED_SOLO_5x5":
            # Get win and loss information
            wins = entry["wins"]
            losses = entry["losses"]

            # Setup a pie chart to display winrate using matplotlib
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

            # Get the user's top 3 most played champions
            championList = champions.getBestChampions(player.puuID)

            # Create the embed to be displayed in discord as a response to the command
            embed = discord.Embed(title = f"{player.username}",
                                  description = f"{player.currRank} {player.currDivision} {player.currLP} LP\nWins: {wins}" +
                                   f" | Losses: {losses}\n\n**Most Played Champions:**\n" +
                                   f"1. {championList[0]}\n2. {championList[1]}\n3. {championList[2]}",
                                  color = discord.Color.from_str("#101539"))
            embed.set_thumbnail(url = f"https://ddragon.leagueoflegends.com/cdn/14.2.1/img/profileicon/{icon}.png")
            file = discord.File("./wr.png", filename = "wr.png")
            embed.set_image(url = "attachment://wr.png")

            return embed, file