def main():
    print("Hello world")
    import asyncio
    import websockets
    import json  # 导入json库用于字典转换为JSON字符串

    async def main(send_message):
        async with websockets.connect("ws://127.0.0.1:1145") as websocket:
            message = 'Hello'
            response = await websocket.recv()
            await websocket.send(send_message)  # 发送JSON字符串而不是字典对象
            print("尝试发送消息")
            print(response)
    asyncio.run(main("Hello world"))

    async def receive():
        async with websockets.connect("ws://127.0.0.1:1145") as websocket:
            while True:
                response = await websocket.recv()
                print(response)
    asyncio.run(receive())