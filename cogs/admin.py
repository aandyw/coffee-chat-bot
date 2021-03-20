import discord
from discord.ext import commands
import cogs.category_emojis as emojis

CHANNEL_NAME = 'coffee-time'


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='coffee_time', aliases=['coffeetime', 'coffee'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def categories(self, ctx, *args):
        """Simple command that begins coffee time event"""

        guild = ctx.guild
        self.channel = discord.utils.get(
            guild.text_channels, name=CHANNEL_NAME)

        if self.channel is None:
            self.channel = await guild.create_text_channel(CHANNEL_NAME)

        response = "React with a category to be assigned categories as roles:\n"

        if len(args) > 0:
            for arg in args:
                response += emojis.category_emojis[arg] + ": " + arg + "\n"
        else:
            response += "No categories entered"

        await ctx.channel.send(response)

    @categories.error
    async def categories_error(self, error, ctx):
        if isinstance(error, commands.CheckFailure):
            await ctx.channel.send("You do not have permission to have ~coffee~")

    # @categories.Cog.listener()
    # async def on_reaction_add(self, reaction, user):
    #     role = discord.utils.get(
    #         user.server.roles, name=emojis.inv_category_emojis[reaction.emoji])
    #     await bot.client.add_roles(user, role)

    # async def on_match(self, user1, user2):
    # guide = ctx.message.guide
    # overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),
    #               guild.me: discord.PermissionOverwrite(read_messages=True)
    # }
    #     channel = await guide.create_text_channel('Coffee Chat', overwrites = overwrites)


def setup(bot):
    bot.add_cog(Admin(bot))
