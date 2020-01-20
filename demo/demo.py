import logging

from pathlib import Path
from textwrap import dedent
from neotasker import task_supervisor
mydir = Path(__file__).parent.as_posix()

import sys

sys.path.insert(0, mydir + '/..')

from tebot import TeBot

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('tebot').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.WARNING)

reply_markup = {
    'inline_keyboard': [[{
        'text': '🐈 Picture',
        'callback_data': '/pic'
    }], [{
        'text': '📹 Video',
        'callback_data': '/vid'
    }], [{
        'text': '⚠️  Alert',
        'callback_data': '/alert'
    }]]
}

mybot = TeBot(interval=2)
with open(mydir + '/../demo_tebot_token.dat') as fh:
    mybot.set_token(fh.read().strip())


@mybot.route(path=['/start', '/help'])
def start(chat_id, **kwargs):
    mybot.send(chat_id,
               text=dedent("""
                <b>Hello, I'm using free Python library
                https://github.com/alttch/tebot</b>
                Test commands:

                /pic: send test picture
                /vid: send test video
                any text: echo it back
                """),
               reply_markup=reply_markup)


@mybot.route(methods='message')
def my_message(chat_id, text, **kwargs):
    mybot.send(text=f'got message:\n---\n{text}\n---')
    mybot.send(text='choose option', reply_markup=reply_markup)


@mybot.route(methods='*')
def default_cmd_handler(chat_id, path, **kwargs):
    mybot.send(text=f'command not implemented: {path}')
    mybot.send(text='choose option', reply_markup=reply_markup)


@mybot.route(path='/pic', methods='*')
def pic(chat_id, **kwargs):
    with open(f'{mydir}/data/cat.jpg', 'rb') as fh:
        media = fh.read()
    mybot.send(text='test pic', media=media)
    mybot.send(text='choose option', reply_markup=reply_markup)


@mybot.route(path='/vid', methods='*')
def vid(chat_id, **kwargs):
    with open(f'{mydir}/data/cat.mp4', 'rb') as fh:
        media = fh.read()
    mybot.send_video(text='test video', media=media)
    mybot.send(text='choose option', reply_markup=reply_markup)


@mybot.route(path='/alert', methods='query')
def alert(**kwargs):
    return {'text': 'ACHTUNG!!! DIE KATZE!!!', 'show_alert': True}


task_supervisor.create_aloop('default', default=True)
task_supervisor.start()

mybot.start()
