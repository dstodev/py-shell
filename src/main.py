from pathlib import Path

from shell import Shell


def main():
    repo_dir = Path(__file__).parent.parent.resolve()

    shell = Shell()

    with shell as s:
        print('--- ls command:')
        print(f'exit code: {s.ls('-la', echo=True)}')
        #      ^                 ^   ^             ^
        # Nested quotes in f-strings allowed since PEP 701 (Python 3.12)
        # https://docs.python.org/3.12/whatsnew/3.12.html#pep-701-syntactic-formalization-of-f-strings

        print('\n--- quotes:')
        print(f'exit code: {s.echo('welcome \' "hello there"', ':)', echo=True)}')

        print('\n--- setting exit code:')
        print(f'exit code: {s.run('(exit 5)', echo=True)}')

        print('\n--- preserving environment variables:')
        print(f'exit code: {s.export('TEST=hello', echo=True)}')

    # Environment is preserved between entries
    with shell as s:
        print('\n--- escaping variables:')
        print(f'exit code: {s.echo('$TEST! :)', echo=True)}')

        # May only escape arguments past the command. Passing the whole command
        # as one string passes to the shell verbatim.
        print('\n--- accessing variables:')
        print(f'exit code: {s.run('echo "$TEST"! ":)"', echo=True)}')

        print('\n--- local variables are dropped:')
        print(f'exit code: {s.run('key=value; echo "|$key|"', echo=True)}')
        print(f'exit code: {s.run('echo "|$key|"', echo=True)}')

        print('\n--- other script inherits environment:')
        print(f'exit code: {s.run(f'{repo_dir}/src/shim.sh', echo=True)}')

        print('\n--- sourcing another script:')
        print(f'exit code: {s.source(f'{repo_dir}/src/shim.sh', echo=True)}')
        print(f'exit code: {s.run(f'echo "from shim: $TEST2"', echo=True)}')

        print('\n--- unknown command:')
        print(f'exit code: {s.abcdef(echo=True)}\n')


if __name__ == '__main__':
    main()
