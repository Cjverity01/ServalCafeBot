import discord
from discord import Interaction, Embed, ButtonStyle
from discord import ui
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from discord.ui import Modal, TextInput, Button, View
import logging
from discord.ext.commands import Bot
import traceback
import aiohttp
from pymongo import MongoClient
from aiohttp import ClientResponseError
from json import JSONDecodeError
from io import BytesIO
import sys
import os
import requests
import time
from datetime import datetime
from discord import app_commands
from logging import getLogger
from aiohttp import ClientResponseError
from json import JSONDecodeError
from io import BytesIO
import sys
import subprocess
# Redirect stdout and stderr to capture all console output
class ConsoleToFile:
    def __init__(self, file_path):
        self.file = open(file_path, "a", encoding="utf-8")
        sys.stdout = self
        sys.stderr = self  # Redirect errors too

    def write(self, message):
        self.file.write(message)
        self.file.flush()  # Ensure log updates instantly
        sys.__stdout__.write(message)  # Print to console as well

    def flush(self):
        self.file.flush()

# Setup file capture
console_logger = ConsoleToFile("bot_console.log")
GIT_AUTH = os.getenv("GIT_AUTH")
LOA_OPEN= True
response_channel_id = 1325942156954960008  # Channel to send the message to
load_dotenv()
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
GUILD_ID = "1272622697079377920"
RANKING_ROLE_ID = int(os.getenv("RANKING_ROLE_ID"))
hex_color = int("86A269", 16)
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent (important for reading message content)
intents.members = True  # Enable the members intent

# Create the bot object and pass intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)



# MongoDB setup
mongo_uri = os.getenv("DATABASE_URI")
client = MongoClient(mongo_uri)
db = client["ServalCafe"]
collection = db["requests"]

logger = getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession()
    logger.info("Loading...")
    logger.info("-" * 20)
    logger.info("Authors: cj_daboi36.")
    logger.info("-" * 20)
    await bot.tree.sync()  # Sync slash commands to Discord
    logger.info("Slash commands synced")
    logger.info("-" * 20)
    logger.info(f'Loaded! Connected To: {bot.user}')
    logger.info("-" * 20)
    logger.info("Started Successfully!")

    # Fetch pending requests from MongoDB on restart
    pending_requests = collection.find({"status": "pending"})
    for request in pending_requests:
        user = await bot.fetch_user(request['user_id'])
        
        embed = Embed(
            title="A LOA Request Has Been Sent In",
            description=f"<@{request['user_id']}> has requested a LOA!",
            color=hex_color  # Using hex_color variable here
        )
        embed.add_field(name="Roblox Username", value=request['roblox_username'], inline=False)
        embed.add_field(name="Discord Username", value=request['discord_username'], inline=False)
        embed.add_field(name="Start Date", value=request['start_date'], inline=True)
        embed.add_field(name="End Date", value=request['end_date'], inline=True)
        embed.add_field(name="Reason", value=request['reason'], inline=False)

        # Create buttons for Accept/Deny
        view = View()
        accept_button = Button(label="Accept", style=ButtonStyle.success)
        deny_button = Button(label="Deny", style=ButtonStyle.danger)

        # Accept button callback
        async def accept_callback(inter: discord.Interaction):
            # Check if the request has already been accepted or denied
            request_data = collection.find_one({"user_id": request['user_id']})
            if request_data['status'] == 'accepted':
                await inter.response.send_message(f"Nice try! <@{request['user_id']}> has already accepted this LOA request.", ephemeral=True)
                return
            elif request_data['status'] == 'denied':
                await inter.response.send_message(f"Nice try! <@{request['user_id']}> has already denied this LOA request.", ephemeral=True)
                return

            embed_accept = Embed(
                title="Your LOA Request Was Accepted",
                description=(
                    f"Hey there <@{request['user_id']}>! "
                    f"Your LOA request was accepted and will start on `{request['start_date']}` "
                    f"and will end on `{request['end_date']}`."
                ),
                color=hex_color  # Using hex_color variable here
            )
            await user.send(embed=embed_accept)
            await inter.response.send_message("LOA request accepted.", ephemeral=True)
            collection.update_one(
                {"user_id": request['user_id']},
                {"$set": {"status": "accepted"}}
            )

        # Deny button callback
        async def deny_callback(inter: discord.Interaction):
            # Check if the request has already been accepted or denied
            request_data = collection.find_one({"user_id": request['user_id']})
            if request_data['status'] == 'accepted':
                await inter.response.send_message(f"Nice try! <@{request['user_id']}> has already accepted this LOA request.", ephemeral=True)
                return
            elif request_data['status'] == 'denied':
                await inter.response.send_message(f"Nice try! <@{request['user_id']}> has already denied this LOA request.", ephemeral=True)
                return

            class DenialReasonModal(Modal, title="Denial Reason"):
                def __init__(self):
                    super().__init__(title="Denial Reason")
                    self.reason = TextInput(
                        label="Reason for Denial",
                        placeholder="Please explain why this LOA request is denied.",
                        required=True
                    )
                    self.add_item(self.reason)

                async def on_submit(self, inter_inner: discord.Interaction):
                    embed_deny = Embed(
                        title="Your LOA Request Was Denied",
                        description=(
                            f"Hey there <@{request['user_id']}>! "
                            f"Your LOA request was denied with the reason:\n``{self.reason.value}``."
                        ),
                        color=hex_color  # Using hex_color variable here
                    )
                    await user.send(embed=embed_deny)
                    await inter_inner.response.send_message("Denial reason submitted and user notified.", ephemeral=True)
                    collection.update_one(
                        {"user_id": request['user_id']},
                        {"$set": {"status": "denied", "denial_reason": self.reason.value}}
                    )

            await inter.response.send_modal(DenialReasonModal())

        accept_button.callback = accept_callback
        deny_button.callback = deny_callback

        view.add_item(accept_button)
        view.add_item(deny_button)
        
        # Log channel to send the LOA requests
        log_channel = bot.get_channel(1335641734448812255)  # Replace with your channel ID
        if log_channel:
            await log_channel.send(embed=embed, view=view)

