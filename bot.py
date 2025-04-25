from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper,UserAuthenticator
from twitchAPI.object.eventsub import ChannelFollowEvent, ChannelPointsAutomaticRewardRedemptionAddEvent,ChannelPointsCustomRewardRedemptionAddEvent,ChannelChatMessageEvent
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.type import AuthScope
from twitchAPI.chat import Chat,EventData,ChatMessage,ChatSub,ChatCommand
from gtts import gTTS

import asyncio
import os
import json
from dotenv import load_dotenv
from playsound import playsound as sound # CUSTOM version of playsound that fixes the block=False issue. 


sound_folder="C:\\twitchstuff\\sfx\\"
def load_config(path):
    # This is Rue's ez json loader, because he likes using JSON for configs. It'll return the JSON as a dict.
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, "r") as f:
        config = json.load(f)
    return config

def setup_ansi(cfg="color_constants.json"):
    # This is for for ANSI colors/styles in the console. 
    ANSI_COLORS = load_config(cfg)
    for key, value in ANSI_COLORS.items():
        # Gotta replace the escape sequences with the actual ANSI codes.
        ANSI_COLORS[key] = value.replace("\\033", "\033")  # Correct escape sequence
    return ANSI_COLORS

# Load the environment variables from the .env file (separate from config loading because .env files are more common for secrets)
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

APP_ID = CLIENT_ID
APP_SECRET = CLIENT_SECRET


# This is the scope. You'll need to add more depending on what the bot needs to be able to do with twitch.
TARGET_SCOPES = [
    AuthScope.MODERATOR_READ_FOLLOWERS,
    AuthScope.CHANNEL_READ_REDEMPTIONS,
    AuthScope.USER_READ_CHAT,
    AuthScope.USER_BOT,
    AuthScope.CHANNEL_BOT,
    AuthScope.CHAT_EDIT,
    AuthScope.USER_WRITE_CHAT
]
# Colorization for console display.
ANSI_COLORS=setup_ansi("color_constants.json")

# Quality of life constants for the ANSI colors
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

command_indicator="!"  # This is the character that indicates a command. You can change it to whatever you want.

# Some rue stuff -- Note, playsound supports mp3, midi and wav. TODO: Config file this.
soundalerts = {
    "OOF" : sound_folder+"sm64_mario_oof.mp3",
    "Easy now fuzzy little man peach" : sound_folder+"easy-now-fuzzy-lil-manpeach.mp3",
    "OOMF" : sound_folder+"super-mario-64-thwomp-sound-online-audio-converter.mp3",
    "HA HA HA HA HA HA HA HAAAAA" : sound_folder+"final-fantasy-x-laugh.mp3",
    "Mama Luigi" : sound_folder+"mama-luigi.mp3",
    "MAMA F-R" : sound_folder+"mama-f-cker_fOf0vFm.mp3",
    "Ever drink Bailey's from a shoe?" : sound_folder+"old-gregg-drunk-baileys-from-a-shoe.mp3",
    "Hello Mario" : sound_folder+"hello-mario-audiotrimmer.mp3",
    "Metal Clang" : sound_folder+"metal-pipe-clang.mp3",
    "HERE WE GAAAAAAAH" : sound_folder+"here-we-go_1.mp3",
    "Soup Crimp": sound_folder+"soup.mp3",
    "Super Mario Shart": sound_folder+"super-mario-shart.mp3"
}
'''
Actual script stuff starts here.
'''


def text_to_speech(text):
    tts = gTTS(text=text, lang='ja',tld='us',slow=False)
    audio_file = "./speech.mp3"
    tts.save(audio_file)
    sound(audio_file,block=False)
    os.remove(audio_file)

async def command_handler(data):
    # This is where you can handle commands. 
    # You can use the data object to get information about the user and the message.
    # For example, you can check if the user is a moderator or a subscriber.
    uname = data.event.chatter_user_name
    #uid = data.event.user_id
    txt = data.event.message.text
    bid = data.event.broadcaster_user_id
    '''
    if txt=="!test":
        # Do whatever the command needs to do.
        sound(sound_folder+"test.ogg",block=False)
        await twitch.send_chat_message(broadcaster_id=bid,sender_id=bid,message="Test sound played.")
        pass
    '''


