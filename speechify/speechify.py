from tabulate import tabulate
import requests
import base64
from typing import List
import io

class SpeechifyAPI:
    """
    A class to interact with the Speechify API.
    """
    def __init__(self):
        """
        Initializes the Speechify API client.
        """
        self.session = requests.Session()
        self.base_url = "https://audio.api.speechify.com"
        self.timeout = 60

        self.headers = {
            "content-type": "application/json",
            "Accept": "*/*",
            "Accept-Base64": "true",
            "Accept-Language": "es-419,es;q=0.6",
            "Origin": "https://speechify.com",
            "Referer": "https://speechify.com/",
            "Sec-GPC": "1",
            "X-Speechify-Client": "EmbeddableSpeechify",
            "X-Speechify-Client-Version": "0.1.301"
        }
        self.session.timeout = self.timeout
        self.session.headers.update(self.headers)

    def get_client_voices(self) -> str:
        """
        Retrieves a list of available client voices from the Speechify API.
        Returns a formatted table with voice information.
        """
        url = f"{self.base_url}/v1/synthesis/client-voices"
        response = self.session.get(url)
        data = response.json()["config"]["onboarding"]["selectableVoices"]
        headers = ("displayName", "name", "gender", "engine", "language")

        voice_info_list: List[List[str]] = []
        for items in data.values():
            voice_info_list.extend([[voice_data.get(value) for value in headers] for voice_data in items])

        return tabulate(voice_info_list, headers, tablefmt="heavy_grid")

    def generate_audio_files(self, paragraph: str, name: str, engine: str, language: str) -> str:
        """
        Generates an audio file from a given paragraph using the Speechify API.
        Args:
            paragraph (str): The text to be converted to audio.
            name (str): The name of the voice to use.
            engine (str): The engine to use for synthesis.
            language (str): The language code for the synthesis.
        Returns:
            str: A success message if the file is generated successfully.
        """
        url = f"{self.base_url}/generateAudioFiles"
        payload = {
            "audioFormat": "mp3",
            "paragraphChunks": [paragraph],
            "voiceParams": {
                "name": name,
                "engine": engine,
                "languageCode": language
            }
        }
        response = self.session.post(url, json=payload)
        data = response.json()
        audio_stream_bytes: bytes = base64.b64decode(data["audioStream"])
        audio_io = io.BytesIO(audio_stream_bytes)
    
        return audio_io  # Retornar BytesIO
