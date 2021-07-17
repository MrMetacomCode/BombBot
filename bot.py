# Importing everything needed.
import json
import os.path
import discord
import random
import pickle
import logging
from datetime import date
from datetime import datetime
from discord import Intents
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# "Typical" logging.
# logging.basicConfig(level=logging.DEBUG, filename='logs.txt')
# logger = logging.getLogger(__name__)
# logger.debug('test')

# Discord "correct" logging.
# logger = logging.getLogger('discord')
# logger.setLevel(logging.ERROR)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)


# Security variables.
TOKEN = os.getenv('BOMBBOT_DISCORD_TOKEN')
SPREADSHEET_ID = '1S-AIIx2EQrLX8RHJr_AVIGPsQjehEdfUmbwKyinOs_I'
TRACKING_SPREADSHEET_ID = '1HhomUgsgjhWWg67M54ZY_RP2l2Ns7LiDCszRJE9XMgQ'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
value_input_option = "USER_ENTERED"

# Setting up intents and initializing bot.
intents = Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

# Setup for Google Spreadsheet to be able to pull from it.
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Logs exception to .txt file.
def log_exception(e):
    logging_file = open("log.txt", "a")
    logging_file.write(f"{datetime.now()}\n{str(e)}\n\n")
    logging_file.close()


# Logs exception to .txt file and send a notification to the bot_commands channel.
async def log_exception_and_report(e):
    logging_file = open("log.txt", "a")
    logging_file.write(f"{datetime.now()}\n{str(e)}\n\n")
    logging_file.close()

    bot_commands_channel = bot.get_channel(740370208778354729)
    await bot_commands_channel.send(f"@MrMetacom BombBot Error:\n{e}")


# Updates values to the given input range on the given spreadsheet.
def update_values(input_range, updated_values, spreadsheet_id):
    request = sheet.values().update(spreadsheetId=spreadsheet_id, range=input_range,
                                    valueInputOption=value_input_option,
                                    body={"values": updated_values}).execute()
    values = input_range.split("!")
    values_ = values[1]
    print(f"Values {values_} updated.")


# Reads the values of the given input range from the given spreadsheet.
def read_values(input_range, spreadsheet_id):
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=input_range).execute()
    values = result.get('values', [])
    return values


# Updates the tracking spreadsheet with the new $bombs command count.
async def func():
    try:
        await bot.wait_until_ready()
        # Opens count.json and gets the amount of times $bombs has been called so far.
        with open('count.json', 'r') as file:
            count_file = json.loads(file.read())
        new_amount = count_file["count"]
        # Gets the current values in column A to determine where the next date should be placed.
        current_values = read_values("Data!A1:A1095", TRACKING_SPREADSHEET_ID)
        next_range = f"Data!A{len(current_values) + 1}:B{len(current_values) + 1}"

        # Gets the current date and creates a list with the new values to be sent to the sheet.
        now = date.today()
        todays_date = f"{now.month}/{now.day}/{now.year}"
        new_value = [[todays_date, new_amount]]
        # Updates the sheet.
        update_values(next_range, new_value, TRACKING_SPREADSHEET_ID)
    except Exception as e:
        log_exception_and_report(e)
        raise e


# On_Ready event that displays useful information when first run.
@bot.event
async def on_ready():
    print("Bot is ready.")
    print(f"Total servers: {len(bot.guilds)}")
    members_set = set()
    for guild in bot.guilds:
        for member in guild.members:
            members_set.add(member)
    members = len(members_set)
    print(f"Total members from all servers: {members}")
    await bot.change_presence(activity=discord.Game("$bombs"))

    try:
        # Runs the function to report the amount of times $bombs has been called today.
        scheduler = AsyncIOScheduler()
        scheduler.add_job(func, CronTrigger(hour=0, minute=0, second=0))
        scheduler.start()
    except Exception as e:
        log_exception_and_report(e)
        raise e


