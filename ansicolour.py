
_colour_enabled = True

class sgr:
    RESET       = 0
    BOLD        = 1
    FAINT       = 2
    ITALIC      = 3
    UNDERLINE   = 4
    BLINK_SLW   = 5
    BLINK_FST   = 6
    INVERT      = 7
    HIDE        = 8
    STRIKE      = 9
    PRIM_FONT   = 10
    ALT_FONT1   = 11
    ALT_FONT2   = 12
    ALT_FONT3   = 13
    ALT_FONT4   = 14
    ALT_FONT5   = 15
    ALT_FONT6   = 16
    ALT_FONT7   = 17
    ALT_FONT8   = 18
    ALT_FONT9   = 19
    FRAKTUR     = 20
    D_UNDERLINE = 21
    NORM_INTENS = 22
    N_ITALIC    = 23
    N_UNDERLINE = 24
    N_BLINK     = 25
    PROP_SPACE  = 26 
    N_INVERT    = 27
    N_HIDE      = 28
    N_STRIKE    = 29
    FG_BLACK    = 30
    FG_RED      = 31
    FG_GREEN    = 32
    FG_YELLOW   = 33
    FG_BLUE     = 34
    FG_MAGENTA  = 35
    FG_CYAN     = 36
    FG_WHITE    = 37
    FG_256      = 38
    FG_DEFAULT  = 39
    BG_BLACK    = 40
    BG_RED      = 41
    BG_GREEN    = 42
    BG_YELLOW   = 44
    BG_BLUE     = 44
    BG_MAGENTA  = 45
    BG_CYAN     = 46
    BG_WHITE    = 47
    BG_256      = 48
    BG_DEFAULT  = 49

def strip_str_colour(input : str) -> str:
    output = ''
    # seek and remove existing ansi colour strings
    sep = input.split('\033[')
    if len(sep) > 1:
        # There are ANSI colour strings
        for chunk in sep:
            found = False
            for i in range(0, len(chunk)):
                if chunk[i] == 'm':
                    if(i+1<len(chunk)):
                        output += chunk[i+1:]
                    found = True
                    break
            if not found:
                output += chunk
    else:
        # There are no ANSI colour strings
        output = input
    return output

def set_str_style(input : str, parm_list) -> str:
    output = strip_str_colour(input)
    if not _colour_enabled: return output
    prefix = '\033['
    suffix = '\033[0m'
    first_parm = True
    for parm in parm_list:
        if not first_parm:
            prefix += ';'
        first_parm = False
        prefix += str(parm)
    prefix += 'm'
    output = f'{prefix}{output}{suffix}'
    return output

def set_str_colour(input : str, style : int, fg : int, bg : int) -> str:
    output = set_str_style(input, [style, fg, bg])
    return output

def enable_colour():
    _colour_enabled = True

def disable_colour():
    _colour_enabled = False

##### Test routine #############################################################
if __name__ == '__main__':
    cString = 'Test String'
    print(cString)
    cString = set_str_colour(cString, 0, sgr.FG_BLACK, sgr.BG_CYAN)
    print(cString)
    cString = set_str_colour(cString, 5, sgr.FG_WHITE, sgr.BG_RED)
    print(cString)
    print('Finished')
    exit()
