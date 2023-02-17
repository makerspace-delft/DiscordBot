import discord, time
from discord.ext import commands

from pprint import pprint

from slack_sdk import WebClient

from os import getenv

import requests
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
    async def sendmessages(self, ctx: commands.Context, channelid: str, limit = 5):  
        response = self.client.conversations_history(channel=channelid)
        limit = min(limit, len(response["messages"]))

        # Iterating through all instances of message
        for i in response["messages"][:limit][::-1]:
            # Declaring the userid and message
            userid = i['user']
            message = i['text']
            
            # If it current user doesn't exist in local dictonary
            if userid not in self.users:
                self.users[userid] = self.client.users_info(user = userid)  
                
            # Get the username
            username = self.users[userid]["user"]["real_name"]

            # Get the image if not defined.
            if "image" not in self.users:
                url = self.users[userid]["user"]["profile"]["image_72"]
                image = BytesIO(requests.get(url).content)
                
                self.users["imageBytes"] = image.getvalue()

            webhook = await ctx.channel.create_webhook(name=username, avatar = self.users["imageBytes"])
            current = await webhook.send(message, wait=True, username=username)
            await webhook.delete()

            if "thread_ts" in i:
                # We have a parent message of a thread
                if i['thread_ts'] == i['ts']:
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
                            self.users[replyuserid] = self.client.users_info(user = replyuserid)  
                            
                        # Get the username
                        responder = self.users[replyuserid]["user"]["real_name"]


                        # Get the image if not defined.
                        if "image" not in self.users:
                            url = self.users[replyuserid]["user"]["profile"]["image_72"]
                            image = BytesIO(requests.get(url).content)
                            self.users["imageBytes"] = image.getvalue()

                        webhookResponse = await ctx.channel.create_webhook(name=responder, avatar = self.users["imageBytes"])
                        await webhookResponse.send(response, username=responder, thread=thread)   
                        await webhookResponse.delete() 
                        time.sleep(1)
            else:
                time.sleep(1)
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Ditto(bot))