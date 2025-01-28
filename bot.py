import discord
from discord import Interaction, Embed, ButtonStyle
from discord import ui
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from discord.ui import Modal, TextInput, Button, View
import logging
from discord.ext.commands import Bot
import traceback
from pymongo import MongoClient
import requests
import time
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
GUILD_ID = os.getenv("GUILD_ID")
RANKING_ROLE_ID = os.getenv("RANKING_ROLE_ID")
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

# Load token from environment variable
TOKEN = os.getenv("TOKEN")

@bot.event
async def on_ready():
    print("Loading...")
    print("---------------------")
    print("Authors: cj_daboi36.")
    print("---------------------")
    await bot.tree.sync()  # Sync slash commands to Discord
    print("Slash commands synced")
    print("---------------------")
    print(f'Loaded! Connected To: {bot.user}')
    print("---------------------")
    print("Started Successfully!")

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
        log_channel = bot.get_channel(1333571422970445955)  # Replace with your channel ID
        if log_channel:
            await log_channel.send(embed=embed, view=view)

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
    
    if member and any(role.id == RANKING_ROLE_ID for role in member.roles):  # Check if user has the required role
        roblox_id = None  # Initialize roblox_id to prevent unbound variable errors
        try:
            # First API call to fetch Roblox ID
            response = requests.get(f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{user.id}", 
                                    headers={"Authorization" : "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"})
            if response.status_code == 200:
                data = response.json()
                roblox_id = data.get("robloxID")  # Extract the 'robloxID' field
                if not roblox_id:
                    await interaction.response.send_message("Could not find a Roblox ID for this user.")
                    return
            else:
                await interaction.response.send_message(f"Failed to fetch Roblox ID. Status Code: {response.status_code}")
                return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while fetching Roblox ID: {e}")
            return

        # Second API call to promote the user
        full_url = f"https://ranking.cjscommissions.xyz/group/promote/?groupid=16461735&user_id={roblox_id}&key=CJSCOMMSRANK"
        try:
            response = requests.get(full_url)
            if response.status_code == 200:
                data = response.json()
                message = data.get("message")
                if message == "The user was promoted!":
                    await interaction.response.send_message(f"Successfully promoted {user.name}!")
            else:
                await interaction.response.send_message(f"Failed to promote user. Status Code: {response.status_code}")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during promotion: {e}")

@bot.tree.command(name="demote", description="Demote a user.")
async def promote(interaction: discord.Interaction, user: discord.User):
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)
    
    if member and any(role.id == RANKING_ROLE_ID for role in member.roles):  # Check if user has the required role
        try:
            roblox_id = None  # Initialize roblox_id to prevent unbound variable errors

            # First API call to fetch Roblox ID
            response = requests.get(f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{user.id}",  
                                    headers={"Authorization" : "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"})
            if response.status_code == 200:
                data = response.json()
                roblox_id = data.get("robloxID")  # Extract the 'robloxID' field
                if not roblox_id:
                    await interaction.response.send_message("Could not find a Roblox ID for this user.")
                    return
            else:
                await interaction.response.send_message(f"Failed to fetch Roblox ID. Status Code: {response.status_code}")
                return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while fetching Roblox ID: {e}")
            return

        # Second API call to demote the user
        full_url = f"https://ranking.cjscommissions.xyz/group/demote/?groupid=16461735&user_id={roblox_id}&key=CJSCOMMSRANK"
        try:
            response = requests.get(full_url)
            if response.status_code == 200:
                data = response.json()
                message = data.get("message")
                if message == "The user was demoted!":
                    await interaction.response.send_message(f"Successfully demoted {user.name}!")
            else:
                await interaction.response.send_message(f"Failed to demote user. Status Code: {response.status_code}")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during demotion: {e}")

