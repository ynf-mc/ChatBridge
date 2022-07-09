import html
import json
from typing import Optional

import websocket

from chatbridge.common.logger import ChatBridgeLogger
from chatbridge.core.client import ChatBridgeClient
from chatbridge.core.network.protocol import ChatPayload, CommandPayload
from chatbridge.impl import utils
from chatbridge.impl.cqhttp.config import CqHttpConfig

ConfigFile = 'ChatBridge_CQHttp.json'
cq_bot: Optional['CQBot'] = None
chatClient: Optional['CqHttpChatBridgeClient'] = None

CQHelpMessage = '''
!!help: 显示本条帮助信息
!!ping: pong!!
'''.strip()


class CQBot(websocket.WebSocketApp):
	def __init__(self, config: CqHttpConfig):
		self.config = config
		websocket.enableTrace(True)
		url = 'ws://{}:{}/'.format(self.config.ws_address, self.config.ws_port)
		if self.config.access_token is not None:
			url += '?access_token={}'.format(self.config.access_token)
		self.logger = ChatBridgeLogger('Bot', file_handler=chatClient.logger.file_handler)
		self.logger.info('Connecting to {}'.format(url))
		# noinspection PyTypeChecker
		super().__init__(url, on_message=self.on_message, on_close=self.on_close)

	def start(self):
		self.run_forever()

	def on_message(self, _, message: str):
		try:
			if chatClient is None:
				return
			data = json.loads(message)
			if 'status' in data:
				self.logger.info('CoolQ return status {}'.format(data['status']))
			elif data['post_type'] == 'message' and data['message_type'] == 'group':
				if data['anonymous'] is None and data['group_id'] == self.config.react_group_id:
					args = data['raw_message'].split(' ')

					if len(args) == 1 and args[0] == '!!help':
						self.logger.info('!!help command triggered')
						self.send_text(CQHelpMessage)

					if len(args) == 1 and args[0] == '!!ping':
						self.logger.info('!!ping command triggered')
						self.send_text('pong!!')

					self.logger.info('sending to mc')
					sender = data['sender']['card']
					if len(sender) == 0:
						sender = data['sender']['nickname']
					text = html.unescape(data['raw_message'])
					chatClient.send_chat(text, sender)
		except:
			self.logger.exception('Error in on_message()')

	def on_close(self, *args):
		self.logger.info("Close connection")

	def _send_text(self, text):
		data = {
			"action": "send_group_msg",
			"params": {
				"group_id": self.config.react_group_id,
				"message": text
			}
		}
		self.send(json.dumps(data))

	def send_text(self, text):
		msg = ''
		length = 0
		lines = text.rstrip().splitlines(keepends=True)
		for i in range(len(lines)):
			msg += lines[i]
			length += len(lines[i])
			if i == len(lines) - 1 or length + len(lines[i + 1]) > 500:
				self._send_text(msg)
				msg = ''
				length = 0

	def send_message(self, sender: str, message: str):
		self.send_text('[{}] {}'.format(sender, message))


class CqHttpChatBridgeClient(ChatBridgeClient):
	def on_chat(self, sender: str, payload: ChatPayload):
		global cq_bot
		if cq_bot is None:
			return
		self.logger.info('Triggered command, sending message {} to qq'.format(payload.formatted_str()))
		cq_bot.send_message(sender, payload.formatted_str())


def main():
	global chatClient, cq_bot
	config = utils.load_config(ConfigFile, CqHttpConfig)
	chatClient = CqHttpChatBridgeClient.create(config)
	utils.start_guardian(chatClient)
	print('Starting CQ Bot')
	cq_bot = CQBot(config)
	cq_bot.start()
	print('Bye')


if __name__ == '__main__':
	main()
