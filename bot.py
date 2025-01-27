import discord
from discord.ext import commands
import time
from dotenv import load_dotenv
import os
from datetime import timedelta
from discord.ui import Modal, TextInput, Button, View
load_dotenv()
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
GUILD_ID = os.getenv("GUILD_ID")
RANKING_ROLE_ID = os.getenv("RANKING_ROLE_ID")
hex_color = int("86A269", 16)
# Create the bot instance
intents = discord.Intents.default()
intents.messages = True  # Enable the messages intent
bot = commands.Bot(command_prefix="!", intents=intents)

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



# Your bot initialization
bot = commands.Bot(command_prefix="!")

# Define the Modal Form for LOA submission
class FormModal(Modal):
    def __init__(self):
        super().__init__(title="LOA Submission Form")

        # Add the text input fields to the modal
        self.robloxuser_input = TextInput(label="What is your Roblox username?", placeholder="Gamingwithcj2011")
        self.dcuser_input = TextInput(label="What Is Your Discord Username?", placeholder="cj_daboi36")
        self.start_input = TextInput(label="When does your LOA start?", placeholder="01/02/25")
        self.end_input = TextInput(label="When does your LOA end?", placeholder="15/02/25")
        self.reason_input = TextInput(label="Why are you requesting this LOA?", placeholder="I am taking a break from Roblox.")
        self.emg_input = TextInput(label="Is it an emergency?", placeholder="No")
        self.recently_input = TextInput(label="Have you had an LOA recently?", placeholder="No, I have not had one for a while.")

        # Add inputs to the modal
        self.add_item(self.robloxuser_input)
        self.add_item(self.dcuser_input)
        self.add_item(self.start_input)
        self.add_item(self.end_input)
        self.add_item(self.reason_input)
        self.add_item(self.emg_input)
        self.add_item(self.recently_input)

    async def callback(self, interaction: discord.Interaction):
        roblox_username = self.robloxuser_input.value
        dc_username = self.dcuser_input.value
        start_date = self.start_input.value
        end_date = self.end_input.value
        reason = self.reason_input.value
        is_emergency = self.emg_input.value
        recently_taken_loa = self.recently_input.value
        
        # Construct the embed to be sent to a set channel
        embed = discord.Embed(
            title="Someone Has Requested an LOA",
            description=f"<@{interaction.user.id}> has requested an LOA. Here is the form:",
            color=discord.Color.green()
        )
        embed.add_field(name="Roblox Username", value=roblox_username, inline=True)
        embed.add_field(name="Discord Username", value=dc_username, inline=True)
        embed.add_field(name="LOA Start Date", value=start_date, inline=True)
        embed.add_field(name="LOA End Date", value=end_date, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Emergency?", value=is_emergency, inline=True)
        embed.add_field(name="Had recent LOA?", value=recently_taken_loa, inline=True)

        # Create the "Accept" button
        accept_button = Button(label="Accept", style=discord.ButtonStyle.green)
        # Create the "Decline" button
        decline_button = Button(label="Decline", style=discord.ButtonStyle.red)

        # Define a View to hold the buttons
        view = View()
        view.add_item(accept_button)
        view.add_item(decline_button)

        # Send the embed and the buttons to the set channel
        channel = bot.get_channel(SET_CHANNEL_ID)  # Replace with the actual channel ID
        await channel.send(content="@everyone", embed=embed, view=view)

        # Interaction response to the user
        await interaction.response.send_message("Your LOA request has been submitted.", ephemeral=True)

        # When the "Accept" button is clicked
        async def on_accept_button_click(interaction: discord.Interaction):
            # Send a DM to the user who requested the LOA
            dm_embed = discord.Embed(
                title="LOA Accepted",
                description=f"Hey <@{interaction.user.id}>! Your LOA has been accepted and will start on {start_date} and end on {end_date}.",
                color=discord.Color.green()
            )
            await interaction.user.send(embed=dm_embed)

            # Confirm acceptance in the channel
            await interaction.response.send_message(f"LOA request from <@{interaction.user.id}> has been accepted!", ephemeral=True)

        accept_button.callback = on_accept_button_click

        # When the "Decline" button is clicked
        async def on_decline_button_click(interaction: discord.Interaction):
            # Create a new modal for the decline reason
            decline_modal = DeclineReasonModal()
            await interaction.response.send_modal(decline_modal)

        decline_button.callback = on_decline_button_click

# Define the Modal Form for Decline reason
class DeclineReasonModal(Modal):
    def __init__(self):
        super().__init__(title="Reason for Declining LOA")

        # Add the text input field for the reason
        self.decline_reason_input = TextInput(label="Why is this LOA declined?", placeholder="Reason for declining the LOA.")
        self.add_item(self.decline_reason_input)

    async def callback(self, interaction: discord.Interaction):
        decline_reason = self.decline_reason_input.value

        # Send a DM to the user with the decline message
        dm_embed = discord.Embed(
            title="Your LOA Was Rejected",
            description=f"Hey <@{interaction.user.id}>! Your LOA was rejected and the reason is: ``{decline_reason}``.",
            color=discord.Color.red()
        )
        await interaction.user.send(embed=dm_embed)

        # Confirm the rejection in the channel
        await interaction.response.send_message(f"LOA request from <@{interaction.user.id}> has been rejected.", ephemeral=True)

# Command that triggers the LOA form submission
@bot.tree.command(name="request-loa", description="Submit an LOA request")
async def loa_command(interaction: discord.Interaction):
    # Trigger the modal to be shown to the user
    modal = FormModal()
    await interaction.response.send_modal(modal)



bot.run(TOKEN)
