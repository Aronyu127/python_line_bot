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
LINE_TARGET_ID = os.environ.get('LINE_TARGET_ID')
IMGUR_CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
GOOD_MORNING_ALBUM_ID = os.environ.get('GOOD_MORNING_ALBUM_ID')
GOOD_MORNING_AUTH = os.environ.get('GOOD_MORNING_AUTH')

imgur_header = {'Authorization': 'Client-ID %s' % IMGUR_CLIENT_ID}
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def main(request):
    body = request.get_data(as_text=True)
    line_receiver_id = request.headers.get('LINE_RECEIVER_ID')

    if line_receiver_id and request.headers.get('GOOD_MORNING_AUTH') == GOOD_MORNING_AUTH:
      push_good_morning_image(line_receiver_id)
    else:
      hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'),
          body.encode('utf-8'), hashlib.sha256).digest()
      signature = base64.b64encode(hash).decode()
      parser = WebhookParser(LINE_CHANNEL_SECRET)

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
    return jsonify({ 'message': 'ok'})

def push_good_morning_image(target_id):
  images = get_images(GOOD_MORNING_ALBUM_ID)
  image_url = random.choice(images)['link']
  line_bot_api.push_message(target_id, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))

def get_images(target_album_id="SUbZW0d"):
    request_url = 'https://api.imgur.com/3/album/%s/images' % target_album_id
    response = requests.get(request_url, headers = imgur_header)
    data = json.loads(response.text)
    images = data['data']
    return images
