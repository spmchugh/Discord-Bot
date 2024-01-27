import discord
from discord import app_commands
from discord.ext import commands
from constants import DISCORD_TOKEN
import commands
from pagination import Pagination

# Sets up client/bot and command tree
client = discord.Client(intents = discord.Intents.default())
tree = discord.app_commands.CommandTree(client)

# Starts the bot and syncs commands
@client.event
async def on_ready():
    print("Bot commands are loading...")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s) successfully.\nBot is ready!")
    except Exception as e:
        print("Synced 0 commands successfully.")
        exit()

# Temporary test command to ensure bot is connected and working
@tree.command(name="hello", description="Says hello to you")
@app_commands.describe()
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

# Setup options for registration command
rankChoices = []
for rank in ["DIAMOND", "EMERALD", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]:
    rankChoices.append(discord.app_commands.Choice(name = rank, value = rank))
divisionChoices = []
for division in ["I", "II", "III", "IV"]:
    divisionChoices.append(discord.app_commands.Choice(name = division, value = division))

# Create registration command
@tree.command(name = "register", description = "Connect your league and discord accounts")
@app_commands.describe(username = "Riot Games name", tag = "Riot Games tag", rank = "Choose your starting rank",
                       division = "Choose your starting division", lp = "Choose your starting LP")
@app_commands.choices(rank = rankChoices)
@app_commands.choices(division = divisionChoices)
async def register(interaction: discord.Interaction, username: str, tag: str, rank: str, division: str, lp: int):
    try:
        commands.register(interaction.user.id, interaction.guild.id, username, tag, rank, division, lp)
        await interaction.response.send_message(f"Registered {interaction.user.mention} as {username}#{tag} with rank {rank} {division} {lp} LP")
    except Exception as e:
        await interaction.response.send_message(e)

@tree.command(name = "unregister", description = "Unregister your account from this bot in this server.")
async def unregister(interaction: discord.Interaction):
    try:
        commands.unregister(interaction.user.id, interaction.guild.id)
        await interaction.response.send_message(f"{interaction.user.mention} has been successfully unregistered")
    except Exception as e:
        await interaction.response.send_message(e)

L = 5    # elements per page

@tree.command(name = "leaderboard", description = "Display the rank improvement leaderboard for this server")
async def leaderboard(interaction: discord.Interaction):
    async def get_page(page: int):
        emb = discord.Embed(title = "Rank Improvement Leaderboard",
                            description = "",
                            color = discord.Color.from_str("#101539"))
        emb.set_thumbnail(url = "https://i.imgur.com/0QKRQ5V.png")
        
        offset = (page - 1) * L
        users = commands.getImprovementLeaderboard(interaction.guild.id)
        for user in users[offset:offset+L]:
            emb.description += f"{user}\n"
        n = Pagination.compute_total_pages(len(users), L)
        emb.set_footer(text=f"Page {page} from {n}")
        return emb, n

    await Pagination(interaction, get_page).navegate()
    
client.run(DISCORD_TOKEN)