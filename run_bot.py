#!./venv/bin/python3.10
from lib import *

async def _submit(bot:WordleBot, image:Attachment, interaction: Interaction) -> None:
    
    # Grab date of submission and try to score the game. If the game
    # cannot be processed, reply with an error message and return.
    date = interaction.created_at.astimezone().date()
    game = bot.scoreGame(await image.read(), date)
    

    # Submit scores to database. If the user has already submit
    # today, then reply with an error message and return.
    baseStats, status = bot.db.submit_data(
        username= str(interaction.user),
        dtime= date,
        win= game.won,
        guesses= game.numGuesses,
        greens= game.uniqueCorrect,
        yellows= game.uniqueMisplaced,
        uniques= game.uniqueAll)
        
    
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

    return








def main() -> None:
    bot = WordleBot(server_id)
    slash_cmd = bot.tree.command

    @slash_cmd(description='Submit a screenshot of your Wordle game!', guild=bot.guild)
    async def submit(interaction: Interaction, image: Attachment) -> None:
        try:
            _submit(bot, image, interaction)

        except InvalidGame as e:
            # update log about invalid game
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        except DoubleSubmit as e:
            # update log about double submit
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        except:
            exc_type, _, exc_traceback = exc_info()

        

    @slash_cmd(description='Get the link to the Wordle webpage.', guild=bot.guild)
    async def link(interaction: Interaction) -> None:
        try:
            # update log about double submit
            await interaction.response.send_message(view= LinkView(), ephemeral= True)

        except:
            
            return

    @slash_cmd(description='Roll an N-sided die!', guild=bot.guild)
    async def roll(interaction: Interaction, faces: app_commands.Range[int, 2, None]) -> None:
        try:
            # update log about double submit
            await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

        except:
            exc_type, _, exc_traceback = exc_info()
            return
    bot.run(bot_token)



if __name__ == '__main__':
    main()
    