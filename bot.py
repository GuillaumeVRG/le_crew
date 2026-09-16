import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
AUTO_ROLE_ID = int(os.getenv("AUTO_ROLE_ID"))
VOICE_HUB_ID = int(os.getenv("VOICE_HUB_ID"))
PORT = int(os.getenv("PORT", 8080))

# Serveur HTTP basique pour UptimeRobot
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is online!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

# Configuration du bot Discord
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Suivi des salons vocaux temporaires créés
temp_channels = {}

@bot.event
async def on_ready():
    print(f"Connecté sous le nom de : {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation : {e}")

@bot.event
async def on_member_join(member):
    # Attribution du rôle automatique
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"Erreur ajout de rôle : {e}")

    # Message de bienvenue
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Bienvenue !",
            description=f"Bienvenue sur le serveur, {member.mention} !",
            color=0x3498DB
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # Création du salon si un membre rejoint le HUB vocal
    if after.channel and after.channel.id == VOICE_HUB_ID:
        category = after.channel.category
        new_channel = await guild.create_voice_channel(
            name=f"Salon de {member.display_name}",
            category=category
        )
        temp_channels[new_channel.id] = member.id
        await member.move_to(new_channel)

    # Nettoyage si le salon temporaire est vide
    if before.channel and before.channel.id in temp_channels:
        if len(before.channel.members) == 0:
            del temp_channels[before.channel.id]
            try:
                await before.channel.delete()
            except Exception as e:
                print(f"Erreur suppression du salon : {e}")

# Lancement du serveur HTTP puis du bot
threading.Thread(target=run_http_server, daemon=True).start()
bot.run(TOKEN)