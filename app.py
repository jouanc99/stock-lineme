# $pip install random time os twstock pandas matplotlib datetime
# #pip install pymongo imgurpython flask
# 在 requirements.txt 中輸入所需以下套件放於同一資料夾內
# -------
import random
import time
import os
import twstock
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from pymongo import MongoClient
from imgurpython import ImgurClient
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser, WebhookHandler)
from linebot.exceptions import (
    InvalidSignatureError)
from linebot.models import *
from flask import Flask, request, abort
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,TemplateSendMessage,ButtonsTemplate,PostbackTemplateAction)
matplotlib.use('Agg')
# -------

app = Flask(__name__)
'''line bot token/secret'''
# channel_secret_8 = 'your channel_secret'
# channel_access_token_8 = 'your channel_access_token'
linebotapi = LineBotApi(os.environ['LineToken'])
parser = WebhookParser(os.environ['LineSecret'])

'''stock bot'''
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # 若為MessageEvent且為TextMessage, echos
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        text=event.message.text

        # for productor infor
        # 輸出api secret
        if(text.lower()=='me'):
            content = str(event.source.user_id)

            linebotapi.reply_message(
                event.reply_token,
                TextSendMessage(text=content)
            )
        # 輸出使用者資料
        elif(text.lower() == 'profile'):
            profile = linebotapi.get_profile(event.source.user_id)
            my_status_message = profile.status_message
            if not my_status_message:
                my_status_message = '-'
            linebotapi.reply_message(
                event.reply_token, [
                    TextSendMessage(
                        text='Display name: ' + profile.display_name
                    ),
                    TextSendMessage(
                        text='picture url: ' + profile.picture_url
                    ),
                    TextSendMessage(
                        text='status_message: ' + my_status_message
                    ),
                ]
            )

        # 輸出查詢股票開收盤/五日價格/成交量/分析
        elif(text.startswith('#')):
            text = text[1:]
            content = ''

            stock_rt = twstock.realtime.get(text)
            my_datetime = datetime.fromtimestamp(stock_rt['timestamp']+8*60*60)
            my_time = my_datetime.strftime('%H:%M:%S')

            # 印出基本資訊
            content += '%s (%s) %s\n' %(
                stock_rt['info']['name'],
                stock_rt['info']['code'],
                my_time)
            content += '現價：%s\n' %(
                format(float(stock_rt['realtime']['latest_trade_price']), '.1f'))
            content += '開盤：%s\n' %(
                format(float(stock_rt['realtime']['open']), '.1f'))
            content += '最高：%s\n' %(
                format(float(stock_rt['realtime']['high']), '.1f'))
            content += '最低：%s\n' %(
                format(float(stock_rt['realtime']['low']), '.1f'))
            content += '成交量：%s\n' %(
                format(float(stock_rt['realtime']['accumulate_trade_volume']), '.1f'))

            # 印出五日股價
            stock = twstock.Stock(text)
            time.sleep(random.randint(5, 10)) # 休
            content += '-----\n'
            content += '最近五日價格：\n'
            price5 = stock.price[-5:][::-1]
            date5 = stock.date[-5:][::-1]
            for i in range(5):
                if i < 4:
                    content += '[%s] %s\n' %(date5[i].strftime("%Y/%m/%d"), price5[i])
                else:
                    content += '[%s] %s\n' %(date5[i].strftime("%Y/%m/%d"), price5[i])

            # 四大買賣點分析
            content += '-----\n'
            content += '四大買賣點分析\n'
            bst4 = twstock.BestFourPoint(stock)
            if bst4.best_four_point_to_buy() != False:
                content += '買點：'
                content += bst4.best_four_point_to_buy()
                content += '\n'
            else:
                content += '非買點\n'
            if bst4.best_four_point_to_sell() != False:
                content += '賣點：'
                content += bst4.best_four_point_to_sell()
            else:
                content += '非賣點'

            linebotapi.reply_message(
                event.reply_token,
                TextSendMessage(text=content)
            )

        # 繪製股票近期線圖
        elif(text.startswith('/')):
            text = text[1:]
            fn = '%s.png' %(text)
            stock = twstock.Stock(text)
            time.sleep(random.randint(5, 10))  # 休
            my_data = {'close':stock.close, 'date':stock.date, 'open':stock.open}
            df1 = pd.DataFrame.from_dict(my_data)

            df1.plot(x='date', y='close')
            plt.title('[%s]' %(stock.sid))
            plt.savefig(fn)
            plt.close()

            # 上傳成圖檔
            #----------------------
            # imgur with account: your mail account
            client_id = 'your client id'
            client_secret = 'your client secret'
            #----------------------

            client = ImgurClient(client_id, client_secret)
            print("Uploading image... ")
            image = client.upload_from_path(fn, anon=True)
            print("Done")

            url = image['link']
            image_message = ImageSendMessage(
                original_content_url=url,
                preview_image_url=url
            )

            linebotapi.reply_message(
                event.reply_token,
                image_message
                )

    return 'OK'


@app.route("/", methods=['GET'])
def basic_url():
    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)