#! /usr/bin/env python3
import asyncio
import os
import signal
import sqlite3
import sys

import discord
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from pretty_help import PrettyHelp

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
BOT_OWNER_ID = os.getenv("OWNER_ID")
DBLITE_FILE = os.getenv("DBLITE_FILE")

SQLITE_CREATE_TABLE = """CREATE TABLE IF NOT EXISTS cookie_scores (
	user_id INT8 PRIMARY KEY,
   	n_cookies INT8 DEFAULT 0
) WITHOUT ROWID;
"""
SQLITE_GET_COOKIE_SCORES = "SELECT * FROM cookie_scores;"
SQLITE_SET_COOKIES_USER = """UPDATE cookie_scores
SET n_cookies = ?
WHERE user_id = ?;
"""
SQLITE_ADD_USER = "INSERT INTO cookie_scores(user_id) VALUES (?);"


def exit_strategy(*_):
    print(" Shutting down...")
    asyncio.run(bot.close())
    conn.close()
    print("Shutdown complete. Goodbye 👋")
    sys.exit(0)


signal.signal(signal.SIGINT, exit_strategy)

intents = discord.Intents(members=True, messages=True)

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    case_insensitive=True,
    description="🍪 Cookie Bot 🍪",
    owner_id="",
    help_command=PrettyHelp(show_index=False, no_category="Command Help"),
    intends=intents,
)

conn: sqlite3.Connection


@bot.command(
    help="Give <user> <x> cookies. The <x> cookies are taken out of your account.",
    aliases=("donate", "give", "throw"),
    usage="@username",
)
async def pay(context: Context, user: discord.Member, n_cookies: int):
    if n_cookies <= 0:
        await context.send("Nice try, but cookies are quite *natural*.")
        return

    if user.id == context.message.author.id:
        await context.send("Don't be so selfish!")
        return

    all_scores = {
        score[0]: score[1]
        for score in conn.execute(SQLITE_GET_COOKIE_SCORES).fetchall()
    }

    if all_scores.get(context.message.author.id) is None:
        conn.execute(SQLITE_ADD_USER, (context.message.author.id,))
        conn.commit()
        all_scores[context.message.author.id] = 0

    if all_scores.get(user.id) is None:
        conn.execute(SQLITE_ADD_USER, (user.id,))
        conn.commit()
        all_scores[user.id] = 0

    conn.execute(
        SQLITE_SET_COOKIES_USER,
        (all_scores[context.message.author.id] - n_cookies, context.message.author.id),
    )
    conn.commit()

    conn.execute(
        SQLITE_SET_COOKIES_USER,
        (all_scores[user.id] + n_cookies, user.id),
    )
    conn.commit()

    await context.send(
        f"{context.message.author.display_name}: {all_scores[context.message.author.id]} => {all_scores[context.message.author.id] - n_cookies}\n"
        f"{user.display_name}: {all_scores[user.id]} => {all_scores[user.id] + n_cookies}\n"
    )


@bot.command(
    help="Rough estimate of <user>'s cookie count",
    aliases=("bal", "state", "show"),
    usage="@username",
)
async def balance(context: Context, user: discord.Member):
    all_scores = {
        score[0]: score[1]
        for score in conn.execute(SQLITE_GET_COOKIE_SCORES).fetchall()
    }
    await context.send(f"{user.display_name} has {all_scores.get(user.id, 0)} cookies.")


@bot.command(
    help="List of global cookie counts", aliases=("best", "sum", "summary", "global")
)
async def top(context: Context):
    message = "Global Scores:\n"
    list = conn.execute(SQLITE_GET_COOKIE_SCORES).fetchall()
    list.sort(key=lambda y: y[1])
    for score in list:
        try:
            username = await context.guild.fetch_member(score[0])
        except:
            username = "MEMBER_NOT_FOUND"
        message += f"{username.display_name}: {score[1]}\n"
    await context.send(message)


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f"Successfully spawned bot '{bot.user.name}' and connected to guild '{guild.name}'."
    )
    await bot.change_presence(activity=discord.Game(name="Cookie Clicker"))


@bot.event
async def on_command_error(context, exception):
    if isinstance(exception, commands.errors.CommandNotFound):
        await context.send("Bip Bop. Me does not compute. Let me *help* you.")
        bot.help_command.context = context
        await bot.help_command.send_bot_help(bot.help_command.get_bot_mapping())
        bot.help_command = PrettyHelp(show_index=False, no_category="Command Help")
    elif isinstance(exception, commands.errors.MissingRequiredArgument):
        await context.send(f"Error: {exception}")
    elif isinstance(exception, commands.errors.MemberNotFound):
        await context.send(f"{exception}")
    else:
        raise exception


if __name__ == "__main__":
    try:
        conn = sqlite3.connect(DBLITE_FILE)
        print(f"Database connection to SQLite DB Version {sqlite3.version} created.")
        conn.execute(SQLITE_CREATE_TABLE)
        conn.commit()
        print("Default table created. Database is ready to go.")
    except Exception as e:
        print(e, file=sys.stderr)

    bot.run(TOKEN)
    exit_strategy()

# The following commands are only for debugging purposes and are subject to changes.
@bot.command(hidden=True)
async def ping(context):
    context.send("pong")


@bot.command(hidden=True)
async def pong(context):
    context.send("ping")
