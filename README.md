# TeBot - Telegram bot library for Python and humans

The goal is to to keep it simple.

<img src="https://img.shields.io/pypi/v/tebot.svg" />
<img src="https://img.shields.io/badge/license-MIT-green.svg" />
<img src="https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg" />

## How to install

```shell
pip3 install tebot
```

## How to use

### Start bot

If your project uses [neotasker](https://github.com/alttch/neotasker)

```python

from tebot import TeBot

# interval - polling interval, must be specified
mybot = TeBot(interval=2)
# obtain token from https://telegram.me/BotFather
mybot.set_token('botsecrettoken')
# optionally - load previous state
import json
with open('bot-state.json') as fh:
    mybot.load(json.loads(fh.read()))
# start bot
mybot.start()
```

If it doesn't:

```python
from neotasker import task_supervisor

task_supervisor.create_aloop('default', default=True)
task_supervisor.start()
mybot = TeBot(interval=2)
mybot.set_token('botsecrettoken')
mybot.start()
```

(refer to **neotasker** documentation for more info)

### Stop bot

```python
mybot.stop()
# if your project doesn't use neotasker
task_supervisor.stop()
# optionally - save bot state
with open('bot-state.json', 'w') as fh:
    fh.write(json.dumps(mybot.serialize()))
```

### Send messages

```python
# text
mybot.send(chat_id, msg='hello world')
# files
with open('image.jpg', 'rb') as fh:
    mybot.send(chat_id, media=fh.read())
```

### Handle incoming messages

Override class methods:

* **handle_message(self, chat_id, text)** handle regular messages
* **handle_command(self, chat_id, cmd)** handle commands (starting with '/')

* **on_message** override to implement advanced handling

# Bot options

```python
mybot.timeout = 5 # set Telegram API timeout (default: 10 sec)
mybot.retry_interval = 1 # if API command fails, re-send it in 1 second
                         # (default: None, don't re-send)
```

### Everything else

Refer to function pydoc for more info.
