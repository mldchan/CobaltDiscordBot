import json
import os
import re

import aiohttp
import discord


intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

with open('config.json', 'r') as f:
    config = json.load(f)

max_upload_size = config['cobalt']['file_size_limit']

if max_upload_size.endswith("m"):
    max_upload_size = int(max_upload_size[:-1]) * 1024 * 1024
elif max_upload_size.endswith("k"):
    max_upload_size = int(max_upload_size[:-1]) * 1024
else:
    max_upload_size = int(max_upload_size)


@bot.event
async def on_message(msg: discord.Message):
    """
    When a message is sent, this function will check if it contains any URLs.
    If it does, it will use the Cobalt API to download the video and then reupload it to the Discord channel.
    If the message contains the string "-a", it will only download the audio.

    Example of Config file:
    {
        "token": "[discord token]",
        "cobalt": {
            "api_url": "[cobalt instance api]",
            "video": "360",
            "audio": "256",
            "max_attachments": "9",
            "file_size_limit": "25m"
        }
    }
    """
    if msg.author.bot:
        return

    urls = [x for x in msg.content.split(" ") if re.match(r'https?://[\da-z.-]+\.[a-z.]{2,6}[/\w .-]*/?', x)]

    if not urls:
        return

    first_url = urls[0]

    audio_only = "-a" in msg.content

    instance = config['cobalt']['api_url']

    json_data = {
        "url": first_url,
        "filenameStyle": "pretty",
        "alwaysProxy": True,
        "videoQuality": config['cobalt']['video'],
        "audioBitrate": config['cobalt']['audio'],
    }

    if audio_only:
        json_data["downloadMode"] = "audio"

    async with (aiohttp.ClientSession() as session):
        async with session.post(instance, headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        }, json=json_data) as details:
            details = await details.json()

            if details['status'] == "error":
                return

            if details['status'] == "redirect" or details['status'] == "tunnel":
                async with session.get(details['url']) as r:
                    with open(details['filename'], "wb") as f1:
                        while True:
                            chunk = await r.content.read(1024)
                            if not chunk:
                                break
                            f1.write(chunk)

                if os.path.exists(details['filename']) and 0 < os.path.getsize(details['filename']) < max_upload_size:
                    await msg.reply(file=discord.File(details['filename']))

                os.remove(details['filename'])
                return

            if details['status'] == "picker":
                files_downloaded = []
                files_to_upload = []
                if details['audio']:
                    async with session.get(details['audio']) as r:
                        with open(details['audioFilename'], "wb") as f1:
                            while True:
                                chunk = await r.content.read(1024)
                                if not chunk:
                                    break
                                f1.write(chunk)
                    files_downloaded.append(details['audioFilename'])
                    if os.path.exists(details['audioFilename']) and 0 < os.path.getsize(
                            details['audioFilename']) < max_upload_size:
                        files_to_upload.append(discord.File(details['audioFilename']))

                for i in range(0, len(details['picker']), config['cobalt']['max_attachments']):
                    curr_files_to_upload = []
                    for j, v in enumerate(details['picker'][i:i + config['cobalt']['max_attachments']]):
                        file_name = v['type'] + str(i + j) + ".jpeg"
                        async with session.get(v['url']) as r:
                            with open(file_name, "wb") as f1:
                                while True:
                                    chunk = await r.content.read(1024)
                                    if not chunk:
                                        break
                                    f1.write(chunk)
                        files_downloaded.append(file_name)
                        if os.path.exists(file_name) and 0 < os.path.getsize(file_name) < max_upload_size:
                            curr_files_to_upload.append(discord.File(file_name))

                    await msg.reply(files=curr_files_to_upload)

                for file in files_downloaded:
                    os.remove(file)

bot.run(config['token'])
