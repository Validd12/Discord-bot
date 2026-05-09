import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# === CONFIGURATION FROM ENV ===
TOKEN = os.getenv('DISCORD_TOKEN')
# Convert ID to integer because env variables are always strings
CHANNEL_ID = int(os.getenv('CHANNEL_ID')) 
URL = "https://www.sshxl.nl/en/rental-offer/long-stay"
CHECK_INTERVAL = 60 
# ==============================

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

DB_FILE = "seen_long_stay.txt"

def get_seen():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f: return set(line.strip() for line in f)

def add_seen(room_id):
    with open(DB_FILE, "a") as f: f.write(f"{room_id}\n")

@client.event
async def on_ready():
    print(f'🚀 Bot is online! Monitoring: {URL}')
    channel = client.get_channel(CHANNEL_ID)
    
    if channel:
        await channel.send("🤖 **Bot is now active!** I am officially watching the SSH website for new rooms.")
    else:
        print("❌ ERROR: Could not find the channel. Check your CHANNEL_ID.")
        
    if not check_ssh.is_running():
        check_ssh.start()

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_ssh():
    channel = client.get_channel(CHANNEL_ID)
    if not channel: return

    seen = get_seen()
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(URL, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        listings = soup.find_all('div', class_='inventory-item')
        if not listings:
            listings = soup.find_all('article')

        for room in listings:
            link_tag = room.find('a', href=True)
            if not link_tag: continue
            
            room_url = "https://www.sshxl.nl" + link_tag['href']
            room_id = link_tag['href'].strip('/').split('/')[-1]

            if room_id not in seen:
                add_seen(room_id)
                
                title = room.find('h3').text.strip() if room.find('h3') else "New Listing"
                price = "Check site"
                price_tag = room.find('span', class_='price')
                if price_tag: price = price_tag.text.strip()

                embed = discord.Embed(
                    title="🔑 NEW LONG-STAY ROOM!",
                    url=room_url,
                    color=0xFF5733 
                )
                embed.add_field(name="Location", value=title, inline=False)
                embed.add_field(name="Rent", value=price, inline=True)
                
                await channel.send(content="@everyone 🏠 **New Room Alert!**", embed=embed)
                print(f"✅ Posted listing: {title}")

    except Exception as e:
        print(f"⚠️ Error: {e}")

client.run(TOKEN)