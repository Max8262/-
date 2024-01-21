LINE_CHANNEL_ACCESS_TOKEN='********'# Insert Your Own LineBot Channel Token
LINE_CHANNEL_SECRET='***********'    # Insert Your Own LineBot Channel Secret
from flask import Flask, request, abort
from linebot.models import FlexSendMessage
from linebot.models import BubbleContainer
from linebot.models import ImageSendMessage
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import pandas as pd
import gspread
import random
from oauth2client.service_account import ServiceAccountCredentials
from linebot.models import FollowEvent, JoinEvent, TextSendMessage
from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageAction, URIAction
from linebot.models import QuickReply, QuickReplyButton, MessageAction
target_number = ''.join(random.sample('0123456789', 4))
# List of words for the hangman game
word_list = ["hangman", "python", "developer", "programming", "chatbot", "openai"]

# Maximum number of incorrect guesses allowed
max_attempts = 6

def choose_word():
    return random.choice(word_list).lower()

Counter=1
list=[1,2,3,4,5,6,7,8,9,10]
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
credentials_file="**********" #download your own API.json file into the same directory
spreadsheet_name = '**********'# name it whatever you want
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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global split_data
    global user_id
    global Money
    global user_message
    user_message=[]
    try:
        if len(event.message.text)==3:
            print("OK")
            user_id = event.source.user_id
            user_message.append(event.message.text)
            Conformation_Message='PLEASE PLACE YOUR ORDER'
        # Adding a quick reply with MessageAction
            quick_reply_items = [
                QuickReplyButton(
                    action=MessageAction(label=str(i), text=str(i))
                ) for i in range(1, 11)
            ]

            quick_reply = QuickReply(items=quick_reply_items)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=Conformation_Message,
                    quick_reply=quick_reply
                )
            )
        elif int(event.message.text) in list:
            user_message.append(event.message.text)
            user_message.append(user_id)
            save_data_to_google_sheets(user_message)
            Received='Received'
            line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Received)
                )
        if len(event.message.text) ==4:
            user_input = event.message.text

            if user_input.isdigit() and len(user_input) == 4:
                result = check_guess(user_input)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=result)
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="Please enter a valid 4-digit number.")
                )
    except ValueError:
        user_input = event.message.text.lower()

        if user_input == "..":
            start_game(event.reply_token)
        elif user_input.isalpha() and len(user_input) == 1:
            make_guess(event.reply_token,context, user_input)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Please enter a single letter as your guess.")
            )

def start_game(reply_token):
    global context
    word_to_guess = choose_word()
    hidden_word = ["_"] * len(word_to_guess)
    incorrect_guesses = 0
    guessed_letters = set()

    reply_message = f"Let's play Hangman!\n\n{' '.join(hidden_word)}"

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=reply_message)
    )

    context = {
        'word_to_guess': word_to_guess,
        'hidden_word': hidden_word,
        'incorrect_guesses': incorrect_guesses,
        'guessed_letters': guessed_letters
    }

    context_to_session(reply_token, context)
def make_guess(reply_token, context, user_input):
    guess = user_input.lower()
    if guess in context.get('guessed_letters', set()):
        reply_message = "You already guessed that letter. Try again."
    elif guess in context['word_to_guess']:
        reveal_letters(context, guess)
        reply_message = f"Good guess!\n\n{' '.join(context['hidden_word'])}"
    else:
        context['incorrect_guesses'] += 1
        reply_message = f"Wrong guess! Attempts remaining: {max_attempts - context['incorrect_guesses']}\n\n{' '.join(context['hidden_word'])}"

    context.setdefault('guessed_letters', set()).add(guess)

    if "_" not in context['hidden_word']:
        reply_message += "\n\nCongratulations! You guessed the word!"
        reset_session(reply_token)
    elif context['incorrect_guesses'] == max_attempts:
        reply_message += f"\n\nGame over! The word was '{context['word_to_guess']}'."
        reset_session(reply_token)
    else:
        reply_message += f"\n\nGuessed letters: {' '.join(context.get('guessed_letters', set()))}"

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=reply_message)
    )

    context_to_session(reply_token, context)
def reveal_letters(context, guess):
    for i, letter in enumerate(context['word_to_guess']):
        if letter == guess:
            context['hidden_word'][i] = guess

def context_to_session(reply_token, context):
    session_key = f"hangman_{reply_token}"
    app.config[session_key] = context

def get_context_from_session(reply_token):
    session_key = f"hangman_{reply_token}"
    return app.config.get(session_key, {})

def reset_session(reply_token):
    session_key = f"hangman_{reply_token}"
    app.config.pop(session_key, None)

def save_data_to_google_sheets(data):
    # Authenticate with Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(credentials)

    # Open the Google Sheets document
    worksheet = gc.open(spreadsheet_name).sheet1

    # Convert the dictionary to a DataFrame
    data_frame = pd.DataFrame([data], columns=['Class', 'Name'])

    # Append data to the worksheet
    worksheet.append_rows(data_frame.values.tolist(), value_input_option='RAW')


def check_guess(guess):
    bulls = cows = 0
    for i in range(4):
        if guess[i] == target_number[i]:
            bulls += 1
        elif guess[i] in target_number:
            cows += 1

    if bulls == 4:
        return "Congratulations! You guessed the correct number."
    else:
        return f"{bulls}A{cows}B"
