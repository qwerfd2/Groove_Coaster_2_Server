import discord
from discord.ext import commands
from discord import Interaction, TextStyle, app_commands
from discord.ui import Modal, TextInput, View, Button
import httpx

from config import DISCORD_BOT_SECRET, DISCORD_BOT_API_KEY, OVERRIDE_HOST, HOST, PORT

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

BIND_CHANNEL_ID = 1439460843015372971

URL_HOST = OVERRIDE_HOST if OVERRIDE_HOST is not None else ("http://" + HOST + ":" + str(PORT) + "/")

def only_in_bind_channel():
    def predicate(interaction: discord.Interaction) -> bool:
        if isinstance(interaction.channel, discord.DMChannel):
            return False
        return interaction.channel_id == BIND_CHANNEL_ID
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    print(f"[Discord] Bot connected as {bot.user}")

    try:
        await bot.tree.sync()
    except Exception as e:
        print("[Discord] Error syncing commands:", e)

    # Register persistent view
    bot.add_view(BindButtons())

    channel = bot.get_channel(BIND_CHANNEL_ID)
    if channel:
        # Delete old messages from the bot
        async for message in channel.history(limit=100):
            if message.author == bot.user:
                try:
                    await message.delete()
                except:
                    pass
        
        # Send the new message with buttons
        await channel.send("Use the buttons below:", view=BindButtons())

        
