from dis import disco
from typing import Union, Callable
import discord
import random

class ChimpButton(discord.ui.Button):
    def __init__(self, callback: Callable[[discord.Interaction], None], custom_id: str, sequence_num: Union[int, None]):
        if sequence_num == None:
            _label_    = ' '
            _disabled_ = True
        else:
            _label_    = sequence_num
            _disabled_ = False
        super().__init__(
            style     = discord.ButtonStyle.primary,
            custom_id = custom_id,
            disabled  = _disabled_,
            label     = _label_)
        self.sequence_num = sequence_num
        self.callback     = callback

class ChimpView(discord.ui.View):
    def __init__(self, length: int = 6, board_size: int = 25) -> None:
        super().__init__()
        self.board_size: int  = board_size
        self.length: int      = length
        self.order: list[int] = []
        self.won = False
        self.lost = False
        # Declaring the type allows the interpreter to infer information. This is left
        # uninitialized because the discord package disallows setting this attribute.
        self.children: list[ChimpButton]

    # Determines the next course of action based on a user's button press.
    def _processButtonPress(self, interaction: discord.Interaction) -> None:
        button_index = int(interaction.data['custom_id'].split('-')[1])

        ### Did the user press the button in order?
        # Yes!
        if button_index == self.order[0]:
            self.order = self.order[1:]

            ### Is this the first button?
            # Yes!
            if self.children[button_index].label == 1:
                for i in self.order:
                    self.children[i].label = ' '
            # No!
            else:
                # Change the label of the corresponding button to dispaly it's sequential number.
                self.children[button_index].label = self.children[button_index].sequence_num

                # If no more buttons to press, user has won.
                if not self.order:
                    self.won = True
                    for button in self.children:
                        button.disabled = True
                        if button.sequence_num != None:
                            button.style = discord.ButtonStyle.success
        # No!
        else:
            self.lost = True
            self.children[button_index].style = discord.ButtonStyle.red
            self.children[button_index].label = self.children[button_index].sequence_num
            self.order.remove(button_index)
            for i, button in enumerate(self.children):
                button.disabled = True
                if i in self.order:
                    button.label = button.sequence_num
                    button.style = discord.ButtonStyle.secondary

    async def buttonCallback(self, interaction: discord.Interaction) -> None:
        self._processButtonPress(interaction)
        if self.lost:
            self.stop()
            await interaction.response.edit_message(content='YOU LOST', view=self)
        elif self.won:
            self.stop()
            await interaction.response.edit_message(content='YOU WON', view=self)
        else:
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
                    callback     = self.buttonCallback,
                    custom_id    = f'button-{i}',
                    sequence_num = (self.order.index(i) + 1) if (i in self.order) else (None) ))
