from yt_dlp import YoutubeDL
from discord import FFmpegPCMAudio
from discord import VoiceClient

import asyncio


class YoutubeHandler:
    def __init__(self):
        self.config = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        self.ffmpeg_config = {
            'before_options':
            '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 200M',
            'options': '-vn'
        }

        self.queue = []
        self.playing = False
        self.voice_client = None
        self.message_callback = None
        self.leave_callback = None
        self.loop = None
        self.skipping = False

    def format_time(self, time: str):
        split = time.split(":")

        if len(split) == 1:
            return split[0] + " segundos"
        else:
            return time + " minutos"

    def play(self, url: str, voice_client: VoiceClient):
        with YoutubeDL(self.config) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            source = FFmpegPCMAudio(audio_url, **self.ffmpeg_config)
            self.voice_client = voice_client
            voice_client.play(source, after=self.next)
            self.playing = True

        return {"title": info["fulltitle"], "duration": self.format_time(info["duration_string"])}

    def next(self, _err):
        if self.skipping:
            self.skipping = False
            return

        if len(self.queue) == 0:
            self.stop()
        else:
            track = self.queue.pop(0)
            self.voice_client.play(track[2], after=self.next)
            asyncio.run_coroutine_threadsafe(
                self.message_callback(track[0], track[1], track[3]),
                self.loop)

    def stop(self):
        self.playing = False
        self.voice_client.stop()
        asyncio.run_coroutine_threadsafe(self.leave_callback("Acabo"), self.loop)

    async def reset(self):
        self.playing = False
        self.voice_client.stop()
        self.voice_client.cleanup()
        await self.voice_client.disconnect()
        asyncio.run_coroutine_threadsafe(self.leave_callback("Xauu"), self.loop)
        self.voice_client = None
        self.queue = []


    def skip(self):
        self.skipping = True

        self.voice_client.stop()
        track = self.queue.pop(0)
        self.voice_client.play(track[2], after=self.next)
        asyncio.run_coroutine_threadsafe(
            self.message_callback(track[0], track[1], track[3]),
            self.loop
        )

    def enqueue(self, url, user):
        with YoutubeDL(self.config) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            source = FFmpegPCMAudio(audio_url, **self.ffmpeg_config)

        self.queue.append([
            info["fulltitle"],
            self.format_time(info["duration_string"]),
            source,
            user])

        return [info["fulltitle"], len(self.queue)]
