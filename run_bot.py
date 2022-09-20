#!./venv/bin/python3.10
from lib import *

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
            # update log about invalid game
            update_log('invalid', user=str(interaction.user))
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        except:
            exc_type, _, exc_traceback = exc_info()
            update_log('exception', exc_name=exc_type.__name__, exc_tb=exc_traceback)
            return

        # Submit scores to database. If the user has already submit
        # today, then reply with an error message and return.
        try:
            baseStats, status = bot.db.submit_data(
                username= str(interaction.user),
                dtime= date,
                win= game.won,
                guesses= game.numGuesses,
                greens= game.uniqueCorrect,
                yellows= game.uniqueMisplaced,
                uniques= game.uniqueAll)

            # update log
            update_log(status, user=str(interaction.user))
            
        except DoubleSubmit as e:
            # update log about double submit
            update_log('doublesub', user=str(interaction.user))
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        except:
            exc_type, _, exc_traceback = exc_info()
            update_log('exception', exc_name=exc_type.__name__, exc_tb=exc_traceback)
            return

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
        try:
            # update log about double submit
            update_log('link', user=str(interaction.user))
            await interaction.response.send_message(view= LinkView(), ephemeral= True)

        except:
            exc_type, _, exc_traceback = exc_info()
            update_log('exception', exc_name=exc_type.__name__, exc_tb=exc_traceback)
            return

    @slash_cmd(description='Roll an N-sided die!', guild=bot.guild)
    async def roll(interaction: Interaction, faces: app_commands.Range[int, 2, None]) -> None:
        try:
            # update log about double submit
            update_log('dieroll', user=str(interaction.user))
            await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

        except:
            exc_type, _, exc_traceback = exc_info()
            update_log('exception', exc_name=exc_type.__name__, exc_tb=exc_traceback)
            return

    update_log('startup')
    bot.run(bot_token)



if __name__ == '__main__':
    register(update_log, 'shutdown')
    main()
    