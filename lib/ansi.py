def _esc(val):
    return f'\033[{val}'

class ansi:

    CLEARLINE   = _esc('2K')
    CURSOR_UP   = _esc('1A')
    HIDE_CURSOR = _esc('?25l')
    SHOW_CURSOR = _esc('?25h')

    _reset      = _esc('0m')
    _bold       = _esc('1m')
    _italic     = _esc('3m')
    _underline  = _esc('4m')

    class fg:
        black   = _esc('30m')
        red     = _esc('31m')
        green   = _esc('32m')
        yellow  = _esc('33m')
        blue    = _esc('34m')
        magenta = _esc('35m')
        cyan    = _esc('36m')
        white   = _esc('37m')

        def rgb(r, g, b):
            return _esc(f'38;2;{r};{g};{b}m')

    class bg:
        black   = _esc('40m')
        red     = _esc('41m')
        green   = _esc('42m')
        yellow  = _esc('43m')
        blue    = _esc('44m')
        magenta = _esc('45m')
        cyan    = _esc('46m')
        white   = _esc('47m')

        def rgb(r, g, b):
            return _esc(f'48;2;{r};{g};{b}m')

    def __init__(self, string):
        self._string = string

    def __str__(self):
        return self._string

    def __add__(self, other):
        return self._string + other

    def bold(self):
        return ansi._bold + self._string + ansi._reset

    def italic(self):
        return ansi._italic + self._string + ansi._reset

    def underline(self):
        return ansi._underline + self._string + ansi._reset

    def rgb(self, r=0, g=0, b=0, bg=False):
        if bg:
            return ansi.bg.rgb(r, g, b) + self._string + ansi._reset

        return ansi.fg.rgb(r, g, b) + self._string + ansi._reset

    def black(self, fg=True):
        if fg:
            return ansi.fg.black + self._string + ansi._reset
        
        return ansi.bg.black + self._string + ansi._reset

    def red(self, fg=True):
        if fg:
            return ansi.fg.red + self._string + ansi._reset
        
        return ansi.bg.red + self._string + ansi._reset

    def green(self, fg=True):
        if fg:
            return ansi.fg.green + self._string + ansi._reset
        
        return ansi.bg.green + self._string + ansi._reset

    def yellow(self, fg=True):
        if fg:
            return ansi.fg.yellow + self._string + ansi._reset
        
        return ansi.bg.yellow + self._string + ansi._reset

    def blue(self, fg=True):
        if fg:
            return ansi.fg.blue + self._string + ansi._reset
        
        return ansi.bg.blue + self._string + ansi._reset

    def magenta(self, fg=True):
        if fg:
            return ansi.fg.magenta + self._string + ansi._reset
        
        return ansi.bg.magenta + self._string + ansi._reset

    def cyan(self, fg=True):
        if fg:
            return ansi.fg.cyan + self._string + ansi._reset
        
        return ansi.bg.cyan + self._string + ansi._reset

    def white(self, fg=True):
        if fg:
            return ansi.fg.white + self._string + ansi._reset
        
        return ansi.bg.white + self._string + ansi._reset

    def gray(self, fg=True):
        if fg:
            return self.rgb(150, 150, 150)

        return self.rgb(150, 150, 150, bg=False)