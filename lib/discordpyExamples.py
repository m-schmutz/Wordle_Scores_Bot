#region Views/Modals
class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value
    # to `True` and stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Confirming", ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`.
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Cancelling", ephemeral=True)
        self.value = False
        self.stop()

# Shows an example of modals being invoked from an interaction
# component (e.g. a button or select menu)
@bot.command(name='modaltest')
async def modaltest(ctx: commands.Context):
    class MyView(discord.ui.View):
        @discord.ui.button(label="Modal Test", style=discord.ButtonStyle.primary)
        async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = MyModal(title="Modal Triggered from Button")
            await interaction.response.send_modal(modal)

        @discord.ui.select(
            placeholder="Pick Your Modal",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="First Modal", description="Shows the first modal"),
                discord.SelectOption(label="Second Modal", description="Shows the second modal")])

        async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
            modal = MyModal(title="Temporary Title")
            modal.title = select.values[0]
            await interaction.response.send_modal(modal)

    await ctx.send("Click Button, Receive Modal", view=MyView())
    return

class WordleGuessModal(discord.ui.Modal):
    def __init__(self, title='Default Title') -> None:
        super().__init__(title)
        self.add_item(
            discord.ui.InputText(
                label='Guess',
                placeholder='Enter a word',
                min_length=5,
                max_length=5))

    async def callback(self, interaction:discord.Interaction):
        embed = discord.Embed(title='Your Response', color=discord.Color.random())
        embed.add_field(name='Your guess', value=self.children[0].value, inline=False)
        await interaction.response.send_message(embeds=[embed])

class WordleGuessView(discord.ui.View):
    @discord.ui.button(label='Click to Guess', style=discord.ButtonStyle.primary)
    async def button_callback(self, button:discord.ui.Button, interaction:discord.Interaction):
        modal = WordleGuessModal(title='Wordle Guess Form')
        await interaction.response.send_modal(modal)
#endregion

#region Registering Application Commands within the Bot's class

# Example 1:
# via self.tree.add_command() with own member function/coroutine
class WordleBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix = '!',
            intents = discord.Intents.all())
        self.synced = False
        self.guild = discord.Object(id=server_id)
        self.tree.add_command(
            discord.app_commands.Command(
                name = 'link',
                description = 'asdf',
                callback = self._link),
            guild = self.guild)

    async def _link(self, interaction:discord.Interaction):
        return await interaction.response.send_message(
            view = WorldeLinkView(),
            ephemeral = True)

# Example 2:
# via CommandTree.command decorator with anonymous coroutine
class WordleBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix = '!',
            intents = discord.Intents.all())
        self.synced = False
        self.guild = discord.Object(id=server_id)

        @discord.app_commands.CommandTree.command(
            self = self.tree,
            name = 'link',
            description = 'Get the link to the Wordle webpage.',
            guild = self.guild)
        async def _(interaction:discord.Interaction):
            return await interaction.response.send_message(
                view = WorldeLinkView(),
                ephemeral = True)
#endregion

#region Help command
@bot.group(invoke_without_command = True) # for this main command (.help)
async def help(ctx):
    await ctx.send("Help! Categories : Moderation, Utils, Fun")

@help.command()   #For this command (.help Moderation)
async def Moderation(ctx):
    await ctx.send("Moderation commands : kick, ban, mute, unban")

@help.command()   #And for this command (.help Utils)
async def Uitls(ctx):
    await ctx.send("Utils : ping, prefix")

@help.command()   #And lastly this command (.help Fun)
async def Fun(ctx): 
    await ctx.send("Fun : 8ball, poll, headsortails")
#endregion