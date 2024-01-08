import discord
from discord import app_commands
from discord.ext import commands
from constants import DISCORD_TOKEN

# Sets up client/bot and command tree
client = discord.Client(intents = discord.Intents.all())
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

# Test command to say hello and ping the user
@tree.command(name="hello", description="Says hello to you")
@app_commands.describe()
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

client.run(DISCORD_TOKEN)