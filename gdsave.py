
from dataclasses import dataclass
import plistlib
import base64
import gzip
import os

import pprint
pp = pprint.PrettyPrinter()

fmt_ver = 1
save = {}

gd_folder = "GeometryDash"

@dataclass
class Level:
    id: int | None
    name: bytes
    description: bytes
    level: bytes
    original_song_id: int
    custom_song_id: int
    length: int
    verified: bool
    coin_1_collected: bool
    coin_2_collected: bool
    coin_3_collected: bool
    coins_needed: int
    attempts: int
    jumps: int

    def __post_init__(self):
        self.signature = (self.name, self.description, self.level,
                          self.original_song_id, self.custom_song_id,
                          self.length, self.verified,
                          self.coin_1_collected, self.coin_2_collected, self.coin_3_collected, self.coins_needed,
                          self.attempts, self.jumps)

    def serialize(self):
        result = b"LRIP"
        result += int.to_bytes(fmt_ver)

        for i in self.signature:
            if isinstance(i, bytes):
                result += int.to_bytes(len(i), 4)
                result += i
            elif isinstance(i, int):
                result += int.to_bytes(i, 4)
            elif isinstance(i, bool):
                result += b"\x00" if i else b"\x01"

        return result

    def parse(self, fp):
        magic = fp.read(4)
        if magic != b"LRIP": return "ERROR: file is not LevelRipper file"
        if int.from_bytes(fp.read(1)) != fmt_ver: return "ERROR: incompatible binary file"
        name_len = int.from_bytes(fp.read(4))
        self.name = fp.read(name_len)
        desc_len = int.from_bytes(fp.read(4))
        self.description = fp.read(desc_len)
        level_len = int.from_bytes(fp.read(4))
        self.level = fp.read(level_len)
        self.original_song_id = int.from_bytes(fp.read(4))
        self.custom_song_id = int.from_bytes(fp.read(4))
        self.length = int.from_bytes(fp.read(4))
        self.verified = fp.read(1) == b"\x01"
        self.coin_1_collected = fp.read(1) == b"\x01"
        self.coin_2_collected = fp.read(1) == b"\x01"
        self.coin_3_collected = fp.read(1) == b"\x01"
        self.coins_needed = int.from_bytes(fp.read(4))
        self.attempts = int.from_bytes(fp.read(4))
        self.jumps = int.from_bytes(fp.read(4))
        
def xor_cipher(data, key):
    result = ""
    for char in data:
        result += chr(char ^ key)
    return result.encode()

def normilize_save(save):
    if len(save) == 0:
        return {"LLM_01": {"_isArr": True}, "LLM_02": 40, 'LLM_03': {'_isArr': True}}
    
    save = save.replace(b"<d>", b"<dict>")    .replace(b"</d>", b"</dict>") \
               .replace(b"<k>", b"<key>")     .replace(b"</k>", b"</key>") \
               .replace(b"<s>", b"<string>")  .replace(b"</s>", b"</string>") \
               .replace(b"<i>", b"<integer>") .replace(b"</i>", b"</integer>") \
               .replace(b"<r>", b"<real>")    .replace(b"</r>", b"</real>") \
               .replace(b"<d />", b"<dict/>") \
               .replace(b"<t />", b"<true/>") \
               .replace(b"<f />", b"<false/>")
    
    save = plistlib.loads(save, fmt=plistlib.FMT_XML)
    return save

def save_format(item, first_run=False):
    if item is True:
        return f"<t />"
    elif item is False:
        return f"<f />"
    elif isinstance(item, int):
        return f"<i>{item}</i>"
    elif isinstance(item, float):
        return f"<r>{item}</r>"
    elif isinstance(item, str):
        return f"<s>{item}</s>"
    elif isinstance(item, str):
        return f"<s>{item}</s>"
    elif isinstance(item, dict) and not first_run:
        if len(item) == 0: return "<d />"
        res = "<d>"
        
        for k, i in item.items():
            if not isinstance(k, str): continue

            res += f"<k>{k}</k>"
            res += save_format(i)

        res += "</d>"
        return res
    elif isinstance(item, dict):
        if len(item) == 0: return "<dict/>"
        res = "<dict>"
        
        for k, i in item.items():
            if not isinstance(k, str): continue

            res += f"<k>{k}</k>"
            res += save_format(i)

        res += "</dict>"
        return res

