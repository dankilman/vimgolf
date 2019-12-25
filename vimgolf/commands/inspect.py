import filecmp
import os
import shutil
import tempfile

from vimgolf import logger, Failure, INSPECT_VIM_PATH
from vimgolf.challenge import (
    Challenge,
    expand_challenge_id,
    validate_challenge_id,
    show_challenge_id_error,
)
from vimgolf.keys import tokenize_raw_keycode_reprs, REPLAY_QUIT_TOKENS
from vimgolf.utils import write
from vimgolf.vim import vim, BASE_ARGS


def inspect(challenge_id, keys, literal_lt, literal_gt):
    challenge_id = expand_challenge_id(challenge_id)
    logger.info('inspect(%s)', challenge_id)

    if not validate_challenge_id(challenge_id):
        show_challenge_id_error()
        raise Failure()

    try:
        challenge = Challenge(challenge_id)
        challenge.load_or_download()
    except Failure:
        raise
    except Exception:
        logger.exception('challenge retrieval failed')
        write('The challenge retrieval has failed', err=True, fg='red')
        write('Please check the challenge ID on vimgolf.com', err=True, fg='red')
        raise Failure()

    src_in_path = challenge.in_path
    name, ext = os.path.splitext(os.path.basename(src_in_path))

    sequences = build_sequences(
        keys=keys,
        literal_gt=literal_gt,
        literal_lt=literal_lt
    )

    with tempfile.TemporaryDirectory() as workspace:
        zfill = lambda s: str(s).zfill(3)

        def dst_path(index):
            return os.path.join(workspace, '{}{}{}'.format(name, zfill(index), ext))

        def script_path(index):
            return os.path.join(workspace, 'mapping{}.vim'.format(zfill(index)))

        def in_path(index):
            return os.path.join(workspace, 'inspect-{}{}{}'.format(name, zfill(index), ext))

        replay_sequences(
            dst_path=dst_path,
            script_path=script_path,
            sequences=sequences,
            src_in_path=src_in_path
        )
        inspect_sequences(
            workspace=workspace,
            dst_path=dst_path,
            in_path=in_path,
            sequences=sequences
        )


def build_sequences(keys, literal_gt, literal_lt):
    tokens = tokenize_raw_keycode_reprs(
        raw_keycode_reprs=keys,
        literal_lt=literal_lt,
        literal_gt=literal_gt,
    )
    return [tokens[:i] for i in range(len(tokens) + 1)]


def replay_sequences(dst_path, script_path, sequences, src_in_path):
    for i, tokens in enumerate(sequences):
        shutil.copy(src_in_path, dst_path(i))
        all_tokens = tokens + REPLAY_QUIT_TOKENS
        escaped_tokens = [
            '\\{}'.format(t) if len(t) > 1 else t
            for t in all_tokens
        ]
        final_keys = ''.join(escaped_tokens)
        with open(script_path(i), 'w') as f:
            f.write('call feedkeys("{}", "t")'.format(final_keys))

        vim(BASE_ARGS + [
            '-S', script_path(i),
            dst_path(i),
        ], check=True)


def inspect_sequences(workspace, dst_path, in_path, sequences):
    in_sequences = find_interesting_sequences(dst_path, sequences)

    prepare_inspect_files(
        in_path=in_path,
        dst_path=dst_path,
        sequences=sequences,
        in_sequences=in_sequences,
    )

    inspect_pairs_path = build_inspect_pairs(
        in_path=in_path,
        in_sequences=in_sequences,
        workspace=workspace,
    )

    vim(BASE_ARGS + [
        '-S', INSPECT_VIM_PATH,
        '-S', inspect_pairs_path,
    ], check=True)


def prepare_inspect_files(dst_path, in_path, in_sequences, sequences):
    for i, in_sequence_index in enumerate(in_sequences):
        with open(in_path(i), 'wb') as in_f:
            if in_sequence_index == 0:
                reprs = '(IN)'
            else:
                reprs = ''.join(sequences[in_sequence_index])
                if in_sequence_index == len(sequences) - 1:
                    reprs = '{} (OUT)'.format(reprs)
            header = '{}\n----------------------\n'.format(reprs)
            in_f.write(bytes(header, 'utf-8'))
            with open(dst_path(in_sequence_index), 'rb') as dst_f:
                in_f.write(dst_f.read())


def build_inspect_pairs(in_path, in_sequences, workspace):
    inspect_pairs = []
    for i in range(len(in_sequences) - 1):
        inspect_pairs.append([in_path(i), in_path(i + 1)])
    # add pair for first/last
    inspect_pairs.append([in_path(0), in_path(len(in_sequences) - 1)])
    inspect_pairs_path = os.path.join(workspace, 'inspect-pairs.vim')
    with open(inspect_pairs_path, 'w') as f:
        f.write("let g:inspectPairs = [")
        for first1, second in inspect_pairs:
            f.write("['{}','{}'],".format(first1, second))
        f.write("]\n")
        f.write('call InspectCompare()')
    return inspect_pairs_path


def find_interesting_sequences(dst_path, sequences):
    last_sequence = len(sequences) - 1
    in_sequences = [0]
    for i in range(len(sequences) - 1):
        if not filecmp.cmp(dst_path(i), dst_path(i + 1)):
            in_sequences.append(i + 1)
    if last_sequence not in in_sequences:
        in_sequences.append(last_sequence)
    return in_sequences
