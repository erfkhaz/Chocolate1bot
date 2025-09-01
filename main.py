import telebot
import time
import os
import json
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7714665335:AAFWB6pC9zc6UcgygQ5cKV8W9yp_zUPgYUk"
DELETE_AFTER = int(os.getenv("DELETE_AFTER", "30"))
ADMIN_ID = 6240676264

bot = telebot.TeleBot(BOT_TOKEN)

FILES_DB = "files.json"
CHANNELS_DB = "channels.json"
USERS_DB = "users.json"
FILES = {}
USER_REQUESTS = {}
USER_VERIFIED = {}
REQUIRED_CHANNELS = []
ALL_USERS = set()

if os.path.exists(USERS_DB):
with open(USERS_DB, "r", encoding="utf-8") as f:
try:
ALL_USERS.update(json.load(f))
except:
pass

if os.path.exists(FILES_DB):
with open(FILES_DB, "r", encoding="utf-8") as f:
try:
FILES.update(json.load(f))
except:
FILES = {}

if os.path.exists(CHANNELS_DB):
with open(CHANNELS_DB, "r", encoding="utf-8") as f:
try:
REQUIRED_CHANNELS = json.load(f)
except:
REQUIRED_CHANNELS = []
else:
REQUIRED_CHANNELS = ["boz_majeh", "moovano"]
with open(CHANNELS_DB, "w", encoding="utf-8") as f:
json.dump(REQUIRED_CHANNELS, f)

def save_users():
with open(USERS_DB, "w", encoding="utf-8") as f:
json.dump(list(ALL_USERS), f)

def delete_later(chat_id, msg_id, delay):
time.sleep(delay)
try:
bot.delete_message(chat_id, msg_id)
except:
pass

@bot.message_handler(commands=['start'])
def start_handler(message):
user_id = message.chat.id
ALL_USERS.add(user_id)
save_users()

args = message.text.split()  
file_key = args[1] if len(args) > 1 else None  

if file_key:  
    USER_REQUESTS[user_id] = file_key  

not_joined = []  
for ch in REQUIRED_CHANNELS:  
    try:  
        member = bot.get_chat_member(f"@{ch}", user_id)  
        if member.status == 'left':  
            not_joined.append(ch)  
    except:  
        not_joined.append(ch)  

if not not_joined:  
    USER_VERIFIED[user_id] = True  
    send_requested_file(user_id)  
    return  

markup = InlineKeyboardMarkup(row_width=1)  
for ch in not_joined:  
    markup.add(InlineKeyboardButton(f"عضویت در @{ch}", url=f"https://t.me/{ch}"))  
