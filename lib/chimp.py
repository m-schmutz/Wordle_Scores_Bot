from typing import Union, Callable, Any
import discord
import random

class ChimpButton(discord.ui.Button):
    def __init__(self, callback: Callable[[discord.Interaction], None], custom_id: str, sequence_num: Union[int, None]):
        if sequence_num == None:
            _label_     = ' '
            _disabled_  = True
        else:
            _label_     = sequence_num
            _disabled_  = False

        super().__init__(
            style = discord.ButtonStyle.primary,
            custom_id = custom_id,
            disabled = _disabled_,
            label = _label_)
        self.sequence_num = sequence_num
        self.callback = callback

class ChimpView(discord.ui.View):
    def __init__(self, length: int = 6, board_size: int = 25) -> None:
        super().__init__()
        self._button_id_delimeter: str = '-'
        self.board_size: int = board_size
        self.length: int = length
        self.order: list[int] = []
        # Declaring the type allows the interpreter to infer information. This is left
        # uninitialized because the discord package disallows setting this attribute.
        self.children: list[ChimpButton]

    def _genCustomId(self, index: int) -> str:
        return f'button{self._button_id_delimeter}{index}'

    def _getCustomIdFromInteraction(self, interaction: discord.Interaction) -> int:
        custom_id: str = interaction.data['custom_id']
        index: str = custom_id.split(self._button_id_delimeter)[1]
        return int(index)

    # Determines the next course of action based on a user's button press.
    def _processButtonPress(self, interaction: discord.Interaction) -> None:
        # Did the user press the next button in order?
        buttonIndex = self._getCustomIdFromInteraction(interaction)

        # Yes!
        if buttonIndex == self.order[0]:
            # Is this the first button?
            # Yes!
            if len(self.order) == self.length:
                self.order = self.order[1:]
                for i in self.order:
                    self.children[i].label = ' '

            # No!
            else:
                # Update our order list and change the label of the corresponding
                # button to dispaly it's sequential number.
                self.order = self.order[1:]
                self.children[buttonIndex].label = str(self.length-len(self.order))

                # if no more buttons to press, user has won
                if not self.order:
                    print('WIN DETECTED')

        # No!
        else: print('LOSS DETECTED')


    async def buttonCallback(self, interaction: discord.Interaction) -> None:
        self._processButtonPress(interaction)
        await interaction.response.edit_message(content='', view=self)

    # Generates 
    def randomizeBoard(self) -> None:
        # generate the board layout
        self.order = []
        for _ in range(self.length):
            while True:
                randIndex = random.randrange(self.board_size)
                if randIndex not in self.order: break
            self.order.append(randIndex)

        # generate the buttons and add them
        for i in range(self.board_size):
            self.add_item(
                ChimpButton(
                    callback = self.buttonCallback,
                    custom_id = self._genCustomId(i),
                    sequence_num = (self.order.index(i) + 1) if (i in self.order) else (None) ))
