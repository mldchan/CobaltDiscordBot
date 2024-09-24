import json
import re


def vvre(reg: re.Pattern[str], prompt: str, defa: object = None) -> object:
    """Valid Value REgex"""
    inp = ''
    while not re.match(reg, inp) and inp != defa:
        inp = input(prompt) if defa is None else input(prompt) or defa

    return inp


def vvc(choices: list[str], prompt: str, defa=None):
    """Valid Value Choices"""
    inp = ''
    while inp not in choices and inp != defa:
        inp = input(prompt) if defa is None else input(prompt) or defa

    return inp


print('Welcome to the Cobalt Discord Bot configuration')
print('Things in [] are choices')
print('Things in () are defaults')
print('Some inputs are validated')
token = input('Enter token: ')

cobalt_api_url = vvre(
    re.compile(r'(?:https?://.)?(?:www[.])?[-a-zA-Z0-9@%._+~#=]{2,256}[.][a-z]{2,6}[-a-zA-Z0-9@:%_+.~#?&/=]*'),
    "Input Cobalt API URL: ")

file_size_limit = vvre(re.compile(r'(^[0-9]{1,2}([mk])?$)?'),
                       'Enter file size limit [number and then k/m for unit] (25m) ', defa='25m')
video_quality = vvc(['144', '240', '360', '480', '720', '1080', '1440', '2160'],
                    'Enter video quality [144/240/360/480/720/1080/1440/2160] (360) ', defa='360')
audio_quality = vvc(['8', '64', '128', '256', '320'],
                    'Enter audio quality [8/64/96/128/256/320] (256) ', defa='256')
max_attachments = vvre(re.compile(r'^[1-9]$'), 'Max attachments per message [1-9] (9) ', defa='9')

data = {
    'token': token,
    'cobalt': {
        'api_url': cobalt_api_url,
        'video': video_quality,
        'audio': audio_quality,
        'max_attachments': max_attachments,
        'file_size_limit': file_size_limit
    }
}

with open('config.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
