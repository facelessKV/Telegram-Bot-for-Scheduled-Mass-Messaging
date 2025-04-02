📬 Telegram Bot for Scheduled Mass Messaging

Looking to send mass messages to your subscribers on a schedule? This bot makes it easy to send bulk messages at specific times, helping you keep your audience engaged without manual intervention!
With this bot, you can automate your communication with a large group of people, sending personalized messages, reminders, or announcements automatically.

✅ What does it do?

 • 📅 Allows scheduling of mass messages to your subscribers
 • 📲 Supports sending texts, images, and videos
 • 🔄 Easily handles subscription and unsubscription
 • 📊 Manages a database of subscribers

🔧 Features

✅ Simple message scheduling and management
✅ Customizable message content (texts, images, videos)
✅ User-friendly subscription management for effortless user interaction

📩 Need to automate your messaging campaigns?

Contact me on Telegram, and I’ll help you set up this bot to streamline your communication! 🚀

===================================================
INSTRUCTIONS FOR INSTALLING AND LAUNCHING A TELEGRAM BOT
===================================================

This file contains detailed installation and startup instructions. 
Telegram bot for mass mailing on Windows and Linux.


CONTENT:
-----------
1. What is this bot doing?
2. Installing Python
   - For Windows
   - For Linux
3. Download and configure the bot
4. Creating a Telegram bot via BotFather
5. Setting up the bot
6. Running the bot
- In Windows
   - On Linux
7. Basic Bot Commands
8. Problem solving


1. WHAT DOES THIS BOT DO?
---------------------
This Telegram bot is designed to send mass mailings to subscribers.
Bot Functions:
- Manage user subscriptions
- Sending messages to all subscribers at once
- Schedule mailings for a specific time
- Support for different types of messages (text, photo, video)


2. INSTALLING PYTHON
------------------

FOR WINDOWS:
------------

1. Download Python 3.10.11:
- Follow the link: https://www.python.org/downloads/release/python-31011 /
- Scroll down to the "Files" section and download the "Windows installer (64-bit)"

2. Install Python:
   - Run the downloaded file
   - IMPORTANT: Check the box "Add Python 3.10 to PATH" at the beginning of the installation!
   - Click "Install Now"

3. Check the installation:
- Open the command prompt (press Win+R, type "cmd" and press Enter)
   - Enter the command: python --version
   - A message should appear with the Python version (for example, "Python 3.10.11")


FOR LINUX:
----------

1. Open a terminal (Ctrl+Alt+T in Ubuntu)

2. Install the necessary packages:
   ```
   sudo apt update
   sudo apt install software-properties-common
   ```

3. Add the Python repository and install Python 3.10:
``
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.10 python3.10-venv python3.10-dev python3-pip
   ```

4. Check the installation:
``
   python3.10 --version
   ```
   The message "Python 3.10.x" should appear


3. DOWNLOAD AND CONFIGURE THE BOT
-----------------------------

FOR WINDOWS:
------------

1. Create a folder for the bot:
   - Open the explorer
   - Create a new folder, for example, C:\telegram-bot

