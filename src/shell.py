# Based on:
# https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/
# https://docs.python.org/3/library/asyncio-subprocess.html
# https://stackoverflow.com/questions/2996887/how-to-replicate-tee-behavior-in-python-when-using-subprocess
# Accessed 10/16/2024


import asyncio
import shlex
import sys
import tempfile
import typing as T


StreamReceiver = T.Callable[[bytes], None]


class Shell:
    def __init__(self):
        self.loop = None
        self.env = {}

    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()

    def __getattr__(self, name):
        def method(*args, **kwargs):
            return self.run(name, *args, **kwargs)
        return method

    def run(self, cmd: str, *args, **kwargs) -> int:
        cmd_line = f'{cmd} {shlex.join(args)}'.strip()
        return self._execute(cmd_line, **kwargs)

    def _execute(self,
                 cmd_line: str,
                 stdout_receiver: StreamReceiver = None,
                 stderr_receiver: StreamReceiver = None,
                 *,
                 echo: bool = False,
                 echo_prefix: str = '$ '
                 ) -> int:
        if echo:
            print(f'{echo_prefix}{cmd_line}')

        if stdout_receiver is None:
            stdout_receiver = lambda line: print(line.decode(), end='')

        if stderr_receiver is None:
            stderr_receiver = lambda line: print(line.decode(), end='', file=sys.stderr)

        with tempfile.NamedTemporaryFile(delete_on_close=False) as temp_env:
            temp_env.close()

            result = self.loop.run_until_complete(
                _stream_subprocess(
                    cmd_line,
                    stdout_receiver,
                    stderr_receiver,
                    self.env,
                    temp_env.name
                ))

            env = {}

            with open(temp_env.name, 'r') as env_file:
                for line in env_file:
                    line = line.strip()
                    key, value = line.split('=', 1)
                    env[key] = value

            self.env = env

        return result


async def _stream_subprocess(cmd: str,
                             stdout_receiver: StreamReceiver,
                             stderr_receiver: StreamReceiver,
                             env: dict = None,
                             env_file: str = ''
                             ) -> int:
    shell = await asyncio.create_subprocess_shell('/bin/bash',
                                                  stdin=asyncio.subprocess.PIPE,
                                                  stdout=asyncio.subprocess.PIPE,
                                                  stderr=asyncio.subprocess.PIPE,
                                                  env=env)
    shell.stdin.write(f'{cmd}\n'.encode())
    shell.stdin.write(b'__rc=$?\n')
    shell.stdin.write(f'printenv > {env_file}\n'.encode())
    shell.stdin.write(b'(exit $__rc)\n')

    shell.stdin.close()

    stdout = asyncio.create_task(_read_stream(shell.stdout, stdout_receiver))
    stderr = asyncio.create_task(_read_stream(shell.stderr, stderr_receiver))
    process = asyncio.create_task(shell.wait())

    await asyncio.wait([
        stdout,
        stderr,
        process
    ])

    assert stdout.done()
    assert stderr.done()
    assert process.done()

    return process.result()


async def _read_stream(stream: asyncio.StreamReader, receiver: StreamReceiver):
    while True:
        line = await stream.readline()

        if line:
            receiver(line)
        else:
            break
