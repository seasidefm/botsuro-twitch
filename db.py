import os
import time

from bson.json_util import dumps
from json import loads

from pymongo import MongoClient
from utils import SongRequest, UserPayload

TEMP_MOVIE_DETAILS = """
Title: Maison Ikkoku |
Synopsis: Maison Ikkoku is a bitter-sweet romantic comedy involving a group of
madcap people who live in a boarding house in 1980s Tokyo. The story focuses
primarily on the gradually developing relationships between Yusaku Godai, a poor
student down on his luck, and Kyoko Otonashi, a young, recently widowed boarding
house manager.
"""


class DB:
    """DB Class
    A convenience wrapper for interacting with the database
    """
    def __init__(self):
        connection_string = os.environ['MONGO_CONNECTION']
        if not connection_string:
            raise EnvironmentError("MONGO_CONNECTION missing in env!")

        self.mongo = MongoClient(connection_string)
        self.db = self.mongo.get_default_database()
        self.collection = self.db.get_collection('requests')

        print("> DB ready for commands")

    @staticmethod
    async def get_video_title():
        return TEMP_MOVIE_DETAILS

    async def save_request(self, req: SongRequest):
        result = self.collection.insert_one(req)
        print(f"Saved request from {req['user']} -> '{req['artist']} - {req['song_title']}'")
        return result

    async def get_requests(self):
        # Get any not marked complete
        requests = self.collection.find({"complete": {"$ne": True}})
        return loads(dumps(list(requests)))

    async def __super_saver(self, user: UserPayload, song_to_superfave):
        super_faves = self.db.get_collection('super_faves')
        already_superfaved = super_faves.find_one({"user": user['user'], "song": song_to_superfave})

        if already_superfaved is None:
            super_faves.insert_one({
                    "user": user["user"],
                    "twitch_id": user["user_id"],
                    "song": song_to_superfave,
                    "date": int(time.time())
                })
            return "added"
        else:
            return "already_exists"

    async def __song_saver(self, user: UserPayload, song_to_add: dict):
        fave_songs = self.db.get_collection('saved_songs')
        user_list = fave_songs.find({"user": user['user']})
        results = list(user_list)
        if len(results) == 0:
            print(f"User list not found for {user}, creating...")
            res = fave_songs.insert_one({
                "user": user['user'],
                "twitch_id": user['user_id'],
                "songs": [{
                    "song": song_to_add,
                    "date": int(time.time())
                }]
            })
            print(res)
            return "created"
        else:
            fave_data = results[0]
            song_titles = []

            for song in fave_data['songs']:
                song_titles.append(song["song"])

            if song_to_add not in song_titles:
                new_song_list = fave_data['songs'] + [{
                    "song": song_to_add,
                    "date": int(time.time())
                }]
                fave_songs.update_one({
                    "user": {
                        "$eq": user['user']
                    }
                }, {
                    "$set": {
                        "twitch_id": user['user_id'],
                        "songs": new_song_list
                    }
                })
                return "added"
            else:
                return "already_exists"

    async def super_fave_song(self, user: UserPayload):
        current_song = (await self.current_song())['song_string']
        if current_song == "":
            return "no_song"
        return await self.__super_saver(user, current_song)

    async def save_current_song(self, user: UserPayload):
        current_song = (await self.current_song())['song_string']
        if current_song == "":
            return "no_song"
        return await self.__song_saver(user, current_song)

    async def save_last_song(self, user: UserPayload):
        last_song = (await self.last_song())['song_string']
        if last_song == "":
            return "no_song"
        return await self.__song_saver(user, last_song)

    def current_song(self):
        collection = self.db.get_collection('current_song')
        requests = collection.find({"type": "current_song"})
        return list(requests)[0]

    async def last_song(self):
        collection = self.db.get_collection('current_song')
        requests = collection.find({"type": "last_song"})
        return list(requests)[0]