@bot.tree.command(name="terminate", description="Terminate a user.")
@commands.has_permissions(administrator=True)  # Restricts command to server admins
async def terminate_user(interaction: discord.Interaction, user: discord.User):  # Renamed function to match the command name
    await interaction.response.defer()  # Defer the response to avoid the 'already acknowledged' error
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member:
        # Debugging: print out the user's role IDs
        print(f"{interaction.user.name} roles: {[role.id for role in member.roles]}")

        if any(role.id == RANKING_ROLE_ID for role in member.roles):  # Check if user has a required role
            try:
                roblox_id = None  # Initialize roblox_id to prevent unbound variable errors

                # First API call to fetch Roblox ID
                response_roblox = requests.get(
                    f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{user.id}",
                    headers={"Authorization": "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"}
                )
                if response_roblox.status_code == 200:
                    data = response_roblox.json()
                    roblox_id = data.get("robloxID")  # Extract the 'robloxID' field
                    if not roblox_id:
                        await interaction.followup.send("Could not find a Roblox ID for this user.")
                        return
                else:
                    await interaction.followup.send(f"Failed to fetch Roblox ID. Status Code: {response_roblox.status_code}")
                    return
            except Exception as e:
                await interaction.followup.send(f"An error occurred while fetching Roblox ID: {e}")
                return

            # Second API call to rank the user
            full_url = f"https://ranking.cjscommissions.xyz/group/rank/?groupid=16461735&user_id={roblox_id}&role_number=1&key=CJSCOMMSRANK"
            try:
                response_rank = requests.get(full_url)
                if response_rank.status_code == 200:
                    data = response_rank.json()
                    message = data.get("message")
                    if message == f"The user's rank has been set to 1!":
                        await interaction.followup.send(f"Successfully terminated the user!")
                    else:
                        await interaction.followup.send(f"Error: {message}")
                else:
                    await interaction.followup.send(f"Failed to terminate user. Status Code: {response_rank.status_code}")
            except Exception as e:
                await interaction.followup.send(f"An error occurred during termination: {e}")
        else:
            await interaction.followup.send("You do not have the required role to terminate users.")
    else:
        await interaction.followup.send("Could not fetch the member details.")
@bot.tree.command(name="direct-message", description="Send a DM to a user")
async def dm(interaction: discord.Interaction, user: discord.User, message: str):
    embed = discord.Embed(
        title=f"A Message From {interaction.guild.name}",
        description=message,
        color=hex_color
    )

    # Set timestamp and footer
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="Powered By Cj's Commissions")

    # Create a variable to track if the interaction response has been sent
    response_sent = False

    # Send the DM to the user
    try:
        await user.send(embed=embed)
        

        # Respond to the interaction after completing all actions
        if not response_sent:
            await interaction.response.send_message(f"Sent DM to {user.name}")
            response_sent = True
    
    except discord.Forbidden:
        # Handle case where the bot cannot send DM (e.g., if the user has DMs disabled)
        if not response_sent:
            await interaction.response.send_message(f"Failed to send DM to {user.name}. They may have DMs disabled.")
            response_sent = True


