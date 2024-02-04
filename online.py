
from turtle import down
import requests
from gdsave import *
import base64
import gzip

base_url = "http://www.boomlings.com/database/"

session = requests.session()
session.headers.update({"User-Agent": ""})
session.params.update({"Content-Type": "application/x-www-form-urlencoded"})

def request_post(endpoint, data):
    return session.post(base_url + endpoint, data=data).content

def parse_level(level_str):
    keys = level_str.split(b":")[::2]
    vals = level_str.split(b":")[1::2]
    data = dict(zip(map(int, keys), vals))
    return Level(int(data[1]), data[2], base64.urlsafe_b64decode(data[3]), gzip.decompress(base64.urlsafe_b64decode(data[4])) if 4 in data else None,
                 int(data[12]), int(data[35]), int(data[15]),
                 False, False, False, False, 0, 0, 0)

def download_level(id):
    return parse_level(request_post("downloadGJLevel22.php", {"levelID": str(id), "secret": "Wmfd2893gb7"}))

def search(query, search_type, level_type, page):
    search_type = [0, 1, 4][search_type]
    raw_return = request_post("getGJLevels21.php", {
        "secret": "Wmfd2893gb7",
        "str": query,
        "type": search_type,
        "page": page,
        "featured": level_type == 1,
        "epic": level_type == 2,
    })
    return [parse_level(i) for i in raw_return.split(b"#")[0].split(b"|")]

# if __name__ == "__main__":
#     search_res = search("lobotomy", 0, 0, 0)
#     print(download_level(search_res[0].id))
