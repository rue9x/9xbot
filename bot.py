from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.object.eventsub import (
    ChannelFollowEvent,
    ChannelPointsAutomaticRewardRedemptionAddEvent,
    ChannelPointsCustomRewardRedemptionAddEvent,
    ChannelChatMessageEvent
)
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.type import AuthScope
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from gtts import gTTS
import random

import asyncio
import os
import json
from dotenv import load_dotenv
import sounddevice as sd
import soundfile as sf
import platform
from pathlib import Path
import random
import re

# ─── CONFIG LOADING ───

def load_config(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

config = load_config("config.json")
soundalerts = load_config(config["soundalerts_path"])
ansi_path = config.get("color_constants_path", "color_constants.json")

# ─── OS DETECTION + FILE PATHS ───

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

if IS_WINDOWS:
    BASE_ASSET_PATH = Path(config["base_asset_path_windows"])
    set_title = lambda title: os.system(f"title {title}")
elif IS_LINUX:
    BASE_ASSET_PATH = Path(config["base_asset_path_linux"])
    set_title = lambda title: print(f"\033]0;{title}\a", end="", flush=True)
else:
    raise RuntimeError("Unsupported OS: only Windows and Linux are supported.")

gfx_folder = BASE_ASSET_PATH / config["gfx_folder"]
sfx_folder = BASE_ASSET_PATH / config["sfx_folder"]
sound_folder = sfx_folder
quote_file = BASE_ASSET_PATH / config["quote_file"]

# ─── TITLE SETUP ───
set_title = (
    (lambda title: os.system(f"title {title}")) if IS_WINDOWS
    else (lambda title: print(f"\033]0;{title}\a", end="", flush=True))
)

# ─── ENV SETUP ───
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

APP_ID = CLIENT_ID
APP_SECRET = CLIENT_SECRET

TARGET_SCOPES = [
    AuthScope.MODERATOR_READ_FOLLOWERS,
    AuthScope.CHANNEL_READ_REDEMPTIONS,
    AuthScope.USER_READ_CHAT,
    AuthScope.USER_BOT,
    AuthScope.CHANNEL_BOT,
    AuthScope.CHAT_EDIT,
    AuthScope.USER_WRITE_CHAT
]

# ─── ANSI COLOR SETUP ───
def setup_ansi(cfg):
    ANSI_COLORS = load_config(cfg)
    for key, value in ANSI_COLORS.items():
        ANSI_COLORS[key] = value.replace("\\033", "\033")
    return ANSI_COLORS

ANSI_COLORS = setup_ansi(ansi_path)
BOLD = ANSI_COLORS['bold']
UNDERLINE = ANSI_COLORS['underline']
RESET = ANSI_COLORS['reset']
RED = ANSI_COLORS['red']
GREEN = ANSI_COLORS['green']
YELLOW = ANSI_COLORS['yellow']
BLUE = ANSI_COLORS['blue']
MAGENTA = ANSI_COLORS['magenta']
CYAN = ANSI_COLORS['cyan']
WHITE = ANSI_COLORS['white']

command_indicator = config["command_indicator"]
default_sound_device = config["default_sound_device"]

set_title("9XBot")

# ─── UTILITY FUNCTIONS ───
def get_sound_devices():
    print(sd.query_devices())
get_sound_devices()

def sound(fn, block=False, device=default_sound_device):
    fn = str(fn)
    sd.default.device = device
    d, fs = sf.read(fn)
    sd.play(d, fs)
    if block:
        sd.wait()

def text_to_speech(text):
    tts = gTTS(text=text, lang='ja', tld='us', slow=False)
    audio_file = config["tts_temp_file"]
    tts.save(audio_file)
    sound(audio_file, block=False)
    os.remove(audio_file)

# ─── EVENT HANDLERS ───

async def command_handler(data):

    def sanitize_quote(text: str) -> str:
        # Remove ANSI escape codes
        text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)
        # Remove newlines and non-printables except basic punctuation
        text = re.sub(r'[^\x20-\x7E]+', ' ', text)
        return text.strip()

    def delete_quote(index: int, file_path=quote_file) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            return "No quotes to delete."

        with open(file_path, "r", encoding="utf-8") as f:
            quotes = f.readlines()

        if index < 1 or index > len(quotes):
            return f"Invalid quote number. Use !quote to see how many there are."

        removed = quotes.pop(index - 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(quotes)

        return f"Deleted quote #{index}: {removed.strip()}"

    def get_random_quote(file_path=quote_file) -> str:
        print (file_path)
        file_path = Path(file_path)
        if not file_path.exists():
            return "No quotes available."

        with open(file_path, "r", encoding="utf-8") as f:
            quotes = f.readlines()

        if not quotes:
            return "No quotes available."

        index = random.randint(0, len(quotes) - 1)
        quote = quotes[index].strip()
        return f"[#{index + 1}] {quote}"

    def add_quote(username: str, quote_text: str, quote_file: quote_file):
        # Strip ANSI codes and unwanted characters
        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        cleaned_text = ansi_escape.sub('', quote_text)
        cleaned_text = cleaned_text.strip()

        if not cleaned_text:
            raise ValueError("Quote is empty after cleaning.")

        full_quote = f"{cleaned_text}"

        with open(quote_file, "a", encoding="utf-8") as f:
            f.write(full_quote + "\n")


    uname = data.event.chatter_user_name
    txt = data.event.message.text
    bid = data.event.broadcaster_user_id

    parts = txt.strip().split(" ", 1)
    command = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if txt.startswith("!addquote"):
        parts = txt.split(maxsplit=1)
        if len(parts) < 2:
            await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message="Usage: !addquote <quote text>")
            return

        try:
            add_quote(uname, parts[1], Path(quote_file))
            await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message="Quote added.")
        except Exception as e:
            await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message=f"Error adding quote: {e}")

    elif txt == "!quote":
        quote = get_random_quote()
        await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message=quote)

    elif txt.startswith("!delquote"):
        try:
            parts = txt.split()
            if len(parts) != 2:
                raise ValueError
            index = int(parts[1])
            msg = delete_quote(index)
        except ValueError:
            msg = "Usage: !delquote [quote number]"

        await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message=msg)

