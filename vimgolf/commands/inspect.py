import shutil
import tempfile
import os
from vimgolf import play
from vimgolf.challenge import Challenge
from vimgolf.keys import Keys


def inspect(challenge_id, keys, literal_lt, literal_gt):
    challenge = Challenge(challenge_id)
    challenge.load_or_download()
    processed_keys = Keys.from_raw_keycode_reprs(
        raw_keycode_reprs=keys,
        literal_lt=literal_lt,
        literal_gt=literal_gt,
    )
    with tempfile.TemporaryDirectory() as d:
        src_in_path = challenge.in_path
        dst_in_path = os.path.join(d, os.path.basename(src_in_path))
        shutil.copy(src_in_path, dst_in_path)
        log_path = os.path.join(d, 'log')
        with open(log_path, 'wb') as f:
            f.write(processed_keys.raw_keys)
        play.replay_single(dst_in_path, log_path)
