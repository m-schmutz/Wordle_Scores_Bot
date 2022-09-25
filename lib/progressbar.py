import ansi

class ProgressBar:
    def __init__(self, total:float=100, width:int=64, fill_char:str='#', empty_char:str='-', left:str='[',
        right:str=']', show_percent:bool=True, percent_precision:int=2, colored:bool=False,
        title:str='Loading...', titleoncomplete:str='Done!') -> None:
        
        assert total > 0, "Total must be positive!"

        self._total             = total
        self._progress          = 0
        self._progressbar       = '!!! PROGRESS BAR NOT BUILT !!!'
        self._width             = width
        self._fill_char         = fill_char
        self._empty_char        = empty_char
        self._left              = left
        self._right             = right
        self._show_percent      = show_percent
        self._percent_precision = percent_precision
        self._colored           = colored
        self._title             = title
        self._titleoncomplete   = titleoncomplete
        self.style(
            width=width,
            fill_char=fill_char,
            empty_char=empty_char,
            left=left,
            right=right,
            show_percent=show_percent,
            percent_precision=percent_precision,
            colored=colored,
            title=title)

    def style(self, width:int=None, fill_char:str=None, empty_char:str=None, left:str=None, right:str=None,
        show_percent:bool=None, percent_precision:int=None, colored:bool=None, title:str=None) -> None:

        if width:
            assert type(width) == int, '\'width\' must be an integer!'
            assert width > 0, '\'width\' must be positive!'
            self._width = width

        if fill_char:
            assert type(fill_char) == str, '\'fill_char\' must be a string!'
            assert len(fill_char) == 1, '\'fill_char\' must be a single character!'
            self._fill_char = fill_char
        
        if empty_char:
            assert type(empty_char) == str, '\'empty_char\' must be a string!'
            assert len(empty_char) == 1, '\'empty_char\' must be a single character!'
            self._empty_char = empty_char
        
        if left:
            assert type(left) == str, '\'left\' must be a string!'
            self._left = left
        
        if right:
            assert type(right) == str, '\'right\' must be a string!'
            self._right = right
        
        if show_percent:
            assert type(show_percent) == bool, '\'show_percent\' must be a boolean!'
            self._show_percent = show_percent
        
        if percent_precision:
            assert type(percent_precision) == int, '\'precision\' must be an integer!'
            self._precision = percent_precision
        
        if colored:
            assert type(colored) == bool, '\'colored\' must be a boolean!'
            self._colored = colored
        
        if title:
            assert type(title) == str, '\'title\' must be a string!'
            self._title = title

        return

    def _build(self) -> None:
        # Calculate the current percentage.
        percent = self._progress / float(self._total)
        
        # Build the inner bar section.
        fill_count = int(percent * self._width)
        inner = (self._fill_char * fill_count) + (self._empty_char * (self._width - fill_count))
        # [OPTIONAL] Color red-to-green based on percentage
        if self._colored:
            # For first half, raise G value from 0 to 255
            if percent < 0.5:
                r = 255
                g = int(255 * percent * 2)
            # For second half, lower R value from 255 to 0
            else:
                r = 255 - int(255 * (percent - 0.5) * 2)
                g = 255

            inner = ansi.ansi(inner).rgb(r, g)

        # Construct the entire progress bar
        self._progressbar = ansi.ansi.HIDE_CURSOR \
            + '\r' + ansi.ansi.CURSOR_UP + ansi.ansi.CLEARLINE + (self._titleoncomplete if percent == 1.00 else self._title) + '\n'\
            + '\r' + ansi.ansi.CLEARLINE + self._left + inner + self._right\
                + (f' {round(100 * percent, self._precision)}%' if self._show_percent else '')\
                + (ansi.ansi.SHOW_CURSOR + '\r\n' if percent == 1.00 else '')

        return

    def update(self, progress, title=None) -> None:
        assert progress >= 0, "Progress must be non-negative!"
        assert progress <= self._total, "Progress cannot exceed the Total!"

        # Make room for the progress bar if this is the first time it's printed.
        if self._progress == 0:
            print()

        # Update the title if a new title is given.
        if title:
            self._title = title

        # Update progress and build.
        self._progress = progress
        self._build()

        print(self._progressbar, end='')
        return

# import time
# pb = ProgressBar(total=497, left='', right='', fill_char='█', empty_char='░')
# for i in range(1, pb._total + 1):
#     time.sleep(3 / pb._total)
#     title = 'some text!' if i < pb._total // 2 else 'alternate text\n\r!'.replace('\n', '').replace('\r', '')
#     pb.update(i, title)
# print('Done!')