async def on_follow(data: ChannelFollowEvent):
    print(f'{data.event.user_name} now follows {data.event.broadcaster_user_name}!')

async def on_auto_redeem(data: ChannelPointsAutomaticRewardRedemptionAddEvent):
    print(f'{data.event.user_name} redeemed {data.event.reward.type} in {data.event.broadcaster_user_name}\'s channel! (AUTO)')

async def on_custom_redeem(data: ChannelPointsCustomRewardRedemptionAddEvent):
    uname = data.event.user_name
    reward = data.event.reward.title
    cost = data.event.reward.cost
    bid = data.event.broadcaster_user_id
    rewardtext = getattr(data.event, "user_input", "")

    print(f'{YELLOW}{UNDERLINE}{BOLD}{uname}{RESET}{YELLOW} redeemed {UNDERLINE}{BOLD}{reward}{RESET}{YELLOW} in {data.event.broadcaster_user_name}\'s channel! (CUSTOM){RESET}')

    if reward in soundalerts:
        try:
            if "Clang" in reward:
                coinflip = random.randint(1,2)
                if coinflip == 2:
                    print ("Coinflip was heads. Playing alternative sound.")
                    sound(sound_folder / 'metal-clang-no.mp3', block=False)
                else:                   
                    print ("Coin flip was tails. Primary sound plays.")
                    sound(sound_folder / soundalerts[reward], block=False)
            else:
                sound(sound_folder / soundalerts[reward], block=False)
            await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message=f"{uname} redeemed \"{reward}\" for {cost} points!")
        except Exception as e:
            print(f"{RED}Error playing sound: {e}{RESET}")
            await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message=f"{uname} tried to play \"{reward}\" for {cost} points, but an error occurred.")

    if reward == "TTS":
        try:
            text_to_speech(rewardtext)
            await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message=f"{uname} redeemed TTS: {rewardtext}")
        except Exception as e:
            print(f"{RED}TTS Error: {e}{RESET}")
            await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message=f"{uname} tried TTS but it failed.")

async def on_chat(data: ChannelChatMessageEvent):
    uname = data.event.chatter_user_name
    txt = data.event.message.text
    print(f"<{uname}> {txt}")
    if txt.startswith(command_indicator):
        await command_handler(data)

# ─── MAIN BOT LOOP ───

async def botloop():
    global twitch
    global helper

    twitch = await Twitch(APP_ID, APP_SECRET)
    helper = UserAuthenticationStorageHelper(twitch, TARGET_SCOPES)
    await helper.bind()

    user = await first(twitch.get_users())
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    await eventsub.listen_channel_points_automatic_reward_redemption_add(user.id, on_auto_redeem)
    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, on_custom_redeem)
    await eventsub.listen_channel_chat_message(user.id, user.id, on_chat)

    try:
        input(f'{BOLD}Press {RESET}{UNDERLINE}{YELLOW}[ENTER]{RESET}{BOLD} to shut down bot.{RESET}\n')
    except KeyboardInterrupt:
        pass
    finally:
        print("Gracefully shutting down.")
        await eventsub.stop()
        await twitch.close()

# ─── RUN ───
if __name__ == "__main__":
    asyncio.run(botloop())
