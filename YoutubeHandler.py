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

    async def extract_url(self, url):
        with YoutubeDL(self.config) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            audio_url = info['url']
            source = FFmpegPCMAudio(audio_url, **self.ffmpeg_config)
            return [info, source]

    async def play(self, url: str, voice_client: VoiceClient):
        self.voice_client = voice_client
        self.playing = True

        track = await self.extract_url(url)

        voice_client.play(track[1], after=self.next)

        return {"title": track[0]["fulltitle"], "duration": self.format_time(track[0]["duration_string"])}

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
        self.voice_client.pause()
        
    def resume(self):
        self.playing = True
        self.voice_client.resume()

    async def reset(self):
        self.playing = False
        self.voice_client.stop()
        self.voice_client.cleanup()
        await self.voice_client.disconnect()
        asyncio.run_coroutine_threadsafe(
            self.leave_callback("Xauu"), self.loop)
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

    async def enqueue(self, url, user):
        track = await self.extract_url(url)

        self.queue.append([
            track[0]["fulltitle"],
            self.format_time(track[0]["duration_string"]),
            track[1],
            user])

        return [track[0]["fulltitle"], len(self.queue)]
