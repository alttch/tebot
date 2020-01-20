# TeBot - Telegram bot library for Python and humans

The goal is to to keep it simple.

<img src="https://img.shields.io/pypi/v/tebot.svg" />
<img src="https://img.shields.io/badge/license-MIT-green.svg" />
<img src="https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg" />

Demo (sometimes may not work): [@demo_tebot](https://telegram.me/demo_tebot)

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
from tebot import TeBot

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

### High level API: routes

**TeBot** has flask-style routes, which may be registered either by calling

```python
    mybot.register_handler(fn, path, methods)
```

or with function decorator:

```python
# message handler. can be only one, registered to handle all regular messages
@mybot.route(methods='message')
def my_message(chat_id, text, **kwargs):
    # some code

# command handler for /start and /help
@mybot.route(path=['/start', '/help'])
def start(chat_id, **kwargs):
    mybot.send(chat_id, 'got HELP command')

# command and callback query handler
@mybot.route(methods='*')
def default_cmd_handler(chat_id, path, **kwargs):
    mybot.send(chat_id, f'command not implemented: {path}')
```

#### Route parameters

* **path** command path, can be string or list/tuple for multiple commands

* **methods** can be either a string or a list/tuple. Valid values are:
  "message", "command" (default if no methods specified) and
  "query"/"callback_query". If "\*" specified, the method is registered for
  both commands and callback queries


#### Method kwargs

The following kwargs are sent to registered methods:

* **path** command path (e.g. "/select" for "/select \* from data")

* **query_string** command query string (e.g. "\* from data" for the above
  example)

* **chat_id** current chat id

* **query_id** callback query id, if method executed as a callback query
  handler

* **payload** full request payload

* **method** "command" or "query" for callback query

#### Method return data

* If command is handled, the method may return nothing

* If callback query is handled, the method may return dict, which is used as a
  payload for the callback query answer (e.g. include "url", "show_alert" etc,
  see Telegram Bot API for more details)

### Low-level API: handlers

Override class methods:

* **handle_message(self, chat_id, text, payload)** handle regular messages

* **handle_command(self, chat_id, cmd, payload)** handle commands (starting
  with '/')

* **handle_query(self, chat_id, query_id, data, payload)** handle callback
  queries. By default, considers all query data are commands

* **on_message** override to implement advanced message handling

* **on_query** override to implement advanced callback query handling

# Bot options

```python
mybot.timeout = 5 # set Telegram API timeout (default: 10 sec)
mybot.retry_interval = 1 # if API command fails, re-send it in 1 second
                         # (default: None, don't re-send)
```

### Everything else

Refer to function pydoc for more info.
