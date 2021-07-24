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
IMGUR_ACCESS_TOKEN = os.environ.get('IMGUR_ACCESS_TOKEN')
BEAUTY_ALBUM_ID = os.environ.get('BEAUTY_ALBUM_ID')
MAIN_ALBUM_ID = os.environ.get('MAIN_ALBUM_ID')

imgur_header = {'Authorization': 'Client-ID %s' % IMGUR_CLIENT_ID}
imgur_auth_header = {'Authorization': 'Bearer %s' % IMGUR_ACCESS_TOKEN}
 
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
        if not isinstance(event.message, TextMessage): 
            continue
        text = event.message.text
        if '新增圖片\n' in text:
          tmp, desc, image_url = text.split('\n')
          response = upload_image_by_url(image_url, desc, MAIN_ALBUM_ID)
          message = ('格式錯誤 新增失敗', '新增成功')[response.status_code == 200]
          reply_instance = TextSendMessage(text=message)
        elif text == '關鍵字查詢':
          images = get_images(MAIN_ALBUM_ID)
          desc_list = [image['description'] for image in images]
          #uniqueness
          uniq_desc_list = list(set(desc_list))
          reply_instance = TextSendMessage(text=','.join(uniq_desc_list))
        else:
            #從一般相簿中過濾 or 從美女相簿中隨機
            if text == '抽':
              images = get_images(BEAUTY_ALBUM_ID)
            else:
              images = [image for image in get_images(MAIN_ALBUM_ID) if image['description'] == text]

            if len(images) == 0:
              return 'do nothing'
            else:
              image_url = random.choice(images)['link']
              reply_instance = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
                
              line_bot_api.reply_message(
                event.reply_token,
                reply_instance
              )
    return jsonify({ 'message': 'ok'})

def get_images(target_album_id="SUbZW0d"):
    request_url = 'https://api.imgur.com/3/album/%s/images' % target_album_id
    response = requests.get(request_url, headers = imgur_header)
    data = json.loads(response.text)
    images = data['data']
    return images

def upload_image_by_url(url, description=None, target_album_id="vr5Ryga"):
    request_url = 'https://api.imgur.com/3/image'
    request_body = { "image": url, "album": target_album_id, "type": 'URL', "description": description}
    response = requests.post(request_url, headers = imgur_auth_header, data = request_body)
    return response
