import discord
from discord.ext import commands

import random
import asyncio
import emoji
import functools
import operator
from datetime import datetime
import numpy as np

CHANNEL_NAME = 'coffee-time'
COLOR = 0x00ff00

# custom message that is sent to matched users
USER_TITLE = "Congrats you've been matched!"
USER_DESC = "You have been matched with `{user}` because you both share some common interests :slight_smile: Feel free to reach out to your match and arrange your coffee chat via any platform that works the best for you.\nHave a good coffee chat! :coffee: :coffee: :coffee:"


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
        self.all_user_id = []   # store all user IDs who react to at least 1 category
        # store all potential matches for each user in format: [ [user, (user match, number of interests in common)] ]
        self.all_matches = {}

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
            return msg.author == ctx.author

        await ctx.author.send(embed=embed_title)  # send title message

        try:
            while True:
                # 30 seconds to reply
                title = await self.bot.wait_for("message", check=msg_check, timeout=30)

                if len(title.content) > TITLE_LIMIT:  # exceeds message limit
                    await ctx.author.send("Oops, looks like you exceeded the message limit \
                        \nYour description can only be {chars} characters long".format(chars=TITLE_LIMIT))
                else:
                    break

            # send description message
            await ctx.author.send(embed=embed_desc)

            while True:
                desc = await self.bot.wait_for("message", check=msg_check, timeout=30)

            # retrieve title until title satisfies length requirement
            while len(title.content) > 200:
                await ctx.channel.send("Oops, the title you entered is too long. Re-enter a new title:")
                title = await self.bot.wait_for("message", check=check_desc, timeout=30)
            await ctx.channel.send("Title is set to: " + title.content)

            await ctx.channel.send(embed=embed_desc)
            desc = await self.bot.wait_for("message", check=check_desc, timeout=30)

            # retrieve description until description satisfies length requirement
            while len(desc.content) > 1000:  # if over message limit
                await ctx.channel.send("Oops, the description you entered is too long. Re-enter a new description:")
                desc = await self.bot.wait_for("message", check=check_desc, timeout=30)
            await ctx.channel.send("Description is set to: " + desc.content)
                if len(desc.content) > DESC_LIMIT:  # exceeds message limit
                    await ctx.author.send("Oops, looks like you exceeded the message limit \
                        \nYour description can only be {chars} characters long".format(chars=DESC_LIMIT))
                else:
                    break

            # send category message
            await ctx.author.send(embed=embed_cats)

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

        # store all potential matches and scores (number of common categories) for each user
        for user1 in all_user_id:
            all_matches[user1] = []
            for user2 in all_user_id:
                if user2 == user1:
                    continue
                else:
                    common_cats = [e for e in user1.roles if e in user2.roles]
                    all_matches[user1].append((user2, len(common_cats)))

        # iterate through all users in keyset of all_matches
        user_index = 0

        # perform matching until no users are left
        while len(all_matches) > 0:
            # store remaining unmatched user (if total number of users is uneven)
            if (len(all_matches) == 1):
                unmatched = all_matches.keys()[0]
                break

            # track potential match with current highest score
            keys = list(all_matches.keys())
            user = keys[user_index]
            cur_matched_user = ""
            cur_max_score = 0

            # find the potential match with highest score
            for matched_tuple in all_matches[user]:
                if matched_tuple[1] >= cur_max_score:
                    cur_matched_user = matched_tuple[0]
                    cur_max_score = matched_tuple[1]

            # check if the user can be matched with the potential match
            if cur_matched_user in all_matches:
                # send matching messages
                user1 = self.bot.get_user(user)
                user2 = self.bot.get_user(cur_matched_user)

                user1_msg = discord.Embed(title=USER_TITLE, description=USER_DESC.format(user=self.bot.get_user(cur_matched_user)), color=COLOR)
                user2_msg = discord.Embed(title=USER_TITLE, description=USER_DESC.format(user=self.bot.get_user(user)), color=COLOR)

                await user1.send(embed=user1_msg)
                await user2.send(embed=user2_msg)

                # remove user's match from potential matches
                all_matches.pop(cur_matched_user)
                user_index += 1
            else:
                # remove the match with the highest score to consider next highest score
                all_matches[user].remove((cur_matched_user, cur_max_score))
                continue

            # remove current user from potential matches
            all_matches.pop(user)




        # users = set()
        # for role in self.emotes_lst[0]:
        #     # print(role)
        #     lst = self.member_roles[role]
        #     # print(len(lst))
        #     while lst:
        #         if len(lst) < 2:
        #             break
        #         # user 1
        #         idx = random.randrange(0, len(lst))
        #         p1_id = lst.pop(idx)
        #         # user 2
        #         idx = random.randrange(0, len(lst))
        #         p2_id = lst.pop(idx)

        #         # if duplicates
        #         if p1_id in users or p2_id in users:
        #             continue
        #         else:
        #             users.add(p1_id)
        #             users.add(p2_id)
        #             user1 = self.bot.get_user(p1_id)
        #             user2 = self.bot.get_user(p2_id)

        #             user1_msg = discord.Embed(
        #                 title=USER_TITLE, description=USER_DESC.format(user=self.bot.get_user(p2_id)), color=COLOR)
        #             user2_msg = discord.Embed(
        #                 title=USER_TITLE, description=USER_DESC.format(user=self.bot.get_user(p1_id)), color=COLOR)

        #             await user1.send(embed=user1_msg)
        #             await user2.send(embed=user2_msg)

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

                    if user not in self.all_users:
                        self.all_user_id.append(user.id)

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

                    if len(user.roles) == 0:
                        self.all_user_id.remove(user.id)

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
