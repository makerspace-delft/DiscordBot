from unicodedata import category
import discord, time
from discord import app_commands
from discord.ext import commands
from asyncio.log import logger
from pprint import pprint
from slack_sdk import WebClient, errors
from os import getenv

class Ditto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = WebClient(token=getenv('SLACK_TOKEN'))
        self.users = {}
    
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
            
        return new_message
    
                
    @app_commands.command(name = "migrate", description="Migrate messages from a slack channel")
    async def migrate(self, interaction: discord.Interaction, channelid: str, limit: int = 5):  
        response = self.client.conversations_history(channel=channelid)
        limit = min(limit, len(response["messages"]))
        
        for webhook in await interaction.channel.webhooks():
            await webhook.delete()
        
        webhook = await interaction.channel.create_webhook(name = "webhook")

        # Iterating through all instances of message
        for i in response["messages"][:limit][::-1]:
            time.sleep(1)
            userid = i['user']
            message = self.formatmsg(i['text'])

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
                    response = self.formatmsg(reply['text'])
                    
                    if replyuserid not in self.users:
                        self.users[replyuserid] = self.client.users_info(user = replyuserid).data   
                        
                    
                    rusername = self.users[replyuserid]["user"]["real_name"]
                    responder = self.users[replyuserid]

                    await webhook.send(response, 
                                       username=rusername, 
                                       thread=thread,
                                       avatar_url = responder["user"]["profile"]["image_72"])

        await webhook.delete()
                
    @app_commands.command(name = "migrateprivate", description = "Migrate messeges from a private slack channel")
    async def migrateprivate(self, interaction: discord.Interaction, channelid: str, limit: int = 5):
        
        try:
            response = self.client.conversations_history(channel=channelid)
        except errors.SlackApiError as err:
            print("Unable to find channel\n", err)
            await interaction.response.send_message("Make sure to add @Scraper to that channel.")
            return


        category = discord.utils.get(interaction.guild.categories, id = 1071808452088836167)

        channel = await interaction.guild.create_text_channel(f'{channelid}', category=category)
        
        
    
                
async def setup(bot: commands.Bot):
    await bot.add_cog(Ditto(bot), guilds = [discord.Object(id = 1071769053091352677)])