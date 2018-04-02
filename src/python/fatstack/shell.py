# import readline
import asyncio
import fatstack.core
import code

ROOT = fatstack.core.ROOT


class Shell:
    def __init__(self):
        self.console = code.InteractiveConsole(ROOT.__dict__)
        asyncio.ensure_future(self.run_shell())

    async def run_shell(self):
        loop = asyncio.get_event_loop()

        while True:
            user_input = await loop.run_in_executor(None, self.console.interact)
            print(user_input)
