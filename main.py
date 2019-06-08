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
LINE_TARGET_ID = os.environ.get('LINE_TARGET_ID')
IMGUR_CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
IMGUR_ACCESS_TOKEN = os.environ.get('IMGUR_ACCESS_TOKEN')
IMGUR_BEAUTY_ALBUM_ID = os.environ.get('IMGUR_BEAUTY_ALBUM_ID')
IMGUR_IMAGE_SOURCE_ALBUM_ID = os.environ.get('IMGUR_IMAGE_SOURCE_ALBUM_ID')
IMGUR_UPLOAD_ALBUM_ID = os.environ.get('IMGUR_UPLOAD_ALBUM_ID')
 
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
            upload_image(image_content, IMGUR_UPLOAD_ALBUM_ID)
        elif isinstance(event.message, TextMessage): 
          text = event.message.text
          if text == '抽':
            #美女相簿全部
            images = get_images(IMGUR_BEAUTY_ALBUM_ID)
          else:
            #一般相簿先找尋描述相同的
            images = [image for image in get_images(IMGUR_IMAGE_SOURCE_ALBUM_ID) if image['description'] == text]
          image_url = random.choice(images)['link']
          line_bot_api.reply_message(
              event.reply_token,
              ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
          )
    return jsonify({ 'message': 'ok'})

def get_images(target_album_id="SUbZW0d"):
    imgur_authorization = 'Client-ID %s' % IMGUR_CLIENT_ID
    request_url = 'https://api.imgur.com/3/album/%s/images' % target_album_id
    headers = {'Authorization': imgur_authorization}
    response = requests.get(request_url, headers = headers)
    data = json.loads(response.text)
    images = data['data']
    return images

def upload_image(file, target_album_id="vr5Ryga"):
    imgur_authorization = 'Bearer %s' % IMGUR_ACCESS_TOKEN
    headers = {'Authorization': imgur_authorization}
    request_url = 'https://api.imgur.com/3/image'
    data = { "image": file, "album": target_album_id, "type": 'file' }
    response = requests.post(request_url, headers = headers, data = data)
    return response
