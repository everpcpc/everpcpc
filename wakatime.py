'''
WakaTime progress visualizer
From: https://github.com/athul/waka-readme
'''

import re
import os
import base64
import sys
import datetime
import requests
import subprocess
import configparser

START_COMMENT = '<!--START_SECTION:waka-->'
END_COMMENT = '<!--END_SECTION:waka-->'
GRAPH_LENGTH = 25
TEXT_LENGTH = 16
listReg = f"{START_COMMENT}[\\s\\S]+{END_COMMENT}"

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.wakatime.cfg"))
waka_key = config["settings"]["api_key"]

api_base_url = "https://wakatime.com/api"
show_title = False
commit_message = "wakatime: update graphics"
blocks = "░▒▓█"
show_time = True 


def this_week() -> str:
    '''Returns a week streak'''
    week_end = datetime.datetime.today() - datetime.timedelta(days=1)
    week_start = week_end - datetime.timedelta(days=6)
    print("Week header created")
    return f"Week: {week_start.strftime('%d %B, %Y')} - {week_end.strftime('%d %B, %Y')}"


def make_graph(percent: float, blocks: str, length: int = GRAPH_LENGTH) -> str:
    '''Make progress graph from API graph'''
    if len(blocks) < 2:
        raise "The BLOCKS need to have at least two characters."
    divs = len(blocks) - 1
    graph = blocks[-1] * int(percent / 100 * length + 0.5 / divs)
    remainder_block = int((percent / 100 * length - len(graph)) * divs + 0.5)
    if remainder_block > 0:
        graph += blocks[remainder_block]
    graph += blocks[0] * (length - len(graph))
    return graph


def get_stats() -> str:
    '''Gets API data and returns markdown progress'''
    encoded_key: str = str(base64.b64encode(waka_key.encode('utf-8')), 'utf-8')
    data = requests.get(
        f"{api_base_url.rstrip('/')}/v1/users/current/stats/last_7_days",
        headers={
            "Authorization": f"Basic {encoded_key}"
        }).json()
    try:
        lang_data = data['data']['languages']
    except KeyError:
        print("Please Add your WakaTime API Key to the Repository Secrets")
        sys.exit(1)

    if show_time == 'true':
        print("Will show time on graph")
        ln_graph = GRAPH_LENGTH
    else:
        print("Hide time on graph")
        ln_graph = GRAPH_LENGTH + TEXT_LENGTH

    data_list = []
    try:
        pad = len(max([l['name'] for l in lang_data[:5]], key=len))
    except ValueError:
        print("The Data seems to be empty. Please wait for a day for the data to be filled in.")
        return '```text\nNo Activity tracked this Week\n```'
    for lang in lang_data[:5]:
        if lang['hours'] == 0 and lang['minutes'] == 0:
            continue

        lth = len(lang['name'])
        text = ""
        if show_time == 'true':
            ln_text = len(lang['text'])
            text = f"{lang['text']}{' '*(TEXT_LENGTH - ln_text)}"

        # following line provides a neat finish
        fmt_percent = format(lang['percent'], '0.2f').zfill(5)
        data_list.append(
            f"{lang['name']}{' '*(pad + 3 - lth)}{text}{make_graph(lang['percent'], blocks, ln_graph)}   {fmt_percent} % ")
    print("Graph Generated")
    data = '\n'.join(data_list)
    if show_title == 'true':
        print("Stats with Weeks in Title Generated")
        return '```text\n'+this_week()+'\n\n'+data+'\n```'
    else:
        print("Usual Stats Generated")
        return '```text\n'+data+'\n```'


def generate_new_readme(stats: str, readme: str) -> str:
    '''Generate a new Readme.md'''
    stats_in_readme = f"{START_COMMENT}\n{stats}\n{END_COMMENT}"
    return re.sub(listReg, stats_in_readme, readme)


if __name__ == '__main__':
    subprocess.check_call(["git", "pull"])
    waka_stats = get_stats()
    rdmd = open("README.md").read()
    new_readme = generate_new_readme(stats=waka_stats, readme=rdmd)
    if new_readme != rdmd:
        print(new_readme)
        with open("README.md", "w") as f:
            f.write(new_readme)
        subprocess.check_call(["git", "commit", "README.md", "-m", commit_message])
        subprocess.check_call(["git", "push"])

