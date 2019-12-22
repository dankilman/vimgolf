import filecmp
import os
import shutil
import tempfile

from vimgolf import play
from vimgolf.challenge import Challenge
from vimgolf.keys import Keys, REPLAY_QUIT_RAW_KEYS


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
        def dst_path(index):
            index = str(index).zfill(3)
            return os.path.join(d, '{}{}{}'.format(name, index, ext))

        def log_path(index):
            index = str(index).zfill(3)
            return os.path.join(d, 'log{}'.format(index))

        for i, processed_keys in sequences:
            shutil.copy(src_in_path, dst_path(i))
            with open(log_path(i), 'wb') as f:
                f.write(processed_keys.raw_keys + REPLAY_QUIT_RAW_KEYS)
            play.replay_single(dst_path(i), log_path(i))

        first_sequence = 0
        last_sequence = len(sequences) - 1
        interesting_sequences = [first_sequence]
        for i in range(len(sequences) - 1):
            different = not filecmp.cmp(dst_path(i), dst_path(i + 1))
            if different:
                interesting_sequences.append(i + 1)
        if last_sequence not in interesting_sequences:
            interesting_sequences.append(last_sequence)

        print(interesting_sequences)
        print(d)
        import time
        time.sleep(600)
