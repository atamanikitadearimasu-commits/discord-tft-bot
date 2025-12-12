import discord
from discord.ext import commands
import os
import requests

DISCORD_TOKEN = os.environ['DISCORD_BOT_TOKEN']
RIOT_TOKEN = os.environ['RIOT_API_TOKEN']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def tft(ctx, *, summoner_name):
    url = f"https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
    headers = {"X-Riot-Token": RIOT_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        message = f"Summoner: {data.get('name')}\nLevel: {data.get('summonerLevel')}"
    else:
        message = f"Error {response.status_code}: Could not fetch summoner info."
    await ctx.send(message)

bot.run(DISCORD_TOKEN)
