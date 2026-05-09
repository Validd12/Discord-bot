import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
channel_env = os.getenv('CHANNEL_ID')
CHANNEL_ID = int(channel_env) if channel_env else 0
URL = "https://www.sshxl.nl/en/rental-offer/long-stay"

# This will save in the current folder
DB_FILE = "seen_long_stay.txt"

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

def get_seen():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f: return set(line.strip() for line in f)

def add_seen(room_id):
    with open(DB_FILE, "a") as f: f.write(f"{room_id}\n")

@client.event
async def on_ready():
    print(f'🚀 Bot is online!')
    
    # Send online message to Discord
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🤖 **Bot is now online and monitoring SSHXL!**")
        
    if not check_ssh.is_running():
        check_ssh.start()

@tasks.loop(seconds=60)
async def check_ssh():
    channel = client.get_channel(CHANNEL_ID)
    if not channel: return

    seen = get_seen()
    
    try:
        # User-Agent makes the bot look like a real browser
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(URL, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return

        soup = BeautifulSoup(r.text, 'html.parser')
        listings = soup.find_all('div', class_='inventory-item') or soup.find_all('article')

        for room in listings:
            link_tag = room.find('a', href=True)
            if not link_tag: continue
            
            href = link_tag['href']
            room_id = href.strip('/').split('/')[-1]

            if room_id not in seen:
                add_seen(room_id)
                room_url = f"https://www.sshxl.nl{href}" if href.startswith('/') else href
                
                # Simple message as requested
                await channel.send(f"A new room appeared! {room_url}")

    except Exception as e:
        print(f"⚠️ Scan Error: {e}")

client.run(TOKEN)
