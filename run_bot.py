#!./venv/bin/python3.10
from lib import *

async def _submit(bot:WordleBot, image:Attachment, interaction: Interaction) -> None:
    
    # Grab date of submission and try to score the game. If the game
    # cannot be processed, reply with an error message and return.
    date = interaction.created_at.astimezone().date()
    game = bot.scoreGame(await image.read(), date)
    

    # Submit scores to database. If the user has already submit
    # today, then reply with an error message and return.
    baseStats = bot.submit_game(date, str(interaction.user), game) 
        
        
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


def main() -> None:

    # initialize WordleBot
    bot = WordleBot(server_id)
    slash_cmd = bot.tree.command

    # command to submit a game
    @slash_cmd(description='Submit a screenshot of your Wordle game!', guild=bot.guild)
    async def submit(interaction: Interaction, image: Attachment) -> None:

        # get exact time of command and the user 
        user = str(interaction.user)
        dtime = datetime.now()

        try:
            # try to submit game
            # update the database and return the event type
            await _submit(bot, image, interaction)

        # otherwise invalid game, update user
        except InvalidGame as e:
            return await interaction.response.send_message(content=e.message, ephemeral=True)


        # log DoubleSubmit
        except DoubleSubmit as e:
            return await interaction.response.send_message(content=e.message, ephemeral=True)

        # log un-handled exception
        except:
            exc_type, _, exc_traceback = exc_info()
    
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

        # log un-handled exception
        except:
            exc_type, _, exc_traceback = exc_info()

    @slash_cmd(description='Roll an N-sided die!', guild=bot.guild)
    async def roll(interaction: Interaction, faces: app_commands.Range[int, 2, None]) -> None:
        
        # get exact time of command and the user 
        user = str(interaction.user)
        dtime = datetime.now()
        
        try:
            # give user die roll and update the log
            await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

        except:
            exc_type, _, exc_traceback = exc_info()

    bot.run(bot_token)



if __name__ == '__main__':
    main()
