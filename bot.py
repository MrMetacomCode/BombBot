import os
import os.path
import random
import pickle
#import logging
from discord import Intents
from discord.ext import commands
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


#logging.basicConfig(level=logging.DEBUG, filename='logs.txt')
#logger = logging.getLogger(__name__)
#logger.debug('test')

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


@bot.command(name='rolldice', help='Simulates rolling dice.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))


@bot.command(name='bombs', help='Find Bombs from Spreadsheet. If bomb name has spaces just smash it all together!')
async def bomb(ctx, country=None, bomb_type=None, battle_rating=None, four_base=None):
    american_bombs = 'Bomb Table!A19:Q29'
    german_bombs = 'Bomb Table!A33:Q39'
    russian_bombs = 'Bomb Table!A43:Q54'
    british_bombs = 'Bomb Table!A58:Q64'
    japanese_bombs = 'Bomb Table!A68:Q81'
    italian_bombs = 'Bomb Table!A85:Q91'
    chinese_bombs = 'Bomb Table!A95:Q115'
    french_bombs = 'Bomb Table!A119:Q125'
    swedish_bombs = 'Bomb Table!A128:Q138'

    bomb_data = {"US": {}, "GERMAN": {}, "RUSSIA": {}, "BRITAIN": {}, "JAPAN": {}, "ITALY": {}, "CHINA": {}, "FRANCE": {}, "SWEDEN": {}}
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

    try:
        if country is None:
            await ctx.send("Country is missing.")

        if bomb_type is None:
            await ctx.send("Bomb type is missing.")

        if battle_rating is None:
            await ctx.send("Battle rating is missing.")
            return

        country = country.upper()
        if country in ['AMERICA', 'AMERICAN', 'USA', 'United_States_of_America']:
            country = 'US'
        elif country in ['DE', 'GERMANY', 'NAZI', 'FATHERLAND']:
            country = 'GERMAN'
        elif country in ['RUSSIA', 'RUSSIAN', 'SOVIET', 'USSR', 'RU']:
            country = 'RUSSIA'
        elif country in ['BRITISH', 'UK']:
            country = 'BRITAIN'
        elif country in ['JP', 'JAPANESE']:
            country = 'JAPAN'
        elif country in ['ITALIAN', 'IT']:
            country = 'ITALY'
        elif country in ['CHINESE', 'CN']:
            country = 'CHINA'
        elif country in ['FRENCH', 'FR']:
            country = 'FRANCE'
        elif country in ['SWEDISH']:
            country = 'SWEDEN'
        if country not in bomb_data:
            await ctx.send("Country is invalid.")

        bomb_type = bomb_type.upper()
        bomb_type_list = []
        for country_ in bomb_data.values():
            for bomb_type_ in country_:
                bomb_type_list.append(bomb_type_)
        if bomb_type not in bomb_type_list:
            await ctx.send("Bomb type is invalid.")
            return

        try:
            battle_rating = float(battle_rating)
        except ValueError:
            await ctx.send("Battle rating is invalid.")
            return

        base_bombs_list = bomb_data[country.upper()][bomb_type.upper()]

        if 1.0 <= battle_rating <= 2.0:
            if four_base == 4:
                base_bombs_required = base_bombs_list[2]
                airfield_bombs_required = int(base_bombs_required) * 5
            else:
                base_bombs_required = base_bombs_list[3]
                airfield_bombs_required = int(base_bombs_required) * 5
        elif 2.3 <= battle_rating <= 3.3:
            if four_base == 4:
                base_bombs_required = base_bombs_list[4]
                airfield_bombs_required = int(base_bombs_required) * 6
            else:
                base_bombs_required = base_bombs_list[5]
                airfield_bombs_required = int(base_bombs_required) * 6
        elif 3.7 <= battle_rating <= 4.7:
            if four_base == 4:
                base_bombs_required = base_bombs_list[6]
                airfield_bombs_required = int(base_bombs_required) * 8
            else:
                base_bombs_required = base_bombs_list[7]
                airfield_bombs_required = int(base_bombs_required) * 8
        elif 5.0 <= battle_rating:
            if four_base == 4:
                base_bombs_required = base_bombs_list[8]
                airfield_bombs_required = int(base_bombs_required) * 15
            else:
                base_bombs_required = base_bombs_list[9]
                airfield_bombs_required = int(base_bombs_required) * 15
        else:
            return

        if base_bombs_required == 0:
            await ctx.send("This bomb data is unavailable.")
        else:
            await ctx.send(
                f"Bombs Required for Bases: {base_bombs_required} \nBombs Required for Airfield: "
                f"{airfield_bombs_required}")

    except Exception as e:
        await ctx.send("User error, try again.")
        raise e


print("Server Running")

bot.run(TOKEN)
