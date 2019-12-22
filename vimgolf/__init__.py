import datetime
import glob
import logging
import os

version_txt = os.path.join(os.path.dirname(__file__), 'version.txt')
with open(version_txt, 'r') as vf:
    __version__ = vf.read().strip()

GOLF_HOST = os.environ.get('GOLF_HOST', 'https://www.vimgolf.com')
GOLF_VIM = os.environ.get('GOLF_VIM', 'vim')

RUBY_CLIENT_VERSION_COMPLIANCE = '0.4.8'

EXPANSION_PREFIX = '+'

USER_HOME = os.path.expanduser('~')

TIMESTAMP = datetime.datetime.utcnow().timestamp()

# Max number of listings by default for 'vimgolf list'
LISTING_LIMIT = 10

# Max number of leaders to show for 'vimgolf show'
LEADER_LIMIT = 3

# Max number of existing logs to retain
LOG_LIMIT = 10

# Max number of parallel web requests.
# As of 2018, most browsers use a max of six connections per hostname.
MAX_REQUEST_WORKERS = 6

# Various paths
PLAY_VIMRC_PATH = os.path.join(os.path.dirname(__file__), 'vimgolf.vimrc')
INSPECT_VIM_PATH = os.path.join(os.path.dirname(__file__), 'vimgolf-inspect.vim')
CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME', os.path.join(USER_HOME, '.config'))
VIMGOLF_CONFIG_PATH = os.path.join(CONFIG_HOME, 'vimgolf')
VIMGOLF_API_KEY_PATH = os.path.join(VIMGOLF_CONFIG_PATH, 'api_key')
DATA_HOME = os.environ.get('XDG_DATA_HOME', os.path.join(USER_HOME, '.local', 'share'))
VIMGOLF_DATA_PATH = os.path.join(DATA_HOME, 'vimgolf')
VIMGOLF_ID_LOOKUP_PATH = os.path.join(VIMGOLF_DATA_PATH, 'id_lookup.json')
VIMGOLF_CHALLENGES_PATH = os.path.join(VIMGOLF_DATA_PATH, 'challenges')
CACHE_HOME = os.environ.get('XDG_CACHE_HOME', os.path.join(USER_HOME, '.cache'))
VIMGOLF_CACHE_PATH = os.path.join(CACHE_HOME, 'vimgolf')
VIMGOLF_LOG_DIR_PATH = os.path.join(VIMGOLF_CACHE_PATH, 'log')
VIMGOLF_LOG_FILENAME = 'vimgolf-{}-{}.log'.format(TIMESTAMP, os.getpid())
VIMGOLF_LOG_PATH = os.path.join(VIMGOLF_LOG_DIR_PATH, VIMGOLF_LOG_FILENAME)

logger = logging.getLogger('vimgolf')


def setup_directories():
    os.makedirs(VIMGOLF_CONFIG_PATH, exist_ok=True)
    os.makedirs(VIMGOLF_DATA_PATH, exist_ok=True)
    os.makedirs(VIMGOLF_CHALLENGES_PATH, exist_ok=True)
    os.makedirs(VIMGOLF_CACHE_PATH, exist_ok=True)
    os.makedirs(VIMGOLF_LOG_DIR_PATH, exist_ok=True)


def init_logger():
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(VIMGOLF_LOG_PATH, mode='w')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def clean_stale_logs():
    logger.info('cleaning stale logs')
    existing_logs_glob = os.path.join(VIMGOLF_LOG_DIR_PATH, 'vimgolf-*-*.log')
    existing_logs = glob.glob(existing_logs_glob)
    log_sort_key = lambda x: float(os.path.basename(x).split('-')[1])
    stale_existing_logs = sorted(existing_logs, key=log_sort_key)[:-LOG_LIMIT]
    for log in stale_existing_logs:
        logger.info('deleting stale log: {}'.format(log))
        try:
            os.remove(log)
        except Exception:
            logger.exception('error deleting stale log: {}'.format(log))


class Failure(Exception):
    pass
