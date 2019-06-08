import os
import base64, hashlib, hmac
import logging
import random
import json
import requests

from flask import abort, jsonify

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage
)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
IMGUR_CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')

#for collect and upload image
LINE_TARGET_ID = os.environ.get('LINE_TARGET_ID')
GOOD_MORNING_ALBUM_ID = os.environ.get('GOOD_MORNING_ALBUM_ID')

BEAUTY_ALBUM_ID = os.environ.get('BEAUTY_ALBUM_ID')
MAIN_ALBUM_ID = os.environ.get('MAIN_ALBUM_ID')

imgur_header = {'Authorization': 'Client-ID %s' % IMGUR_CLIENT_ID}
 
def main(request):
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    parser = WebhookParser(LINE_CHANNEL_SECRET)

    body = request.get_data(as_text=True)
    hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'),
        body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode()

    if signature != request.headers['X_LINE_SIGNATURE']:
        return abort(405)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return abort(405)


    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if isinstance(event.message, ImageMessage) and (event.source.type == 'room' and event.source.user_id == LINE_TARGET_ID):
            image_message_id = event.message.id
            image_content = line_bot_api.get_message_content(image_message_id).content
            upload_image(image_content, GOOD_MORNING_ALBUM_ID)
        elif isinstance(event.message, TextMessage): 
          text = event.message.text
          if text == '抽':
            #美女相簿全部
            images = get_images(BEAUTY_ALBUM_ID)
          else:
            #一般相簿先找尋描述相同的
            images = [image for image in get_images(MAIN_ALBUM_ID) if image['description'] == text]
          image_url = random.choice(images)['link']
          line_bot_api.reply_message(
              event.reply_token,
              ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
          )
    return jsonify({ 'message': 'ok'})

def get_images(target_album_id="SUbZW0d"):
    request_url = 'https://api.imgur.com/3/album/%s/images' % target_album_id
    response = requests.get(request_url, headers = imgur_header)
    data = json.loads(response.text)
    images = data['data']
    return images

def upload_image(file, target_album_id="vr5Ryga"):
    request_url = 'https://api.imgur.com/3/image'
    request_body = { "image": file, "album": target_album_id, "type": 'file' }
    response = requests.post(request_url, headers = imgur_header, data = request_body)
    return response
