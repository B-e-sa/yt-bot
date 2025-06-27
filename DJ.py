from discord import VoiceChannel
from discord import VoiceClient
from discord.ext import commands

import discord as ds


class DJ:
    def __init__(self):
        self.voice_client: VoiceClient = None
        self.channel_id: int | None = None

        self.intents = ds.Intents.default()
        self.intents.message_content = True
        self.intents.guilds = True
        self.intents.voice_states = True

        self.client = ds.Client(intents=self.intents)

        self.bot = commands.Bot(command_prefix='dj ', intents=self.intents)

    def get_intents(self):
        return self.intents

    async def join_channel(self, channel: VoiceChannel):
        self.channel_id = channel.id
        voice_client = await channel.connect()
        self.voice_client = voice_client

    async def disconect_channel(self):
        await self.voice_client.disconnect()
        self.voice_client = None
        self.channel_id = None

    def reset(self):
        self.voice_client = None
        self.channel_id = None
