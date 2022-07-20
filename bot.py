import os  # for importing env vars for the bot to use
from time import time

from twitchio.ext import commands

import mqtt
from api.service import SeasideAPI
from db import DB
from utils import SongRequest

HELP_MESSAGE = '''
Get song info --> ?song or ?last |
Request future songs --> ?request artist name - song title |
Get movie info --> ?watching or ?w |
Save song to your list --> ?save or ?heart |
SUPER FAVE a song in your list --> ?superfave or ?superheart
'''


def get_context(ctx: commands.Context) -> (int, str):
    return ctx.author.id, ctx.author.name


def get_discord_message() -> str:
    link = os.getenv('DISCORD_LINK')
    return f"Want to join our discord and get to know the community? Link your twitch account to Discord, then join here --> {link}"


emoji = {
    "nod": "seasid3IsForNod",
    "pray": "seasid3IsForPray",
    "cool": "seasid3IsForCool",
    "wave": "seasid3IsForWave",
}


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

        # Init Seaside API interaction
        self.api = SeasideAPI()

        # Setup mqtt client for later
        self.client = mqtt.get_mqtt_client()

    def send_heat_message(self, song: bytes):
        c = self.client
        c.connect(os.environ['MQTT_HOST'], 8883, 60)
        c.publish(topic=mqtt.topics['NEW_HEAT'], payload=song)
        c.disconnect()

    async def event_ready(self):
        # We are logged in and ready to chat and use commands...
        print(f'> Bot ready, logged in as: {self.nick}')
        print(f'> Watching channel(s): {self.channels}')

    # Format responses for current faves
    # ===================================================
    def __format_fave_response(self, result: str, username: str):
        if result == "EXISTS":
            return f"{username} You already saved this song! {emoji['pray']}"
        elif result == "ERROR":
            return f"{username} Something went wrong! Please tell @Duke_Ferdinand {emoji['pray']}"
        else:
            return f"{username} Added to your saved list! {emoji['cool']}"

            # TODO: Move this to the API!
            print("Updating heat for current song")
            song = self.db.current_song()
            print(f"-> {song['song_string']}")
            self.send_heat_message(song['song_string'])

    def __format_superfave_response(self, result: str, username: str):
        if result == "EXISTS":
            return f"{username} You already superfaved this song! {emoji['pray']}"
        elif result == "ERROR":
            return f"{username} Something went wrong! Please tell @Duke_Ferdinand {emoji['pray']}"
        else:
            return f"{username} That's a nice superfave, good taste {emoji['nod']}"

            # TODO: Move this to the API!
            print("Updating heat for current song")
            song = self.db.current_song()
            print(f"-> {song['song_string']}")
            self.send_heat_message(song['song_string'])

    # Format responses for last faves
    # ===================================================
    @staticmethod
    def __format_last_fave(result: str, username: str):
        if result == "EXISTS":
            return f"{username} You already saved that song! {emoji['pray']}"
        elif result == "ERROR":
            return f"{username} Something went wrong! Please tell @Duke_Ferdinand {emoji['pray']}"
        else:
            return f"{username} Added last song to your saved list! {emoji['cool']}"

    @staticmethod
    def __format_last_superfave(result: str, username: str):
        if result == "EXISTS":
            return f"{username} You already superfaved that song! {emoji['pray']}"
        elif result == "ERROR":
            return f"{username} Something went wrong! Please tell @Duke_Ferdinand {emoji['pray']}"
        else:
            return f"{username} Nice! Added that to your superfave list {emoji['nod']}"

    # Helpful
    # ===========================
    @commands.command(name="help", aliases=["h"])
    async def help(self, ctx: commands.Context):
        print(f"> Command 'help' called by: {ctx.author.name}")
        await ctx.send(HELP_MESSAGE)

    # Social
    # ===========================
    @commands.command(name="discord", aliases=["server"])
    async def discord(self, ctx: commands.Context):
        print(f"> Command 'help' called by: {ctx.author.name}")
        await ctx.send(get_discord_message())

    # Fun
    # ===========================
    @commands.command(name="hey", aliases=["hello", "hi"])
    async def hey(self, ctx: commands.Context):
        print(f"> Command 'hey' called by: {ctx.author.name}")
        await ctx.send(f"{ctx.author.display_name} Hey hey heyyyyyy! I'm ride on time {emoji['wave']}")

    # Movie info
    # ===========================
    @commands.command(name="watching", aliases=["w", "movie", "video"])
    async def watching(self, ctx: commands.Context):
        print(f"> Command 'watching' called by: {ctx.author.name}")
        video = await self.db.get_video_title()
        await ctx.send(f"{ctx.author.display_name} This is what we are watching:")
        await ctx.send(video)

    # Song requests
    # ===========================
    @commands.command(name="request")
    async def log_request(self, ctx: commands.Context):
        print(f"> Command 'request' called by: {ctx.author.name}")
        request_args = ctx.message.content.replace('?request', '')
        split = request_args.split(' - ', 1)

        if len(split) >= 2:
            user_id, username = get_context(ctx)
            request = SongRequest({
                "user": username,
                "user_id": user_id,
                "artist": split[0].strip(),
                "song_title": split[1].strip(),
                "request_date": int(time()),
            })

            await self.db.save_request(request)
            await ctx.send(
                f"{ctx.author.display_name} Got it, that's '{request['artist']} - {request['song_title']}' CoolCat"
            )
        else:
            if ctx.author.name == "discosparkle":
                await ctx.send(f"{ctx.author.display_name} Nah b, you playin")
            else:
                await ctx.send(f"Sorry, {ctx.author.display_name} I didn't get that. See ?help for format! {emoji['pray']}")

    # Song ID
    # ===========================
    @commands.command(name="song", aliases=["s", "playing", "current"])
    async def song(self, ctx: commands.Context):
        print(f"> Command 'song' called by: {ctx.author.name}")
        song = self.api.now_playing()
        if song != "ERROR":
            await ctx.send(f"{ctx.author.display_name} Current song: {song}")
        else:
            await ctx.send(f"Something went wrong getting the current song! {emoji['pray']}")

    @commands.command(name="last", aliases=["l", "last-song", "prev"])
    async def last_song(self, ctx: commands.Context):
        print(f"> Command 'last' called by: {ctx.author.name}")
        song = self.api.last_song()
        if song != "ERROR":
            await ctx.send(f"{ctx.author.display_name} Last song: {song}")
        else:
            await ctx.send(f"Something went wrong getting the last song! {emoji['pray']}")

    # Fave commands
    # ===========================
    @commands.command(name="save", aliases=["fave", "heart", "favorite", "love", "like"])
    async def save_song(self, ctx: commands.Context):
        user_id, username = get_context(ctx)
        print(f"> Command 'save' called by: {username}")
        result = self.api.add_fave(user_id)
        response = self.__format_fave_response(result, ctx.author.display_name)
        await ctx.send(response)

    @commands.command(name="save-last", aliases=["fave-last", "heart-last", "favorite-last"])
    async def save_last_song(self, ctx: commands.Context):
        user_id, username = get_context(ctx)
        print(f"> Command 'save' called by: {username}")
        result = self.api.add_fave(user_id, last=True)
        response = self.__format_last_fave(result, ctx.author.display_name)
        await ctx.send(response)

    # Superfave commands
    # ===========================
    @commands.command(name="superfave", aliases=["supersave", "superlove", "superheart"])
    async def super_fave_song(self, ctx: commands.Context):
        user_id, username = get_context(ctx)
        print(f"> Command 'superfave' called by: {username}")
        result = self.api.add_superfave(user_id)
        response = self.__format_superfave_response(result, ctx.author.display_name)
        await ctx.send(response)

    @commands.command(name="superfave-last", aliases=["supersave-last", "superlove-last", "superheart-last"])
    async def super_fave_last(self, ctx: commands.Context):
        user_id, username = get_context(ctx)
        print(f"> Command 'superfave-last' called by: {username}")
        result = self.api.add_superfave(user_id, last=True)
        response = self.__format_last_superfave(result, ctx.author.display_name)
        await ctx.send(response)
