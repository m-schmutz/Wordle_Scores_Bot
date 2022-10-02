#!./venv/bin/python3.10
from lib import *

async def _submit(bot:WordleBot, image:Attachment, interaction: Interaction) -> str:
    
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
        file= await image.to_file(),
        embed= SubmissionEmbed(
            date= date,
            user= interaction.user,
            attachment_filename= image.filename,
            stats= baseStats))

    await interaction.followup.send(
        content= bot.getResponse(
            solved= game.won,
            numGuesses= game.numGuesses),
        ephemeral= True)

    # return the event (submit, new)
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

        # get exact time of command and the user 
        user = str(interaction.user)
        dtime = datetime.now()

        try:
            # try to submit game
            # update the database and return the event type
            event = await _submit(bot, image, interaction)

            # check if the user is new
            if event == 'new':
                log.update(dtime, user, event, f'{user} added as new user')
                event = 'submit'

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
            log.update(dtime, user, 'doublesub', f'{user} attempted double submit')
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        # log un-handled exception
        except:
            exc_type, _, exc_traceback = exc_info()
            log.update(dtime, user, 'exception', f'{exc_type.__name__} raised', traceback=exc_traceback)
    
    # command to get wordle link
    @slash_cmd(description='Get the link to the Wordle webpage.', guild=bot.guild)
    async def link(interaction: Interaction) -> None:
        
        # get exact time of command and the user 
        user = str(interaction.user)
        dtime = datetime.now()

        try:
            # try to print link
            # update log about double submit
            await interaction.response.send_message(view= LinkView(), ephemeral= True)
            log.update(dtime, user, 'link', f'{user} requested link')

        # log un-handled exception
        except:
            exc_type, _, exc_traceback = exc_info()
            log.update(dtime, user, 'exception', f'{exc_type.__name__} raised', traceback=exc_traceback)

    @slash_cmd(description='Roll an N-sided die!', guild=bot.guild)
    async def roll(interaction: Interaction, faces: app_commands.Range[int, 2, None]) -> None:
        
        # get exact time of command and the user 
        user = str(interaction.user)
        dtime = datetime.now()
        
        try:
            # give user die roll and update the log
            await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')
            log.update(dtime, user, 'rolldie', f'{user} requested die roll')

        except:
            exc_type, _, exc_traceback = exc_info()
            log.update(dtime, user, 'exception', f'{exc_type.__name__} raised', traceback=exc_traceback)

    # update log about start up
    log.update(datetime.now(), 'WordleBot', 'su/sd', 'WordleBot Starting up')
    bot.run(bot_token)



if __name__ == '__main__':
    main()