def unnormilize_save(save):
    # DEV NOTE: rob is fucking bastard
    #           somewhy outer dict should be <dict>
    #           while all inside ones should be <d>
    #           also, <plist> tag should have gjver="2.0"
    #           rob i will murder you, someday
    save_str = """<?xml version="1.0"?><plist version="1.0" gjver="2.0">%s</plist>"""

    save_str = save_str % save_format(save, True)

    return save_str.encode()

def load_savefile():
    global save

    save = xor_cipher(save, 0xb)
    save = base64.urlsafe_b64decode(save)
    save = gzip.decompress(save)
    save = normilize_save(save)

def save_savefile():
    global save

    save = unnormilize_save(save)
    save = gzip.compress(save)
    save = base64.urlsafe_b64encode(save)
    save = xor_cipher(save, 0xb)

def parse_file(fp, isRaw):
    l = Level(None, b"Imported Level", b"", b"",
              0, 0, 0, False,
              False, False, False, 0,
              0, 0)

    if isRaw:
        l.level = fp.read()
        return l, None
    
    err = l.parse(fp)

    return l, err

def reload_save():
    global save
    save = open(os.path.join(os.getenv("LocalAppData"), gd_folder, "CCLocalLevels.dat"), "rb").read()
    load_savefile()

def import_level(level):
    # rob...
    # why
    for i in list(filter(lambda x: x[:2] == "k_", save["LLM_01"].keys()))[::-1]:
        save['LLM_01']['k_' + str(int(i[2:]) + 1)] = save['LLM_01'][i]
    
    save['LLM_01']['k_0'] = {
        'k2': level.name.decode(), # name
        'k3': base64.urlsafe_b64encode(level.description).decode(), # description
        'k4': base64.urlsafe_b64encode(gzip.compress(level.level)).decode(), # level itself
        'k42': level.original_song_id,
        'k45': level.custom_song_id,
        'k23': level.length,
        'k14': level.verified,
        'k61': level.coin_1_collected,
        'k62': level.coin_2_collected,
        'k63': level.coin_3_collected,
        'k37': level.coins_needed,
        'k18': level.attempts,
        'k36': level.jumps,
        'k21': 2, # custom level
        'k50': 40, # binary version (needed for gd)
        'kCEK': 4, # idk what that even is
    }
    save_savefile()
    open(os.path.join(os.getenv("LocalAppData"), gd_folder, "CCLocalLevels.dat"), "wb").write(save)
    load_savefile()

def export_levels():
    res = []
    for i in [i for k, i in save["LLM_01"].items() if k.startswith("k_")]:
        if "k4" not in i: continue

        res.append(
            Level(None, i["k2"].encode(),
                  base64.urlsafe_b64decode(i["k3"]) if "k3" in i.keys() else b"",
                  gzip.decompress(base64.urlsafe_b64decode(i["k4"])),
                  i["k42"] if "k42" in i.keys() else 0,
                  i["k45"] if "k45" in i.keys() else 0,
                  i["k23"] if "k23" in i.keys() else 0,
                  i["k14"] if "k14" in i.keys() else False,
                  i["k61"] if "k61" in i.keys() else False,
                  i["k62"] if "k62" in i.keys() else False,
                  i["k63"] if "k63" in i.keys() else False,
                  i["k37"] if "k37" in i.keys() else 0,
                  i["k18"] if "k18" in i.keys() else 0,
                  i["k36"] if "k36" in i.keys() else 0,
                  )
        )
    return res

# if __name__ == "__main__":
#     reload_save()
#     import_level(Level(b"new", b"wow", b"kS38,1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1000_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1001_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1009_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1002_5_1_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1013_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1014_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1005_5_1_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1006_5_1_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1004_7_1_15_1_18_0_8_1|,kA13,0,kA15,0,kA16,0,kA14,,kA6,0,kA7,0,kA25,0,kA17,0,kA18,0,kS39,0,kA2,0,kA3,0,kA8,0,kA4,0,kA9,0,kA10,0,kA22,0,kA23,0,kA24,0,kA27,1,kA40,1,kA41,1,kA42,1,kA28,0,kA29,0,kA31,1,kA32,1,kA36,0,kA43,0,kA44,0,kA45,1,kA33,1,kA34,1,kA35,0,kA37,1,kA38,1,kA39,1,kA19,0,kA26,0,kA20,0,kA21,0,kA11,0;1,75,2,15,3,15,155,1;"))
#     save_savefile()
#     open(os.path.join(os.getenv("LocalAppData"), gd_folder, "CCLocalLevels.dat"), "wb").write(save)
#     reload_save()