# Fun dice rolling game.
@bot.command(name='rolldice', help='Simulates rolling dice.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))


# Helper function that turns lists into numbered strings with line breaks.
def embed_maker(thing_list):
    list_number = 1
    embed = ""
    for thing in thing_list:
        item = f"{list_number} = {thing}\n"
        embed += item
        list_number += 1
    return embed


# Command that returns bombs needed for bases and airfield.
@bot.command(name='bombs', aliases=['bomb'], help='For War Thunder game. Finds bombs from spreadsheet and returns '
                                                  'bombs required to destroy a base and bombs required to destroy '
                                                  'an airfield.')
async def bomb(ctx):
    # Defining country data ranges from the spreadsheet.
    with open('count.json', 'r') as file:
        count_file = json.loads(file.read())
    american_bombs = 'Bomb Table!B19:Q29'
    german_bombs = 'Bomb Table!B33:Q39'
    russian_bombs = 'Bomb Table!B43:Q54'
    british_bombs = 'Bomb Table!B58:Q64'
    japanese_bombs = 'Bomb Table!B68:Q81'
    italian_bombs = 'Bomb Table!B85:Q91'
    chinese_bombs = 'Bomb Table!B95:Q115'
    french_bombs = 'Bomb Table!B119:Q125'
    swedish_bombs = 'Bomb Table!B128:Q138'

    # Setting up a dict to hold each country's bomb data.
    bomb_data = {"US": {}, "GERMAN": {}, "RUSSIA": {}, "BRITAIN": {}, "JAPAN": {}, "ITALY": {}, "CHINA": {},
                 "FRANCE": {}, "SWEDEN": {}}

    def get_bomb_data(bombs, country_abbreviation):
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=bombs).execute()
        country_list = result.get('values', [])
        for items in country_list:
            bomb_data[country_abbreviation][items[0]] = items[1:]

    # Adds each country's bomb data to the bomb_data dict.
    get_bomb_data(american_bombs, "US")
    get_bomb_data(german_bombs, "GERMAN")
    get_bomb_data(russian_bombs, "RUSSIA")
    get_bomb_data(british_bombs, "BRITAIN")
    get_bomb_data(japanese_bombs, "JAPAN")
    get_bomb_data(italian_bombs, "ITALY")
    get_bomb_data(chinese_bombs, "CHINA")
    get_bomb_data(french_bombs, "FRANCE")
    get_bomb_data(swedish_bombs, "SWEDEN")

    try:
        # Creates a list of the countries.
        countries = []
        for country_number in bomb_data:
            countries.append(country_number)

        # Uses the helper function to make a numbered list of the countries.
        countries_embed = embed_maker(countries)

        # Makes an embed and sends it.
        embedvar = discord.Embed(title="Select a country to view bombs from:",
                                 description=countries_embed,
                                 color=0x00ff00)
        await ctx.send(embed=embedvar)

        # Checks to see if the user has replied
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        # Gives the user 5 tries to enter a number
        for x in range(5):
            # Gets the input from the user
            country_number = (await bot.wait_for('message', check=check)).content
            # Tries to convert it to an integer
            try:
                country_number = int(country_number)
            # If the user didn't enter a number this will tell them to and go back to the top of the loop
            except ValueError:
                await ctx.send("Please use a number.")
                continue
            # If the user entered a number it will break from the loop and continue with the rest of the code
            break
        else:
            # If the user doesn't enter a number in 5 tries, end the command sequence
            await ctx.send("You didn't use a number. Goodbye.")
            return

        for x in range(9):
            if country_number == x + 1:
                country = countries[x]
                bombs = []
                for bomb_ in bomb_data[countries[x]]:
                    bombs.append(bomb_)

                bombs_embed = embed_maker(bombs)
                embedvar = discord.Embed(title=f"Select a bomb from {country}:",
                                         description=bombs_embed,
                                         color=0x00ff00)
                await ctx.send(embed=embedvar)
                break
            elif x == 8:
                # If they choose a number that isn't listed it tells the user and ends the command sequence
                await ctx.send("Couldn't find that country's bombs.")
                return

        # Again gives the user 5 tries to enter a number
        for x in range(5):
            bomb_number = (await bot.wait_for('message', check=check)).content
            try:
                bomb_number = int(bomb_number)
            except ValueError:
                await ctx.send("Please use a number.")
                continue
            break
        else:
            await ctx.send("You didn't use a number. Goodbye.")
            return

        # Loop to figure out which number and corresponding bomb was selected
        for x in range(len(bomb_data[country]) + 1):
            if bomb_number == x:
                bomb_type = bombs[x - 1]

        # Asks the user to enter the battle rating of their match
        await ctx.send("Enter battle rating:")
        for x in range(5):
            battle_rating = (await bot.wait_for('message', check=check)).content
            try:
                battle_rating = float(battle_rating)
            except ValueError:
                await ctx.send("Please use a decimal number. If it is a whole number just put it as 4.0 for example.")
                continue
            break
        else:
            await ctx.send("You didn't use a decimal. Goodbye.")
            return

        # Asks the user if the map has four bases
        await ctx.send("Is this a four base map? Enter 'YES' or 'NO'")
        for x in range(5):
            four_base = (await bot.wait_for('message', check=check)).content
            try:
                four_base = str(four_base)
                if four_base.lower() != "yes" and four_base.lower() != "no":
                    raise ValueError
            except ValueError:
                await ctx.send("Please enter 'YES' or 'NO'.")
                continue
            break
        else:
            await ctx.send("You didn't enter 'YES' or 'NO'. Goodbye.")
            return

        # Creates a list of the data needed to destroy a base using the country and bomb type
        base_bombs_list = bomb_data[country][bomb_type]

        four_base = four_base.upper()
        # Using the battle_rating and four_base variables calculates bombs needed for bases and airfield
        try:
            if 1.0 <= battle_rating <= 2.0:
                if four_base == "YES":
                    base_bombs_required = base_bombs_list[2]
                    airfield_bombs_required = int(base_bombs_required) * 5
                else:
                    base_bombs_required = base_bombs_list[3]
                    airfield_bombs_required = int(base_bombs_required) * 5
            elif 2.3 <= battle_rating <= 3.3:
                if four_base == "YES":
                    base_bombs_required = base_bombs_list[4]
                    airfield_bombs_required = int(base_bombs_required) * 6
                else:
                    base_bombs_required = base_bombs_list[5]
                    airfield_bombs_required = int(base_bombs_required) * 6
            elif 3.7 <= battle_rating <= 4.7:
                if four_base == "YES":
                    base_bombs_required = base_bombs_list[6]
                    airfield_bombs_required = int(base_bombs_required) * 8
                else:
                    base_bombs_required = base_bombs_list[7]
                    airfield_bombs_required = int(base_bombs_required) * 8
            elif 5.0 <= battle_rating:
                if four_base == "YES":
                    base_bombs_required = base_bombs_list[8]
                    airfield_bombs_required = int(base_bombs_required) * 15
                else:
                    base_bombs_required = base_bombs_list[9]
                    airfield_bombs_required = int(base_bombs_required) * 15
            else:
                # Will only send if the user enters a negative battle rating
                await ctx.send("That battle rating doesn't exist.")
                return
        # If there isn't any data in the cell then it will return this error, which means the data hasn't been added yet
        except ValueError as e:
            await ctx.send(
                "This bomb data hasn't been added to the spreadsheet yet. If you are requesting a 4 base "
                "map, it may be too soon. Please refer to 3 base map data and multiply it by 2x for each "
                "base to get approximate 4 base data.")
            return

        # If everything works it send how many bombs per base and airfield
        await ctx.send(
            f"Bombs Required for Bases: {base_bombs_required} \nBombs Required for Airfield: "
            f"{airfield_bombs_required}")

    # If something breaks in all that then it will send this message
    except Exception as e:
        log_exception(e)
        await ctx.send(f"User error, try again. Error message:\n{e}")
        raise e

    try:
        count = int(count_file["count"])
        new_count = count + 1
        count_file["count"] = new_count

        with open('count.json', 'w') as file:
            file.write(json.dumps(count_file))
    except Exception as e:
        log_exception_and_report(e)
        raise e


@bot.command(name='count', help='Displays number of times $bombs has been called.')
async def count_output(ctx):
    with open('count.json', 'r') as file:
        count_file = json.loads(file.read())

    count_ = int(count_file["count"])
    await ctx.send(f"$bombs has been called a total of {count_} times.")


print("Server Running")
bot.run(TOKEN)