markup.add(InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership"))  
bot.send_message(user_id, "قبل از دریافت فایل، باید عضو کانال‌های زیر بشی 😘", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
user_id = call.from_user.id
not_joined = []

for ch in REQUIRED_CHANNELS:  
    try:  
        member = bot.get_chat_member(f"@{ch}", user_id)  
        if member.status == 'left':  
            not_joined.append(ch)  
    except:  
        not_joined.append(ch)  

if not_joined:  
    text = "😢 هنوز عضو همه کانالا نشدی:\n\n"  
    markup = InlineKeyboardMarkup(row_width=1)  
    for ch in not_joined:  
        text += f"🔹 @{ch}\n"  
        markup.add(InlineKeyboardButton(f"عضویت در @{ch}", url=f"https://t.me/{ch}"))  
    text += "\nعضو شو و دوباره روی دکمه زیر بزن 😘"  
    markup.add(InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership"))  
    try:  
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup)  
    except:  
        pass  
    bot.answer_callback_query(call.id, "همه کانالا عضو نیستی 😔")  
else:  
    USER_VERIFIED[user_id] = True  
    bot.answer_callback_query(call.id, "عضویت تایید شد 💖")  
    try:  
        bot.delete_message(call.message.chat.id, call.message.message_id)  
    except:  
        pass  
    bot.send_message(user_id, "✅ عضویت تایید شد! صبر کن فایل بیاد برات...")  
    send_requested_file(user_id)

def send_requested_file(user_id):
file_key = USER_REQUESTS.get(user_id)
if file_key and file_key in FILES:
data = FILES[file_key]
ftype = data['type']
file_id = data.get('file_id')
caption = data.get('caption', None)

if ftype == 'photo':  
        sent = bot.send_photo(user_id, file_id, caption=caption)  
    elif ftype == 'video':  
        sent = bot.send_video(user_id, file_id, caption=caption)  
    elif ftype == 'document':  
        sent = bot.send_document(user_id, file_id, caption=caption)  
    elif ftype == 'audio':  
        sent = bot.send_audio(user_id, file_id, caption=caption)  
    elif ftype == 'voice':  
        sent = bot.send_voice(user_id, file_id, caption=caption)  
    elif ftype == 'text':  
        sent = bot.send_message(user_id, caption or "📄 متن بدون عنوان")  
    elif ftype == 'subtitle':  
        sent = bot.send_document(user_id, file_id, caption=caption)  
    else:  
        sent = bot.send_message(user_id, "فایل ناشناس بود 😅")  

    bot.send_message(user_id, f"⏳ فایل بالا فقط {DELETE_AFTER} ثانیه می‌مونه! ذخیره‌ش کن 😘")  
    Thread(target=delete_later, args=(user_id, sent.message_id, DELETE_AFTER)).start()

@bot.message_handler(commands=['channels'])
def show_channels(message):
if message.chat.id != ADMIN_ID:
return
if not REQUIRED_CHANNELS:
bot.reply_to(message, "📭 هیچ کانالی تنظیم نشده.")
else:
text = "📢 لیست کانال‌های عضویت اجباری:\n\n"
for ch in REQUIRED_CHANNELS:
text += f"🔹 @{ch}\n"
bot.reply_to(message, text)

@bot.message_handler(commands=['addchannel'])
def add_channel(message):
if message.chat.id != ADMIN_ID:
return
parts = message.text.split()
if len(parts) != 2 or not parts[1].startswith('@'):
bot.reply_to(message, "❌ فرمت درست: /addchannel @username")
return

ch = parts[1][1:]  
if ch in REQUIRED_CHANNELS:  
    bot.reply_to(message, "⚠️ این کانال قبلاً اضافه شده.")  
    return  

REQUIRED_CHANNELS.append(ch)  
with open(CHANNELS_DB, "w", encoding="utf-8") as f:  
    json.dump(REQUIRED_CHANNELS, f)  
bot.reply_to(message, f"✅ کانال @{ch} اضافه شد.")

@bot.message_handler(commands=['removechannel'])
def remove_channel(message):
if message.chat.id != ADMIN_ID:
return
parts = message.text.split()
if len(parts) != 2 or not parts[1].startswith('@'):
bot.reply_to(message, "❌ فرمت درست: /removechannel @username")
return

ch = parts[1][1:]  
if ch not in REQUIRED_CHANNELS:  
    bot.reply_to(message, "⚠️ این کانال تو لیست نیست.")  
    return  

REQUIRED_CHANNELS.remove(ch)  
with open(CHANNELS_DB, "w", encoding="utf-8") as f:  
    json.dump(REQUIRED_CHANNELS, f)  
bot.reply_to(message, f"✅ کانال @{ch} حذف شد.")

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio', 'voice', 'text'])
def handle_upload(message):
if message.chat.id != ADMIN_ID:
return

caption = message.caption or message.text or ""  
file_type = None  
file_id = None  
send_to_all = "#all" in caption.lower()  

if message.photo:  
    file = message.photo[-1]  
    file_type = 'photo'  
    file_id = file.file_id  
elif message.video:  
    file_type = 'video'  
    file_id = message.video.file_id  
elif message.document:  
    filename = message.document.file_name or ""  
    ext = os.path.splitext(filename)[1].lower()  
    if ext in ['.srt', '.vtt']:  
        file_type = 'subtitle'  
    else:  
        file_type = 'document'  
    file_id = message.document.file_id  
elif message.audio:  
    file_type = 'audio'  
    file_id = message.audio.file_id  
elif message.voice:  
    file_type = 'voice'  
    file_id = message.voice.file_id  
elif message.text:  
    file_type = 'text'  

if not file_type:  
    return  

if send_to_all:  
    sent_count = 0  
    for uid in list(ALL_USERS):  
        try:  
            if file_type == 'photo':  
                bot.send_photo(uid, file_id, caption=caption)  
            elif file_type == 'video':  
                bot.send_video(uid, file_id, caption=caption)  
            elif file_type == 'document':  
                bot.send_document(uid, file_id, caption=caption)  
            elif file_type == 'audio':  
                bot.send_audio(uid, file_id, caption=caption)  
            elif file_type == 'voice':  
                bot.send_voice(uid, file_id, caption=caption)  
            elif file_type == 'text':  
                bot.send_message(uid, caption or "📄 متن بدون عنوان")  
            elif file_type == 'subtitle':  
                bot.send_document(uid, file_id, caption=caption)  
            sent_count += 1  
        except:  
            continue  
    bot.reply_to(message, f"📤 فایل برای {sent_count} نفر ارسال شد.")  
else:  
    code = str(int(time.time()))  
    FILES[code] = {  
        "type": file_type,  
        "file_id": file_id,  
        "caption": caption  
    }  
    with open(FILES_DB, "w", encoding="utf-8") as f:  
        json.dump(FILES, f)  
    link = f"https://t.me/{bot.get_me().username}?start={code}"  
    bot.send_message(message.chat.id, f"✅ فایل ذخیره شد!\n\n🔗 لینک اختصاصی: {link}")

print("Bot is running...")
bot.polling()

