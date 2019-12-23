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
    keycode_reprs = full_processed_keys.keycode_reprs
    sequences = [
        Keys.from_keycode_reprs(keycode_reprs[:i])
        for i in range(len(keycode_reprs) + 1)
    ]

    with tempfile.TemporaryDirectory() as d:

        def dst_path(index):
            index = str(index).zfill(3)
            return os.path.join(d, '{}{}{}'.format(name, index, ext))

        def log_path(index):
            index = str(index).zfill(3)
            return os.path.join(d, 'log{}'.format(index))

        def in_path(index):
            index = str(index).zfill(3)
            return os.path.join(d, 'inspect-{}{}{}'.format(name, index, ext))

        for i, processed_keys in enumerate(sequences):
            shutil.copy(src_in_path, dst_path(i))
            with open(log_path(i), 'wb') as f:
                f.write(processed_keys.raw_keys + REPLAY_QUIT_RAW_KEYS)
            play.replay(dst_path(i), log_path(i))

        first_sequence = 0
        last_sequence = len(sequences) - 1
        in_sequences = [first_sequence]
        for i in range(len(sequences) - 1):
            different = not filecmp.cmp(dst_path(i), dst_path(i + 1))
            if different:
                in_sequences.append(i + 1)
        if last_sequence not in in_sequences:
            in_sequences.append(last_sequence)

        for i, in_sequence_index in enumerate(in_sequences):
            with open(in_path(i), 'wb') as in_f:
                if in_sequence_index == first_sequence:
                    reprs = '(IN)'
                else:
                    reprs = ''.join(sequences[in_sequence_index].keycode_reprs)
                    if in_sequence_index == last_sequence:
                        reprs = '{} (OUT)'.format(reprs)
                header = '{}\n----------------------\n'.format(reprs)
                in_f.write(bytes(header, 'utf-8'))
                with open(dst_path(in_sequence_index), 'rb') as dst_f:
                    in_f.write(dst_f.read())

        inspect_pairs = []
        for i in range(len(in_sequences) - 1):
            inspect_pairs.append([in_path(i), in_path(i+1)])
        inspect_pairs.append([in_path(0), in_path(len(in_sequences) - 1)])

        # TODO fix <Del> handling
        inspect_pairs_path = os.path.join(d, 'inspect-pairs.vim')
        with open(inspect_pairs_path, 'w') as f:
            f.write("let g:inspectPairs = [")
            for first, second in inspect_pairs:
                f.write("['{}','{}'],".format(first, second))
            f.write("]\n")
            f.write('call InspectCompare()')

        play.inspect(inspect_pairs_path)
