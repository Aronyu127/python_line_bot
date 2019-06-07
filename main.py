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

def main(request):
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
    channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

    line_bot_api = LineBotApi(channel_access_token)
    parser = WebhookParser(channel_secret)

    body = request.get_data(as_text=True)
    hash = hmac.new(channel_secret.encode('utf-8'),
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
        if not isinstance(event.message, ImageMessage):
            continue

        image_url = get_random_image_url()
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        )
    return jsonify({ 'message': 'ok'})
def get_random_image_url(target_album_id="SUbZW0d"):
    imgur_client_id = "88377d50670b893"
    imgur_authorization = 'Client-ID %s' % imgur_client_id
    request_url = 'https://api.imgur.com/3/album/%s/images' % target_album_id
    headers = {'Authorization': imgur_authorization}
    response = requests.get(request_url, headers = headers)
    data = json.loads(response.text)
    images = data['data']
    return random.choice(images)['link']
    # imgur_access_token = "1123aca8af562d84650f8d9ad70f595842a6e43c"
