import json
import math
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


def get_base_bombs_required(bomb_name, country_name, battle_rating_range):
    bombs_c.execute(f"""SELECT "{battle_rating_range}" FROM {country_name} WHERE bomb_name=:bomb_name""",
                    {'bomb_name': bomb_name})
    return bombs_c.fetchone()


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


# EST = Estimated
async def get_bomb_data(ctx, bomb_name, country, battle_rating, four_base):
    battle_rating_multipliers = {"1.0-2.0": 5, "2.3-3.3": 6, "3.7-4.7": 8, "5.0+": 15}
    base_hp_multipliers = {"1.0-2.0": 0.75, "2.3-3.3": 1, "3.7-4.7": 1.25, "5.0+": 1.5}
    base_prefix = "3_base_"
    if four_base == "Yes":
        base_prefix = "4_base_"
    is_estimated = False

    base_bombs_required = get_base_bombs_required(bomb_name, country, f"{base_prefix}{battle_rating}")[0]
    if base_bombs_required is None or "whole lotta these" in base_bombs_required:
        answer = "Unknown (hasn't been researched/calculated yet)"

        if base_bombs_required is not None and "whole lotta these" in base_bombs_required:
            answer = base_bombs_required

        results_title = f"Answer from spreadsheet: {answer}.\n"
        results_description = f"\nIf you know what this result should be, feel free to let us know: https://forms.gle/7eyNQkT2zwyBB21z5" \
                              f"\n\nHow can we make this bot better? What new features would you like to see? " \
                              f"<https://forms.gle/ybTx84kKcTepzEXU8>\nP.S. We're now a verified Discord bot! Thanks for all the support!"

        embedvar = discord.Embed(title=results_title,
                                 description=results_description,
                                 color=0x00ff00)
        await ctx.interaction.followup.send(embed=embedvar)
        return False
    elif "EST" in base_bombs_required:
        try:
            base_bombs_required = int(base_bombs_required.split(" ")[0])
        except ValueError:
            base_bombs_required = "Whoops, error. Guess you'll have to full send it."

        is_estimated = True
    airfield_bombs_required = int(math.ceil(int(base_bombs_required) * battle_rating_multipliers[battle_rating] / base_hp_multipliers[battle_rating]))
    return {"base_bombs_required": base_bombs_required, "airfield_bombs_required": airfield_bombs_required, "EST": is_estimated}


@bot.command(name='bombs', aliases=['bomb'], help='Returns bombs to destroy base and airfield.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(options=[]))
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

            def country_check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return False
                if interaction_.message.id != country_choice_message.id:
                    return False
                return True

            interaction = await bot.wait_for("component_interaction", check=country_check)
            await interaction.response.defer_update()

            country_number_components.disable_components()
            await interaction.message.edit(components=country_number_components)

            country_number = int(interaction.component.custom_id)
            country = countries[country_number - 1]

            bomb_values = get_bombs_by_country(country)
            bomb_names = fetchall_to_list(bomb_values)

            bombs_embed = embed_maker(bomb_names)
            embedvar = discord.Embed(title=f"Select a bomb from {country}:",
                                     description=bombs_embed,
                                     color=0x00ff00)
            bombs_numbers_components = list_to_number_buttons(bomb_names)
            bombs_choice_message = await ctx.interaction.followup.send(embed=embedvar,
                                                                       components=bombs_numbers_components)

            def bombs_check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return False
                if interaction_.message.id != bombs_choice_message.id:
                    return False
                return True

            interaction = await bot.wait_for("component_interaction", check=bombs_check)
            await interaction.response.defer_update()

            bombs_numbers_components.disable_components()
            await interaction.message.edit(components=bombs_numbers_components)

            bomb_number = int(interaction.component.custom_id)
            bomb_name = bomb_names[bomb_number - 1]

            # Asks the user to enter the battle rating of their current match.
            battle_rating_multipliers = {"1.0-2.0": 5, "2.3-3.3": 6, "3.7-4.7": 8, "5.0+": 15}
            battle_rating_ranges = battle_rating_multipliers.keys()
            battle_rating_rages_button_components = list_to_buttons(battle_rating_ranges)
            br_choice_message = await ctx.interaction.followup.send("Select a battle rating range:",
                                                                    components=battle_rating_rages_button_components)

            def check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return False
                if interaction_.message.id != br_choice_message.id:
                    return False
                return True

            interaction = await bot.wait_for("component_interaction", check=check)
            await interaction.response.defer_update()

            battle_rating_rages_button_components.disable_components()
            await interaction.message.edit(components=battle_rating_rages_button_components)

            battle_rating = interaction.component.custom_id

            # Asks the user if the map has four bases
            confirmation_components = discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    (yes_button := discord.ui.Button(label="Yes")),
                    (no_button := discord.ui.Button(label="No")),
                ),
            )
            confirmation_message = await ctx.interaction.followup.send("Is this a four base map?",
                                                                       components=confirmation_components)

            def check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return False
                if interaction_.custom_id not in [yes_button.custom_id, no_button.custom_id]:
                    return False
                return True

            interaction = await bot.wait_for("component_interaction", check=check)
            await interaction.response.defer_update()

            confirmation_components.disable_components()
            await interaction.message.edit(components=confirmation_components)

            four_base = interaction.component.label

            # Using the battle_rating and four_base variables calculates bombs needed for bases and airfield.
            bomb_results = await get_bomb_data(ctx, bomb_name, country, battle_rating, four_base)

            if bomb_results is False:
                return

            base_bombs_required = bomb_results["base_bombs_required"]
            airfield_bombs_required = bomb_results["airfield_bombs_required"]

            planes_with_selected_bomb = remove_duplicates_from_list(get_ordnances_by_plane(country, bomb_name))
            planes_with_selected_bomb_string = list_to_string(planes_with_selected_bomb)
            planes_with_selected_bomb_string = f"\nPlanes that can hold the {bomb_name} from {country}: \n{planes_with_selected_bomb_string}\n"
            if len(planes_with_selected_bomb) == 0:
                planes_with_selected_bomb_string = f"\nThere aren't any planes from {country} that have the {bomb_name}\n"

            bombs_needed_title = f"__Bombs Required for Bases: {base_bombs_required}__ \n__Bombs Required for Airfield: " \
                                 f"{airfield_bombs_required}__"
            if bomb_results["EST"]:
                results_title = f"Unknown (hasn't been researched/calculated yet)"
                results_description = f"However, here is an __***estimate***__ that may or may not be accurate:\n**{bombs_needed_title}**" \
                                      f"\n\nIf you know what this result should be, feel free to let us know: https://forms.gle/7eyNQkT2zwyBB21z5" \
                                      f"\n{planes_with_selected_bomb_string}" \
                                      f"\nHow can we make this bot better? What new features would you like to see? " \
                                      f"<https://forms.gle/ybTx84kKcTepzEXU8>\nP.S. We're now a verified Discord bot! Thanks for all the support!"
            else:
                results_title = bombs_needed_title
                results_description = f"\n{planes_with_selected_bomb_string}" \
                                      f"\nThe planes addition above was suggested by a user.\nHow can we make this bot better? What new features would you like to see? " \
                                      f"<https://forms.gle/ybTx84kKcTepzEXU8>\nP.S. We're now a verified Discord bot! Thanks for all the support!"
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
            "BombBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure BombBot has the permission `Use Application Commands`. "
            "If that doesn't work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/754879715659087943")


bot.remove_command("help")


async def main():
    await bot.login(TOKEN)
    await bot.register_application_commands(list(bot.commands))
    await bot.connect()


print("Bot is starting...")
loop = bot.loop
loop.run_until_complete(main())
