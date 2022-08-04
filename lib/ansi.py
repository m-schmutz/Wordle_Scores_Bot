def _esc(val) -> str:
    return f'\033[{val}'
CLEARLINE   = _esc('2K')
CURSOR_UP   = _esc('1A')
HIDE_CURSOR = _esc('?25l')
SHOW_CURSOR = _esc('?25h')

class ansi:
    def __init__(self, string:str = None) -> None:
        self._string = string
    def __repr__(self) -> str:
        return self._string
    def __str__(self) -> str:
        return self._string
    def __add__(self, other):
        self._string += other
        return self

class sgr(ansi):
    class fg:
        black,\
        red,\
        green,\
        yellow,\
        blue,\
        magenta,\
        cyan,\
        white = (_esc(f'3{i}m') for i in range(8))

        def rgb(r, g, b):
            return _esc(f'38;2;{r};{g};{b}m')
    class bg:
        black,\
        red,\
        green,\
        yellow,\
        blue,\
        magenta,\
        cyan,\
        white = (_esc(f'4{i}m') for i in range(8))

        def rgb(r, g, b):
            return _esc(f'48;2;{r};{g};{b}m')

    def __init__(self, string) -> None:
        super().__init__(string)
        self._reset,\
        self._bold,\
        self._faint,\
        self._italic,\
        self._underline = (_esc(f'{i}m') for i in range(5))

    # Update the underlying string
    def apply(self, sequence:str):
        self._string = sequence + self._string + self._reset
        return self

    # Font
    def bold(self):
        return self.apply(self._bold)
    def faint(self):
        return self.apply(self._faint)
    def italic(self):
        return self.apply(self._italic)
    def underline(self):
        return self.apply(self._underline)

    # Colors
    def black(self, bg=False):
        return self.apply(self.bg.black if bg else self.fg.black)
    def blue(self, bg=False):
        return self.apply(self.bg.blue if bg else self.fg.blue)
    def cyan(self, bg=False):
        return self.apply(self.bg.cyan if bg else self.fg.cyan)
    def green(self, bg=False):
        return self.apply(self.bg.green if bg else self.fg.green)
    def magenta(self, bg=False):
        return self.apply(self.bg.magenta if bg else self.fg.magenta)
    def red(self, bg=False):
        return self.apply(self.bg.red if bg else self.fg.red)
    def white(self, bg=False):
        return self.apply(self.bg.white if bg else self.fg.white)
    def yellow(self, bg=False):
        return self.apply(self.bg.yellow if bg else self.fg.yellow)
    def rgb(self, r=0, g=0, b=0, bg=False):
        return self.apply(self.bg.rgb(r, g, b) if bg else self.fg.rgb(r, g, b))

class cursor(ansi):
    def __init__(self) -> None:
        super().__init__(string='')

    def apply(self, sequence:str):
        self._string = _esc(sequence)
        return self

    def up(self, n:int = 1):
        return self.apply(f'{n}A')

    def down(self, n:int = 1):
        return self.apply(f'{n}B')

    def right(self, n:int = 1):
        return self.apply(f'{n}C')

    def left(self, n:int = 1):
        return self.apply(f'{n}D')



### Forwarding functions, for convenience ###
# SGR
def bold(string) -> ansi:
    return sgr(string).bold()
def faint(string) -> ansi:
    return sgr(string).faint()
def italic(string) -> ansi:
    return sgr(string).italic()
def underline(string) -> ansi:
    return sgr(string).underline()
def black(string, bg=False) -> ansi:
    return sgr(string).black(bg)
def blue(string, bg=False) -> ansi:
    return sgr(string).blue(bg)
def cyan(string, bg=False) -> ansi:
    return sgr(string).cyan(bg)
def green(string, bg=False) -> ansi:
    return sgr(string).green(bg)
def magenta(string, bg=False) -> ansi:
    return sgr(string).magenta(bg)
def red(string, bg=False) -> ansi:
    return sgr(string).red(bg)
def white(string, bg=False) -> ansi:
    return sgr(string).white(bg)
def yellow(string, bg=False) -> ansi:
    return sgr(string).yellow(bg)
def rgb(string, r=0, g=0, b=0, bg=False) -> ansi:
    return sgr(string).rgb(r,g,b,bg)

# Cursor
def cursor_up(string, end=False):
    return cursor(string)