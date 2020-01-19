import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('tebot').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.WARNING)

from tebot import TeBot
from neotasker import task_supervisor

task_supervisor.create_aloop('default', default=True)
task_supervisor.start()

mybot = TeBot(interval=2)
with open('demo_tebot_token.dat') as fh:
    mybot.set_token(fh.read().strip())
mybot.start()
