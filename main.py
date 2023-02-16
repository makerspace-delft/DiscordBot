import discord
from discord.ext import commands

from os import getenv, listdir
from dotenv import load_dotenv

load_dotenv()
TOKEN = getenv('TOKEN')

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print("I am ready!")

for filename in listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(TOKEN)