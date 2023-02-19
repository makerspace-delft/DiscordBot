from asyncio.log import logger
import discord, time, requests
from discord.ext import commands

from pprint import pprint
import slack

from slack_sdk import WebClient

from os import getenv

from io import BytesIO



class Ditto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = WebClient(token=getenv('SLACK_TOKEN'))
        self.users = {}
    
    @commands.command()
    async def ditto(self, ctx: commands.Context, name, *msg):
        webhook = await ctx.channel.create_webhook(name=name)
        await webhook.send(" ".join(msg), username=name)

        webhooks = await ctx.channel.webhooks()
        for webhook in webhooks:
                await webhook.delete()
    
    @commands.command()
    async def webhooks(self, ctx: commands.Context):
        webhook = await ctx.channel.create_webhook(name = "webhook")
        for i in range(20):
            await webhook.send(str(i), username = str(i))
            time.sleep(1)
        await webhook.delete()
                
    @commands.command()
    async def migrate(self, ctx: commands.Context, channelid: str, limit = 5):  
        response = self.client.conversations_history(channel=channelid)
        limit = min(limit, len(response["messages"]))
        
        for webhook in await ctx.channel.webhooks():
            await webhook.delete()
        
        webhook = await ctx.channel.create_webhook(name = "webhook")

        # Iterating through all instances of message
        for i in response["messages"][:limit][::-1]:
            time.sleep(1)
            userid = i['user']
            message = i['text']
            
            # If it current user doesn't exist in local dictonary
            if userid not in self.users:
                self.users[userid] = self.client.users_info(user = userid).data  
            
            slackuser = self.users[userid]              
            username = slackuser["user"]["real_name"]
            
            current = await webhook.send(message, 
                                         wait=True, 
                                         username=username, 
                                         avatar_url=slackuser["user"]["profile"]["image_72"])

            # We have a parent message of a thread
            if "thread_ts" in i and i['thread_ts'] == i['ts']:
                
                # Create the orginal thread message
                msg = await current.fetch()
                thread = await msg.create_thread(name=message[:min(len(message), 90)], auto_archive_duration=1440)
                
                # Getting a dictonary of replies
                replies = self.client.conversations_replies(
                    channel=channelid,
                    ts = i['ts']
                )

                # We skip the first message as this is the one that created the thread
                for reply in replies['messages'][1:]:
                    replyuserid = reply['user']
                    response = reply['text']
                    # If it current user doesn't exist in local dictonary
                    # make API request
                    if replyuserid not in self.users:
                        self.users[replyuserid] = self.client.users_info(user = replyuserid).data  
                        
                    # Get the username
                    rusername = self.users[replyuserid]["user"]["real_name"]
                    responder = self.users[replyuserid]

                    await webhook.send(response, 
                                       username=rusername, 
                                       thread=thread,
                                       avatar_url = responder["user"]["profile"]["image_72"])
                await thread.clo   

        await webhook.delete()
                
        
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Ditto(bot))