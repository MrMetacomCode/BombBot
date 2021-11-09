import json
import os.path
import sqlite3
import discord
import pickle
from datetime import date
from datetime import datetime
from discord.ext import commands
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Security variables.
TOKEN = os.getenv('BOMBBOT_DISCORD_TOKEN')
SPREADSHEET_ID = '1Ra9Ca60nwIlG_aGVS9bITjM94SJ6H5vIocl2SRVEOcM'
TRACKING_SPREADSHEET_ID = '1HhomUgsgjhWWg67M54ZY_RP2l2Ns7LiDCszRJE9XMgQ'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
value_input_option = "USER_ENTERED"
bombs_conn = sqlite3.connect('Bombs.db')
bombs_c = bombs_conn.cursor()
ordnance_conn = sqlite3.connect('PlaneOrdnances.db')
ordnance_c = ordnance_conn.cursor()

# Setting up intents and initializing bot.
intents = discord.Intents(messages=True, guilds=True, bans=True, dm_messages=True, dm_reactions=True, dm_typing=True,
                          emojis=True, guild_messages=True, guild_reactions=True, guild_typing=True, invites=True,
                          members=True, reactions=True)
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
        log_exception(e)
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
    await bot.change_presence(activity=discord.Game("/bombs"))

    try:
        # Runs the function to report the amount of times $bombs has been called today.
        scheduler = AsyncIOScheduler()
        scheduler.add_job(func, CronTrigger(hour=23, minute=59, second=0))
        scheduler.start()
    except Exception as e:
        log_exception(e)
        raise e


# Helper function that turns lists into numbered strings with line breaks.
def embed_maker(thing_list):
    list_number = 1
    embed = ""
    for thing in thing_list:
        item = f"{list_number} = {thing}\n"
        embed += item
        list_number += 1
    return embed


def get_bomb_by_name(bomb_name, country_name):
    bombs_c.execute(f"SELECT * FROM {country_name} WHERE bomb_name=:bomb_name", {'bomb_name': bomb_name})
    return bombs_c.fetchall()


def get_bombs_by_country(country_name):
    bombs_c.execute(f"SELECT * FROM {country_name}")
    return bombs_c.fetchall()


def fetchall_to_list(fetchall_result):
    items = []
    for item in fetchall_result:
        items.append(item[0])
    return items


def remove_duplicates_from_list(items_list):
    return list(dict.fromkeys(items_list))


def get_ordnances_by_plane(country_name, bomb_name):
    if "(" in bomb_name:
        bomb_name = bomb_name.split("(")[0]
    bomb_name_items = bomb_name.split(" ")

    query = ""
    for item in bomb_name_items:
        if item == bomb_name_items[-1]:
            query += f"Ordnance like '%{item}%'"
        else:
            query += f"Ordnance like '%{item}%' AND "

    if len(bomb_name_items) > 1:
        ordnance_c.execute(f"SELECT PlaneName FROM {country_name} WHERE ({query})")
    else:
        ordnance_c.execute(f"SELECT PlaneName FROM {country_name} WHERE Ordnance LIKE '%{bomb_name}%'")
    return fetchall_to_list(ordnance_c.fetchall())


def list_to_string(item_list):
    if len(item_list) == 1:
        return f"{item_list[0]}"
    items_string = ""
    for item in item_list:
        if item == item_list[-1]:
            items_string += f"and {item}"
        else:
            items_string += f"{item}, "
    return items_string


def list_to_number_buttons(list_items):
    number_buttons = []
    for number in list(range(1, len(list_items) + 1)):
        button = discord.ui.Button(label=str(number), custom_id=str(number))
        number_buttons.append(button)
    number_components = discord.ui.MessageComponents.add_buttons_with_rows(*number_buttons)
    return number_components


def list_to_buttons(list_items):
    buttons = []
    for item in list_items:
        button = discord.ui.Button(label=str(item), custom_id=str(item))
        buttons.append(button)
    buttons_components = discord.ui.MessageComponents.add_buttons_with_rows(*buttons)
    return buttons_components


