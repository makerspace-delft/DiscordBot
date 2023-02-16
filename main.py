import asyncio
import discord
from discord.ext import commands

from os import getenv, listdir
from dotenv import load_dotenv

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print("I am ready!")
    
async def load():
    for filename in listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)
        

asyncio.run(main())