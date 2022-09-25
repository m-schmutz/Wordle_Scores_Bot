#!./venv/bin/python3.10
from lib import *

async def _submit(bot:WordleBot, image:Attachment, interaction: Interaction) -> None:
    
    # Grab date of submission and try to score the game. If the game
    # cannot be processed, reply with an error message and return.
    date = interaction.created_at.astimezone().date()
    game = bot.scoreGame(await image.read(), date)
    

    # Submit scores to database. If the user has already submit
    # today, then reply with an error message and return.
    baseStats, event = bot.db.submit_data(
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

    return event

def main() -> None:

    # initialize WordleBot
    bot = WordleBot(server_id)
    slash_cmd = bot.tree.command

    # initialize log
    log = LogUpdate()

    # command to submit a game
    @slash_cmd(description='Submit a screenshot of your Wordle game!', guild=bot.guild)
    async def submit(interaction: Interaction, image: Attachment) -> None:

        user = str(interaction.user)
        dtime = datetime.now()
        # try to submit game
        try:
            # update the database and return the event type
            event = _submit(bot, image, interaction)
            dtime
            # check if the user is new
            if event == 'new':
                log.update(dtime, user, event, f'{user} added as new user')

            # log submitted game
            log.update(dtime, user, event, f'{user} submitted game')

        # log InvalidGame
        except InvalidGame as e:
            # update log about invalid game
            log.update(dtime, user, 'invalid', f'{user} submitted invalid game')
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        # log DoubleSubmit
        except DoubleSubmit as e:
            # update log about double submit
            # log submitted game
            log.update(dtime, user, 'doublesub', f'{user} attempted double submit')
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        # log un-handled exception
        except:
            exc_type, _, exc_traceback = exc_info()
            log.update(dtime, user, 'exception', f'{exc_type.__name__} raised', traceback=exc_traceback)

        
    # command to get wordle link
    @slash_cmd(description='Get the link to the Wordle webpage.', guild=bot.guild)
    async def link(interaction: Interaction) -> None:
        # try to print link
        try:
            # update log about double submit
            await interaction.response.send_message(view= LinkView(), ephemeral= True)

        # log un-handled exception
        except:
            exc_type, _, exc_traceback = exc_info()
            log.update(datetime.now(), str(interaction.user), 'exception', f'{exc_type.__name__} raised', traceback=exc_traceback)

    @slash_cmd(description='Roll an N-sided die!', guild=bot.guild)
    async def roll(interaction: Interaction, faces: app_commands.Range[int, 2, None]) -> None:
        try:
            # update log about double submit
            await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

        except:
            exc_type, _, exc_traceback = exc_info()
            log.update(datetime.now(), str(interaction.user), 'exception', f'{exc_type.__name__} raised', traceback=exc_traceback)


    bot.run(bot_token)



if __name__ == '__main__':
    main()
    