import html
import json
from typing import Optional

import websocket

from chatbridge.common.logger import ChatBridgeLogger
from chatbridge.core.client import ChatBridgeClient
from chatbridge.core.network.protocol import ChatPayload, CommandPayload
from chatbridge.impl import utils
from chatbridge.impl.cq_ch.config import CqHttpConfig

ConfigFile = 'ChatBridge_CQ_Ch.json'
cq_ch_bot: Optional['CQChBot'] = None
chatClient: Optional['CqHttpChatBridgeClient'] = None

CQChHelpMessage = '''
!!help: 显示本条帮助信息
!!ping: pong!!
'''.strip()

# 收到频道消息
# 上报数据

# 字段	类型	可能的值	说明
# post_type	string	message	上报类型
# message_type	string	guild	消息类型
# sub_type	string	channel	消息子类型
# guild_id	string		频道ID
# channel_id	string		子频道ID
# user_id	string		消息发送者ID
# message_id	string		消息ID
# sender	Sender		发送者
# message	Message		消息内容



class CQChBot(websocket.WebSocketApp):
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
			elif data['post_type'] == 'message' and data['message_type'] == 'guild' and data['sub_type'] == 'channel'\
					and data['guild_id'] == self.config.guild_id and data['channel_id'] == self.config.channel_id:
				msg = data['message']
				self.logger.info('sending to mc ' + msg)
				sender = data['sender']
				if len(sender) == 0:
					sender = data['sender']['nickname']
				text = html.unescape(msg)
				chatClient.send_chat(str(text), sender)
		except:
			self.logger.exception('Error in on_message()')

	def on_close(self, *args):
		self.logger.info("Close connection")

	def _send_text(self, text):
		data = {
			"action": "send_guild_channel_msg",
			"params": {
				"guild_id": self.config.guild_id,
				"channel_id": self.config.channel_id,
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
		global cq_ch_bot
		if cq_ch_bot is None:
			return
		cq_ch_bot.send_message(sender, payload.formatted_str())


def main():
	global chatClient, cq_ch_bot
	config = utils.load_config(ConfigFile, CqHttpConfig)
	chatClient = CqHttpChatBridgeClient.create(config)
	utils.start_guardian(chatClient)
	print('Starting CQ Bot')
	cq_ch_bot = CQChBot(config)
	cq_ch_bot.start()
	print('Bye')


if __name__ == '__main__':
	main()
