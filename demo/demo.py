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
def start(**kwargs):
    mybot.send(dedent("""
                <b>Hello, I'm using free Python library
                https://github.com/alttch/tebot</b>
                Test commands:

                /pic: send test picture
                /vid: send test video
                any text: will echo it back
                file: will calculate its sha256 sum
                """),
               reply_markup=reply_markup)


@mybot.route(methods='message')
def my_message(text, payload, **kwargs):
    if 'photo' in payload or 'video' in payload or 'audio' in payload:
        mybot.send('please send media as a file')
    elif 'document' in payload:
        data = mybot.get_file_content(payload['document'].get('file_id'))
        if data is None:
            mybot.send('unable to download file')
        else:
            import hashlib
            h = hashlib.sha256(data).hexdigest()
            mybot.send(f'SHA256: {h}')
    else:
        mybot.send(f'got message:\n---\n{text}\n---')
    mybot.send('choose an option', reply_markup=reply_markup)


@mybot.route(methods='*')
def default_cmd_handler(path, **kwargs):
    mybot.send(f'command not implemented: {path}')
    mybot.send('choose an option', reply_markup=reply_markup)


@mybot.route(path='/pic', methods='*')
def pic(**kwargs):
    with open(f'{mydir}/data/cat.jpg', 'rb') as fh:
        media = fh.read()
    mybot.send('test pic', media=media)
    mybot.send('choose an option', reply_markup=reply_markup)


@mybot.route(path='/vid', methods='*')
def vid(**kwargs):
    with open(f'{mydir}/data/cat.mp4', 'rb') as fh:
        media = fh.read()
    mybot.send_video(caption='test video', media=media)
    mybot.send('choose an option', reply_markup=reply_markup)


@mybot.route(path='/alert', methods='query')
def alert(**kwargs):
    return {'text': 'ACHTUNG!!! DIE KATZE!!!', 'show_alert': True}


task_supervisor.create_aloop('default', default=True)
task_supervisor.start()

mybot.start()
