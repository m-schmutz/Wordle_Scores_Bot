class ANSI:

    _reset      = "\033[0m"
    _bold       = "\033[1m"
    _italic     = "\033[3m"
    _underline  = "\033[4m"

    class fg:
        black   = "\033[30m"
        red     = "\033[31m"
        green   = "\033[32m"
        yellow  = "\033[33m"
        blue    = "\033[34m"
        magenta = "\033[35m"
        cyan    = "\033[36m"
        white   = "\033[37m"
        def rgb(r, g, b): return f"\033[38;2;{r};{g};{b}m"

    class bg:
        black   = "\033[40m"
        red     = "\033[41m"
        green   = "\033[42m"
        yellow  = "\033[43m"
        blue    = "\033[44m"
        magenta = "\033[45m"
        cyan    = "\033[46m"
        white   = "\033[47m"
        def rgb(r, g, b): return f"\033[48;2;{r};{g};{b}m"

    def __init__(self, string):
        self._string = string

    def __str__(self):
        return self._string

    def __add__(self, other):
        return self._string + other

    def bold(self):
        return ANSI._bold + self._string + ANSI._reset

    def italic(self):
        return ANSI._italic + self._string + ANSI._reset

    def underline(self):
        return ANSI._underline + self._string + ANSI._reset

    def rgb(self, r=0, g=0, b=0, bg=False):
        if bg:
            return ANSI.bg.rgb(r, g, b) + self._string + ANSI._reset

        return ANSI.fg.rgb(r, g, b) + self._string + ANSI._reset

    def black(self, fg=True):
        if fg:
            return ANSI.fg.black + self._string + ANSI._reset
        
        return ANSI.bg.black + self._string + ANSI._reset

    def red(self, fg=True):
        if fg:
            return ANSI.fg.red + self._string + ANSI._reset
        
        return ANSI.bg.red + self._string + ANSI._reset

    def green(self, fg=True):
        if fg:
            return ANSI.fg.green + self._string + ANSI._reset
        
        return ANSI.bg.green + self._string + ANSI._reset

    def yellow(self, fg=True):
        if fg:
            return ANSI.fg.yellow + self._string + ANSI._reset
        
        return ANSI.bg.yellow + self._string + ANSI._reset

    def blue(self, fg=True):
        if fg:
            return ANSI.fg.blue + self._string + ANSI._reset
        
        return ANSI.bg.blue + self._string + ANSI._reset

    def magenta(self, fg=True):
        if fg:
            return ANSI.fg.magenta + self._string + ANSI._reset
        
        return ANSI.bg.magenta + self._string + ANSI._reset

    def cyan(self, fg=True):
        if fg:
            return ANSI.fg.cyan + self._string + ANSI._reset
        
        return ANSI.bg.cyan + self._string + ANSI._reset

    def white(self, fg=True):
        if fg:
            return ANSI.fg.white + self._string + ANSI._reset
        
        return ANSI.bg.white + self._string + ANSI._reset