@bot.tree.command(name="ping", description="Ping the bot")
async def ping(interaction: discord.Interaction):
    start_time = time.time()  # Record the start time
    await interaction.response.defer()  # Defer the interaction

    end_time = time.time()  # Record the end time
    ping_time = (end_time - start_time) * 1000  # Convert to milliseconds
    

    embed = discord.Embed(
        title="Pong!",
        description=f"Response took `{ping_time:.2f}` milliseconds.",
        color=hex_color
    )
    
    
    await interaction.followup.send(embed=embed)
@bot.tree.command(name="groupmembers", description="Check group members.")
async def groupmembers(interaction: discord.Interaction):
    full_url = "https://ranking.cjscommissions.xyz/group/members/?groupid=16461735&key=CJSCOMMSRANK"
    
    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            data = response.json()
            member_count = data.get("member_count")
            
            if member_count is not None:
                await interaction.response.send_message(f"We have {member_count} members!")
            else:
                await interaction.response.send_message("Could not find member count in the response.")
        else:
            await interaction.response.send_message(f"Failed to get data. Status Code: {response.status_code}")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")
@bot.tree.command(name="promote", description="Promote a user.")
async def promote(interaction: discord.Interaction, user: discord.User):
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == RANKING_ROLE_ID for role in member.roles):
        roblox_id = None
        try:
            # Fetch Roblox ID
            response = requests.get(f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{user.id}", 
                                    headers={"Authorization": "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"})
            if response.status_code == 200:
                data = response.json()
                roblox_id = data.get("robloxID")
                if not roblox_id:
                    await interaction.response.send_message("Could not find a Roblox ID for this user.")
                    return
            else:
                await interaction.response.send_message(f"Failed to fetch Roblox ID. Status Code: {response.status_code}")
                return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while fetching Roblox ID: {e}")
            return

        # Call to promote user
        try:
            full_url = f"https://ranking.cjscommissions.xyz/group/promote/?groupid=16461735&user_id={roblox_id}&key=CJSCOMMSRANK"
            response = requests.get(full_url)
            if response.status_code == 200:
                data = response.json()
                message = data.get("message")
                if message == "The user was promoted!":
                    await interaction.response.send_message(f"Successfully promoted {user.name}!")
                else:
                    await interaction.response.send_message(f"Failed to promote user: {message}")
            else:
                await interaction.response.send_message(f"Failed to promote user. Status Code: {response.status_code}")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during promotion: {e}")
    else:
        await interaction.response.send_message("You do not have the required role to promote users.")


@bot.tree.command(name="demote", description="Demote a user.")
async def demote(interaction: discord.Interaction, user: discord.User):
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == RANKING_ROLE_ID for role in member.roles):
        roblox_id = None
        try:
            # Fetch Roblox ID
            response = requests.get(f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{user.id}",  
                                    headers={"Authorization": "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"})
            if response.status_code == 200:
                data = response.json()
                roblox_id = data.get("robloxID")
                if not roblox_id:
                    await interaction.response.send_message("Could not find a Roblox ID for this user.")
                    return
            else:
                await interaction.response.send_message(f"Failed to fetch Roblox ID. Status Code: {response.status_code}")
                return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while fetching Roblox ID: {e}")
            return

        # Call to demote user
        try:
            full_url = f"https://ranking.cjscommissions.xyz/group/demote/?groupid=16461735&user_id={roblox_id}&key=CJSCOMMSRANK"
            response = requests.get(full_url)
            if response.status_code == 200:
                data = response.json()
                message = data.get("message")
                if message == "The user was demoted!":
                    await interaction.response.send_message(f"Successfully demoted {user.name}!")
                else:
                    await interaction.response.send_message(f"Failed to demote user: {message}")
            else:
                await interaction.response.send_message(f"Failed to demote user. Status Code: {response.status_code}")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during demotion: {e}")
    else:
        await interaction.response.send_message("You do not have the required role to demote users.")
