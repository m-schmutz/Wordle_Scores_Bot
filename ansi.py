class ansi:

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
