import discord
from discord.ext import commands, tasks
import time, aiohttp, asyncio, os
from datetime import datetime, timedelta
import logging

# =========================
# LOGGING SETUP
# =========================
file_handler = logging.FileHandler('bot.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

try:
    import sys
    if sys.platform == "win32":
        import os
        os.system("chcp 65001 > nul")
        console_handler.setStream(sys.stdout)
except:
    pass

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================
TOKEN = "" # PUT YOUR DISCORD BOT TOKEN HERE! WARNING: DO NOT SHARE THIS TO ANYONE!
ROBLOX_COOKIE = "" # PUT YOUR ROBLOXSECURITY TOKEN HERE! WARNING: DO NOT SHARE THIS TO ANYONE!

if not TOKEN:
    logger.error("DISCORD_TOKEN not set!")
    exit(1)

# Guild IDs
GUILD_IDS = [1361762978420101441] # PUT YOUR DISCORD GUILD ID HERE!

# Channels - WATCH THESE FOR "FOUND" KEYWORD
CHANNEL_GLITCH_WATCH = 1408933228189847634
CHANNEL_DREAMSPACE_WATCH = 1408933138410766506
CHANNEL_DEV_FINDINGS = 1408933411313418361
CHANNEL_STATUS = 1408933515780685864

# Roles - do not change
ROLE_DEV = 1408934014395351171
ROLE_ZERO = 1408935091547144232
ROLE_STIGMA = 1408935121830019133
ROLE_DIMENSIONAL = 1422646382258294794

# Roblox IDs - do not change unless a developer/owner is changed. 
# do not change anything below this unless you know what you are doing.
DEV_IDS = [3929062638, 3620970055, 1343308718, 934375856,
           1971714479, 2036136520, 525498778, 8079577622]
OWNER_IDS = {
    2912484262: None,
    419860256: "zero",
    361208413: "stigma",
    108254410: "dimensional",
    3746869261: None,
}

# Logos
LOGO_DEFAULT = "https://yt3.googleusercontent.com/JaiZqZNxNPXvU6QRT6hbhiFCa3pnx_3eow_yyIBBX9Q3PggjlhybflGQ9wUxnySzH5jC9qqVIg=s900-c-k-c0x00ffffff-no-rj"

# Colors
COLOR_DEV = 0xFFFFFF
COLOR_STATUS = 0xFFFFFF
COLOR_RED = 0xFF0000

# Constants
SOLS_RNG_GAME_ID = 5361032378
GLITCH_BADGE_ID = "3137343012568311"
DREAMSPACE_BADGE_ID = "3625566987462442"
DIMENSIONAL_BADGE_ID = ""  # Replace with actual badge ID
MAX_RETRIES = 3
API_TIMEOUT = 10

# =========================
# BOT SETUP
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

startup_time = time.time()
biome_find_count = 0  # Tracks "found" messages from watch channels
dev_count = 0
owner_count = 0
status_message = None
already_announced = set()
api_error_count = 0

# =========================
# HELPERS
# =========================
async def make_api_request(session, method, url, **kwargs):
    """Make API request with retries and error handling"""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.request(method, url, timeout=API_TIMEOUT, **kwargs) as resp:
                return resp.status, await resp.json()
        except asyncio.TimeoutError:
            logger.warning(f"API request timeout (attempt {attempt + 1}/{MAX_RETRIES}): {url}")
        except Exception as e:
            logger.error(f"API request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(2 ** attempt)
    
    return None, None

async def get_usernames(user_ids):
    """Get Roblox usernames from user IDs with error handling"""
    if not user_ids:
        return {}
        
    try:
        async with aiohttp.ClientSession() as sess:
            status, data = await make_api_request(
                sess, "POST", "https://users.roblox.com/v1/users",
                json={"userIds": user_ids}
            )
            
            if status == 200 and data:
                return {u["id"]: u["name"] for u in data.get("data", [])}
            else:
                logger.warning(f"Failed to get usernames: status {status}")
                return {uid: f"User_{uid}" for uid in user_ids}
                
    except Exception as e:
        logger.error(f"Error getting usernames: {e}")
        return {uid: f"User_{uid}" for uid in user_ids}

async def check_badge(user_id, badge_id):
    """Check if user has a specific badge"""
    if not ROBLOX_COOKIE:
        return False
        
    try:
        cookies = {".ROBLOSECURITY": ROBLOX_COOKIE}
        async with aiohttp.ClientSession(cookies=cookies) as sess:
            status, data = await make_api_request(
                sess, "GET", 
                f"https://badges.roblox.com/v1/users/{user_id}/badges/awarded-dates?badgeIds={badge_id}"
            )
            
            if status == 200 and data:
                return len(data.get("data", [])) > 0
            return False
            
    except Exception as e:
        logger.error(f"Error checking badge for user {user_id}: {e}")
        return False

# =========================
# DEV DETECTION
# =========================
async def announce_dev(uid, username, status):
    """Announce developer/owner presence"""
    try:
        role_pings = [f"<@&{ROLE_DEV}>"]
        
        owner_type = OWNER_IDS.get(uid)
        if owner_type == "zero":
            role_pings.append(f"<@&{ROLE_ZERO}>")
        elif owner_type == "stigma":
            role_pings.append(f"<@&{ROLE_STIGMA}>")
        elif owner_type == "dimensional":
            role_pings.append(f"<@&{ROLE_DIMENSIONAL}>")

        profile_url = f"https://www.roblox.com/users/{uid}/profile"
        embed = discord.Embed(
            title="Sol's Developer/Owner Found!",
            description=(f"**Username:** {username}\n"
                        f"**User ID:** {uid}\n"
                        f"**Status:** {status}\n"
                        f"**Profile:** [Open profile]({profile_url})"),
            color=COLOR_DEV,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=LOGO_DEFAULT)
        
        # Check for dimensional badge if this is 54_xyz
        if uid == 108254410:        
            channel = bot.get_channel(CHANNEL_DEV_FINDINGS)
        if channel:
            await channel.send(" ".join(role_pings), embed=embed)
            logger.info(f"Announced dev {username} ({uid}) online")
        else:
            logger.error("Dev findings channel not found")
            
    except Exception as e:
        logger.error(f"Error announcing dev {uid}: {e}")

async def announce_dev_left(uid, username):
    """Announce developer/owner left"""
    try:
        profile_url = f"https://www.roblox.com/users/{uid}/profile"
        embed = discord.Embed(
            title="Developer/Owner Left Server",
            description=(f"**Username:** {username}\n"
                        f"**User ID:** {uid}\n"
                        f"**Profile:** [Open profile]({profile_url})"),
            color=COLOR_RED,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=LOGO_DEFAULT)
        
        channel = bot.get_channel(CHANNEL_DEV_FINDINGS)
        if channel:
            await channel.send(embed=embed)
            logger.info(f"Announced dev {username} ({uid}) left")
            
    except Exception as e:
        logger.error(f"Error announcing dev left {uid}: {e}")

# =========================
# STATUS UPDATER
# =========================
@tasks.loop(minutes=1.3)
async def status_updater():
    """Update bot status message"""
    global status_message
    try:
        channel = bot.get_channel(CHANNEL_STATUS)
        if not channel:
            logger.warning("Status channel not found, skipping status update")
            return
            
        uptime = time.time() - startup_time
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        
        embed = discord.Embed(
            title="📡 Bot Status (Auto-Update)",
            description=(
                f"**Uptime:** {uptime_str} | **Ping:** {round(bot.latency*1000)}ms\n"
                f"**Biome Finds:** {biome_find_count} | **API Errors:** {api_error_count} \n"
                f"**Active Devs:** {dev_count} | **Active Owners:** {owner_count}\n"
            ),
            color=COLOR_STATUS,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=LOGO_DEFAULT)
        
        if status_message:
            try:
                await status_message.edit(embed=embed)
            except discord.NotFound:
                status_message = await channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning("No permission to edit status message")
        else:
            status_message = await channel.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Error updating status: {e}")

@status_updater.before_loop
async def before_status_updater():
    await bot.wait_until_ready()

# =========================
# ROBLOX POLLING
# =========================
@tasks.loop(minutes=1.3)
async def roblox_poll():
    """Poll Roblox presence API"""
    global dev_count, owner_count, already_announced, api_error_count
    
    if not ROBLOX_COOKIE:
        logger.warning("No Roblox cookie provided, skipping presence check")
        return
        
    user_ids = DEV_IDS + list(OWNER_IDS.keys())
    if not user_ids:
        return
        
    try:
        cookies = {".ROBLOSECURITY": ROBLOX_COOKIE}
        async with aiohttp.ClientSession(cookies=cookies) as sess:
            status, data = await make_api_request(
                sess, "POST", "https://presence.roblox.com/v1/presence/users",
                json={"userIds": user_ids}
            )
            
            if status != 200 or not data:
                api_error_count += 1
                logger.warning(f"Roblox presence API error: status {status}")
                return
                
    except Exception as e:
        api_error_count += 1
        logger.error(f"Roblox API error: {e}")
        return

    id_to_username = await get_usernames(user_ids)

    dev_count = 0
    owner_count = 0
    current_online = set()

    for user in data.get("userPresences", []):
        uid = user.get("userId")
        state = user.get("userPresenceType")
        game_id = user.get("universeId")
        username = id_to_username.get(uid, f"User_{uid}")

        if state == 2 and game_id == SOLS_RNG_GAME_ID:
            current_online.add(uid)
            
            if uid in DEV_IDS:
                dev_count += 1
            if uid in OWNER_IDS:
                owner_count += 1
                
            if uid not in already_announced:
                await announce_dev(uid, username, "in Sol's RNG")

    for uid in already_announced - current_online:
        username = id_to_username.get(uid, f"User_{uid}")
        await announce_dev_left(uid, username)

    already_announced = current_online

@roblox_poll.before_loop
async def before_roblox_poll():
    await bot.wait_until_ready()

# =========================
# EVENTS
# =========================
@bot.event
async def on_message(message):
    """Handle incoming messages - track 'found' keyword in watch channels"""
    global biome_find_count
    
    try:
        if message.author.bot:
            return
            
        # Check if message is in watch channels and contains "found"
        if message.channel.id in [CHANNEL_GLITCH_WATCH, CHANNEL_DREAMSPACE_WATCH]:
            if "found" in message.content.lower():
                biome_find_count += 1
                logger.info(f"Biome find detected in channel {message.channel.id}. Total finds: {biome_find_count}")
            
        await bot.process_commands(message)
        
    except Exception as e:
        logger.error(f"Error processing message {message.id}: {e}")

@bot.event
async def on_ready():
    """Bot ready event"""
    try:
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Sol's RNG Servers"
        ))
        
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} global slash commands")
        except Exception as e:
            logger.error(f"Failed to sync global slash commands: {e}")
            
        for guild_id in GUILD_IDS:
            try:
                await bot.tree.sync(guild=discord.Object(id=guild_id))
                logger.info(f"Synced commands for guild {guild_id}")
            except Exception as e:
                logger.error(f"Failed to sync commands for guild {guild_id}: {e}")
        
        if not status_updater.is_running():
            status_updater.start()
        if not roblox_poll.is_running():
            roblox_poll.start()
            
        logger.info("Bot logged in as %s", bot.user)
        
    except Exception as e:
        logger.error(f"Error in on_ready: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    logger.error(f"Command error in {ctx.command}: {error}")

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle general errors"""
    logger.error(f"Bot error in event {event}", exc_info=True)

# =========================
# SLASH COMMANDS
# =========================
@bot.tree.command(name="status", description="Show bot status and stats")
async def status_cmd(interaction: discord.Interaction):
    """Status command"""
    try:
        uptime = time.time() - startup_time
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        
        embed = discord.Embed(
            title="📊 Bot Status",
            description=(
               f"**Uptime:** {uptime_str} | **Ping:** {round(bot.latency*1000)}ms\n"
                f"**Biome Finds:** {biome_find_count} | **API Errors:** {api_error_count} \n"
                f"**Active Devs:** {dev_count} | **Active Owners:** {owner_count}\n"
            ),
            color=COLOR_STATUS,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=LOGO_DEFAULT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await interaction.response.send_message("An error occurred while fetching status.", ephemeral=True)

# =========================
# GRACEFUL SHUTDOWN
# =========================
async def shutdown():
    """Graceful shutdown procedure"""
    logger.info("Shutting down bot...")
    
    if status_updater.is_running():
        status_updater.cancel()
    if roblox_poll.is_running():
        roblox_poll.cancel()
    
    await bot.close()

# =========================
# RUN
# =========================
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot shutdown complete")