@bot.tree.command(name="rank", description="Rank a user.")
async def setrank(interaction: discord.Interaction, user: discord.User, rank: str):
    await interaction.response.defer()  # Defer the response to avoid the 'already acknowledged' error
    
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member:
        # Debugging: print out the user's role IDs
        print(f"{interaction.user.name} roles: {[role.id for role in member.roles]}")

        if any(role.id == RANKING_ROLE_ID for role in member.roles):
            try:
                roblox_id = None  # Initialize roblox_id to prevent unbound variable errors

                # First API call to fetch Roblox ID
                response_roblox = requests.get(
                    f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{user.id}",
                    headers={"Authorization": "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"}
                )
                if response_roblox.status_code == 200:
                    data = response_roblox.json()
                    roblox_id = data.get("robloxID")  # Extract the 'robloxID' field
                    if not roblox_id:
                        await interaction.followup.send("Could not find a Roblox ID for this user.")
                        return
                else:
                    await interaction.followup.send(f"Failed to fetch Roblox ID. Status Code: {response_roblox.status_code}")
                    return
            except Exception as e:
                await interaction.followup.send(f"An error occurred while fetching Roblox ID: {e}")
                return

            # Second API call to rank the user
            full_url = f"https://ranking.cjscommissions.xyz/group/rank/?groupid=16461735&user_id={roblox_id}&role_number={rank}&key=CJSCOMMSRANK"
            try:
                response_rank = requests.get(full_url)
                if response_rank.status_code == 200:
                    data = response_rank.json()
                    message = data.get("message")
                    if message == f"The user's rank has been set to {rank}!":
                        await interaction.followup.send(f"Successfully ranked the user!")
                    else:
                        await interaction.followup.send(f"Error: {message}")
                else:
                    await interaction.followup.send(f"Failed to rank user. Status Code: {response_rank.status_code}")
            except Exception as e:
                await interaction.followup.send(f"An error occurred during ranking: {e}")
        else:
            await interaction.followup.send("You do not have the required role to rank users.")
    else:
        await interaction.followup.send("Could not fetch the member details.")


@bot.tree.command(name="shift", description="Start a shift")
async def shift(interaction: discord.Interaction):
    # Settings for this command
    required_role_id = 1317560300060541112  # The required role ID for this command
    role_to_ping = 1308833378153267210  # The role to ping

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == 1325941896438223001 for role in member.roles):
        # Get the channel to send the message to
        channel = bot.get_channel(response_channel_id)

        if channel:
            # Create the embed
            embed = discord.Embed(
                title="A new shift is starting",
                description="A new shift at the cafe is starting! Why don't you come on down and get a nice cup of coffee? We hope to see you there!",
                color=hex_color
            )
            embed.add_field(name="Session Host", value=interaction.user.mention, inline=False)
            embed.add_field(name="Game Link", value="https://www.roblox.com/games/11856007309/Serval-Cafe-Version-2", inline=False)
            embed.set_footer(text="Bot Powered by Cj's Commissions")

            # Send the message with or without the role ping (conditionally)
            if role_to_ping:
                await channel.send(content=f"@everyone", embed=embed)
            else:
                await channel.send(embed=embed)

            await interaction.response.send_message("Shift started successfully. Please stay in the shift for at least 15 minutes or you will be striked!", ephemeral=True)
        else:
            await interaction.response.send_message("An error occured while sending.", ephemeral=True)
    else:
        await interaction.response.send_message("Nuh - Uh. You don't have the required role to run this command.", ephemeral=True)
@bot.tree.command(name="shiftend", description="Start a shift")
async def shift(interaction: discord.Interaction):
    # Settings for this command

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == 1325941896438223001 for role in member.roles):
        # Get the channel to send the message to
        channel = bot.get_channel(response_channel_id)

        if channel:
            # Create the embed
            embed = discord.Embed(
                title="The Recent Shift Has Ended",
                description="The recent shift has now ended! Thank you to all the attendees. Dont forget to checkout the shift picture in <#1325942156954960008>!",
                color=hex_color
            )

            embed.set_footer(text="Bot Powered by Cj's Commissions")
            await channel.send(embed=embed)

            await interaction.response.send_message("Shift ended successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occured while sending.", ephemeral=True)
    else:
        await interaction.response.send_message("Nuh - Uh. You don't have the required role to run this command.", ephemeral=True)
@bot.tree.command(name="training", description="Start a training")
async def shift(interaction: discord.Interaction):
    # Settings for this command
    required_role_id = 1317560300060541112  # The required role ID for this command
    role_to_ping = 1308833378153267210  # The role to ping


    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == 1333537526232645685 for role in member.roles):
        # Get the channel to send the message to
        channel = bot.get_channel(response_channel_id)

        if channel:
            # Create the embed
            embed = discord.Embed(
                title="A Training Is Starting",
                description="A new training is starting! If you want to become staff or rank up, come on down and join us! We wish you the best of luck! If you are not a trainee, join https://www.roblox.com/games/16761624805/Application-Centre to apply!",
                color=hex_color
            )
            embed.add_field(name="Host", value=interaction.user.mention, inline=False)
            embed.add_field(name="Game Link", value="https://www.roblox.com/games/12122228919/Serval-Cafe-Trainings", inline=False)
            embed.set_footer(text="Bot Powered by Cj's Commissions")
            await channel.send(content=f"<@1325941884144844853>", embed=embed)
            await interaction.response.send_message("Training started sucessfully! The link is linked [here](https://www.roblox.com/games/12122228919/Serval-Cafe-Trainings)", ephemeral=True)
        else:
            await interaction.response.send_message("An error occured while sending.", ephemeral=True)
    else:
        await interaction.response.send_message("Nuh - Uh. You don't have the required role to run this command.", ephemeral=True)
