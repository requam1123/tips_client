# ui/style.py
class Term:
    RESET = '\033[0m' # END
    BOLD = '\033[1m' # 粗体
    
    # 颜色
    FG_YELLOW = '\033[33m'
    BG_BLUE = '\033[44m'
    FG_WHITE = '\033[37m'
    
    # 屏幕控制
    CLEAR = '\033[H\033[2J'
    ALT_SCREEN_ON = '\033[?1049h'
    ALT_SCREEN_OFF = '\033[?1049l'