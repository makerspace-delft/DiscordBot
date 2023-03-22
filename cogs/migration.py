from asyncio.log import logger
import os
import discord
from discord import app_commands
from discord.ext import commands
from asyncio import sleep
from pprint import pprint
import requests, shutil
from slack_sdk import WebClient, errors
from os import getenv
import re


TIMEOUT = 10

class Ditto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = WebClient(token=getenv('SLACK_TOKEN'))
        self.users = {}
        self.cookies = {
            "d": getenv('SLACK_USER')
        }
        self.lastTs = None
    
    @commands.command()
    async def sync(self, ctx: commands.Context):
        fmt = await ctx.bot.tree.sync(guild = ctx.guild)
        await ctx.send(f"Synced {len(fmt)} commands")
        
    
    @app_commands.command(name = "ditto", description="ditto someone")
    async def ditto(self, interaction: discord.Interaction, name: str, msg: str):
        webhook = await interaction.channel.create_webhook(name=name)
        interaction.response.is_done
        await webhook.send(msg, username=name)
        await webhook.delete()
        
    def formatmsg(self, message: str) -> str:
        
        new_message = message
        for j in range(len(message)):
            try:
                if message[j:j+2] == "<@" and message[j+13] == '>':
                    user = message[j+2:j+13]

                    if user not in self.users:
                        self.users[user] = self.client.users_info(user = user).data  

                    new_message = new_message.replace("<@" + user + ">", "@" + self.users[user]["user"]["real_name"])
                
                
            except: pass 
        
        new_message = re.sub(r'\*<([^|]+)\|[^>]+>\*', r'\1', new_message)
         # replace <https://BLANK> with https://BLANK
        new_message = re.sub(r'<([^>]+)>', r'\1', new_message)
        
        new_message = new_message.replace("*", "**")

        return new_message
    
    

    
    async def sendmessages(self, channel: discord.Interaction.channel, channelid: str, limit: int, response: dict, after: str):
        for webhook in await channel.webhooks():
            await webhook.delete()
        
        webhook: discord.Webhook = await channel.create_webhook(name = "webhook")
        
        messages = (response["messages"])
        
        channel = self.client.conversations_info(channel=channelid).data["channel"]["name"]
        
        end = len(messages)
        
        for index, msg in enumerate(messages):
            if msg['ts'] == after:
                end = index
                
        total = len(messages[:end][::-1][:limit] if after else messages[:limit][::-1])
        
        lastMessage = None
        # Iterating through all instances of message
        for index, slackMessage in enumerate(messages[:end][::-1][:limit] if after else messages[:limit][::-1]):        
            await sleep(TIMEOUT)
            
            logger.log(20, f"{channel.upper()} {index+1} messages migrated out of {total} ts: {slackMessage['ts']}")
            # print(f"{index+1} messages migrated out of {limit}", end = "\r")
            try:
                if "user" not in slackMessage:
                    continue
                
                userid = slackMessage['user']
                message = self.formatmsg(slackMessage['text'])
                lastMessage = slackMessage['ts']
                
                # If it current user doesn't exist in local dictonary
                if userid not in self.users:
                    self.users[userid] = self.client.users_info(user = userid).data  
                    
                slackuser = self.users[userid]           
                username = slackuser["user"]["profile"]["display_name"]


                
                for i in range(0, len(message), 2000):
                    current = await webhook.send(message[i:min(len(message), i+2000)],
                                                    wait=True,
                                                    username=username,
                                                    avatar_url=slackuser["user"]["profile"]["image_72"])
            
                
                if "files" in slackMessage:
                    filemsg = "";
                    for file in slackMessage['files']:
                        if (file['size'] <= 8 * 1000 * 1000):
                            fileResponse = requests.get(file['url_private'], cookies=self.cookies, stream=True)
                            with open(file['name'], 'wb') as out_file:
                                fileResponse.raw.decode_content = True
                                shutil.copyfileobj(fileResponse.raw, out_file)

                            del fileResponse
                            
                            await sleep(TIMEOUT)
                            
                            current = await webhook.send(file=discord.File(file['name']), 
                                            wait = True, 
                                            username=username, 
                                            avatar_url=slackuser["user"]["profile"]["image_72"])
                            os.remove(file['name'])
                            
                        else:
                            filetype = file['pretty_type']
                            filemsg += f"\n**{filetype}**: {file['url_private']}"
                    
                    if filemsg != "":
                        current = await webhook.send(filemsg, 
                                            wait = True, 
                                            username=username, 
                                            avatar_url=slackuser["user"]["profile"]["image_72"])

            
                
                # We have a parent message of a thread
                if "thread_ts" in slackMessage and slackMessage['thread_ts'] == slackMessage['ts']:
                    if message == "": message = "Thread"
                    # Create the orginal thread message
                    msg = await current.fetch()
                    thread = await msg.create_thread(name=message[:min(len(message), 90)], auto_archive_duration=1440)
                    
                    # Getting a dictonary of replies
                    replies = self.client.conversations_replies(
                        channel=channelid,
                        ts = slackMessage['ts']
                    )

                    # We skip the first message as this is the one that created the thread
                    for rindex, reply in enumerate(replies['messages'][1:]):  
                        await sleep(TIMEOUT)
                        
                        print(f"{rindex+1} replies migrated out of {len(replies['messages'])}", end = "\r")
                        
                        replyuserid = reply['user']
                        response = self.formatmsg(reply['text'])
                        
                        if replyuserid not in self.users:
                            self.users[replyuserid] = self.client.users_info(user = replyuserid).data   
                            
                        rusername = self.users[replyuserid]["user"]["real_name"]
                        responder = self.users[replyuserid]

                        await webhook.send(response, 
                                        username=rusername, 
                                        thread=thread,
                                        avatar_url = responder["user"]["profile"]["image_72"])
        
            except Exception as e:
                logger.log(40, f"Error: {e}")
        await webhook.delete()              
        print("\nMigrated all messages!")
        
        return lastMessage
    
                
    @app_commands.command(name = "migrate", description="Migrate messages from a slack channel")
    async def migrate(self, interaction: discord.Interaction, channelid: str, limit: int = 5, after: str = None):  
        try:
            response = self.client.conversations_history(channel=channelid, limit=1000)
        except errors.SlackApiError as err:
            await interaction.response.send_message("Channel not found. Make sure to add @Scraper to that channel. You can do that by pinging @Scraper in slack")
            return
        
        limit = min(limit, len(response["messages"]))
                
        await interaction.response.send_message(f"Migrating {limit} messages")
        
        lastmessage = await self.sendmessages(interaction.channel, channelid, limit, response, after)
        
        await interaction.channel.send(f"Successfully migrated {limit} messages")
        if lastmessage:
            await interaction.channel.send(f"Last message TS is {lastmessage}")

    @app_commands.command(name = "migrateprivate", description = "Migrate messeges from a private slack channel")
    async def migrateprivate(self, interaction: discord.Interaction, channelid: str, limit: int = 5):
        
        try:
            response = self.client.conversations_history(channel=channelid)
        except errors.SlackApiError as err:
            print("Unable to find channel\n", err)
            await interaction.response.send_message("Make sure to add @Scraper to that channel. You can do that by pinging @Scraper in slack")
            return
        
        category = discord.utils.get(interaction.guild.categories, id = 1071808452088836167)

        
        for channel in category.channels:
            if channel.name == channelid.lower():
                await channel.set_permissions(interaction.user, read_messages=True, send_messages=False)
                await interaction.response.send_message(f"Channel already exists, I have added you to <#{channel.id}>!")
                
                return

        channel = await interaction.guild.create_text_channel(f'{channelid}', category=category)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=False)
        
        await interaction.response.send_message(f"Created a private channel for you: <#{channel.id}>! Message will be loaded soon \:D")
        
        await self.sendmessages(channel, channelid, limit, response)
        
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Ditto(bot), guilds = [discord.Object(id = 1071769053091352677)])