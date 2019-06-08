import os
import base64, hashlib, hmac
import logging
import random
import json
import requests

from flask import abort, jsonify

from linebot import (
    LineBotApi
)
from linebot.models import (
    ImageSendMessage
)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_TARGET_ID = os.environ.get('LINE_TARGET_ID')
IMGUR_CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
IMGUR_ALBUM_ID = os.environ.get('IMGUR_ALBUM_ID')

def main(request):
    images = get_images(IMGUR_ALBUM_ID)
    image_url = random.choice(images)['link']
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    line_bot_api.push_message(LINE_TARGET_ID, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))

    return jsonify({ 'message': 'ok'})

def get_images(target_album_id="SUbZW0d"):
    imgur_authorization = 'Client-ID %s' % IMGUR_CLIENT_ID
    request_url = 'https://api.imgur.com/3/album/%s/images' % target_album_id
    headers = {'Authorization': imgur_authorization}
    response = requests.get(request_url, headers = headers)
    data = json.loads(response.text)
    images = data['data']
    return images
