from random import choice, randint
from discord import Intents, Object, Interaction, Attachment, ButtonStyle, app_commands
from discord.ui import Button, View
from discord.ext import commands

from chimp import ChimpView
from database import BotDatabase, DoubleSubmit
from wordle import SubmissionReply, UnidentifiableGame, _gameAnalyzer
from credentials import bot_token, server_id

class WordleBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix= '!',
            intents= Intents.all(),
            help_command= None)
        self.synced = False
        self.guild = Object(id=server_id)

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync(guild=self.guild)
            self.synced = True

        print(f'\'{self.user}\' logged in and ready!')

    def getResponse(self, solved: bool, numGuesses: int, *argeater) -> str:
        if solved:
            if numGuesses < 3:
                return choice(['damn that\'s crazy.. i have google too 🙄', 'suuuuuuuure\nyou just *knew* it right? 🤔'])
            
            if numGuesses < 5:
                return choice(['ok?', 'yea', 'cool', 'yep', 'that\'s definitely a game'])

            return choice([f'it actually took you {numGuesses} guess{"es" if numGuesses > 1 else ""}. lmao.', 'garbage'])
        return choice(['you suck!', 'better luck next time idiot'])



def main() -> None:
    ga = _gameAnalyzer()
    db = BotDatabase(db_path='./lib/stats.db')
    bot = WordleBot()

    ### Discord Bot Application Commands
    @bot.tree.command(name= 'submit',
        description= 'Submit a screenshot of your Wordle game!',
        guild= bot.guild)
    async def _(interaction: Interaction, image: Attachment):
        # Shhhhhhhhhhhh we'll get there, Discord...
        await interaction.response.defer()
        date = interaction.created_at.astimezone().date()

        # Find the game and score it
        try:
            results = ga.scoreGame(await image.read(), date)
        except UnidentifiableGame as e:
            await interaction.followup.send(content=e.message, ephemeral=True)
            return

        # Submit to database
        try:
            stats = db.submit_data(str(interaction.user), date, *results)
        except DoubleSubmit as e:
            await interaction.followup.send(content=e.message, ephemeral=True)
            return

        # Reply with stats
        await interaction.followup.send(
            embed= SubmissionReply(
                username= interaction.user.name,
                stats= stats),
            file= await image.to_file(spoiler=True))

        await interaction.followup.send(
            content= bot.getResponse(*results),
            ephemeral= True)

    @bot.tree.command(name= 'chimp',
        description= 'Are you smarter than a chimp? Play this quick memorization game to find out!',
        guild= bot.guild)
    async def _(interaction: Interaction):
        chimp = ChimpView()
        await interaction.response.send_message(view=chimp)

    @bot.tree.command(name= 'link',
        description= 'Get the link to the Wordle webpage.',
        guild= bot.guild)
    async def _(interaction: Interaction):
        await interaction.response.send_message(
            view= View(timeout=0).add_item(
                Button(
                    label= 'Play Wordle',
                    style= ButtonStyle.link,
                    url= 'https://www.nytimes.com/games/wordle/index.html')),
            ephemeral= True)

    @bot.tree.command(name='roll',
        description= 'Roll an N-sided die!',
        guild= bot.guild)
    async def _(interaction: Interaction, faces: app_commands.Range[int, 2, None]):
        await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

    bot.run(bot_token)

if __name__ == '__main__':
    main()
