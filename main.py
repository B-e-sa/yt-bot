
from discord import Message
from discord.ext.commands import Context
from dotenv import load_dotenv
from DJ import DJ
from YoutubeHandler import YoutubeHandler

import logging
import os
import asyncio

ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'default_search': 'auto',
    'outtmpl': 'song.%(ext)s',
}

load_dotenv()
token = os.getenv('DS_TOKEN')

handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')

dj = DJ()
bot = dj.bot

yt_handler = YoutubeHandler()


async def pre_flight(ctx: Context) -> str:
    if ctx.author.voice is None:
        await ctx.send("Você não tá em um canal de voz")
        return "no_channel"

    if dj.channel_id:
        # bot em um canal de voz, o usuário o invoca em um canal diferente
        if ctx.author.voice.channel.id != dj.channel_id:
            await ctx.send("Canal de voz diferente do meu")
            return "different_channel"

        # bot no mesmo canal de voz do usuário
        else:
            return "same_channel"

    return "free"


commands = [
    ["toca", "toco um link do youtube"],
    ["pula", "pulo a música atual"],
    ["parou", "paro a musica (usa de novo para retornar)"],
    ["tchau", "vo imbora"],
    ["fila", "mostro as musicas na fila"]]


@bot.command()
async def ajuda(ctx: Context):
    commands_str = "\n"

    for command in commands:
        commands_str += command[0] + ": " + command[1] + "\n"

    await ctx.send("Prefixo: dj" + commands_str)


@bot.event
async def on_voice_state_update(member, _, after):
    if member == bot.user and after.channel == None:
        await dj.reset()


@bot.event
async def on_ready():
    print("Conectado")
    yt_handler.loop = asyncio.get_running_loop()


@bot.event
async def on_message(msg: Message):
    if msg.author == bot.user:
        return

    await bot.process_commands(msg)


@bot.command()
async def tchau(ctx: Context):
    if await pre_flight(ctx) == "same_channel":
        yt_handler.reset()
        dj.reset()


@bot.command()
async def parou(ctx: Context):
    if await pre_flight(ctx) == "same_channel":
        if yt_handler.playing:
            yt_handler.stop()
        else:
            yt_handler.resume()


@bot.command()
async def pula(ctx: Context):
    if await pre_flight(ctx) == "same_channel":
        if len(yt_handler.queue) > 0:
            yt_handler.skip()
        else:
            yt_handler.stop()


async def announce_track(ctx: Context, title, duration, user):
    return await ctx.send(
        "Tocando: " + title + "\n"
        + "Duração: " + duration + "\n"
        + "Pedido por: " + user)


@bot.command()
async def fila(ctx: Context):
    queue_str = ""

    if len(yt_handler.queue) > 0:
        queue = yt_handler.queue
        for i in range(len(yt_handler.queue)):
            queue_str += f"{i}. " + queue[i][0] + " == " + queue[i][3] + "\n"
    else:
        queue_str = "Fila vazia amor"

    await ctx.send(queue_str)


@bot.command()
async def toca(ctx: Context, arg: str):
    if not yt_handler.leave_callback:
        async def announce_leave(message: str):
            await ctx.send(message)

        yt_handler.leave_callback = announce_leave

    bot_status = await pre_flight(ctx)

    if arg.find("youtube") == -1:
        await ctx.send("Não é link do youtube endeota")
        return

    if bot_status == "free":
        await ctx.send("Só um estante")
        await dj.join_channel(ctx.author.voice.channel)
        info = await yt_handler.play(arg, dj.voice_client)
        await announce_track(ctx, info["title"], info["duration"], ctx.author.name)

    if bot_status == "same_channel":
        if not yt_handler.playing:
            await ctx.send("Só um estante")
            info = await yt_handler.play(arg, dj.voice_client)
            await announce_track(ctx, info["title"], info["duration"], ctx.author.name)

        else:
            if not yt_handler.message_callback:
                async def message_callback(title, duration, user):
                    await ctx.send(
                        "Tocando: " + title + "\n"
                        + "Duração: " + duration + "\n"
                        + "Pedido por: " + user)

                yt_handler.message_callback = message_callback

            await ctx.send("Tá bom, tá bom, calma")
            track = await yt_handler.enqueue(arg, ctx.author.name)
            await ctx.send("Butando " + track[0] + " na fila," + " posicão " + str(track[1] + 1))


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
