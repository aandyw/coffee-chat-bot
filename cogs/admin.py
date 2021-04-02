import discord
from discord.ext import commands

import random
import asyncio
import emoji
import functools
import operator
from datetime import datetime

CHANNEL_NAME = 'coffee-time'
COLOR = 0x00ff00

# custom message that is sent to matched users
USER_TITLE = "Congrats you've been matched!"
USER_DESC = "You have been matched with `{user}` because you guys share some common interests :slight_smile: Feel free to reach out to your match and arrange your coffee chat via any platform that works the best for you.\nHave a good coffee chat! :coffee: :coffee: :coffee:"


TITLE_LIMIT = 200
DESC_LIMIT = 1000
CATEGORY_LIMIT = 5


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None  # the CHANNEL_NAME to send shit to
        self.event_msg = None  # event object message
        self.emotes_lst = None  # list of emotes
        self.member_roles = {}  # keep track of which user has role

    @commands.command(name='coffee_time', aliases=['coffeetime', 'coffee'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def categories(self, ctx, *args):
        """Simple command that begins coffee time event"""

        author = ctx.author
        guild = ctx.guild

        # checks if server has the channel
        self.channel = discord.utils.get(
            guild.text_channels, name=CHANNEL_NAME)

        # if the channel does not exist then create it
        if self.channel is None:
            self.channel = await guild.create_text_channel(CHANNEL_NAME)

        ### EMBEDDED MESSAGES ###

        # title
        embed_title = discord.Embed(
            title="Title", description="Enter the title for your coffee time event\nMax 200 characters", color=COLOR)

        # description
        embed_desc = discord.Embed(
            title="Description", description="Enter the description for your coffee time event\nMax 1000 characters", color=COLOR)

        # event start time
        embed_start = discord.Embed(
            title="Start time", description="Enter a starting time for your event", color=COLOR)

        # event categories
        embed_cats = discord.Embed(
            title="Categories", description="Enter the categories that you wish to have\nMax 5 categories", color=COLOR)

        # category emotes
        embed_emotes = discord.Embed(
            title="Emotes", description="Enter the emotes to be associated with the above categories\nMax 5 emotes", color=COLOR)

        ### MESSAGE VERFICATIONS ###
        def msg_check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        await ctx.channel.send(embed=embed_title)  # send title message

        try:
            while True:
                # 30 seconds to reply
                title = await self.bot.wait_for("message", check=msg_check, timeout=30)

                if len(title.content) > TITLE_LIMIT:  # exceeds message limit
                    await ctx.channel.send("Oops, looks like you exceeded the message limit \
                        \nYour description can only be {chars} characters long".format(chars=TITLE_LIMIT))
                else:
                    break

            # send description message
            await ctx.channel.send(embed=embed_desc)

            while True:
                desc = await self.bot.wait_for("message", check=msg_check, timeout=30)

                if len(desc.content) > DESC_LIMIT:  # exceeds message limit
                    await ctx.channel.send("Oops, looks like you exceeded the message limit \
                        \nYour description can only be {chars} characters long".format(chars=DESC_LIMIT))
                else:
                    break

            # send category message
            await ctx.channel.send(embed=embed_cats)

            while True:
                cats = await self.bot.wait_for("message", check=msg_check, timeout=30)

                num_categories = len((cats.content).split())
                if num_categories <= CATEGORY_LIMIT:

                    # send emotes message
                    await ctx.channel.send(embed=embed_emotes)

                    while True:
                        emotes = await self.bot.wait_for("message", check=msg_check, timeout=30)

                        if len((emotes.content).split()) != num_categories or len((emotes.content).split()) > CATEGORY_LIMIT:
                            await ctx.channel.send("Wow, looks like you messed up \
                            \nYou don't have the same number of emotes as your categories silly")
                        else:
                            break
                    break
                else:
                    await ctx.channel.send("Oops, looks like you exceeded number of categories\
                        \nYou can only have {num} categories".format(num=CATEGORY_LIMIT))

            print("Creating event message...")
            # creates a list of emotes
            self.emotes_lst = await asyncio.gather(self.split_emotes(emotes.content))

            # creates the emote-category messag
            cats_msg_content = await asyncio.gather(
                self.format_cats_emotes(cats.content, self.emotes_lst[0]))
            response = desc.content + "\nReact to the categories you are interested in!\n"

            # builds the custom embed discord message
            embed_msg = discord.Embed(
                title=title.content, description=response, color=COLOR)
            # event time and given categories
            embed_msg.add_field(name="Time", value=datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"), inline=False)
            embed_msg.add_field(name="Categories",
                                value=cats_msg_content[0], inline=False)
            # add footer with information about how created event at what time
            embed_msg.set_footer(text="Created by {author}\n{time}".format(
                author=ctx.author.name, time=datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

            # send message to CHANNEL_NAME
            self.event_msg = await self.channel.send(embed=embed_msg)

            # reacts to created event message
            await asyncio.gather(self.event_reactions(self.event_msg, self.emotes_lst[0]))

            # creates the new roles
            await asyncio.gather(self.create_roles(guild, self.emotes_lst[0]))

        except asyncio.TimeoutError:
            await ctx.send("Seems like you're busy so let's try this later.")

    @categories.error
    async def categories_error(self, error, ctx):
        if isinstance(error, commands.CheckFailure):
            await ctx.channel.send("You do not have permission to have ~coffee~")

    @commands.command(name='start', aliases=['s'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def start(self, ctx, *args):
        ### PERFORM MATCHING ###

        users = set()
        for role in self.emotes_lst[0]:
            # print(role)
            lst = self.member_roles[role]
            # print(len(lst))
            while lst:
                if len(lst) < 2:
                    break
                # user 1
                idx = random.randrange(0, len(lst))
                p1_id = lst.pop(idx)
                # user 2
                idx = random.randrange(0, len(lst))
                p2_id = lst.pop(idx)

                # if duplicates
                if p1_id in users or p2_id in users:
                    continue
                else:
                    users.add(p1_id)
                    users.add(p2_id)
                    user1 = self.bot.get_user(p1_id)
                    user2 = self.bot.get_user(p2_id)

                    user1_msg = discord.Embed(
                        title=USER_TITLE, description=USER_DESC.format(user=self.bot.get_user(p2_id)), color=COLOR)
                    user2_msg = discord.Embed(
                        title=USER_TITLE, description=USER_DESC.format(user=self.bot.get_user(p1_id)), color=COLOR)

                    await user1.send(embed=user1_msg)
                    await user2.send(embed=user2_msg)

        guild = ctx.guild
        await asyncio.gather(self.delete_roles(guild, self.emotes_lst[0]))
        await asyncio.gather(self.reinit())

    ### EVENT LISTENERS ###

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.bot.user.id != payload.user_id and payload.message_id == self.event_msg.id:
            emote = payload.emoji.name
            if emote in self.emotes_lst[0]:
                guild = self.bot.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, name=emote)
                user = payload.member
                if role is not None and user is not None:
                    await user.add_roles(role)
                    self.member_roles[emote].append(payload.user_id)
                    print(self.member_roles)
                else:
                    print(role, user)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if self.bot.user.id != payload.user_id and payload.message_id == self.event_msg.id:
            emote = payload.emoji.name
            if emote in self.emotes_lst[0]:
                guild = self.bot.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, name=emote)
                user = await guild.fetch_member(payload.user_id)
                if role is not None and user is not None:
                    await user.remove_roles(role)
                    self.member_roles[emote].remove(payload.user_id)
                    print(self.member_roles)
                else:
                    print(role, user)

    async def reinit(self):
        """ REINITIALIZED ALL DEFINED EVENT VARIABLES """
        self.channel = None
        self.event_msg = None
        self.emotes_lst = None
        self.member_roles = {}
        print("ALL EVENT VARIABLES HAVE BEEN REINITIALIZED")

    ### ROLE MANAGEMENT ###
    async def create_roles(self, guild, emotes_lst):
        """ Creates temporary discord roles using emotes """
        # print(emotes_lst)
        for role in emotes_lst:
            # print(role)
            await guild.create_role(name=role)

    async def delete_roles(self, guild, emotes_lst):
        """ Deletes the temporary discord roles """
        for role in emotes_lst:
            print(role)
            role_object = discord.utils.get(guild.roles, name=role)
            await role_object.delete()

    ### REACTIONS ###

    async def event_reactions(self, event_msg, emotes_lst):
        """ Function to add reactions to the event message """
        for emote in emotes_lst:
            await event_msg.add_reaction(emote)

    ### CATEGORIES AND EMOTES ###
    async def split_emotes(self, emotes):
        """ Splitting the given emotes into a list of separated emotes """
        emotes_lst = emoji.get_emoji_regexp().split(emotes)
        em_split_whitespace = [substr.split() for substr in emotes_lst]
        em_split = functools.reduce(operator.concat, em_split_whitespace)
        return em_split

    async def format_cats_emotes(self, categories, emotes_lst):
        """ Function to create a formated string containing categories and emotes """
        categories_lst = categories.split()
        msg_content = ""

        for cat, emote in zip(categories_lst, emotes_lst):
            self.member_roles[emote] = []
            msg_content += "[{emote}] {cat}\n".format(emote=emote, cat=cat)

        return msg_content


def setup(bot):
    bot.add_cog(Admin(bot))
