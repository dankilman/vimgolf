import os
import shutil
import tempfile

from vimgolf import play
from vimgolf.challenge import Challenge
from vimgolf.keys import Keys


def inspect(challenge_id, keys, literal_lt, literal_gt):
    challenge = Challenge(challenge_id)
    challenge.load_or_download()
    src_in_path = challenge.in_path
    name, ext = os.path.splitext(os.path.basename(src_in_path))

    full_processed_keys = Keys.from_raw_keycode_reprs(
        raw_keycode_reprs=keys,
        literal_lt=literal_lt,
        literal_gt=literal_gt,
    )
    keycode_reps = full_processed_keys.keycode_reprs
    sequences = [
        (i, Keys.from_keycode_reprs(keycode_reps[:i]))
        for i in range(len(keycode_reps) + 1)
    ]

    with tempfile.TemporaryDirectory() as d:
        for i, processed_keys in sequences:
            i = str(i).zfill(3)
            dst_in_path = os.path.join(d, '{}{}{}'.format(name, i, ext))
            shutil.copy(src_in_path, dst_in_path)
            log_path = os.path.join(d, 'log{}'.format(i))
            with open(log_path, 'wb') as f:
                f.write(processed_keys.raw_keys)
            play.replay_single(dst_in_path, log_path)
        print(d)
        import time
        time.sleep(600)
