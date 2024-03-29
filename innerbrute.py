from itertools import islice
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

RETRIES = 3

CLIENT_NAME_IDS = range(1, 120)
with open("payloads/CLIENT_VERSIONS.txt", "r", encoding="utf-8") as f:
    CLIENT_VERSIONS = list(filter(None, map(str.rstrip, f)))
with open("payloads/post_data.txt", "r", encoding="utf-8") as f:
    data_template = f.read().rstrip()
if not os.path.exists('responses'):
    os.makedirs('responses')

INNERTUBE_HOSTS = [
    {
        "video_id": "vJz8QzO1VzQ", # normal video
        "domain": "www.youtube.com",
        "key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
        "headers": {
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/",
            "Accept-Language": "de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.52"
        }
    },
    {
        "video_id": "pckuS--UlV4", # video "for kids"
        "domain": "www.youtubekids.com",
        "key": "AIzaSyBbZV_fZ3an51sF-mvs5w37OqqbsTOzwtU",
        "headers": {
            "Origin": "https://www.youtubekids.com",
            "Referer": "https://www.youtubekids.com/",
            "Accept-Language": "de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.52"
        }
    },
    {
        "video_id": "RY607kB2QiU", # music video
        "domain": "music.youtube.com",
        "key": "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30",
        "headers": {
            "Origin": "https://music.youtube.com",
            "Referer": "https://music.youtube.com/",
            "Accept-Language": "de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.52"
        }
    },
    {
        "video_id": "zv9NimPx3Es", # another music video
        "domain": "music.youtube.com",
        "key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
        "headers": {
            "Origin": "https://music.youtube.com",
            "Referer": "https://music.youtube.com/",
            "Accept-Language": "de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.52"
        }
    }
]

def run(variant):
    host, client_name_id, client_version, id_ = variant
    try_id = "_".join(map(str, (client_name_id, client_version, id_, host["domain"], host["key"])))

    code, err = 0, None
    for i in range(0, RETRIES + 1):
        if i:
            time.sleep(0.5)

        try:
            response = requests.post(
                f"https://{host['domain']}/youtubei/v1/player?key={host['key']}",
                headers=host["headers"], timeout=5, data=data_template % {
                    'videoId': host["video_id"],
                    'clientName': client_name_id,
                    'clientVersion': client_version,
                })
        except Exception as e:
            code, err = 0, str(e)
        else:
            code, err = response.status_code, None
            break

    if code == 200:
        with open(f"responses/{try_id}.json", "w", encoding="utf-8") as f:
            f.write(response.text)

    return try_id, code, err

_hosts_count = len(INNERTUBE_HOSTS)
variants = [
    (host, client_name_id, client_version, _hosts_count - i)
    for client_name_id in CLIENT_NAME_IDS
    for client_version in CLIENT_VERSIONS
    for i, host in enumerate(INNERTUBE_HOSTS)
]
N = len(variants)
start = int(sys.argv[1]) if sys.argv[1:] else 0
if start:
    print(f'Resuming after {start}')
    variants = variants[start:]

valid = failed = invalid = 0
with ThreadPoolExecutor() as pool:
    tasks = pool.map(run, variants)
    print("Tasks queued")
    for i, (try_id, code, err) in enumerate(tasks, start + 1):
        if err:
            failed += 1
            msg = f'Failed {err}'
        elif code == 200:
            valid += 1
            msg = f'Success {code}'
        else:
            invalid += 1
            msg = f'Invalid {code}'
        print(f"[{i: 6}/{N} {i/N: 7.2%}] {try_id} {msg}. (Valid {valid} | Invalid {invalid} | Failed {failed})")
