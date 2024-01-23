LINE_CHANNEL_ACCESS_TOKEN='###########' # Pls insert Channel Token
LINE_CHANNEL_SECRET='#############'    # Pls insert Channel Secret
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from linebot.models import FollowEvent, JoinEvent, TextSendMessage
from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageAction, URIAction
Counter=1
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
credentials_file="###########" # You can put your own json file from Google 
spreadsheet_name = '########' # Make sure to name it correctly with the one you set up in Google Sheets
@app.route("/", methods=["POST"])
def webhook_handler():
    # verify signature if needed
    # add logic to handle the request
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(code=400,description="An error has been raised")
        # 或是 abort(400) 也可以... 目的是要回報 Bad Request，至於為什麼是400...請看文章下方...
    return 'OK'

@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    # Send a welcome message to the user
    welcome_message = f'''
1.豬肉肥而不膩、瘦而不柴\n
2.蛋黃超級香\n
3.配料充實\n
4.糯米很有嚼勁不過軟 不過硬\n



糯米彈牙，覆了一層飽滿且誘人的油光，接著蛋黃的鹹味經細細品嚐後在齒縫間綻開，最後是豬肉的豐盈口感和層次變化，令人驚艷!
'''
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_message))

@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    welcome_message = f'''
1.豬肉肥而不膩、瘦而不柴
2.蛋黃超級香
3.配料充實
4.糯米很有嚼勁不過軟 不過硬



~~糯米彈牙，覆了一層飽滿且誘人的油光，接著蛋黃的鹹味經細細品嚐後在齒縫間綻開，最後是豬肉的豐盈口感和層次變化，令人驚艷!~~
'''
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_message))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global split_data
    global user_id
    global Money
    if event.message.text.lower().replace("\n","") not in ["y", "是", "對"]:
        user_id = event.source.user_id
        user_message = event.message.text
        split_data=user_message.split()
        Conformation=split_data[2]
        Money=int(split_data[2])*35
        Money_message=f"Accumulated Money is " + str(Money)
        split_data.append(Money)
        split_data.append(user_id)
        Conformation_Message = f"Is your Order: {Conformation} balls (Y/N)\nAccumulated Money is {Money}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=Conformation_Message))
    else:
        save_data_to_google_sheets(split_data)
    # Respond with a message containing the assigned number
        reply_message = f"Your number is {user_id}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

def save_data_to_google_sheets(data):
    # Authenticate with Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(credentials)

    # Open the Google Sheets document
    worksheet = gc.open(spreadsheet_name).sheet1

    # Convert the dictionary to a DataFrame
    data_frame = pd.DataFrame([data], columns=['Class', 'Name','quantity' ,'Money' ,'User_ID'])

    # Append data to the worksheet
    worksheet.append_rows(data_frame.values.tolist(), value_input_option='RAW')
