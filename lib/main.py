from random import randint
from discord import Interaction, Attachment, app_commands
from wordle import SubmissionEmbed, InvalidGame, WordleBot, DoubleSubmit, LinkView
from credentials import bot_token, server_id

def main() -> None:
    bot = WordleBot(server_id)
    slash_cmd = bot.tree.command

    @slash_cmd(description='Submit a screenshot of your Wordle game!', guild=bot.guild)
    async def submit(interaction: Interaction, image: Attachment) -> None:

        # Grab date of submission and try to score the game. If the game
        # cannot be processed, reply with an error message and return.
        date = interaction.created_at.astimezone().date()
        try:
            game = bot.scoreGame(await image.read(), date)
        except InvalidGame as e:
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        # Submit scores to database. If the user has already submit
        # today, then reply with an error message and return.
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
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        # Reply to user's submission with stats.
        await interaction.response.send_message(
            embed= SubmissionEmbed(
                username= interaction.user.name,
                stats= baseStats),
            file= await image.to_file(spoiler=True))

        await interaction.followup.send(
            content= bot.getResponse(
                solved= game.won,
                numGuesses= game.numGuesses),
            ephemeral= True)

    @slash_cmd(description='Get the link to the Wordle webpage.', guild=bot.guild)
    async def link(interaction: Interaction) -> None:
        await interaction.response.send_message(view= LinkView(), ephemeral= True)

    @slash_cmd(description='Roll an N-sided die!', guild=bot.guild)
    async def roll(interaction: Interaction, faces: app_commands.Range[int, 2, None]) -> None:
        await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

    bot.run(bot_token)

if __name__ == '__main__':
    main()
