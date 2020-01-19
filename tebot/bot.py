import neotasker
import requests
import logging
import time
import threading

logger = logging.getLogger('tebot')


class TeBot(neotasker.BackgroundIntervalWorker):

    def handle_message(self, chat_id, text):
        """
        Override to handle text messages

        By default contains simple echo demo
        """
        self.send(chat_id, msg=f'Got text: {text}')

    def handle_command(self, chat_id, cmd):
        """
        Override to handle commands

        By default contains simple demo with a couple of cmds
        """
        from pathlib import Path
        mydir = Path(__file__).parent.as_posix()
        if cmd in ['start', 'help']:
            from textwrap import dedent
            self.send_message(
                chat_id,
                dedent("""
                <b>Hello, I'm using free Python library
                https://github.com/alttch/tebot</b>
                Test commands:

                /pic: send test picture
                /vid: send test video
                any cmd: echo it back
                """))
        elif cmd == 'pic':
            with open(f'{mydir}/demodata/cat.jpg', 'rb') as fh:
                media = fh.read()
            self.send(chat_id, msg='test pic', media=media)
        elif cmd == 'vid':
            with open(f'{mydir}/demodata/cat.mp4', 'rb') as fh:
                media = fh.read()
            # it's recommended to send video with send_video method
            # as filetype.guess sometimes can not detect all formats
            self.send_video(chat_id, caption='test video', media=media)
        else:
            self.send(chat_id, msg=f'Command unknown: {cmd}')

    def on_message(self, msg):
        """
        Override to implement extended message handling
        """
        chat = msg.get('chat')
        if not chat: return
        chat_id = chat.get('id')
        if not chat_id or self.is_duplicate(msg.get('message_id'), chat_id):
            return
        text = msg.get('text')
        if not text: return
        text = text.split('@')[0]
        return self.handle_command(
            chat_id, text[1:]) if text.startswith('/') else self.handle_message(
                chat_id, text)

    def set_token(self, token=None):
        """
        Set bot token

        Must be set before start

        Obtain at https://telegram.me/BotFather
        """
        if token:
            self.__uri = f'https://api.telegram.org/bot{token}'
        self.__token = token

    def is_duplicate(self, msg_id, chat_id):
        """
        Filters duplicate messages

        Called automatically by default on_message
        """
        with self.lock:
            if chat_id in self._chat_id_processed and self._chat_id_processed[
                    chat_id] >= msg_id:
                return True
            else:
                self._chat_id_processed[chat_id] = msg_id
                return False

    def serialize(self):
        """
        Serialize bot data to prevent duplicates after restart
        """
        return {'update_offset': self.update_offset}

    def load(self, state):
        """
        Load serialized data (usually before start)
        """
        self.update_offset = state.get('update_offset', 0)

    def is_ready(self):
        """
        Is bot ready to launch

        Returns: True if token is set
        """
        return self.__token is not None

    def test(self):
        """
        Calls getMe test method

        Returns: API result as-is
        """
        result = self.call('getMe')
        return result

    def send(self,
             chat_id,
             msg='',
             media=None,
             mode='HTML',
             disable_preview=False,
             quiet=False):
        """
        Universal send method

        Tries to guess what and how to send

        If media is not None, tries to detect media type automatically

        Args:
            chat_id: chat id
            msg: message text
            media: media to send
            mode: formatting mode (default: HTML)
            disable_preview: disable web page preview
            quiet: send quiet message (without notification)
        """
        if media is None:
            return self.send_message(chat_id, msg, mode, disable_preview, quiet)
        else:
            import filetype
            ft = filetype.guess(media)
            mt = ft.mime.split('/', 1)[0] if ft else None
            if mt == 'image':
                send_func = self.send_photo
            elif mt == 'video':
                send_func = self.send_video
            elif mt == 'audio':
                send_func = self.send_audio
            else:
                send_func = self.send_document
            return send_func(chat_id, media, msg, mode, quiet)

    def send_message(self,
                     chat_id,
                     msg,
                     mode='HTML',
                     disable_preview=False,
                     quiet=False):
        """
        Sends text message

        Args:
            chat_id: chat id
            msg: message text
            mode: formatting mode (default: HTML)
            disable_preview: disable web page preview
            quiet: send quiet message (without notification)
        """
        return self.call(
            'sendMessage', {
                'chat_id': chat_id,
                'text': msg,
                'parse_mode': mode,
                'disable_web_page_preview': disable_preview,
                'disable_notification': quiet
            }) is not None

    def send_photo(self, chat_id, media, caption='', mode='HTML', quiet=False):
        """
        Sends picture file

        Args:
            chat_id: chat id
            media: binary data
            caption: caption text
            mode: formatting mode (default: HTML)
            disable_preview: disable web page preview
            quiet: send quiet message (without notification)
        """
        return self.call(
            'sendPhoto', {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': mode,
                'disable_notification': quiet
            }, {'photo': media})

    def send_audio(self, chat_id, media, caption='', mode='HTML', quiet=False):
        """
        Sends audio file

        Args:
            chat_id: chat id
            media: binary data
            caption: caption text
            mode: formatting mode (default: HTML)
            disable_preview: disable web page preview
            quiet: send quiet message (without notification)
        """
        return self.call(
            'sendAudio', {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': mode,
                'disable_notification': quiet
            }, {'audio': media})

    def send_video(self, chat_id, media, caption='', quiet=False):
        """
        Sends video

        Args:
            chat_id: chat id
            caption: caption text
            media: binary data
            mode: formatting mode (default: HTML)
            disable_preview: disable web page preview
            quiet: send quiet message (without notification)
        """
        return self.call(
            'sendVideo', {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML',
                'disable_notification': quiet
            }, {'video': media})

    def send_document(self,
                      chat_id,
                      media,
                      caption='',
                      mode='HTML',
                      quiet=False):
        """
        Sends file of any type

        Args:
            chat_id: chat id
            media: binary data
            caption: caption text
            mode: formatting mode (default: HTML)
            disable_preview: disable web page preview
            quiet: send quiet message (without notification)
        """
        return self.call(
            'sendDocument', {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': mode,
                'disable_notification': quiet
            }, {'document': media})

    def __init__(self, *args, **kwargs):
        self.__token = None
        self.__uri = None
        self.timeout = 10
        self.retry_interval = None
        self.update_offset = 0
        self._chat_id_processed = {}
        self.lock = threading.RLock()
        super().__init__(*args, **kwargs)

    def run(self, **kwargs):
        if not self.__token:
            raise RuntimeError('token not provided')
        result = self.call('getUpdates', {'offset': self.update_offset + 1})
        if result and 'result' in result:
            for m in result['result']:
                if 'message' in m:
                    result = self.on_message(m['message'])
                update_id = m.get('update_id')
                if update_id and update_id > self.update_offset:
                    self.update_offset = update_id
                if result is False:
                    return False
        else:
            logger.error('Invalid getUpdates result')

    def call(self, func, args=None, files=None, retry=None):
        logger.debug(f'Telegram API call {func}')
        if files:
            r = requests.post(f'{self.__uri}/{func}',
                              data=args,
                              files=files,
                              timeout=self.timeout)
        else:
            r = requests.post(f'{self.__uri}/{func}',
                              json=args,
                              timeout=self.timeout)
        if r.ok:
            result = r.json()
            if result.get('ok'): return result
        else:
            logger.error(f'API call failed, code: {r.status_code}')
            if retry is False or (retry is None and not self.retry_interval):
                return None
            time.sleep(self.retry_interval)
            return self.call(func=func, args=args, files=files, retry=False)
