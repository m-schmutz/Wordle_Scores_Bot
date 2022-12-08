#!./venv/bin/python3.10
from lib import *

def main() -> None:
    # initialize WordleBot
    bot = WordleBot(server_id)
    slash_cmd = bot.tree.command

    # slash command for submitting games
    @slash_cmd(description='Submit a screenshot of your Wordle game!', guild=bot.guild)
    async def submit(interaction: Interaction, image: Attachment) -> None:
        
        # try block is used to catch any unexpected exceptions that occur and log them
        try:
            # Grab date of submission and try to score the game. If the game
            # cannot be processed, reply with an error message and return.
            date = interaction.created_at.astimezone()
            game = bot.scoreGame(await image.read(), date, str(interaction.user))

            # if invalid game is given, game will be None
            # update log and send error message
            if not game:
                return await interaction.response.send_message(content='Image not recognized as valid Wordle game', ephemeral=True)


            # Submit scores to database. If the user has already submitted
            # today, then reply with an error message and return.
            baseStats, event_type = bot.submit_game(date, str(interaction.user), game) 

            # if the game submission failed
            # notify user
            if not baseStats:
                return await interaction.response.send_message(content=f'error occurred: {event_type}', ephemeral=True)

                
            # Reply to user's submission with stats.
            await interaction.response.send_message(
                file= await image.to_file(),
                embed= SubmissionEmbed(
                    date= date,
                    user= interaction.user,
                    attachment_filename= image.filename,
                    stats= baseStats))

            # send insult
            await interaction.followup.send(
                content= bot.getResponse(
                    solved= game.won,
                    numGuesses= game.numGuesses),
                ephemeral= True)


        # log un-handled exception
        except:
            print(f'caught it in run_bot line:52')
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


    @bot.event
    async def on_command_error(ctx, error):
        print(f'{ctx = }')
        print(f'{error = }')


    bot.run(bot_token)



if __name__ == '__main__':
    main()
