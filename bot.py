import asyncio
import datetime
import os  # for importing env vars for the bot to use
from time import time

from twitchio.ext import commands

import mqtt
from db import DB
from utils import SongRequest

HELP_MESSAGE = '''
Request future songs --> ?request artist name - song title |
Get movie info --> ?watching or ?w |
Save song to your list --> ?save or ?heart
'''


class Bot(commands.Bot):
    def __init__(self):
        self.db = DB()
        print("> DB class ready")

        token = os.environ["BOT_TOKEN"]
        channels = os.environ["CHANNEL"]

        if not token or not channels:
            raise EnvironmentError("Cannot find one of BOT_TOKEN or CHANNEL in env")

        if ',' in channels:
            channels = channels.split(',')
        else:
            channels = [channels]

        super().__init__(token=token, prefix="?", initial_channels=channels)
        self.channels = channels

        # Setup mqtt client for later
        self.client = mqtt.get_mqtt_client()

    def send_heat_message(self, song: bytes):
        c = self.client
        c.connect(os.environ['MQTT_HOST'], 5555, 60)
        c.publish(topic=mqtt.topics['NEW_HEAT'], payload=song)
        c.disconnect()

    async def event_ready(self):
        # We are logged in and ready to chat and use commands...
        print(f'> Bot ready, logged in as: {self.nick}')
        print(f'> Watching channel(s): {self.channels}')

    # Helpful
    # ===========================
    @commands.command(name="help", aliases=["h"])
    async def help(self, ctx: commands.Context):
        print(f"> Command 'help' called by: {ctx.author.name}")
        await ctx.send(HELP_MESSAGE)

    # Fun
    # ===========================
    @commands.command(name="hey", aliases=["hello", "hi"])
    async def hey(self, ctx: commands.Context):
        print(f"> Command 'hey' called by: {ctx.author.name}")
        await ctx.send(f"{ctx.author.name} Hey hey heyyyyyy! I'm ride on time VoHiYo")

    # Movie info
    # ===========================
    @commands.command(name="watching", aliases=["w", "movie", "video"])
    async def watching(self, ctx: commands.Context):
        print(f"> Command 'watching' called by: {ctx.author.name}")
        video = await self.db.get_video_title()
        await ctx.send(f"{ctx.author.name} This is what we are watching:")
        await ctx.send(video)

    # Song requests
    # ===========================
    @commands.command(name="request")
    async def log_request(self, ctx: commands.Context):
        print(f"> Command 'request' called by: {ctx.author.name}")
        request_args = ctx.message.content.replace('?request', '')
        split = request_args.split('-', 1)

        if len(split) >= 2:
            request = SongRequest({
                "user": ctx.author.name,
                "artist": split[0].strip(),
                "song_title": split[1].strip(),
                "request_date": int(time()),
            })

            await self.db.save_request(request)
            await ctx.send(
                f"{ctx.author.name} Got it, that's '{request['artist']} - {request['song_title']}' CoolCat"
            )
        else:
            if ctx.author.name == "discosparkle":
                await ctx.send(f"{ctx.author.name} Nah b, you playin")
            else:
                await ctx.send(f"Sorry, {ctx.author.name} I didn't get that. See ?help for format! BabyRage")

    # Song ID
    # ===========================
    @commands.command(name="song", aliases=["s", "playing", "current"])
    async def song(self, ctx: commands.Context):
        print(f"> Command 'song' called by: {ctx.author.name}")
        song = await self.db.current_song()
        await ctx.send(f"{ctx.author.name} Current song: {song['song_string']}")

    @commands.command(name="last", aliases=["l", "last-song", "prev"])
    async def last_song(self, ctx: commands.Context):
        print(f"> Command 'last' called by: {ctx.author.name}")
        song = await self.db.last_song()
        await ctx.send(f"{ctx.author.name} Last song: {song['song_string']}")

    # Fave commands
    # ===========================
    @commands.command(name="save", aliases=["fave", "heart", "favorite", "love", "like"])
    async def save_song(self, ctx: commands.Context):
        print(f"> Command 'save' called by: {ctx.author.name}")
        result = await self.db.save_current_song(ctx.author.name)
        if result == "already_exists":
            await ctx.send(f"{ctx.author.name} You already saved this song! BabyRage")
        elif result == "no_song":
            await ctx.send(f"{ctx.author.name} No song is playing, use ?fave-last BabyRage")
        else:
            await ctx.send(f"{ctx.author.name} Added to your saved list! CoolCat")

            print("Updating heat for current song")
            song = await self.db.current_song()
            print(f"-> {song['song_string']}")
            self.send_heat_message(song['song_string'])

    @commands.command(name="save-last", aliases=["fave-last", "heart-last", "favorite-last"])
    async def save_last_song(self, ctx: commands.Context):
        print(f"> Command 'save-last' called by: {ctx.author.name}")
        result = await self.db.save_last_song(ctx.author.name)
        if result == "already_exists":
            await ctx.send(f"{ctx.author.name} You already saved that song! BabyRage")
        elif result == "no_song":
            await ctx.send(f"{ctx.author.name} No last song to add! BabyRage")
        else:
            await ctx.send(f"{ctx.author.name} Added to your saved list! CoolCat")
