import asyncio
import signal
import sys

from migro.uploader.utils import loop


async def ask_exit():
    """Loop and tasks shutdown callback."""

    # Handling tasks differently based on Python version due to the deprecation
    # of asyncio.Task.all_tasks() and asyncio.Task.current_task() in favor of
    # asyncio.all_tasks() and asyncio.current_task() without the need for the event loop.
    if sys.version_info < (3, 7):
        tasks = [t for t in asyncio.Task.all_tasks() if t is not
                 asyncio.Task.current_task()]
    else:
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

    [task.cancel() for task in tasks]

    if sys.version_info < (3, 7):
        await asyncio.gather(*tasks)
    else:
        await asyncio.gather(*tasks, return_exceptions=True)

    running_loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) else asyncio.get_event_loop()
    running_loop.stop()


try:
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda: asyncio.ensure_future(ask_exit())
        )
except NotImplementedError:
    if not sys.platform.startswith('win'):
        raise
