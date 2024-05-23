import os
import json
import base64
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Token:
    def __init__(self):

        url = os.getenv("BASE_URL") + "/api/sessions"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": os.getenv("API_KEY")
        }
        data = {
            "session": {
                "email": os.getenv("EMAIL").strip().replace("\n", ""),
                "password": os.getenv("PASSWORD").strip().replace("\n", "")
            }
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        token = ""
        expires = 0.0
        if response.status_code == 200:
            body = json.loads(response.content.decode('utf-8'))
            decode_token = json.loads(base64.b64decode(body['session']['token'].split('.')[1].encode('utf-8') + b'=='))
            token = decode_token["token"]
            expires = float(decode_token["expires"])

        self.token = token
        self.expires = expires


    def update_token(self) -> None | dict[str, str]:
        url = os.getenv("BASE_URL") + "/api/sessions"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": os.getenv("API_KEY")
        }
        data = {
            "session": {
                "email": os.getenv("EMAIL").strip().replace("\n", ""),
                "password": os.getenv("PASSWORD").strip().replace("\n", "")
            }
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        token = ""
        expires = 0.0
        if response.status_code == 200:
            body = json.loads(response.content.decode('utf-8'))
            decode_token = json.loads(base64.b64decode(body['session']['token'].split('.')[1].encode('utf-8') + b'=='))
            token = decode_token["token"]
            expires = float(decode_token["expires"])
        
        self.token = token
        self.expires = expires


    def check_token_expired(self) -> bool:
        provided_time = datetime.fromtimestamp(self.expires)

        current_time = datetime.now()

        if current_time < provided_time:
            return False

        return True
