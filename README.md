## 9xbot
Rue's custom twitch bot. Easily customizable python

## Installation Guide

To use the 9xbot Twitch bot, follow these steps:

1. Install Git: If you don't have Git installed, you can download it from the official website: [https://git-scm.com/downloads](https://git-scm.com/downloads).

2. Install Python 3.11: If you don't have Python installed, you can download it from the official website: [https://www.python.org/downloads](https://www.python.org/downloads).

3. Clone the 9xbot repository: Open a terminal or command prompt and run the following command to clone the repository to your local machine:
    ```
    git clone https://github.com/rue9x/9xbot.git
    ```

4. Navigate to the project directory: Change to the 9xbot directory by running the following command:
    ```
    cd 9xbot
    ```

4a. OPTIONAL: Set up a venv:
    ```
    py -m venv venv
    activate
    ```
    
5. Install the required dependencies: Run the following command to install the necessary Python packages:
    ```
    pip install wheel
    pip install -r requirements.txt
    ```

6. Configure the bot: Open the `.env` file in a text editor and update the required settings -- Client Secret, Client ID, Redirect_URI. User tokens will be generated on the fly.

7. Run the bot: Start the bot by running the following command:
    ```
    python bot.py
    ```

8. A browser window should pop up asking you to log into twitch. This lets the bot act as you in your channel. It should only occur on first launch and when the token is lost.

9. Close the bot with ESC or ctrl+C.

10. Set up config.json:

Your default_sound_device is the device you want sounds played through. When you run the bot, it'll print out a list of these for your reference.

Your base_asset_path_(OS) should be a folder containing a folder for graphics, and a folder for sounds. 

Example:
{
  "command_indicator": "!",
  "default_sound_device": "Voicemeeter AUX Input (VB-Audio Voicemeeter VAIO), Windows DirectSound",
  "base_asset_path_windows": "C:/users/ruela/twitchstuff",
  "base_asset_path_linux": "/home/rue/twitchstuff",
  "gfx_folder": "gfx",
  "sfx_folder": "sfx",
  "color_constants_path": "color_constants.json",
  "soundalerts_path": "soundalerts.json",
  "tts_temp_file": "./speech.mp3",
  "quote_file": "./quotes.txt"
}



That's it! The 9xbot Twitch bot should now be up and running. You can customize its behavior by modifying the code in the `bot.py` file.

