import os
from dotenv import load_dotenv

# DISCORD PACKAGE
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('TOKEN')

initial_extensions = ['cogs.admin']

bot = commands.Bot(command_prefix='!',
                   description='Coffee bot for coffee chats')

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    print(
        f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

bot.run(TOKEN, bot=True, reconnect=True)

# bot.py handles basic discord processing and runs modules

# TODO: Setup admin commands
#   -Starting coffee chat (admin decides on categories and members will react to categories)
#       e.g. (Data science, web dev, programming, reading,...)
#   -Number of people in a group
#   -Setup time limit for when to react
#  Once these details are provided pass inforamtion onto the messaging module

# TODO: Messaging (once people have been matched)
# Once timelimit for the message is up people who have reacted to the message will be paired together
#    -Passing details to matching.py to process matches
#    -Receives output from matching.py; tell people who they have been matched with
#    -Discord bot will send a DM to member with

# TODO: Matching algorithm
#    Some simple database (text file); keeps track of people who have been matched
#    People who react to same cateogries will be matched together
