import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load variables from Railway's "Variables" tab
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
# Use a fallback value if CHANNEL_ID isn't found to prevent crashing
channel_env = os.getenv('CHANNEL_ID')
CHANNEL_ID = int(channel_env) if channel_env else 0
URL = "https://www.sshxl.nl/en/rental-offer/long-stay"

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

# Railway's file system is temporary. 
# This file will reset if the bot restarts unless you use a Volume, 
# but for now, this will prevent immediate spam.
DB_FILE = "seen_long_stay.txt"

def get_seen():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f: return set(line.strip() for line in f)

def add_seen(room_id):
    with open(DB_FILE, "a") as f: f.write(f"{room_id}\n")

@client.event
async def on_ready():
    print(f'🚀 Railway Bot is online!')
    if not check_ssh.is_running():
        check_ssh.start()

@tasks.loop(seconds=60)
async def check_ssh():
    channel = client.get_channel(CHANNEL_ID)
    if not channel: return

    seen = get_seen()
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        listings = soup.find_all('div', class_='inventory-item')
        if not listings: listings = soup.find_all('article')

        for room in listings:
            link_tag = room.find('a', href=True)
            if not link_tag: continue
            
            room_id = link_tag['href'].strip('/').split('/')[-1]

            if room_id not in seen:
                add_seen(room_id)
                room_url = "https://www.sshxl.nl" + link_tag['href']
                await channel.send(f"🏠 **New Room Alert!**\n{room_url}")

    except Exception as e:
        print(f"⚠️ Scan Error: {e}")

client.run(TOKEN)