# Command that returns bombs needed for bases and airfield.
@bot.command(name='bombs', aliases=['bomb'], help='Returns bombs to destroy base and airfield.')
async def bomb(ctx):
    if hasattr(ctx, "interaction"):
        with open('count.json', 'r') as file:
            count_file = json.loads(file.read())
        try:
            countries = ["America", "Britain", "China", "France", "Germany", "Italy", "Japan", "Russia", "Sweden"]

            # Uses the helper function to make a numbered list of the countries.
            countries_embed = embed_maker(countries)

            # Makes an embed and sends it.
            embedvar = discord.Embed(title="Select a country to view bombs from:",
                                     description=countries_embed,
                                     color=0x00ff00)
            country_number_components = list_to_number_buttons(countries)
            await ctx.interaction.response.send_message(embed=embedvar, components=country_number_components)

            country_choice_message = await ctx.interaction.original_message()

            def check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return True
                if interaction_.message.id != country_choice_message.id:
                    return True
                return True

            interaction = await bot.wait_for("component_interaction", check=check)

            country_number_components.disable_components()
            await interaction.response.edit_message(components=country_number_components)

            country_number = int(interaction.component.custom_id)
            country = countries[country_number - 1]

            bomb_values = get_bombs_by_country(country)
            bomb_names = fetchall_to_list(bomb_values)

            bombs_embed = embed_maker(bomb_names)
            embedvar = discord.Embed(title=f"Select a bomb from {country}:",
                                     description=bombs_embed,
                                     color=0x00ff00)
            bombs_numbers_components = list_to_number_buttons(bomb_names)
            await ctx.interaction.followup.send(embed=embedvar, components=bombs_numbers_components)

            bombs_choice_message = await ctx.interaction.original_message()

            def check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return True
                if interaction_.message.id != bombs_choice_message.id:
                    return True
                return True

            interaction = await bot.wait_for("component_interaction", check=check)

            bombs_numbers_components.disable_components()
            await interaction.response.edit_message(components=bombs_numbers_components)

            bomb_number = int(interaction.component.custom_id)
            bomb_name = bomb_names[bomb_number - 1]

            # Asks the user to enter the battle rating of their current match.
            battle_rating_ranges = ["1.0-2.0", "2.3-3.3", "3.7-4.7", "5.0+"]
            battle_rating_rages_button_components = list_to_buttons(battle_rating_ranges)
            await ctx.interaction.followup.send("Select a battle rating range:", components=battle_rating_rages_button_components)

            br_choice_message = await ctx.interaction.original_message()

            def check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return True
                if interaction_.message.id != br_choice_message.id:
                    return True
                return True

            interaction = await bot.wait_for("component_interaction", check=check)

            battle_rating_rages_button_components.disable_components()
            await interaction.response.edit_message(components=battle_rating_rages_button_components)

            battle_rating = interaction.component.custom_id

            # Asks the user if the map has four bases
            confirmation_components = discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    discord.ui.Button(label="Yes", custom_id="YES"),
                    discord.ui.Button(label="No", custom_id="NO"),
                ),
            )
            await ctx.interaction.followup.send("Is this a four base map?", components=confirmation_components)

            confirmation_message = await ctx.interaction.original_message()

            def check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return True
                if interaction_.message.id != confirmation_message.id:
                    return True
                return True

            interaction = await bot.wait_for("component_interaction", check=check)

            confirmation_components.disable_components()
            await interaction.response.edit_message(components=confirmation_components)

            four_base = interaction.component.custom_id

            # Creates a list of the data needed to destroy a base using the country and bomb type.
            base_bombs_list = get_bomb_by_name(bomb_name, country)[0][1:]

            # Using the battle_rating and four_base variables calculates bombs needed for bases and airfield.
            try:
                if battle_rating == "1.0-2.0":
                    if four_base == "YES":
                        base_bombs_required = base_bombs_list[0]
                        airfield_bombs_required = int(base_bombs_required) * 5
                    else:
                        base_bombs_required = base_bombs_list[1]
                        airfield_bombs_required = int(base_bombs_required) * 5
                elif battle_rating == "2.3-3.3":
                    if four_base == "YES":
                        base_bombs_required = base_bombs_list[2]
                        airfield_bombs_required = int(base_bombs_required) * 6
                    else:
                        base_bombs_required = base_bombs_list[3]
                        airfield_bombs_required = int(base_bombs_required) * 6
                elif battle_rating == "3.7-4.7":
                    if four_base == "YES":
                        base_bombs_required = base_bombs_list[4]
                        airfield_bombs_required = int(base_bombs_required) * 8
                    else:
                        base_bombs_required = base_bombs_list[5]
                        airfield_bombs_required = int(base_bombs_required) * 8
                elif battle_rating == "5.0+":
                    if four_base == "YES":
                        base_bombs_required = base_bombs_list[6]
                        airfield_bombs_required = int(base_bombs_required) * 15
                    else:
                        base_bombs_required = base_bombs_list[7]
                        airfield_bombs_required = int(base_bombs_required) * 15

            # If there isn't any data in the cell then it will return this error, which means the data hasn't been added yet.
            except ValueError:
                results_title = f"Answer from spreadsheet: Unknown (hasn't been researched/calculated yet).\n"
                results_description = f"\nIf you know what this result should be, feel free to let us know: https://forms.gle/7eyNQkT2zwyBB21z5" \
                                      f"\n\nHow can we make this bot better? What new features would you like to see? " \
                                      f"<https://forms.gle/ybTx84kKcTepzEXU8>\nP.S. We're being reviewed as a verified bot! Thanks for all the support!"
                embedvar = discord.Embed(title=results_title,
                                         description=results_description,
                                         color=0x00ff00)

                # If everything works it send how many bombs per base and airfield
                await ctx.interaction.followup.send(embed=embedvar)
                return
            except TypeError:
                await ctx.interaction.followup.send(
                    "This bomb data hasn't been added to the spreadsheet yet. If you are requesting a 4 base "
                    "map, it may be too soon. Please refer to 3 base map data and multiply it by 2x for each "
                    "base to get **approximate** 4 base data.")
                return

            planes_with_selected_bomb = remove_duplicates_from_list(get_ordnances_by_plane(country, bomb_name))
            planes_with_selected_bomb_string = list_to_string(planes_with_selected_bomb)
            planes_with_selected_bomb_string = f"\nPlanes that can hold the {bomb_name} from {country}: \n{planes_with_selected_bomb_string}\n"
            if len(planes_with_selected_bomb) == 0:
                planes_with_selected_bomb_string = f"\nThere aren't any planes from {country} that have the {bomb_name}\n"

            results_title = f"__Bombs Required for Bases: {base_bombs_required}__ \n__Bombs Required for Airfield: " \
                            f"{airfield_bombs_required}__"
            results_description = f"\n{planes_with_selected_bomb_string}" \
                                  f"\nThe planes addition above was suggested by a user.\nHow can we make this bot better? What new features would you like to see? " \
                                  f"<https://forms.gle/ybTx84kKcTepzEXU8>\nP.S. We're being reviewed as a verified bot! Thanks for all the support!"
            embedvar = discord.Embed(title=results_title,
                                     description=results_description,
                                     color=0x00ff00)

            # If everything works it send how many bombs per base and airfield
            await ctx.interaction.followup.send(embed=embedvar)

        # If something breaks in all that then it will send this message
        except Exception as e:
            log_exception(e)
            await ctx.interaction.followup.send(f"User error, try again. Error message:\n{e}")
            raise e

        try:
            count = int(count_file["count"])
            new_count = count + 1
            count_file["count"] = new_count

            with open('count.json', 'w') as file:
                file.write(json.dumps(count_file))
        except Exception as e:
            log_exception(e)
            raise e
    else:
        await ctx.send(
            "BombBot is now using slash commands! Simply type / and it will bring up the list of commands to use.")


@bot.command(name='count', help='Displays number of times /bombs has been called.')
async def count_output(ctx):
    with open('count.json', 'r') as file:
        count_file = json.loads(file.read())

    count_ = int(count_file["count"])
    await ctx.interaction.response.send_message(f"$bombs has been called a total of {count_} times.")


async def main():
    await bot.login(TOKEN)
    # Only uncomment if a command was added or a command name, description, args, etc. has changed.
    await bot.register_application_commands()
    await bot.connect()


print("Server Running")
loop = bot.loop
loop.run_until_complete(main())
