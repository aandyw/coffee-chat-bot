import discord
from discord.ext import commands

import asyncio
import emoji
import functools
import operator
from datetime import datetime

CHANNEL_NAME = 'coffee-time'
category_emoji = {}
inv_category_emoji = {v: k for k, v in category_emoji.items()}


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None  # the CHANNEL_NAME to send shit to
        self.event_msg = None  # event object message

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
            title="Title", description="Enter the title for your coffee time event\nMax 200 characters", color=0x00ff00)

        # description
        embed_desc = discord.Embed(
            title="Description", description="Enter the description for your coffee time event\nMax 1000 characters", color=0x00ff00)

        # event start time
        embed_start = discord.Embed(
            title="Start time", description="Enter a starting time", color=0x00ff00)

        embed_cats = discord.Embed(
            title="Categories", description="Enter the categories that you wish to have", color=0x00ff00)

        embed_emotes = discord.Embed(
            title="Emotes", description="Enter the emotes to be associated with the above categories", color=0x00ff00)

        ### MESSAGE VERFICATIONS ###
        def check_title(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and len(msg.content) <= 200

        def check_desc(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and len(msg.content) <= 1000

        # def check_time(msg):
        #     return msg.author == ctx.author and msg.channel == ctx.channel and len(msg.content) <= 1000

        def check_cats(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and len(msg.content) <= 1000

        await ctx.channel.send(embed=embed_title)

        try:
            # 30 seconds to reply
            title = await self.bot.wait_for("message", check=check_title, timeout=30)

            if (len(title.content) > 200):  # if over message limit
                await ctx.channel.send("Oops, the title you entered is too long.")

            await ctx.channel.send(embed=embed_desc)
            desc = await self.bot.wait_for("message", check=check_desc, timeout=30)

            if (len(desc.content) > 1000):  # if over message limit
                await ctx.channel.send("Oops, the description you entered is too long.")

            # await ctx.channel.send(embed=embed_start)
            # event_time = await self.bot.wait_for("message", check=check_cats, timeout=30)
            # year = event_time[0, 4]
            # month = event_time[4, 6]
            # day = event_time[6, 8]
            # event_time = datetime.datetime()

            await ctx.channel.send(embed=embed_cats)
            cats = await self.bot.wait_for("message", check=check_cats, timeout=30)

            await ctx.channel.send(embed=embed_emotes)
            emotes = await self.bot.wait_for("message", check=check_cats, timeout=30)

            # check categories and emotes ....
            emotes_lst = await asyncio.gather(self.split_emotes(emotes.content))
            cats_msg_content = await asyncio.gather(
                self.format_cats_emotes(cats.content, emotes_lst[0]))
            response = desc.content + "\nReact to the categories you are interested in!\n"
            embed_msg = discord.Embed(
                title=title.content, description=response, color=0x00ff00)
            # event time and given categories
            embed_msg.add_field(name="Time", value="test", inline=False)
            embed_msg.add_field(name="Categories",
                                value=cats_msg_content[0], inline=False)
            # add footer with information about how created event at what time
            embed_msg.set_footer(text="Created by {author}\n{time}".format(
                author=ctx.author.name, time=datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

            # send message to CHANNEL_NAME
            self.event_msg = await self.channel.send(embed=embed_msg)

            # event reactions
            await asyncio.gather(self.event_reactions(self.event_msg, emotes_lst[0]))

        except asyncio.TimeoutError:
            await ctx.send("Sorry, you didn't reply in time!")

    @ categories.error
    async def categories_error(self, error, ctx):
        if isinstance(error, commands.CheckFailure):
            await ctx.channel.send("You do not have permission to have ~coffee~")

    async def split_emotes(self, emotes):
        """  """
        emotes_lst = emoji.get_emoji_regexp().split(emotes)
        em_split_whitespace = [substr.split() for substr in emotes_lst]
        em_split = functools.reduce(operator.concat, em_split_whitespace)
        return em_split

    async def format_cats_emotes(self, categories, emotes_lst):
        """ Function to create a formated string containing categories and emotes """
        categories_lst = categories.split()
        msg_content = ""

        for cat, emote in zip(categories_lst, emotes_lst):
            msg_content += "[{emote}] {cat}\n".format(emote=emote, cat=cat)

        return msg_content

    async def event_reactions(self, event_msg, emotes_lst):
        """ Function to add reactions to the event message """
        for emote in emotes_lst:
            await event_msg.add_reaction(emote)

    @ commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction, user):
        inv_category_emoji = {v: k for k, v in category_emoji.items()}

        role = discord.utils.get(
            user.server.roles, name=inv_category_emoji[reaction.emoji])
        await bot.client.add_roles(user, role)


def setup(bot):
    bot.add_cog(Admin(bot))
