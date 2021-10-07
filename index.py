from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import os, sys, re, time, sqlite3, moviepy.editor as mp
from shutil import rmtree
from config import *

app = Client('bot', api_id, api_hash, bot_token=token)
conn = sqlite3.connect('data.db')

c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, status TEXT DEFAULT '', time INTEGER NOT NULL)""")
conn.commit()

def button(_type):
    if _type == 'user':
        reply_markup = [
            [InlineKeyboardButton('convert mp4 to mp3', callback_data='mp4-mp3'), InlineKeyboardButton('convert mp4 to gif', callback_data='mp4-gif')]
        ]
    if _type == 'back':
        reply_markup = [[InlineKeyboardButton('Back', callback_data='Back')]]
    return InlineKeyboardMarkup(reply_markup)

@app.on_message(~filters.channel)
async def _(_, message: Message):
    def check(pattern, string = None, flags = re.I) -> re.Match:
        return re.match(f"^{pattern}$", string or message.text or '', flags)
    user = message.from_user
    user_id = user.id if bool(user and user.id) else 0
    status: str = c.execute(f'SELECT status FROM users WHERE id = {user_id}').fetchone()[0] if bool(c.execute(f'SELECT EXISTS (SELECT status FROM users WHERE id = {user_id})').fetchone()[0]) else ''
    
    if check('/start'):
        if not c.execute(f'SELECT EXISTS (SELECT status FROM users WHERE id = {user_id})').fetchone()[0]:
            await message.reply(f'Welcome to the bot, {user.first_name}🌹', reply_markup = button('user'))
            c.execute(f'''INSERT INTO users VALUES ({user_id}, '', {int(time.time())}) ''')
        else:
            await message.reply(f'Welcome Back, {user.first_name}🌹', reply_markup = button('user'))
            c.execute(f'''UPDATE users SET status = '' WHERE id = '{user_id}' ''')
    
    if user_id in sudo:
        if check('/r'):
            c.execute(f'''UPDATE users SET status = '' WHERE id = '{user_id}' ''')
            conn.commit()
            await message.reply('➜ ReStart')
            os.execl(sys.executable, sys.executable, *sys.argv)
    
    if check('mp4-mp3', status):
        if message.video:
            c.execute(f'''UPDATE users SET status = '' WHERE id = '{user_id}' ''')
            folder = f'downloads/{user_id}/'
            if not os.path.exists(folder): os.mkdir(folder)
            name = await message.download(folder)
            msg = await message.reply('Please wait')
            with mp.VideoFileClip(name) as video:
                filename = folder+'music.mp3'
                video.save_frame(folder+'png.png')
                video.audio.write_audiofile(filename)
            await message.reply_audio(filename, title=f'{user_id}.mp3', thumb=folder+'/png.png')
            await msg.delete()
            await message.reply(f'Thanks {user.first_name} for using my bot 🌹', reply_markup = button('user'))
            rmtree(folder)
        else:
            await message.reply('Please send a video', reply_markup = button('back'))
    if check('mp4-gif', status):
        if message.video:
            folder = f'downloads/{user_id}/'
            if not os.path.exists(folder): os.mkdir(folder)
            name = await message.download(folder)
            msg = await message.reply('Please wait')
            c.execute(f'''UPDATE users SET status = '' WHERE id = '{user_id}' ''')
            with mp.VideoFileClip(name, audio=False) as video:
                filename = folder+'video.mp4'
                video.write_videofile(filename)
            await message.reply_animation(filename)
            await msg.delete()
            await message.reply(f'Thanks {user.first_name} for using my bot 🌹', reply_markup = button('user'))
            rmtree(folder)
        else:
            await message.reply('Please send a video', reply_markup = button('back'))
    conn.commit()

@app.on_callback_query()
async def callback(_, callback: CallbackQuery):
    def check(pattern, string = None, flags = re.I) -> re.Match:
        return re.match(f"^{pattern}$", string or callback.data, flags)
    user = callback.from_user
    user_id = user.id
    
    if (r := check('mp4-mp3|mp4-gif')):
        await callback.edit_message_text('send your video', reply_markup = button('back'))
        c.execute(f'''UPDATE users SET status = '{r.group()}' WHERE id = '{user_id}' ''')
    if check('Back'):
        await callback.edit_message_text('Welcome back', reply_markup = button('user'))
        c.execute(f'''UPDATE users SET status = '' WHERE id = '{user_id}' ''')
    conn.commit()

app.run()