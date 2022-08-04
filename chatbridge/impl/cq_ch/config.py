from chatbridge.core.config import ClientConfig


class CqHttpConfig(ClientConfig):
	ws_address: str = '127.0.0.1'
	ws_port: int = 6700
	access_token: str = ''
	guild_id: str = '123abc'
	channel_id: str = '12345679'