@bot.tree.command(name="trainingend", description="End a training")
async def shift(interaction: discord.Interaction):
    # Settings for this command
    required_role_id = 1317560300060541112  # The required role ID for this command
    role_to_ping = 1308833378153267210  # The role to ping

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == 1333537526232645685 for role in member.roles):
        # Get the channel to send the message to
        channel = bot.get_channel(response_channel_id)

        if channel:
            # Create the embed
            embed = discord.Embed(
                title="The Recent Training Has Ended",
                description="The recent training has ended! Congratulations to anyone who passed. If you failed, don’t be disheartened there is always next time!",
                color=hex_color
            )
            embed.set_footer(text="Bot Powered by Cj's Commissions")
            await channel.send(content=f"<@1325941884144844853>", embed=embed)
            await interaction.response.send_message("Training started sucessfully! The link is linked [here](https://www.roblox.com/games/12122228919/Serval-Cafe-Trainings)", ephemeral=True)
        else:
            await interaction.response.send_message("An error occured while sending.", ephemeral=True)
    else:
        await interaction.response.send_message("Nuh - Uh. You don't have the required role to run this command.", ephemeral=True)
@bot.tree.command(name="traininglock", description="Lock a training")
async def shift(interaction: discord.Interaction):
    # Settings for this command
    required_role_id = 1317560300060541112  # The required role ID for this command
    role_to_ping = 1308833378153267210  # The role to ping

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == 1333537526232645685 for role in member.roles):
        # Get the channel to send the message to
        channel = bot.get_channel(response_channel_id)

        if channel:
            # Create the embed
            embed = discord.Embed(
                title="The Training Has Locked",
                description="The server has been locked for the training. If you disconnect, open a ticket and we will unlock it for you!",
                color=hex_color
            )
            embed.set_footer(text="Bot Powered by Cj's Commissions")
            await channel.send(content=f"<@1325941884144844853>", embed=embed)
            await interaction.response.send_message("Locked successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occured while sending.", ephemeral=True)
    else:
        await interaction.response.send_message("Nuh - Uh. You don't have the required role to run this command.", ephemeral=True)
@bot.tree.command(name="trainingcancel", description="Cancel a training")
async def shift(interaction: discord.Interaction):
    # Settings for this command
    required_role_id = 1317560300060541112  # The required role ID for this command
    role_to_ping = 1308833378153267210  # The role to ping


    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == 1333537526232645685 for role in member.roles):
        # Get the channel to send the message to
        channel = bot.get_channel(response_channel_id)

        if channel:
            # Create the embed
            embed = discord.Embed(
                title="The Training Has Been Cancelled",
                description="The recent training has been cancelled! Sorry for any inconvenience caused.",
                color=hex_color
            )
            embed.set_footer(text="Bot Powered by Cj's Commissions")
            await channel.send(content=f"<@1325941884144844853>", embed=embed)
            await interaction.response.send_message("Cancelled successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occured while sending.", ephemeral=True)
    else:
        await interaction.response.send_message("Nuh - Uh. You don't have the required role to run this command.", ephemeral=True)
