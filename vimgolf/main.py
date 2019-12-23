import functools
import sys

from click import argument, option, group

from vimgolf import (
    __version__,
    commands,
    Failure,
    logger,
    init_logger,
    clean_stale_logs,
    setup_directories,
)
from vimgolf.commands.ls import parse_list_spec
from vimgolf.utils import write


@group()
def main():
    setup_directories()
    init_logger()
    clean_stale_logs()
    logger.info('vimgolf started')


def command(*cmd_args, **cmd_kwargs):
    def result(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Failure:
                sys.exit(1)
        return main.command(*cmd_args, **cmd_kwargs)(wrapper)
    return result


@command()
@argument('in_file')
@argument('out_file')
def local(in_file, out_file):
    """launch local challenge """
    commands.local(in_file, out_file)


@command()
@argument('challenge_id')
def put(challenge_id):
    """launch vimgolf.com challenge"""
    commands.put(challenge_id)


@command()
@argument('spec', default='', callback=lambda _, __, value: parse_list_spec(value))
@option('-i', '--incomplete', is_flag=True, help='Show incomplete (not submitted) items only')
def ls(spec, incomplete):
    """list vimgolf.com challenges (spec syntax: [PAGE][:LIMIT])"""
    commands.ls(incomplete=incomplete, **spec)


@command()
@argument('challenge_id')
@option('-t', '--tracked', is_flag=True, help='Include tracked data')
def show(challenge_id, tracked):
    """show vimgolf.com challenge"""
    commands.show(challenge_id, tracked)


@command()
@argument('api_key', default='')
def config(api_key):
    """configure your vimgolf.com credentials"""
    commands.config(api_key or None)


@command()
@argument('challenge_id')
@argument('keys')
@option('-l', '--literal-lt')
@option('-g', '--literal-gt')
def inspect(challenge_id, keys, literal_lt, literal_gt):
    """inspect behaviour of a key sequence applied to challenge"""
    commands.inspect(challenge_id, keys, literal_lt, literal_gt)


@command()
def version():
    """display the version number"""
    write(__version__)


if __name__ == '__main__':
    main()
