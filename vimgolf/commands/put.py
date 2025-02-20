import tempfile

from vimgolf import (
    __version__,
    logger,
    RUBY_CLIENT_VERSION_COMPLIANCE,
    Failure,
)
from vimgolf.api_key import get_api_key, validate_api_key, show_api_key_help
from vimgolf.challenge import (
    expand_challenge_id,
    validate_challenge_id,
    show_challenge_id_error,
    Challenge,
)
from vimgolf.play import play
from vimgolf.utils import write, confirm


def put(challenge_id, keys, diff=False):
    challenge_id = expand_challenge_id(challenge_id)
    logger.info('put(%s)', challenge_id)

    if not validate_challenge_id(challenge_id):
        show_challenge_id_error()
        raise Failure()

    api_key = get_api_key()
    if not validate_api_key(api_key):
        write('An API key has not been configured', fg='red')
        write('Uploading to vimgolf.com is disabled', fg='red')
        show_api_key_help()
        if not confirm('Play without uploads?'):
            raise Failure()

    try:
        compliant = fetch_and_validate_challenge(challenge_id)
    except Failure:
        raise
    except Exception:
        logger.exception('challenge retrieval failed')
        write('The challenge retrieval has failed', err=True, fg='red')
        write('Please check the challenge ID on vimgolf.com', err=True, fg='red')
        raise Failure()

    challenge = Challenge(
        id=challenge_id,
        compliant=compliant,
        api_key=api_key
    ).load()
    with tempfile.TemporaryDirectory() as d:
        play(challenge, d, keys=keys, diff=diff)
    challenge.update_metadata()


def fetch_and_validate_challenge(challenge_id):
    write('Downloading vimgolf challenge {}'.format(challenge_id), fg='yellow')
    challenge = Challenge(challenge_id)
    challenge.load_or_download()
    challenge_spec = challenge.spec
    compliant = challenge_spec.get('client') == RUBY_CLIENT_VERSION_COMPLIANCE
    if not compliant:
        message = 'vimgolf=={} is not compliant with vimgolf.com'.format(__version__)
        write(message, err=True, fg='red')
        write('Uploading to vimgolf.com is disabled', err=True, fg='red')
        write('vimgolf may not function properly', fg='red')
        try:
            from distutils.version import StrictVersion
            client_compliance_version = StrictVersion(RUBY_CLIENT_VERSION_COMPLIANCE)
            api_version = StrictVersion(challenge_spec['client'])
            action = 'upgrade' if api_version > client_compliance_version else 'downgrade'
        except Exception:
            action = 'update'
        write('Please {} vimgolf to a compliant version'.format(action), fg='yellow')
        if not confirm('Try to play without uploads?'):
            raise Failure()
    return compliant