2. Save all the bot files to this folder:
- main.py
- requirements.txt
- .env (we'll create it later)


FOR LINUX:
----------

1. Create a folder for the bot:
   ```
   mkdir ~/telegram-bot
   cd ~/telegram-bot
   ```

2. Save all the bot files to this folder:
- main.py
- requirements.txt
- .env (we'll create it later)


4. CREATING A TELEGRAM BOT VIA BOTFATHER
---------------------------------------

1. Open Telegram and find @BotFather (the official bot creation bot)

2. Write the command: /newbot

3. Come up with a name for your bot (for example, "My Mailing bot")

4. Come up with a username for the bot that should end with "bot"
(for example, "my_newsletter_bot")

5. After successful creation, BotFather will give you a bot TOKEN. 
   It looks something like this: 1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ

6. IMPORTANT: Save this token! You will need it to set up the bot.


5. SETTING UP THE BOT
---------------

1. Create a file.env in the bot folder:

FOR WINDOWS:
------------
- Open Notepad
And Paste It In:
     ```
     BOT_TOKEN=YOUR_TOKEN_OT_BOTFATHER
     ADMIN_IDS=your_id_in_thelegram
     ``
- Replace "your_token_ot_botfather" with the token received from BotFather
   - Replace "your_id_in telegram" with your Telegram ID (you can find it from the bot @userinfobot)
   - Save the file named ".env" (with a dot at the beginning) in the bot folder
   
   attention: When saving the file in Notepad, specify:
   - File name: .env
- File type: All files (not Text documents)

FOR LINUX:
----------
- Open the terminal and navigate to the folder with the bot
- Run the command:
     ```
     nano .env
     ``
- Insert:
     ```
     BOT_TOKEN=YOUR_TOKEN_OT_BOTFATHER
     ADMIN_IDS=your_id_in_thelegram
     ``
- Replace "your_token_ot_botfather" with the token received from BotFather
   - Replace "your_id_in telegram" with your Telegram ID
   - Save the file: press Ctrl+O, then Enter, then Ctrl+X to exit


6. INSTALL DEPENDENCIES AND LAUNCH THE BOT
-------------------------------------

FOR WINDOWS:
------------

1. Open the command prompt as an administrator:
   - Press Win + X
- Select "Windows Terminal (Administrator)" or "Command Prompt (Administrator)"

2. Go to the bot folder:
``
   cd C:\путь\к\вашей\папке\telegram-bot
   ```
   For example: `cd C:\telegram-bot `

3. Create a virtual environment:
   ```
   python -m venv venv
   ```

4. Activate the virtual environment:
   ```
   venv\Scripts\activate
   ```
   The prefix (venv) should appear on the command line.

5. Install the dependencies:
``
   pip install -r requirements.txt
   ```

6. Launch the bot:
   ```
   python main.py
   ```

FOR LINUX:
----------

1. Open the terminal and navigate to the folder with the bot:
``
   cd ~/telegram-bot
   ```

2. Create a virtual environment:
   ```
   python3.10 -m venv venv
   ```

3. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```
   The prefix (venv) should appear in the terminal.

4. Install the dependencies:
``
   pip install -r requirements.txt
   ```

5. Launch the bot:
   ```
   python main.py
   ```


7. BASIC BOT COMMANDS
----------------------

After launching, you can use the following commands to chat with the bot:

FOR ALL USERS:
- /start - getting started with the bot
- /subscribe - subscribe to the newsletter
- /unsubscribe - unsubscribe from the mailing
list - /status - check the subscription status

FOR ADMINISTRATORS ONLY:
- /send_message - send a message to all subscribers
- /stats - view bot statistics (subscribers, mailing lists)


8. PROBLEM SOLVING
----------------

Problem: The bot does not start, it gives the error "No module named 'aiogram'"
Solution: Make sure that you have activated the virtual environment and installed the dependencies

Problem: When starting the bot, the error is "No such file or directory"
Solution: Make sure you are in the correct folder with the bot files.

Problem: The bot has started, but does not respond to commands.
Decision: 
- Check if the token is specified correctly in the .env file.
- Make sure that the bot is running (the console should have the message "The bot is running and ready to work!")
- In Telegram, find your bot by name and click the "Start" button or send the command /start

Problem: The bot responds, but the admin commands don't work.
Solution: Check if your ID is specified correctly in the .env file (in the ADMIN_IDS parameter)


LAUNCHING THE BOT THE NEXT TIME YOU USE IT
-------------------------------------

FOR WINDOWS:
- Open the command prompt
- Go to the folder with the bot: `cd C:\путь\к\telegram-bot `
- Activate the virtual environment: `venv\Scripts\activate`
- Launch the bot: `python main.py `

FOR LINUX:
- Open the terminal
- Go to the folder with the bot: `cd~/telegram-bot`
- Activate the virtual environment: `source venv/bin/activate`
- Launch the bot: `python main.py `

To stop the bot: press Ctrl+C in the command prompt/terminal window