@bot.tree.command(name="rank", description="Rank a user.")
async def setrank(interaction: discord.Interaction, user: discord.User, rank: str):
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)
    if member and any(role.id == RANKING_ROLE_ID for role in member.roles):
     
        try:
            roblox_id = None  # Initialize roblox_id to prevent unbound variable erro
            # First API call to fetch Roblox ID
            response_roblox = requests.get(
                f"https://api.blox.link/v4/public/guilds/1272622697079377920/discord-to-roblox/{user.id}",
                headers={"Authorization": "2e306432-1dcc-4d3a-88d2-3fdb7d84a221"}
            )
            if response_roblox.status_code == 200:
                data = response_roblox.json()
                roblox_id = data.get("robloxID")  # Extract the 'robloxID' field
                if not roblox_id:
                    await interaction.response.send_message("Could not find a Roblox ID for this user.")
                    return
            else:
                await interaction.response.send_message(f"Failed to fetch Roblox ID. Status Code: {response_roblox.status_code}")
                return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while fetching Roblox ID: {e}")
            return

        # Second API call to rank the user
        full_url = f"https://ranking.cjscommissions.xyz/group/rank/?groupid=16461735&user_id={roblox_id}&role_number={rank}&key=CJSCOMMSRANK"
        try:
            response_rank = requests.get(full_url)
            if response_rank.status_code == 200:
                data = response_rank.json()
                message = data.get("message")
                if message == f"The user's rank has been set to {rank}!":
                    await interaction.response.send_message(f"Successfully ranked the user!")
                else:
                    await interaction.response.send_message(f"Error: {message}")
            else:
                await interaction.response.send_message(f"Failed to rank user. Status Code: {response_rank.status_code}")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during ranking: {e}")
    else:
        await interaction.response.send_message("You do not have the required role to rank users.")
@bot.tree.command(name="shift", description="Start a shift")
async def shift(interaction: discord.Interaction):
    # Settings for this command
    required_role_id = 1317560300060541112  # The required role ID for this command
    role_to_ping = 1308833378153267210  # The role to ping
    response_channel_id = 1308833433379934218  # Channel to send the message to

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == "1325941896438223001" for role in member.roles):
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
                await channel.send(content=f"<@&1325941898212540426>", embed=embed)
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
    response_channel_id = 1308833433379934218  # Channel to send the message to

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == "1325941896438223001" for role in member.roles):
        # Get the channel to send the message to
        channel = bot.get_channel(response_channel_id)

        if channel:
            # Create the embed
            embed = discord.Embed(
                title="The Recent Shift Has Ended",
                description="The recent shift has now ended! Thank you to all the attendees. Dont forget to checkout the shift picture in <#1305300770354368532>!",
                color=hex_color
            )

            embed.set_footer(text="Bot Powered by Cj's Commissions")
            await channel.send(embed=embed)

            await interaction.response.send_message("Shift started successfully. Please stay in the shift for at least 15 minutes or you will be striked!", ephemeral=True)
        else:
            await interaction.response.send_message("An error occured while sending.", ephemeral=True)
    else:
        await interaction.response.send_message("Nuh - Uh. You don't have the required role to run this command.", ephemeral=True)
@bot.tree.command(name="training", description="Start a training")
async def shift(interaction: discord.Interaction):
    # Settings for this command
    required_role_id = 1317560300060541112  # The required role ID for this command
    role_to_ping = 1308833378153267210  # The role to ping
    response_channel_id = 1308833433379934218  # Channel to send the message to

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == "1333537526232645685" for role in member.roles):
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
    response_channel_id = 1308833433379934218  # Channel to send the message to

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == "1333537526232645685" for role in member.roles):
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
    response_channel_id = 1308833433379934218  # Channel to send the message to

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == "1333537526232645685" for role in member.roles):
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
    response_channel_id = 1308833433379934218  # Channel to send the message to

    # Check if the interaction is in a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command must be run in a guild.")
        return

    # Fetch the specific guild and member
    guild = await bot.fetch_guild(GUILD_ID)
    member = await guild.fetch_member(interaction.user.id)

    if member and any(role.id == "1333537526232645685" for role in member.roles):
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
    await interaction.channel.purge(limit=amount)  
    await interaction.response.send_message(f"Purged {amount} messages.", delete_after=5)  
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
        log_channel = self.bot.get_channel(1333571422970445955)  # Replace with your channel ID
        if log_channel:
            await log_channel.send(embed=embed, view=view)
        await interaction.response.send_message("Your LOA request has been submitted!", ephemeral=True)

@bot.tree.command(name="request-loa", description="Request an LOA")
async def loa_command(interaction: discord.Interaction):
    modal = LoaForm(bot)
    await interaction.response.send_modal(modal)
bot.run(TOKEN)
