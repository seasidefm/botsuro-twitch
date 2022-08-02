import os
from unittest import result
import requests


class Song:
    def __init__(self, song: dict):
        self.artist = song['artist']
        self.song = song['song']
        self.timestamp = song['timestamp']

    def to_string(self):
        return f"{self.artist} - {self.song}"


class SeasideAPI:
    def __init__(self):
        token = os.environ.get('SEASIDE_API_KEY')
        host = os.environ.get('SEASIDE_API_HOST', default="https://api.seaside.fm")

        if not token:
            raise EnvironmentError("Cannot find SEASIDE_API_KEY! All services should use an API key.")

        self.token = token
        self.host = host

    def __fetch(self, method: str, path: str, data):
        return getattr(requests, method.lower())(
            self.format_url(path),
            json=data,
            headers={
                'Authorization': self.token,
            }
        )

    @staticmethod
    def __parse_fave_response(res):
        if res.status_code == 200:
            return "OK"

        if res.status_code == 204:
            return "UPDATED"

        # Legacy response, must be phased out!
        if res.status_code == 409:
            return "EXISTS"

        # Default to assuming something bad happened
        print(res.json())
        return "ERROR"

    def format_url(self, path: str):
        return f"{self.host}{path}"

    def now_playing(self):
        print('Getting current song')
        result = self.__fetch(
            'GET',
            '/songs/current',
            None
        )

        response = result.json()

        if response['data']:
            return Song(response['data']).to_string()

        print(result, response)
        return "ERROR"

    def last_song(self):
        print('Getting last song')
        result = self.__fetch(
            'GET',
            '/songs/last',
            None
        )

        response = result.json()

        if response['data']:
            return Song(response['data']).to_string()

        print(result, response)
        return "ERROR"

    def add_fave(self, user_id: str, last=False):
        print(f'Adding fave for {user_id}')
        result = self.__fetch(
            'POST',
            '/faves',
            {
                "user_id": user_id,
                "song": "last" if last else "current"
            }
        )

        return self.__parse_fave_response(result)

    def add_superfave(self, user_id: str, last=False):
        print(f'Adding superfave for {user_id}')
        result = self.__fetch(
            'POST',
            '/faves/superfave',
            {
                "user_id": user_id,
                "song": "last" if last else "current"
            }
        )

        return self.__parse_fave_response(result)

    def get_translation(self, lang: str, text: str) -> str:
        print("Getting translation for >")
        print("----------------------------------------------------------")
        print(f"> {text}")
        print("----------------------------------------------------------")

        result = self.__fetch(
            'POST',
            '/translate',
            {
                "text": text,
                "target": lang
            }
        )

        parsed = result.json()

        return parsed['data'] or None


