import json
import sys
import time

from chatterbot import ChatBot
from slackclient import SlackClient


class Bot(object):
    def __init__(self, config_file):
        config = json.load(open(config_file))
        self.chatbot = ChatBot(
            'Robot Overload',
            io_adapter='chatterbot.adapters.io.NoOutputAdapter',
            database=config['database'])
        self.chatbot.train('chatterbot.corpus.english')
        self.chatbot.train('chatterbot.corpus.english.greetings')
        self.chatbot.train('chatterbot.corpus.english.conversations')

        self.token = config['token']
        self.bot_id = config['bot_id']
        self.slack_client = None

    def connect(self):
        self.slack_client = SlackClient(self.token)
        self.slack_client.rtm_connect()
        self.last_ping = 0

    def start(self):
        self.connect()
        while True:
            for reply in self.slack_client.rtm_read():
                self.input(reply)
            self.autoping()
            time.sleep(.1)

    def input(self, data):
        text = data.get('text', '')
        if data.get('type') == 'message' and self.bot_id in text:
            channel = data['channel']
            text = text.replace(self.bot_id, '')
            response =  self.chatbot.get_response(text)
            self.output([channel, response])

    def output(self, output):
        limiter = False
        channel = self.slack_client.server.channels.find(output[0])
        if channel != None and output[1] != None:
            if limiter == True:
                time.sleep(.1)
                limiter = False
            message = output[1].encode('ascii','ignore')
            channel.send_message("{}".format(message))
            limiter = True

    def autoping(self):
        now = int(time.time())
        if now > self.last_ping + 3:
            self.slack_client.server.ping()
            self.last_ping = now

if __name__ == '__main__':
    bot = Bot(sys.argv[1])

    try:
        bot.start()
    except KeyboardInterrupt:
        sys.exit(0)
