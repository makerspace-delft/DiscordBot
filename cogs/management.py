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
from discord.utils import get
# discord member
from discord import Member

import re

class Management(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def check_if_admin(self, ctx):
        member = ctx.author
        roles = member.roles
        if not get(roles, name="Admin"):
            return False
        return True
    
    def check_can_create_in_category(self, ctx, category):
        member = ctx.author
        roles = member.roles
        category = re.sub(r'[^\w\s]','',category).strip()
        if not get(roles, name=category) and not get(roles, name="Admin"):
            return False
        return True
    
    def check_category_exists(self, ctx, category):
        guild = ctx.guild
        cat = discord.utils.get(guild.categories, name=category)
        if not cat:
            return False
        return True
    
    # A decorator to ensure the command can be used in the group

    @app_commands.command(name = "createchannel", description="Creates a channel and adds the caller to the private channel")
    async def createchannel(self, interaction: discord.Interaction, group: str, name:str, visibility: str = "private"):
        ctx = await self.bot.get_context(interaction)
        guild = ctx.guild
        member = ctx.author

        if not self.check_can_create_in_category(ctx, group) and not self.check_if_admin(ctx):
            await interaction.response.send_message(f"You do not have permission to create a channel in {group}")
            return
        
        if not self.check_category_exists(ctx, group) and not self.check_if_admin(ctx):
            await interaction.response.send_message(f"Category {group} does not exist")
            return

        admin_role = get(guild.roles, name="Admin")
        if visibility == "private":
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
        else:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }

        cat = discord.utils.get(guild.categories, name=group)
        if not cat:
            cat = await guild.create_category(group)

        channel = await guild.create_text_channel(name, overwrites=overwrites, category=cat)
        await interaction.response.send_message(f"Channel {channel.mention} created")

    @app_commands.command(name = "createvoicechannel", description="Creates a voice channel and adds the caller to the private channel")
    async def createvoicechannel(self, interaction: discord.Interaction, group: str, name:str, visibility: str = "private"):
        ctx = await self.bot.get_context(interaction)
        guild = ctx.guild
        member = ctx.author
        admin_role = get(guild.roles, name="Admin")

        if not self.check_can_create_in_category(ctx, group) and not self.check_if_admin(ctx):
            await interaction.response.send_message(f"You do not have permission to create a channel in {group}")
            return
        
        if not self.check_category_exists(ctx, group) and not self.check_if_admin(ctx):
            await interaction.response.send_message(f"Category {group} does not exist")
            return
        
        if visibility == "private":
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
        else:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }

        cat = discord.utils.get(guild.categories, name=group)
        if not cat:
            cat = await guild.create_category(group)

        channel = await guild.create_voice_channel(name, overwrites=overwrites, category=cat)
        await interaction.response.send_message(f"Channel {channel.mention} created")

    @app_commands.command(name = "addtotextchannel", description="Adds a user to a channel")
    async def addtotextchannel(self, interaction: discord.Interaction, channel: discord.TextChannel, user: discord.Member):
        ctx = await self.bot.get_context(interaction)

        # Check if the user adding the user has permission to add the user by checking for the override
        if ctx.author not in channel.overwrites:
            await interaction.response.send_message(f"You do not have permission to add users to {channel.mention}")
            return

        overwrites = channel.overwrites
        if user in overwrites:
            await interaction.response.send_message(f"{user.mention} is already in {channel.mention}")
            return
        
        overwrites[user] = discord.PermissionOverwrite(read_messages=True)
        await channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"Added {user.mention} to {channel.mention}")
    
    @app_commands.command(name = "removefromtextchannel", description="Removes a user from a channel")
    async def removefromtextchannel(self, interaction: discord.Interaction, channel: discord.TextChannel, user: discord.Member):
        ctx = await self.bot.get_context(interaction)

        # Only allow admins to remove users from channels
        if not self.check_if_admin(ctx):
            await interaction.response.send_message(f"You do not have permission to remove users from {channel.mention}")
            return

        overwrites = channel.overwrites
        if user not in overwrites:
            await interaction.response.send_message(f"{user.mention} is not in {channel.mention}")
            return
        
        del overwrites[user]
        await channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"Removed {user.mention} from {channel.mention}")

    @app_commands.command(name = "addtovoicechannel", description="Adds a user to a channel")
    async def addtovoicechannel(self, interaction: discord.Interaction, channel: discord.VoiceChannel, user: discord.Member):
        ctx = await self.bot.get_context(interaction)

        # Check if the user adding the user has permission to add the user by checking for the override
        if ctx.author not in channel.overwrites:
            await interaction.response.send_message(f"You do not have permission to add users to {channel.mention}")
            return
        
        overwrites = channel.overwrites
        if user in overwrites:
            await interaction.response.send_message(f"{user.mention} is already in {channel.mention}")
            return
        
        overwrites[user] = discord.PermissionOverwrite(read_messages=True)
        await channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"Added {user.mention} to {channel.mention}")
    
    @app_commands.command(name = "removefromvoicechannel", description="Removes a user from a channel")
    async def removefromvoicechannel(self, interaction: discord.Interaction, channel: discord.VoiceChannel, user: discord.Member):
        ctx = await self.bot.get_context(interaction)

        # Only allow admins to remove users from channels
        if not self.check_if_admin(ctx):
            await interaction.response.send_message(f"You do not have permission to remove users from {channel.mention}")
            return
        
        overwrites = channel.overwrites
        if user not in overwrites:
            await interaction.response.send_message(f"{user.mention} is not in {channel.mention}")
            return
        
        del overwrites[user]
        await channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"Removed {user.mention} from {channel.mention}")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Management(bot), guilds = [discord.Object(id = 1071769053091352677)])