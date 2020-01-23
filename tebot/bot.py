import neotasker
import requests
import logging
import time
import threading

logger = logging.getLogger('tebot')

g = threading.local()


class TeBot(neotasker.BackgroundIntervalWorker):

    def route(self, *args, **kwargs):
        """
        route decorator
        """

        def inner(fn):
            methods = kwargs.get('methods', [])
            path = kwargs.get('path')
            self.register_route(fn, path, methods)

        return inner

    def register_route(self, fn, path=None, methods='command'):
        """
        Register route

        Args:
            fn: route function
            path: list of commands, string or list
            methods: "message" (message handler, can be only one), "command"
                (default), "query" / "callback_query", "*" for all, string or
                list

        """
        if not methods:
            methods = 'command'
        if not isinstance(methods, tuple) and not isinstance(methods, list):
            methods = [methods]
        for method in methods:
            if method == 'message':
                if path:
                    raise ValueError(
                        'Can not register route with path for messages')
                else:
                    self.handle_message = fn
            if not isinstance(path, tuple) and not isinstance(path, list):
                path = [path]
            if method in ('command', '*'):
                for p in path:
                    self._command_routes[p] = fn
            if method in ('query', 'callback_query', '*'):
                for p in path:
                    self._query_routes[p] = fn

    def handle_message(self, text, **kwargs):
        """
        Override to handle text messages

        By default contains simple echo
        """
        self.send(text=text)

    def handle_command(self, chat_id, cmd, payload, **kwargs):
        """
        Override to handle commands

        By default contains simple demo with a couple of cmds
        """
        path = cmd.split(' ', 1)
        fn = self._command_routes.get(path[0])
        if fn is None:
            fn = self._command_routes.get(None)
        if fn is None:
            logger.error(f'No command handler for {path[0]}')
            return None
        else:
            kwargs['path'] = path[0]
            try:
                kwargs['query_string'] = path[1]
            except:
                kwargs['query_string'] = None
            kwargs['chat_id'] = chat_id
            kwargs['payload'] = payload
            kwargs['method'] = 'command'
            return fn(**kwargs)

    def handle_query(self, chat_id, query_id, data, payload, **kwargs):
        """
        Override to handle queries

        By default considers all queries are commands
        """
        path = data.split(' ', 1)
        fn = self._query_routes.get(path[0])
        if fn is None:
            fn = self._query_routes.get(None)
        if fn is None:
            logger.error(f'No callback query handler for {path[0]}')
            return None
        else:
            kwargs['chat_id'] = chat_id
            kwargs['query_id'] = query_id
            kwargs['path'] = path[0]
            try:
                kwargs['query_string'] = path[1]
            except:
                kwargs['query_string'] = None
            kwargs['payload'] = payload
            kwargs['method'] = 'query'
            result = fn(**kwargs)
            if result is None:
                result = {}
            return self.answer_query(query_id, **result)

    def on_message(self, msg):
        """
        Override to implement extended message handling
        """
        chat = msg.get('chat')
        if not chat: return
        chat_id = chat.get('id')
        message_id = msg.get('message_id')
        if not chat_id or self.is_duplicate_message(chat_id, message_id):
            return
        text = msg.get('text', '')
        g.chat_id = chat_id
        return self.handle_command(
            chat_id, text, message_id=message_id,
            payload=msg) if text.startswith('/') else self.handle_message(
                chat_id=chat_id, text=text, message_id=message_id, payload=msg)

    def on_query(self, query):
        """
        Override to implement extended query handling
        """
        query_id = query.get('id')
        msg = query.get('message')
        if not msg: return
        chat = msg.get('chat')
        if not chat: return
        chat_id = chat.get('id')
        if not chat_id or self.is_duplicate_query(chat_id, query_id):
            return
        g.query_id = query_id
        g.chat_id = chat_id
        message_id = msg.get('message_id')
        return self.handle_query(chat_id,
                                 query_id,
                                 query.get('data'),
                                 message_id=message_id,
                                 payload=query)

    def set_token(self, token=None):
        """
        Set bot token

        Must be set before start

        Obtain at https://telegram.me/BotFather
        """
        if token:
            self.__uri = f'https://api.telegram.org/bot{token}'
            self.__furi = f'https://api.telegram.org/file/bot{token}'
        self.__token = token

    def is_duplicate_message(self, chat_id, message_id):
        """
        Filters duplicate messages

        Called automatically by default on_message
        """
        with self._lock:
            if chat_id in self._chat_id_processed_message and \
                    self._chat_id_processed_message[
                    chat_id] == message_id:
                return True
            else:
                self._chat_id_processed_message[chat_id] = message_id
                return False

    def is_duplicate_query(self, chat_id, query_id):
        """
        Filters duplicate querys

        Called automatically by default on_query
        """
        with self._lock:
            if chat_id in self._chat_id_processed_query and \
                    self._chat_id_processed_query[
                    chat_id] == query_id:
                return True
            else:
                self._chat_id_processed_query[chat_id] = query_id
                return False

    def serialize(self):
        """
        Serialize bot data to prevent duplicates after restart
        """
        return {'update_offset': self._update_offset}

    def load(self, state):
        """
        Load serialized data (usually before start)
        """
        self._update_offset = state.get('update_offset', 0)

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

    def send(
            self,
            text='',
            chat_id=None,
            media=None,
            mode='HTML',
            **kwargs,
    ):
        """
        Universal send method

        Tries to guess what and how to send

        If media is not None, tries to detect media type automatically

        Args:
            text: message text
            media: media to send
            chat_id: chat id
            mode: formatting mode (default: HTML)
            other API args: passed as-is
        """
        if chat_id is None:
            chat_id = g.chat_id
        if media is None:
            return self.send_message(text=text,
                                     chat_id=chat_id,
                                     mode=mode,
                                     **kwargs)
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
            return send_func(media=media,
                             caption=text,
                             chat_id=chat_id,
                             mode=mode,
                             **kwargs)

    def send_message(self, chat_id=None, text='', mode='HTML', **kwargs):
        """
        Sends text message

        Args:
            text: message text
            chat_id: chat id
            mode: formatting mode (default: HTML)
            other API args: passed as-is
        """
        if chat_id is None:
            chat_id = g.chat_id
        return self.call(
            'sendMessage',
            self._format_payload(
                {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': mode,
                }, **kwargs)) is not None

    def send_photo(self,
                   media='',
                   caption='',
                   chat_id=None,
                   mode='HTML',
                   **kwargs):
        """
        Sends picture file

        Args:
            media: binary data
            caption: caption text
            chat_id: chat id
            mode: formatting mode (default: HTML)
            other API args: passed as-is
        """
        if chat_id is None:
            chat_id = g.chat_id
        return self.call(
            'sendPhoto',
            self._format_payload(
                {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': mode,
                }, **kwargs), {'photo': media})

    def send_audio(self,
                   media='',
                   caption='',
                   chat_id=None,
                   mode='HTML',
                   **kwargs):
        """
        Sends audio file

        Args:
            media: binary data
            caption: caption text
            chat_id: chat id
            mode: formatting mode (default: HTML)
            other API args: passed as-is
        """
        if chat_id is None:
            chat_id = g.chat_id
        return self.call(
            'sendAudio',
            self._format_payload(
                {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': mode
                }, **kwargs), {'audio': media})

    def send_video(self,
                   media='',
                   caption='',
                   chat_id=None,
                   mode='HTML',
                   **kwargs):
        """
        Sends video

        Args:
            media: binary data
            caption: caption text
            chat_id: chat id
            mode: formatting mode (default: HTML)
            other API args: passed as-is
        """
        if chat_id is None:
            chat_id = g.chat_id
        return self.call(
            'sendVideo',
            self._format_payload(
                {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': mode
                }, **kwargs), {'video': media})

    def send_document(self,
                      media='',
                      caption='',
                      chat_id=None,
                      mode='HTML',
                      **kwargs):
        """
        Sends file of any type

        Args:
            media: binary data
            caption: caption text
            chat_id: chat id
            mode: formatting mode (default: HTML)
            other API args: passed as-is
        """
        if chat_id is None:
            chat_id = g.chat_id
        return self.call(
            'sendDocument',
            self._format_payload(
                {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': mode
                }, **kwargs), {'document': media})

    def answer_query(self, query_id=None, **kwargs):
        """
        Answer callback query

        Args:
            query_id: callback query id
            other API args: passed as-is
        """
        if query_id is None:
            query_id = g.query_id
        return self.call(
            'answerCallbackQuery',
            self._format_query_payload({'callback_query_id': query_id},
                                       **kwargs))

    def get_file(self, file_id):
        """
        Get file object
        """
        return self.call('getFile', payload={'file_id': file_id})

    def get_file_content(self, file_id):
        """
        Download file by file_id

        Raises:
            RuntimeError: if file can't be downloaded
            Other: requests module exceptions
        """
        return self.download_file(
            file_path=self.get_file(file_id)['result']['file_path'])

    def download_file(self, file_path, retry=None):
        """
        Download file by file path

        Raises:
            RuntimeError: if file can't be downloaded
            Other: requests module exceptions
        """
        r = requests.get(f'{self.__furi}/{file_path}')
        if r.ok:
            return r.content
        else:
            logger.error(f'API call failed, code: {r.status_code}')
            if retry is False or (retry is None and not self.retry_interval):
                raise RuntimeError('Unable to download file')
            time.sleep(self.retry_interval if self.retry_interval else retry)
            return self.call(func=func,
                             payload=payload,
                             files=files,
                             retry=False)

    def set_webhook(self, url, **kwargs):
        """
        Set bot webhook
        """
        payload = kwargs.copy()
        payload['url'] = url
        return self.call('setWebhook', payload=payload)

    def delete_webhook(self):
        """
        Delete bot webhook
        """
        return self.call('deleteWebhook')

    def __init__(self, *args, **kwargs):
        self.__token = None
        self.__uri = None
        self.__furi = None
        self.timeout = 10
        self.retry_interval = None
        self.default_reply_markup = None
        self._update_offset = 0
        self._chat_id_processed_message = {}
        self._chat_id_processed_query = {}
        self._lock = threading.RLock()
        self._command_routes = {}
        self._query_routes = {}
        super().__init__(*args, **kwargs)

    def process_update(self, payload):
        """
        Process Telegram API update object
        """
        update_id = payload.get('update_id')
        if update_id and update_id > self._update_offset:
            self._update_offset = update_id
        if 'message' in payload:
            self.supervisor.spawn(self.on_message, payload['message'])
        elif 'callback_query' in payload:
            self.supervisor.spawn(self.on_query, payload['callback_query'])

    def run(self, **kwargs):
        if not self.__token:
            raise RuntimeError('token not provided')
        result = self.call('getUpdates', {'offset': self._update_offset + 1})
        if result and 'result' in result:
            for m in result['result']:
                self.process_update(m)
        else:
            logger.warning('Invalid getUpdates result')

    def call(self, func, payload=None, files=None, retry=None):
        """
        Call API method
        
        Args:
            payload: API call payload
            files: files
            retry: False - do not retry, None - default retry, number - retry
            interval
        """
        logger.debug(f'Telegram API call {func}')
        if files:
            r = requests.post(f'{self.__uri}/{func}',
                              data=payload,
                              files=files,
                              timeout=self.timeout)
        else:
            r = requests.post(f'{self.__uri}/{func}',
                              json=payload,
                              timeout=self.timeout)
        if r.ok:
            result = r.json()
            if result.get('ok'): return result
        else:
            logger.error(f'API call failed, code: {r.status_code}')
            if retry is False or (retry is None and not self.retry_interval):
                return None
            time.sleep(self.retry_interval if self.retry_interval else retry)
            return self.call(func=func,
                             payload=payload,
                             files=files,
                             retry=False)

    def _format_payload(self, payload, **kwargs):
        payload.update(kwargs)
        if 'reply_markup' in payload:
            if payload['reply_markup'] is None:
                del payload['reply_markup']
        else:
            if self.default_reply_markup:
                payload['reply_markup'] = self.default_reply_markup
        return payload

    def _format_query_payload(self, payload, **kwargs):
        payload.update(kwargs)
        return payload
