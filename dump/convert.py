import json
import re

def convert(text: str) -> str:
    # Conversion dictionary for CircleMUD to Rhost colors
    color_conversion = {
        "n": "%cn",   # normal
        "d": "%cx",   # black
        "D": "%ch%cx",# bright black
        "0": "%cX",   # background black
        "b": "%cb",   # blue
        "B": "%ch%cb",# bright blue
        "1": "%cB",   # background blue
        "g": "%cg",   # green
        "G": "%ch%cg",# bright green
        "2": "%cG",   # background green
        "c": "%cc",   # cyan
        "C": "%ch%cc",# bright cyan
        "3": "%cC",   # background cyan
        "r": "%cr",   # red
        "R": "%ch%cr",# bright red
        "4": "%cR",   # background red
        "m": "%cm",   # magenta
        "M": "%ch%cm",# bright magenta
        "5": "%cM",   # background magenta
        "y": "%cy",   # yellow
        "Y": "%ch%cy",# bright yellow
        "6": "%cY",   # background yellow
        "w": "%cw",   # white
        "W": "%ch%cw",# bright white
        "7": "%cW",   # background white
        "l": "%cf",   # blink
        "o": "%ch",   # bold
        "u": "%cu",   # underline
        "e": "%ci",   # reverse video,
        "@": "@",     # escaped @
    }

    # Regular expression to match CircleMUD color codes
    color_code_pattern = re.compile(r'@([A-Za-z0-9@])')

    def replace_color_code(match):
        circle_code = match.group(1)
        return color_conversion.get(circle_code, '')

    def eliminate_spaces_before_R(text: str) -> str:
        # Pattern to match spaces before %R and replace them
        return re.sub(r' +(?=%R)', '', text)

    def replace_spaces(text: str) -> str:
        return re.sub(r' {3,}', lambda match: f"[space({len(match.group(0))})]", text)

    def trim_right(text: str) -> str:
        # Pattern to match trailing whitespace, %R, %T, and %cn
        trim_pattern = re.compile(r'(\s|%R|%T|%cn)+$')
        return re.sub(trim_pattern, '', text)

    # Escape % characters for Rhost.
    converted_text = text.replace("%", "%%")

    # Replace CircleMUD color codes with Rhost softcode format
    converted_text = re.sub(color_code_pattern, replace_color_code, converted_text)

    # Replace line breaks and tabs
    converted_text = converted_text.replace('\r\n', '%R').replace('\n', '%R').replace('\t', '%t')

    # Eliminate contiguous spaces that precede a %R
    converted_text = eliminate_spaces_before_R(converted_text)

    # Replace contiguous spaces with [space(n)]
    converted_text = replace_spaces(converted_text)

    # Trim right side of the string of all whitespace, %R, %T, and %cn
    converted_text = trim_right(converted_text)

    return converted_text

ROOMS = dict()
AREAS = dict()

def initialize():
    global ROOMS, AREAS
    with open("rooms.json", "r") as f:
        ROOMS = {room["vn"]: room for room in json.load(f)}
    with open("areas.json", "r") as f:
        AREAS = {area["vn"]: area for area in json.load(f)}

    for vn, area in AREAS.items():
        for rvn in area.get("rooms", list()):
            ROOMS[rvn]["area"] = vn

    ROOMS = {vn: room for vn, room in ROOMS.items() if room.get("area", None) != 7}

def process_areas():
    with open("areas.txt", "w") as f:
        for vn, area in AREAS.items():
            f.write(f"think [u(ANEW,{vn},{area['name']})]\n")

        for vn, area in AREAS.items():
            if (parent := area.get("parent", None)) is not None:
                f.write(f"@tel [u(AOBJ,{vn})]=[u(AOBJ,{parent})]\n")

def process_rooms():
    with open("rooms.txt", "w") as f:
        for i, (vn, room) in enumerate(ROOMS.items()):
            # every 1000 rooms, send a special command
            if i % 1000 == 0:
                f.write("@cmdquota me=99999\n")
            f.write(f"@@ ----- Begin of Room {vn} -----\n")
            name = convert(room["name"])
            f.write(f"think [u(RNEW,{vn},{name})]\n")
            if "%" in name:
                f.write(f"@name/ansi [u(ROBJ,{vn})]={name}\n")
            if (description := room.get("look_description", None)) is not None:
                f.write(f"@describe [u(ROBJ,{vn})]={convert(description)}\n")
            if (area := room.get("area", None)) is not None:
                f.write(f"@zone/add [u(ROBJ,{vn})]=[u(AOBJ,{area})]\n")
            f.write("@@ ------ End of Room\n")

def process_exits():
    with open("exits.json", "r") as infile:
        exits = json.load(infile)
    with open("exits.txt", "w") as f:
        for i, ex in enumerate(exits):
            # every 1000 exits, send a special command
            if i % 1000 == 0:
                f.write("@cmdquota me=99999\n")

            location = ex.get("room", -1)
            if not (location in ROOMS):
                continue
            data = ex.get("data", dict())
            if not data:
                continue
            destination = data.get("to_room", -1)
            if not (destination in ROOMS):
                continue
            direction = ex.get("direction", -1)
            f.write(f"think [u(ENEW,{direction},{location},{destination})]\n")


def check_scripts():
    scripts = dict()
    with open("dgScriptPrototypes.json", "r") as infile:
        scripts = json.load(infile)

    max_length = 0

    for script in scripts:
        script_commands = len(script.get("cmdlist", list()))
        if script_commands > max_length:
            max_length = script_commands

    print(f"Max script length: {max_length}")


def main():
    initialize()
    check_scripts()
    #process_areas()
    #process_rooms()
    #process_exits()
    #process_items()
    #process_mobiles()


if __name__ == '__main__':
    main()