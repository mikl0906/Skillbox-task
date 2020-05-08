"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                user_login = decoded.replace("login:", "").replace("\r\n", "")
                if next((x for x in self.server.clients if x.login == user_login), None) is None:
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.transport.write(
                        f"Привет, {user_login}!".encode()
                    )
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.send_history()
                else:
                    self.transport.write(
                        f"Логин {user_login} занят, попробуйте другой".encode()
                    )
                    self.login = None
                    self.connection_lost("exception")
        else:
            self.send_message(decoded)

    def send_history(self):
        for i in range(-10, 0):
            try:
                self.transport.write(f"{self.server.history.pop(i)}\n".encode())
            except IndexError:
                pass

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        self.server.history.append(format_string)
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print(f"Соединение установлено")

    def connection_lost(self, exception):
        # self.server.clients.remove(self)
        print(f"Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