@bot.tree.command(name="ban", description="Ban a user from the server")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    # Check if the bot has the ban_members permission
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("I don't have permission to ban members!", ephemeral=True)
        return

    # Check if the command user has the required role
    if not any(role.id == 1325941896438223001 for role in interaction.user.roles):  # Ensure role ID is an integer
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    try:
        # Attempt to send the user a DM
        embed = discord.Embed(
            title="You Have Been Banned",
            description=f"Oh-No! You have been banned for: {reason}. If you think this is a mistake, contact an admin!",
            color=hex_color
        )
        embed.set_footer(text="Bot Powered by Cj's Commissions")
        await user.send(embed=embed)
    except discord.Forbidden:
        # DM failed, continue to ban
        pass

    try:
        # Ban the user
        await user.ban(reason=reason)
        await interaction.response.send_message(f"Banned {user.mention} successfully!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to ban this user.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred while banning: {e}", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user from the server")
async def unban(interaction: discord.Interaction, user_id: int):
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)
    
    if member and any(role.id == 1325941896438223001 for role in member.roles):  # Ensure role ID is an integer
        try:
            # Attempt to unban the user
            user = discord.Object(user_id)  # Convert the user ID to a discord.Object
            await guild.unban(user)
            await interaction.response.send_message(f"Unbanned user with ID {user_id} successfully!", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message(f"No banned user with ID {user_id} found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to unban user. Error: {e}", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

@bot.tree.command(name="purge", description="Purge a number of messages")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer()  # Defers the response
    await interaction.channel.purge(limit=amount)  # Purges the messages
    await interaction.followup.send(f"Purged {amount} messages.")  # Sends the follow-up message

@bot.tree.command(name="kick", description="Kick a user from the server")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)
    
    if member and any(role.id == 1325941896438223001 for role in member.roles):  # Ensure role ID is an integer
        try:
            # Create the embed
            embed = discord.Embed(
                title="You Have Been Kicked",
                description=f"Oh no! You have been kicked for: {reason}. You can rejoin via: https://discord.gg/HxntPDGZ57",
                color=hex_color
            )
            embed.set_footer(text="Bot Powered by Cj's Commissions")
            
            # Try sending the DM to the user
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                await interaction.response.send_message(f"Could not DM {user.name}, but they will be kicked.", ephemeral=True)
            
            # Kick the user
            await user.kick(reason=reason)
            await interaction.response.send_message(f"Kicked {user.name} successfully!", ephemeral=True)
        
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick {user.name}. Error: {e}", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)


@bot.tree.command(name="timeout", description="Timeout a user.")
async def mute(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided"):
    # Check if the bot has the moderate_members permission
    if not interaction.guild.me.guild_permissions.moderate_members:
        await interaction.response.send_message("I don't have permission to timeout members!", ephemeral=True)
        return

    # Check if the command user has the required role
    if not any(role.id == 1325941896438223001 for role in interaction.user.roles):  # Ensure role ID is an integer
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    # Create an embed for the user
    embed = discord.Embed(
        title="You Have Been Timed Out",
        description=f"Oh-No! You have been timed out for: {reason}. It will be removed in {duration} minutes.",
        color=hex_color
    )
    embed.set_footer(text="Bot Powered by Cj's Commissions")

    try:
        # Timeout the user
        await user.timeout(timedelta(minutes=duration), reason=reason)

        # Attempt to send a DM
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            pass  # Ignore if the user has DMs disabled

        # Send confirmation to the interaction user
        await interaction.response.send_message(f"Timed out {user.mention} for {duration} minute(s). Reason: {reason}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to timeout this user.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Failed to timeout {user.name}. Error: {e}", ephemeral=True)
class LoaForm(Modal, title="Request An LOA"):
    def __init__(self, bot: Bot):
        super().__init__(title="Request An LOA")
        self.bot = bot

        # Add text input fields
        self.roblox_username = TextInput(
            label="Roblox Username",
            placeholder="Gamingwithcj2011",
            required=True
        )
        self.discord_username = TextInput(
            label="Discord Username",
            placeholder="cj_daboi36",
            required=True
        )
        self.start_date = TextInput(
            label="Start Date",
            placeholder="22/02/25",
            required=True
        )
        self.end_date = TextInput(
            label="End Date",
            placeholder="25/02/25",
            required=True
        )
        self.reason = TextInput(
            label="Reason For Request",
            placeholder="I want a break",
            required=True
        )

        # Add the fields to the modal
        self.add_item(self.roblox_username)
        self.add_item(self.discord_username)
        self.add_item(self.start_date)
        self.add_item(self.end_date)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        # Save the LOA request to MongoDB
        loa_data = {
            "user_id": interaction.user.id,
            "roblox_username": self.roblox_username.value,
            "discord_username": self.discord_username.value,
            "start_date": self.start_date.value,
            "end_date": self.end_date.value,
            "reason": self.reason.value,
            "status": "pending",  # Set status as pending initially
        }
        collection.insert_one(loa_data)

        # Create the embed to send to the log channel
        embed = Embed(
            title="A LOA Request Has Been Sent In",
            description=f"<@{interaction.user.id}> has requested a LOA!",
            color=hex_color
        )
        embed.add_field(name="Roblox Username", value=self.roblox_username.value, inline=False)
        embed.add_field(name="Discord Username", value=self.discord_username.value, inline=False)
        embed.add_field(name="Start Date", value=self.start_date.value, inline=True)
        embed.add_field(name="End Date", value=self.end_date.value, inline=True)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)

        # Create buttons for Accept/Deny
        view = View()
        accept_button = Button(label="Accept", style=ButtonStyle.success)
        deny_button = Button(label="Deny", style=ButtonStyle.danger)

        # Accept button callback
        async def accept_callback(inter: discord.Interaction):
            loa_request = collection.find_one({"user_id": interaction.user.id})
            if loa_request:
                if loa_request["status"] != "pending":
                    status = loa_request["status"]
                    await inter.response.send_message(f"Nuh - uh, <@{interaction.user.id}> has already {status} this LOA request.", ephemeral=True)
                    return

                embed_accept = Embed(
                    title="Your LOA Request Was Accepted",
                    description=(
                        f"Hey there <@{interaction.user.id}>! "
                        f"Your LOA request was accepted and will start on `{self.start_date.value}` "
                        f"and will end on `{self.end_date.value}`."
                    ),
                    color=hex_color
                )
                await interaction.user.send(embed=embed_accept)
                await inter.response.send_message("LOA request accepted.", ephemeral=True)
                collection.update_one(
                    {"user_id": interaction.user.id},
                    {"$set": {"status": "accepted"}}
                )

        # Deny button callback
        async def deny_callback(inter: discord.Interaction):
            loa_request = collection.find_one({"user_id": interaction.user.id})
            if loa_request:
                if loa_request["status"] == "accepted":
                    await inter.response.send_message(f"Nice try! <@{loa_request['user_id']}> already accepted this request.", ephemeral=True)
                    return
                elif loa_request["status"] == "denied":
                    await inter.response.send_message(f"Nice try! <@{loa_request['user_id']}> already denied this request.", ephemeral=True)
                    return
                elif loa_request["status"] == "pending":
                    class DenialReasonModal(Modal, title="Denial Reason"):
                        def __init__(self):
                            super().__init__(title="Denial Reason")
                            self.reason = TextInput(
                                label="Reason for Denial",
                                placeholder="Please explain why this LOA request is denied.",
                                required=True
                            )
                            self.add_item(self.reason)

                        async def on_submit(self, inter_inner: discord.Interaction):
                            embed_deny = Embed(
                                title="Your LOA Request Was Denied",
                                description=(
                                    f"Hey there <@{interaction.user.id}>! "
                                    f"Your LOA request was denied with the reason:\n``{self.reason.value}``."
                                ),
                                color=hex_color
                            )
                            await interaction.user.send(embed=embed_deny)
                            await inter_inner.response.send_message("Denial reason submitted and user notified.", ephemeral=True)
                            collection.update_one(
                                {"user_id": interaction.user.id},
                                {"$set": {"status": "denied", "denial_reason": self.reason.value}}
                            )

                    await inter.response.send_modal(DenialReasonModal())

        accept_button.callback = accept_callback
        deny_button.callback = deny_callback

        view.add_item(accept_button)
        view.add_item(deny_button)

        # Send the embed to the target channel
        log_channel = self.bot.get_channel(1335641734448812255)  # Replace with your channel ID
        if log_channel:
            await log_channel.send(embed=embed, view=view)
        await interaction.response.send_message("Your LOA request has been submitted!", ephemeral=True)


@bot.tree.command(name="request-loa", description="Request an LOA")
async def requestloa(interaction: discord.Interaction):
    if LOA_OPEN:  # No need for == True, since it's already a boolean
        try:
            # Send the LOA modal form
            await interaction.response.send_modal(LoaForm(bot))
        except Exception as e:
            print(f"Error showing modal: {e}")
            await interaction.response.send_message(
                "An error occurred while processing your request. Please try again later.",
                ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "LOA Requests are disabled.",
            ephemeral=True
        )
@bot.tree.command(name="toggle-loa", description="Enable or disable LOA requests (Admin only)")
@commands.has_permissions(administrator=True)  # Restricts command to server admins
async def toggle_loa(interaction: discord.Interaction):
    global LOA_OPEN  # Allows modification of the global variable
    LOA_OPEN = not LOA_OPEN  # Toggle the value (True -> False, False -> True)

    status = "enabled" if LOA_OPEN else "disabled"
    await interaction.response.send_message(
        f"LOA requests have been **{status}**.",
        ephemeral=True  # Message is only visible to the admin
    )
@bot.tree.command(name="restart", description="Restarts the bot.")
@commands.is_owner()
async def restart(interaction: discord.Interaction):
    await interaction.response.send_message("Restarting bot... 🔄", ephemeral=True)
    sys.exit()
# Restart the bot using PM2
@bot.tree.command(name="update", description="Pulls latest code and restarts the bot (Owner only)")
@commands.is_owner()
async def update(interaction: discord.Interaction):
    await interaction.response.send_message("Updating bot... 🔄", ephemeral=True)

    # Set Git remote to ensure it's correct
    subprocess.run(["git", "remote", "set-url", "origin", "https://github.com/Cjverity01/ServalCafeBot"])

    # Pull the latest code
    pull_result = subprocess.run(["git", "pull"], capture_output=True, text=True)

    if "Already up to date." in pull_result.stdout:
        await interaction.followup.send("✅ Bot is already up to date!", ephemeral=True)
    else:
        await interaction.followup.send("✅ Update pulled! Restarting bot... 🔄", ephemeral=True)
        sys.exit()  # Restart the bot using PM2
strikecollection = db["strikes"]
@bot.tree.command(name="strike", description="Give a user a strike with a reason.")
@commands.has_permissions(administrator=True)  # Restricts command to server admins
async def strike(interaction: discord.Interaction, member: discord.User, reason: str):
    if member.id == "1050494667613012049":
        await interaction.response.send_message(f"You Can't strike <@1050494667613012049>, Silly!", ephemeral=True)
    try:
        # Fetch the user data from MongoDB (synchronously)
        user_data = strikecollection.find_one({"user_id": member.id})
        
        # Debug: Print the result of the find query to see what it returns
        print(f"User data fetched: {user_data}")
        
        # If user doesn't exist, create the record
        if not user_data:
            user_data = {"user_id": member.id, "strikes": 0, "reasons": []}

        # Update the strike count and log the reason
        new_strike_count = user_data["strikes"] + 1  # Increment by 1 for each strike
        user_data["reasons"].append(reason)

        # Update the MongoDB document
        strikecollection.update_one(
            {"user_id": member.id},
            {"$set": {"strikes": new_strike_count, "reasons": user_data["reasons"]}},
            upsert=True
        )

        # Notify the admin that the strike has been applied
        await interaction.response.send_message(f"{member.mention} now has {new_strike_count} strike(s). Reason: {reason}", ephemeral=True)

        # If the user reaches 3 strikes, send them a DM and reset the strike count
        if new_strike_count >= 3:
            embed = discord.Embed(
                title="You Have Reached 3 Strikes",
                description=f"You have reached ``3`` strikes so you will be suspended for 5 days shortly. The most recent strike is for the reason: {reason}.",
                color=hex_color
            )
            embed.set_footer(text="Bot Powered by Cj's Commissions")
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                print(f"Could not DM {member.mention}. DMs might be closed.")
            
            # After sending the DM, reset the strike count to 0 in the database
            strikecollection.update_one(
                {"user_id": member.id},
                {"$set": {"strikes": 0}},  # Reset the strikes to 0
                upsert=True
            )

        else:
            # Send the general strike message to the user
            embed = discord.Embed(
                title="You have been striked",
                description=f"Hello, {member.mention}. You have received a strike for {reason}.",
                color=hex_color
            )
            embed.set_footer(text="Bot Powered by Cj's Commissions")
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                print(f"Could not DM {member.mention}. DMs might be closed.")
                # Continue execution even if DMs are closed

        # Now, handle the Roblox ID fetch and ranking
        roblox_id = None  # Initialize roblox_id to prevent unbound variable errors
        try:
            # First API call to fetch Roblox ID
            response_roblox = requests.get(
                f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{member.id}",
                headers={"Authorization": "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"}
            )
            if response_roblox.status_code == 200:
                data = response_roblox.json()
                roblox_id = data.get("robloxID")  # Extract the 'robloxID' field
                if not roblox_id:
                    await interaction.followup.send("Could not find a Roblox ID for this user.")
                    return
            else:
                await interaction.followup.send(f"Failed to fetch Roblox ID. Status Code: {response_roblox.status_code}")
                return
        except Exception as e:
            await interaction.followup.send(f"An error occurred while fetching Roblox ID: {e}")
            return

        # Second API call to rank the user
        full_url = f"https://ranking.cjscommissions.xyz/group/rank/?groupid=16461735&user_id={roblox_id}&role_number=4&key=CJSCOMMSRANK"
        requests.get(full_url)  # We just call the API without handling the response data

    except Exception as e:
        print(f"Error in strike command: {e}")
        await interaction.response.send_message("An error occurred while applying the strike.", ephemeral=True)
@bot.tree.command(name="debug")
@commands.is_owner()
async def debug_hastebin(interaction: discord.Interaction):
    """Posts bot's console logs to Hastebin."""
    haste_url = os.environ.get("HASTE_URL", "https://hastebin.cc")

    # Ensure console output is logged to a file
    sys.stdout.flush()  # Flush the current output buffer
    with open("bot_console.log", "rb") as f:
        logs = BytesIO(f.read().strip())

    try:
        async with bot.session.post(f"{haste_url}/documents", data=logs) as resp:
            data = await resp.json()
            key = data.get("key")

            if not key:
                raise KeyError("No key returned from Hastebin")

            embed = discord.Embed(
                title="Debug Logs",
                description=f"{haste_url}/{key}",
                color=discord.Color.blue(),
            )
            await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="Debug Logs",
            color=discord.Color.red(),
            description="Something went wrong. Unable to upload logs to Hastebin.",
        )
        embed.set_footer(text=f"Error: {e}")
        await interaction.response.send_message(embed=embed)
bot.run(os.getenv("TOKEN"))

