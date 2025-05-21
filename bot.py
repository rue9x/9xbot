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

import asyncio
import os
import json
from dotenv import load_dotenv
import sounddevice as sd
import soundfile as sf
import platform
from pathlib import Path

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
    audio_file = config["tts_temp_path"]
    tts.save(audio_file)
    sound(audio_file, block=False)
    os.remove(audio_file)

# ─── EVENT HANDLERS ───

async def command_handler(data):
    uname = data.event.chatter_user_name
    txt = data.event.message.text
    bid = data.event.broadcaster_user_id

    #if txt == "!test":
    #    sound(sound_folder / "grabish.mp3", block=False)
    #    await twitch.send_chat_message(broadcaster_id=bid, sender_id=bid, message="Test sound played.")

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
