from random import randint
from credentials import bot_token, server_id
from discord import Interaction, Attachment, ButtonStyle, app_commands
from discord.ui import Button, View
from chimp import ChimpView
from database import DoubleSubmit
from wordle import SubmissionReply, UnidentifiableGame, WordleBot

def main() -> None:
    bot = WordleBot(server_id)

    ### Discord Bot Application Commands
    @bot.tree.command(name='submit',
        description= 'Submit a screenshot of your Wordle game!',
        guild= bot.guild)
    async def _(interaction: Interaction, image: Attachment):

        # Grab date of submission.
        date = interaction.created_at.astimezone().date()

        # Attempt to score the game.
        # If it cannot be scored, reply accordingly.
        try:
            game = bot.scoreGame(await image.read(), date)
        except UnidentifiableGame as e:
            await interaction.response.send_message(content=e.message, ephemeral=True)
            return

        # Attempt to submit scores to database.
        # If the user has already submit today's game, reply accordingly.
        try:
            baseStats = bot.db.submit_data(
                username= str(interaction.user),
                dtime= date,
                win= game.won,
                guesses= game.numGuesses,
                greens= game.uniqueCorrect,
                yellows= game.uniqueMisplaced,
                uniques= game.uniqueAll)
        except DoubleSubmit as e:
            await interaction.response.send_message(content=e.message, ephemeral=True)
            return

        # Reply with stats
        await interaction.response.send_message(
            embed= SubmissionReply(
                username= interaction.user.name,
                stats= baseStats),
            file= await image.to_file(spoiler=True))

        await interaction.followup.send(
            content= bot.getResponse(
                solved= game.won,
                numGuesses= game.numGuesses),
            ephemeral= True)

    @bot.tree.command(name='chimp',
        description= 'Are you smarter than a chimp? Play this quick memorization game to find out!',
        guild= bot.guild)
    async def _(interaction: Interaction):
        chimp = ChimpView()
        await interaction.response.send_message(view=chimp)

    @bot.tree.command(name='link',
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

    ### Start the bot
    bot.run(bot_token)

if __name__ == '__main__':
    main()
