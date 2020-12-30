# import os
import os.path
import discord
import random
import pickle
import logging
from discord import Intents
from discord.ext import commands
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# "Typical" logging.
# logging.basicConfig(level=logging.DEBUG, filename='logs.txt')
# logger = logging.getLogger(__name__)
# logger.debug('test')

# Discord correct logging.
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)


TOKEN = os.getenv('BOMBBOT_DISCORD_TOKEN')
SPREADSHEET_ID = '1S-AIIx2EQrLX8RHJr_AVIGPsQjehEdfUmbwKyinOs_I'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

intents = Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

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


@bot.event
async def on_ready():
    print("Bot is ready.")
    print(f"Total servers: {len(bot.guilds)}")
    print("Server names:")
    for guild in bot.guilds:
        print(guild.name)


@bot.command(name='rolldice', help='Simulates rolling dice.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))


@bot.command(name='testbombs')
async def test_bomb(ctx):
    american_bombs = 'Bomb Table!B19:Q29'
    german_bombs = 'Bomb Table!B33:Q39'
    russian_bombs = 'Bomb Table!B43:Q54'
    british_bombs = 'Bomb Table!B58:Q64'
    japanese_bombs = 'Bomb Table!B68:Q81'
    italian_bombs = 'Bomb Table!B85:Q91'
    chinese_bombs = 'Bomb Table!B95:Q115'
    french_bombs = 'Bomb Table!B119:Q125'
    swedish_bombs = 'Bomb Table!B128:Q138'

    bomb_data = {"US": {}, "GERMAN": {}, "RUSSIA": {}, "BRITAIN": {}, "JAPAN": {}, "ITALY": {}, "CHINA": {},
                 "FRANCE": {}, "SWEDEN": {}}
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=american_bombs).execute()
    american_list = result.get('values', [])
    for items in american_list:
        bomb_data["US"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=german_bombs).execute()
    german_list = result.get('values', [])
    for items in german_list:
        bomb_data["GERMAN"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=russian_bombs).execute()
    russian_list = result.get('values', [])
    for items in russian_list:
        bomb_data["RUSSIA"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=british_bombs).execute()
    british_list = result.get('values', [])
    for items in british_list:
        bomb_data["BRITAIN"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=japanese_bombs).execute()
    japanese_list = result.get('values', [])
    for items in japanese_list:
        bomb_data["JAPAN"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=italian_bombs).execute()
    italian_list = result.get('values', [])
    for items in italian_list:
        bomb_data["ITALY"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=chinese_bombs).execute()
    chinese_list = result.get('values', [])
    for items in chinese_list:
        bomb_data["CHINA"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=french_bombs).execute()
    french_list = result.get('values', [])
    for items in french_list:
        bomb_data["FRANCE"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=swedish_bombs).execute()
    swedish_list = result.get('values', [])
    for items in swedish_list:
        bomb_data["SWEDEN"][items[0]] = items[1:]

    def embed_maker(thing_list):
        list_number = 1
        embed = ""
        for thing in thing_list:
            item = f"{list_number} = {thing}\n"
            embed += item
            list_number += 1
        return embed

    try:
        countries = []
        for country_number in bomb_data:
            countries.append(country_number)

        countries_embed = embed_maker(countries)

        embedvar = discord.Embed(title="Select a country to view bombs from:",
                                 description=countries_embed,
                                 color=0x00ff00)
        await ctx.send(embed=embedvar)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            country_number = int((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please use a number.")
            return

        if country_number == 1:
            country = countries[0]
            bombs = []
            for bomb_ in bomb_data[countries[0]]:
                bombs.append(bomb_)

            american_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {country}:",
                                     description=american_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 2:
            country = countries[1]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            german_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[1]}:",
                                     description=german_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 3:
            country = countries[2]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            russian_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[2]}:",
                                     description=russian_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 4:
            country = countries[3]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            british_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[3]}:",
                                     description=british_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 5:
            country = countries[4]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            japanese_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[4]}:",
                                     description=japanese_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 6:
            country = countries[5]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            german_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[5]}:",
                                     description=german_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 7:
            country = countries[6]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            german_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[6]}:",
                                     description=german_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 8:
            country = countries[7]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            german_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[7]}:",
                                     description=german_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 9:
            country = countries[8]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            german_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[8]}:",
                                     description=german_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        else:
            await ctx.send("Couldn't find that country's bombs.")
            return

        try:
            bomb_number = int((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please use a number.")
            return

        for x in range(len(bomb_data[country])):
            if bomb_number == x:
                bomb_type = bombs[x - 1]

        await ctx.send("Enter battle rating:")
        try:
            battle_rating = float((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please use a decimal number.")
            return

        await ctx.send("Is this a four base map? Enter 'YES' or 'NO'")
        try:
            four_base = str((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please enter 'YES' or 'NO'.")
            return

        base_bombs_list = bomb_data[country][bomb_type]

        try:
            four_base = int(four_base)
        except ValueError:
            four_base = str(four_base)
            four_base = four_base.upper()
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
                await ctx.send("That battle rating doesn't exist.")
                return
        except ValueError:
            await ctx.send(
                "This bomb data hasn't been added to the spreadsheet yet. If you are requesting a 4 base "
                "map, it may be too soon. Please refer to 3 base map data and multiply it by 2x for each "
                "base to get approximate 4 base data.")
            return

        await ctx.send(
            f"Bombs Required for Bases: {base_bombs_required} \nBombs Required for Airfield: "
            f"{airfield_bombs_required}")

    except Exception as e:
        await ctx.send("User error, try again.")
        raise e


@bot.command(name='bombs', aliases=['bomb'], help='For War Thunder game. Finds bombs from spreadsheet and returns '
                                                  'bombs required to destroy a base and bombs required to destroy an '
                                                  'airfield.')
async def bomb(ctx):
    american_bombs = 'Bomb Table!B19:Q29'
    german_bombs = 'Bomb Table!B33:Q39'
    russian_bombs = 'Bomb Table!B43:Q54'
    british_bombs = 'Bomb Table!B58:Q64'
    japanese_bombs = 'Bomb Table!B68:Q81'
    italian_bombs = 'Bomb Table!B85:Q91'
    chinese_bombs = 'Bomb Table!B95:Q115'
    french_bombs = 'Bomb Table!B119:Q125'
    swedish_bombs = 'Bomb Table!B128:Q138'

    bomb_data = {"US": {}, "GERMAN": {}, "RUSSIA": {}, "BRITAIN": {}, "JAPAN": {}, "ITALY": {}, "CHINA": {},
                 "FRANCE": {}, "SWEDEN": {}}
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=american_bombs).execute()
    american_list = result.get('values', [])
    for items in american_list:
        bomb_data["US"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=german_bombs).execute()
    german_list = result.get('values', [])
    for items in german_list:
        bomb_data["GERMAN"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=russian_bombs).execute()
    russian_list = result.get('values', [])
    for items in russian_list:
        bomb_data["RUSSIA"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=british_bombs).execute()
    british_list = result.get('values', [])
    for items in british_list:
        bomb_data["BRITAIN"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=japanese_bombs).execute()
    japanese_list = result.get('values', [])
    for items in japanese_list:
        bomb_data["JAPAN"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=italian_bombs).execute()
    italian_list = result.get('values', [])
    for items in italian_list:
        bomb_data["ITALY"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=chinese_bombs).execute()
    chinese_list = result.get('values', [])
    for items in chinese_list:
        bomb_data["CHINA"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=french_bombs).execute()
    french_list = result.get('values', [])
    for items in french_list:
        bomb_data["FRANCE"][items[0]] = items[1:]

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=swedish_bombs).execute()
    swedish_list = result.get('values', [])
    for items in swedish_list:
        bomb_data["SWEDEN"][items[0]] = items[1:]

    def embed_maker(thing_list):
        list_number = 1
        embed = ""
        for thing in thing_list:
            item = f"{list_number} = {thing}\n"
            embed += item
            list_number += 1
        return embed

    try:
        countries = []
        for country_number in bomb_data:
            countries.append(country_number)

        countries_embed = embed_maker(countries)

        embedvar = discord.Embed(title="Select a country to view bombs from:",
                                 description=countries_embed,
                                 color=0x00ff00)
        await ctx.send(embed=embedvar)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            country_number = int((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please use a number.")
            return

        if country_number == 1:
            country = countries[0]
            bombs = []
            for bomb_ in bomb_data[countries[0]]:
                bombs.append(bomb_)

            american_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {country}:",
                                     description=american_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 2:
            country = countries[1]
            bombs = []
            for bomb_ in bomb_data[countries[1]]:
                bombs.append(bomb_)

            german_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[1]}:",
                                     description=german_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 3:
            country = countries[2]
            bombs = []
            for bomb_ in bomb_data[countries[2]]:
                bombs.append(bomb_)

            russian_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[2]}:",
                                     description=russian_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 4:
            country = countries[3]
            bombs = []
            for bomb_ in bomb_data[countries[3]]:
                bombs.append(bomb_)

            british_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[3]}:",
                                     description=british_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 5:
            country = countries[4]
            bombs = []
            for bomb_ in bomb_data[countries[4]]:
                bombs.append(bomb_)

            japanese_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[4]}:",
                                     description=japanese_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 6:
            country = countries[5]
            bombs = []
            for bomb_ in bomb_data[countries[5]]:
                bombs.append(bomb_)

            italian_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[5]}:",
                                     description=italian_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 7:
            country = countries[6]
            bombs = []
            for bomb_ in bomb_data[countries[6]]:
                bombs.append(bomb_)

            chinese_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[6]}:",
                                     description=chinese_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 8:
            country = countries[7]
            bombs = []
            for bomb_ in bomb_data[countries[7]]:
                bombs.append(bomb_)

            france_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[7]}:",
                                     description=france_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        elif country_number == 9:
            country = countries[8]
            bombs = []
            for bomb_ in bomb_data[countries[8]]:
                bombs.append(bomb_)

            sweden_bombs_embed = embed_maker(bombs)
            embedvar = discord.Embed(title=f"Select a bomb from {countries[8]}:",
                                     description=sweden_bombs_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)
        else:
            await ctx.send("Couldn't find that country's bombs.")
            return

        try:
            bomb_number = int((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please use a number.")
            return

        for x in range(len(bomb_data[country]) + 1):
            if bomb_number == x:
                bomb_type = bombs[x - 1]

        await ctx.send("Enter battle rating:")
        try:
            battle_rating = float((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please use a decimal number.")
            return

        await ctx.send("Is this a four base map? Enter 'YES' or 'NO'")
        try:
            four_base = str((await bot.wait_for('message', check=check)).content)
        except ValueError:
            await ctx.send("Please enter 'YES' or 'NO'.")
            return

        base_bombs_list = bomb_data[country][bomb_type]

        try:
            four_base = int(four_base)
        except ValueError:
            four_base = str(four_base)
            four_base = four_base.upper()
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
                await ctx.send("That battle rating doesn't exist.")
                return
        except ValueError:
            await ctx.send(
                "This bomb data hasn't been added to the spreadsheet yet. If you are requesting a 4 base "
                "map, it may be too soon. Please refer to 3 base map data and multiply it by 2x for each "
                "base to get approximate 4 base data.")
            return

        await ctx.send(
            f"Bombs Required for Bases: {base_bombs_required} \nBombs Required for Airfield: "
            f"{airfield_bombs_required}")

    except Exception as e:
        await ctx.send("User error, try again.")
        raise e


print("Server Running")

bot.run(TOKEN)
