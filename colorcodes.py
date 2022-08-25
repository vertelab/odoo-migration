class Colorcodes(object):
    Green = '\033[92m'
    Green_bg = '\033[102;5m'
    Grey100 = '\033[38;5;242m\033[48;5;231m'
    LightPink1 = '\033[38;5;239m\033[48;5;217m'
    SteelBlue1 = '\033[38;5;237m\033[48;5;81m'
    Red = '\033[91m'
    Red_bg = '\033[101;5m'
    Reset = '\033[0m'
    Yellow = '\033[33m'  # 33, 93
    Yellow_bg = '\033[43;5m'  # 43, 103

    def __init__(self):
        self.num = 0

    def green_fg(self, text):
        return self.Green + text + self.Reset

    def green_bg(self, text):
        return self.Green_bg + text + self.Reset

    def grey100_bg(self, text):
        return self.Grey100 + text + self.Reset

    def light_pink_bg(self, text):
        return self.LightPink1 + text + self.Reset

    def print_colors(self, text, color=None, end="\n"):
        if color == 'tg':
            self.print_tg(text, end=end)
        elif not color:
            print(text, end=end)
        else:    
            print(eval(f"self.{color}(text)"), end=end)

    def print_tg(self, text, end=''):
        self.num += 1
        if self.num % 6 in [1, 5]:
            print(self.steel_blue_bg(text), end=end)
        if self.num % 6 in [2, 4]:
            print(self.light_pink_bg(text), end=end)
        if self.num % 6 in [3]:
            print(self.grey100_bg(text), end=end)
        if self.num % 6 in [0]:
            self.num = 0
            print(text, end=end)

    def red_bg(self, text):
        return self.Red_bg + text + self.Reset

    def red_fg(self, text):
        return self.Red + text + self.Reset
    
    def steel_blue_bg(self, text):
        return self.SteelBlue1 + text + self.Reset

    def yellow_bg(self, text):
        return self.Yellow_bg + text + self.Reset

    def yellow_fg(self, text):
        return self.Yellow + text + self.Reset