import discord
from typing import Callable, Optional

class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, getPage: Callable):
        """
        Constructor for paginator to set display the leaderboard

        Arguments:
        interaction - the command to be responded to
        getPage - get the page to be displayed
        """
        self.interaction = interaction
        self.getPage = getPage
        self.totalPages: Optional[int] = None
        self.index = 1
        super().__init__(timeout = 5)

    async def navigate(self):
        """
        Send embed as message and add buttons if multiple pages
        """
        emb, self.totalPages = await self.getPage(self.index)
        if self.totalPages == 1:
            await self.interaction.response.send_message(embed=emb)
        elif self.totalPages > 1:
            self.update_buttons()
            await self.interaction.response.send_message(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        """
        Edit the message by changing to a different page

        Arguments:
        interaction - the command that the embed is a response to
        """
        emb, self.totalPages = await self.getPage(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        """
        Disabled buttons if on first or last page
        """
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == self.totalPages

    @discord.ui.button(label = "<", style= discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        """
        Go to the previous page

        Arguments:
        label - the text to be displayed on button
        style = color and style of the button
        """
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(label = ">", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        """
        Go to the next page

        Arguments:
        label - the text to be displayed on button
        style = color and style of the button
        """
        self.index += 1
        await self.edit_page(interaction)

    async def on_timeout(self):
        """
        Remove buttons after an amount of time specified in the constructor
        """
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    def getPageCount(totalResults: int, resultsPerPage: int):
        """
        Get the number of pages needed to display all the results
        
        Arguments
        totalResults - total number of results to display
        resultsPerPage - the number of results to be displayed per page
        """
        return int(((totalResults - 1) // resultsPerPage) + 1)

