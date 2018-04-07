import asyncio
import fatstack as fs
from code import InteractiveConsole
import sys
import logging

log = logging.getLogger("Shell")


class Shell(InteractiveConsole):
    def __init__(self, namespace):
        log.info("Initializing interactive shell.")
        super().__init__(namespace)

        fs.loop.register(self.run_shell())

    async def interact(self):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        self.write("FATStack {}\n".format(fs.__version__))
        more = 0
        while 1:
            try:
                if more:
                    prompt = sys.ps2
                else:
                    prompt = sys.ps1
                try:
                    line = await self.raw_input(prompt)
                except EOFError:
                    self.write("\n")
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0

    async def raw_input(self, prompt=""):
        return await asyncio.get_event_loop().run_in_executor(None, input, prompt)

    async def run_shell(self):
        await self.interact()
        exit()
