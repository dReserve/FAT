import asyncio
import fatstack.core
from code import InteractiveConsole
import sys

ROOT = fatstack.core.ROOT


class Shell(InteractiveConsole):
    def __init__(self, namespace):
        super().__init__(namespace)
        asyncio.ensure_future(self.run_shell())

    async def interact(self, banner=None, exitmsg=None):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        self.write("FATStack {}\n".format(fatstack.__version__))
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
        if exitmsg is None:
            self.write('now exiting %s...\n' % self.__class__.__name__)
        elif exitmsg != '':
            self.write('%s\n' % exitmsg)

    async def raw_input(self, prompt=""):
        return await asyncio.get_event_loop().run_in_executor(None, input, prompt)

    async def run_shell(self):
        await self.interact()
        exit()
        # fatstack.core.loop.exit_loop("Exiting.")
