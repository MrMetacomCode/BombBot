import os
import pickle
import sqlite3
import discord
from bomb import BombClass
from discord import Intents
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from apscheduler.triggers.cron import CronTrigger
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from apscheduler.schedulers.asyncio import AsyncIOScheduler

conn = sqlite3.connect('bombs.db')
c = conn.cursor()
TOKEN = os.getenv('BOMBBOT_DISCORD_TOKEN')
SPREADSHEET_ID = '1Ra9Ca60nwIlG_aGVS9bITjM94SJ6H5vIocl2SRVEOcM'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

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


@tasks.loop(hours=168)
async def update_tables_loop():
    create_tables()
    update_tables()
    print("SQL Lite database updated.")


@bot.event
async def on_ready():
    print("Bot is ready.")
    update_tables_loop.start()


# Reads the values of the given input range from the given spreadsheet.
def read_values(input_range, spreadsheet_id):
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=input_range).execute()
    values = result.get('values', [])
    return values


def insert_bomb(bomb, country_name):
    with conn:
        c.execute(f"INSERT INTO {country_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            bomb.bomb_name, bomb._4base_1_0_2_0, bomb._3base_1_0_2_0, bomb._4base_2_3_3_3, bomb._3base_2_3_3_3,
            bomb._4base_3_7_4_7,
            bomb._3base_3_7_4_7, bomb._4base_5_0_up, bomb._3base_5_0_up))


def get_bomb_by_name(bomb_name, country_name):
    c.execute(f"SELECT * FROM {country_name} WHERE bomb_name=:bomb_name", {'bomb_name': bomb_name})
    return c.fetchall()


def add_bomb_values_to_db(list_values, country_name):
    for items in list_values:
        items_without_empty_strings = [None if i == '' else i for i in items]
        new_bomb = BombClass(items_without_empty_strings[0], items_without_empty_strings[3],
                             items_without_empty_strings[4], items_without_empty_strings[5],
                             items_without_empty_strings[6], items_without_empty_strings[7],
                             items_without_empty_strings[8], items_without_empty_strings[9],
                             items_without_empty_strings[10])
        insert_bomb(new_bomb, country_name)


countries = ["american", "britain", "china", "french", "german", "italy", "japan", "russia", "sweden"]


def create_tables():
    for country in countries:
        try:
            with conn:
                c.execute(f"DROP TABLE {country}")
        except Exception as e:
            continue

    c.execute("""CREATE TABLE american (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE german (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE russia (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE britain (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE japan (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE italy (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE china (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE french (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")

    c.execute("""CREATE TABLE sweden (
                bomb_name text,
                [4_base_1.0-2.0] text,
                [3_base_1.0-2.0] text,
                [4_base_2.3-3.3] text,
                [3_base_2.3-3.3] text,
                [4_base_3.7-4.7] text,
                [3_base_3.7-4.7] text,
                [4_base_5.0+] text,
                [3_base_5.0+] text
                )""")


def update_tables():
    for country in countries:
        with conn:
            c.execute(f'DELETE FROM {country};', )

    # Table ranges for each country.
    american_bombs = 'Bomb Table!A19:K29'
    german_bombs = 'Bomb Table!A33:K39'
    russian_bombs = 'Bomb Table!A43:K55'
    british_bombs = 'Bomb Table!A59:K65'
    japanese_bombs = 'Bomb Table!A70:K83'
    italian_bombs = 'Bomb Table!A87:K93'
    chinese_bombs = 'Bomb Table!A97:K117'
    french_bombs = 'Bomb Table!A121:K127'
    swedish_bombs = 'Bomb Table!A130:K140'

    # Read values from each country.
    american_values = read_values(american_bombs, SPREADSHEET_ID)
    german_values = read_values(german_bombs, SPREADSHEET_ID)
    russian_values = read_values(russian_bombs, SPREADSHEET_ID)
    british_values = read_values(british_bombs, SPREADSHEET_ID)
    japanese_values = read_values(japanese_bombs, SPREADSHEET_ID)
    italian_values = read_values(italian_bombs, SPREADSHEET_ID)
    chinese_values = read_values(chinese_bombs, SPREADSHEET_ID)
    french_values = read_values(french_bombs, SPREADSHEET_ID)
    swedish_values = read_values(swedish_bombs, SPREADSHEET_ID)

    with conn:
        # Updating tables with new data.
        add_bomb_values_to_db(american_values, "american")
        add_bomb_values_to_db(german_values, "german")
        add_bomb_values_to_db(russian_values, "russia")
        add_bomb_values_to_db(british_values, "britain")
        add_bomb_values_to_db(japanese_values, "japan")
        add_bomb_values_to_db(italian_values, "italy")
        add_bomb_values_to_db(chinese_values, "china")
        add_bomb_values_to_db(french_values, "french")
        add_bomb_values_to_db(swedish_values, "sweden")


print("Server Running")
bot.run(TOKEN)