async def get_account_info(discord_id: str):
    request_url = URL_HOST + "discord_get_bind"
    request_post = {"discord_id": discord_id}
    request_headers = {"X-API-KEY": DISCORD_BOT_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.post(request_url, data=request_post, headers=request_headers)
        response_data = response.json()
        print("get_account_info called by ", discord_id, " response payload:", response.text)

        prefix = "✅ " if response_data.get("state") == 1 else "❌ "
        return prefix + response_data.get("message", "No message provided.")

async def get_otp(username: str, bind_token: str, discord_id: str):
    request_url = URL_HOST + "discord_get_token"
    request_post = {
        "username": username,
        "bind_token": bind_token,
        "discord_id": discord_id
    }
    request_headers = {"X-API-KEY": DISCORD_BOT_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.post(request_url, data=request_post, headers=request_headers)
        print("get_otp called by ", discord_id, " response payload:", response.text)
        response_data = response.json()

        prefix = "✅ " if response_data.get("state") == 1 else "❌ "
        return prefix + response_data.get("message", "No message provided.")
    
async def reset_password(password: str, discord_id: str):
    request_url = URL_HOST + "discord_reset_password"
    request_post = {
        "password": password,
        "discord_id": discord_id
    }
    request_headers = {"X-API-KEY": DISCORD_BOT_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.post(request_url, data=request_post, headers=request_headers)
        print("reset_password called by ", discord_id, " response payload:", response.text)
        response_data = response.json()

        prefix = "✅ " if response_data.get("state") == 1 else "❌ "
        return prefix + response_data.get("message", "No message provided.")

async def ban_user_from_game_service(discord_id: str):
    try:
        request_url = URL_HOST + "discord_ban"
        request_post = {"discord_id": discord_id}
        request_headers = {"X-API-KEY": DISCORD_BOT_API_KEY}

        async with httpx.AsyncClient() as client:
            response = await client.post(request_url, data=request_post, headers=request_headers)
            data = response.json()
            print("ban_user_from_game_service called by ", discord_id, " response payload:", response.text)

            prefix = "✅ " if data.get("state") == 1 else "❌ "
            return prefix + data.get("message", "No message provided.")

    except Exception as e:
        return f"❌ Error: {str(e)}"

async def try_unban_user_from_game_service(discord_id: str):
    try:
        request_url = URL_HOST + "discord_unban"
        request_post = {"discord_id": discord_id}
        request_headers = {"X-API-KEY": DISCORD_BOT_API_KEY}

        async with httpx.AsyncClient() as client:
            response = await client.post(request_url, data=request_post, headers=request_headers)
            data = response.json()
            print("try_unban_user_from_game_service called by ", discord_id, " response payload:", response.text)

            prefix = "✅ " if data.get("state") == 1 else "❌ "
            return prefix + data.get("message", "No message provided.")

    except Exception as e:
        return f"❌ Error: {str(e)}"

# -------------------------------
# Modal Definition
# -------------------------------

class BindModal(Modal, title="Bind Your Account"):
    username = TextInput(
        label="Username",
        placeholder="Enter your in-game username",
        style=TextStyle.short,
        required=True,
    )

    bind_token = TextInput(
        label="Bind Token",
        placeholder="Enter your bind token",
        style=TextStyle.short,
        required=True,
    )

    async def on_submit(self, interaction: Interaction):
        username = self.username.value
        bind_token = self.bind_token.value

        if not username or not username.strip():
            return await interaction.response.send_message(
                "❌ Username cannot be empty.", ephemeral=True
            )
        
        if len(username) < 6 or len(username) > 20:
            return await interaction.response.send_message(
                "❌ Username length not valid.", ephemeral=True
            )

        if not bind_token or not bind_token.strip():
            return await interaction.response.send_message(
                "❌ Bind token cannot be empty.", ephemeral=True
            )
        
        if len(bind_token) > 10:
            return await interaction.response.send_message(
                "❌ Bind token length not valid.", ephemeral=True
            )

        discord_id = str(interaction.user.id)

        response = await get_otp(username, bind_token, discord_id)
        await interaction.response.send_message(response, ephemeral=True)

class PasswordResetModal(Modal, title="Password Reset"):
    password = TextInput(
        label="New Password (Requirement: 6 characters or longer)",
        placeholder="Your New Password",
        style=TextStyle.short,
        required=True,
    )

    repeat_password = TextInput(
        label="Repeat New Password",
        placeholder="Repeat The Password",
        style=TextStyle.short,
        required=True,
    )

    async def on_submit(self, interaction: Interaction):
        password = self.password.value
        repeat_password = self.repeat_password.value

        if not password or not password.strip():
            return await interaction.response.send_message(
                "❌ Password cannot be empty.", ephemeral=True
            )

        if not repeat_password or not repeat_password.strip():
            return await interaction.response.send_message(
                "❌ Repeat Password cannot be empty.", ephemeral=True
            )
        
        if len(password) < 6:
            return await interaction.response.send_message(
                "❌ Password must have 6 or more characters.", ephemeral=True
            )
        
        if password != repeat_password:
            return await interaction.response.send_message(
                "❌ Repeat Password does not match.", ephemeral=True
            )

        discord_id = str(interaction.user.id)

        response = await reset_password(password, discord_id)
        await interaction.response.send_message(response, ephemeral=True)

class BindButtons(View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent buttons

    @discord.ui.button(label="Bind Account", style=discord.ButtonStyle.primary, custom_id="btn_bind")
    async def bind_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(BindModal())

    @discord.ui.button(label="Who Am I?", style=discord.ButtonStyle.secondary, custom_id="btn_whoami")
    async def whoami_button(self, interaction: Interaction, button: Button):
        discord_id = str(interaction.user.id)
        response = await get_account_info(discord_id)
        await interaction.response.send_message(response, ephemeral=True)

    @discord.ui.button(label="Reset Password", style=discord.ButtonStyle.danger, custom_id="btn_password_reset")
    async def password_reset_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(PasswordResetModal())

# -------------------------------
# Member Events
# -------------------------------

@bot.event
async def on_member_remove(member):
    print(f"{member.name} left the server → banning in-game.")
    await ban_user_from_game_service(str(member.id))

@bot.event
async def on_member_join(member):
    print(f"{member.name} joined the server → unbanning in-game if needed.")
    await try_unban_user_from_game_service(str(member.id))

# -------------------------------
# Prefix command error handler
# -------------------------------

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: {error.param.name}.", ephemeral=True)
    else:
        await ctx.send(f"❌ Error: {str(error)}", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send("❌ This bot does not accept direct messages. Please use it in a server.")
        return

    if message.channel.id == BIND_CHANNEL_ID:
        # Delete user messages
        await message.delete()
        return

bot.run(DISCORD_BOT_SECRET)