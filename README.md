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

5. Install the required dependencies: Run the following command to install the necessary Python packages:
    ```
    pip install -r requirements.txt
    ```
    NOTE: A custom version of playsound is used. Make sure you use requirements.txt!
    
6. Configure the bot: Open the `.env` file in a text editor and update the required settings -- Client Secret, Client ID, Redirect_URI. User tokens will be generated on the fly.

7. Run the bot: Start the bot by running the following command:
    ```
    python bot.py
    ```

8. A browser window should pop up asking you to log into twitch. This lets the bot act as you in your channel. It should only occur on first launch and when the token is lost.

That's it! The 9xbot Twitch bot should now be up and running. You can customize its behavior by modifying the code in the `bot.py` file.