import discord
from discord.ext import commands

from slack_sdk import WebClient

from os import getenv

import requests
from io import BytesIO

class Ditto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = WebClient(token=getenv('TOKEN2'))
        self.users = {} 
        

    @commands.command()
    async def ditto(self, ctx: commands.Context, name, *msg):
        webhook = await ctx.channel.create_webhook(name=name)
        await webhook.send(" ".join(msg), username=name)

        webhooks = await ctx.channel.webhooks()
        for webhook in webhooks:
                await webhook.delete()
                
    @commands.command()
    async def sendmessages(self, ctx: commands.Context, channelid: str, limit = 5):
        response = self.client.conversations_history(channel=channelid)
        
        for i in response["messages"][:limit][::-1]:
            userid = i['user']
            message = i['text']
            
            if userid not in self.users:
                self.users[userid] = self.client.users_info(user = userid)          
            
            username = self.users[userid]["user"]["real_name"]
            
            if "image" not in self.users:
                
                url = self.users[userid]["user"]["profile"]["image_original"]
                image = BytesIO(requests.get(url).content)
                
                self.users["imageBytes"] = image.getvalue()
            
            
            webhook = await ctx.channel.create_webhook(name=username, avatar = self.users["imageBytes"])
            await webhook.send(message, username=username)
            
        
        webhooks = await ctx.channel.webhooks()
        for webhook in webhooks:
                await webhook.delete()
    

def setup(bot: commands.Bot):
    bot.add_cog(Ditto(bot))