#! /usr/bin/env python3
from email import message
import os

import discord
from pretty_help import PrettyHelp
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
BOT_OWNER_ID = os.getenv("OWNER_ID")

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    case_insensitive=True,
    description="🍪 Cookie Bot 🍪",
    owner_id="",
    help_command=PrettyHelp(show_index=False, no_category="Command Help"),
)


@bot.command(name="pay", help="Give <user> a delicious cookie")
async def pay(context, username: str):
    await context.send(f"Imagine a cookie being sent to {username}")


@bot.command(name="bal", help="Rough estimate of <user>'s cookie count")
async def bal(context, username: str):
    await context.send("> 100")


@bot.command(name="top", help="List of global cookie counts")
async def top(context):
    await context.send("nobody")


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f"{bot.user.name} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})"
    )
    await bot.change_presence(activity=discord.Game(name="Cookie Clicker"))


@bot.event
async def on_command_error(context, exception):
    if isinstance(exception, commands.errors.CommandNotFound):
        bot.help_command.context = context
        await bot.help_command.send_bot_help(bot.help_command.get_bot_mapping())
        bot.help_command = PrettyHelp(show_index=False, no_category="Command Help")
    elif isinstance(exception, commands.errors.MissingRequiredArgument):
        await context.send(f"Error: {exception}")
    else:
        raise exception


bot.run(TOKEN)