async def on_follow(data: ChannelFollowEvent):
    # This happens when someone follows the channel.
    print(f'{data.event.user_name} now follows {data.event.broadcaster_user_name}!')

async def on_auto_redeem(data: ChannelPointsAutomaticRewardRedemptionAddEvent):
    # This happens when someone uses an "automatic" reward, such as gigantifying emotes (default twitch stuff).
    print(f'{data.event.user_name} redeemed {data.event.reward.type} in {data.event.broadcaster_user_name}\'s channel! (AUTO)')

async def on_custom_redeem(data: ChannelPointsCustomRewardRedemptionAddEvent):
    # This happens when someone redeems a custom channel point reward.
    uname = data.event.user_name
    reward = data.event.reward.title
    cost = data.event.reward.cost
    bid = data.event.broadcaster_user_id
    try:
        rewardtext = data.event.user_input
    except:
        rewardtext = ""
    print(f'{YELLOW}{UNDERLINE}{BOLD}{data.event.user_name}{RESET}{YELLOW} redeemed {UNDERLINE}{BOLD}{data.event.reward.title}{RESET}{YELLOW} in {data.event.broadcaster_user_name}\'s channel! (CUSTOM){RESET}')
    
    # Simple channel point sound alert system.
    if data.event.reward.title in soundalerts:
        try:
            sound(soundalerts[data.event.reward.title],block=False)
            await twitch.send_chat_message(broadcaster_id=data.event.broadcaster_user_id,sender_id=data.event.broadcaster_user_id,message=f"{uname} redeemed \"{data.event.reward.title}\" for {cost} points!")
        except Exception as e:
            print (f"{RED}Error playing sound: {e}{RESET}")
            print (f"User who tried to play sound: {uname}")
            print (f"Reward title: {reward}")
            print (f"Reward cost: {cost}")
            await twitch.send_chat_message(broadcaster_id=data.event.broadcaster_user_id,sender_id=data.event.broadcaster_user_id,message=f"{uname} redeemed \"{data.event.reward.title}\" for {cost} points, but an error has occurred. Error was logged.")
    
    if data.event.reward.title == "TTS":
        try:
            text_to_speech(rewardtext)
            await twitch.send_chat_message(broadcaster_id=bid,sender_id=bid,message=f"{uname} redeemed TTS: {rewardtext}")
        except Exception as e:
            print (e)
            await twitch.send_chat_message(broadcaster_id=bid,sender_id=bid,message=f"{uname} redeemed TTS: {rewardtext} but it failed. Check the logs.")
            
        
async def on_chat(data:ChannelChatMessageEvent):
    # This happens when someone sends any text message in chat. 
    uname = data.event.chatter_user_name
    txt = data.event.message.text
    print (f"<{uname}> {txt}")

    if txt.startswith(command_indicator):
        # If the message starts with the command indicator, run the command handler.
        await command_handler(data)
    pass


async def botloop():
    # This is the main loop for the script. 
    global twitch
    global helper
    '''
    First we have to get your authentication token. We use a helper for this. When you run this
    script it will probably open a browser and ask you to connect with your twitch account. Do it.
    It shouldn't bother you again until the token expires. It saves locally as user_token.json.
    '''

    twitch = await Twitch(APP_ID, APP_SECRET)
    helper = UserAuthenticationStorageHelper(twitch, TARGET_SCOPES)
    #token,refresh_token = await(auth.authenticate())

    await helper.bind()

    # This listens for a user to do literally anthing.
    user = await first(twitch.get_users())
    # create eventsub websocket instance and start the client.
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    # Here's where you set up different events and say what function they call when they're triggered.  
    await eventsub.listen_channel_points_automatic_reward_redemption_add(user.id, on_auto_redeem)
    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, on_custom_redeem)
    await eventsub.listen_channel_chat_message(user.id, user.id, on_chat)
    
    # All of the above runs on its own thread, so you can still get away with an input to kill the bot.
    try:
        input(f'{BOLD}Press {RESET}{UNDERLINE}{YELLOW}[ENTER]{RESET}{BOLD} to shut down bot.{RESET}\n')
    except KeyboardInterrupt:
        pass
    finally:
        # If we hit enter to kill the bot, we can do gracefully shut down here and then quit.
        print ("Gracefully shutting down.")
        await eventsub.stop()
        await twitch.close()
        quit()

if __name__ == "__main__":
    asyncio.run(botloop())