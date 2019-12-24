import filecmp
import os
import shutil
import tempfile

from vimgolf import play, logger, Failure
from vimgolf.challenge import (
    Challenge,
    expand_challenge_id,
    validate_challenge_id,
    show_challenge_id_error,
)
from vimgolf.keys import REPLAY_QUIT_KEYCODE_REPRS, tokenize_raw_keycode_reprs
from vimgolf.utils import write


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

        def mapping_path(index):
            return os.path.join(workspace, 'mapping{}.vim'.format(zfill(index)))

        def in_path(index):
            return os.path.join(workspace, 'inspect-{}{}{}'.format(name, zfill(index), ext))

        replay_sequences(
            workspace=workspace,
            dst_path=dst_path,
            mapping_path=mapping_path,
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


def replay_sequences(workspace, dst_path, mapping_path, sequences, src_in_path):
    log_path = os.path.join(workspace, 'log')
    mapping = '\\q'
    with open(log_path, 'w') as f:
        f.write(mapping)
    for i, tokens in enumerate(sequences):
        shutil.copy(src_in_path, dst_path(i))
        keycode_reprs = ''.join(tokens)
        final_keycode_reprs = '{}{}'.format(keycode_reprs, REPLAY_QUIT_KEYCODE_REPRS)
        with open(mapping_path(i), 'w') as f:
            f.write('nnoremap {} {}'.format(mapping, final_keycode_reprs))
        play.replay(infile=dst_path(i), logfile=log_path, mappingfile=mapping_path(i))


def inspect_sequences(workspace, dst_path, in_path, sequences):
    result = find_interesting_sequences(dst_path, sequences)
    in_sequences = result['sequences']
    first = result['first']
    last = result['last']

    prepare_inspect_files(
        in_path=in_path,
        dst_path=dst_path,
        first=first,
        last=last,
        sequences=sequences,
        in_sequences=in_sequences,
    )

    inspect_pairs_path = build_inspect_pairs(
        in_path=in_path,
        in_sequences=in_sequences,
        workspace=workspace,
    )

    play.inspect(inspect_pairs_path)


def prepare_inspect_files(dst_path, first, in_path, in_sequences, last, sequences):
    for i, in_sequence_index in enumerate(in_sequences):
        with open(in_path(i), 'wb') as in_f:
            if in_sequence_index == first:
                reprs = '(IN)'
            else:
                reprs = ''.join(sequences[in_sequence_index])
                if in_sequence_index == last:
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
    path = os.path.join(workspace, 'inspect-pairs.vim')
    with open(path, 'w') as f:
        f.write("let g:inspectPairs = [")
        for first1, second in inspect_pairs:
            f.write("['{}','{}'],".format(first1, second))
        f.write("]\n")
        f.write('call InspectCompare()')
    inspect_pairs_path = path
    return inspect_pairs_path


def find_interesting_sequences(dst_path, sequences):
    first_sequence = 0
    last_sequence = len(sequences) - 1
    in_sequences = [first_sequence]
    for i in range(len(sequences) - 1):
        if not filecmp.cmp(dst_path(i), dst_path(i + 1)):
            in_sequences.append(i + 1)
    if last_sequence not in in_sequences:
        in_sequences.append(last_sequence)
    return {
        'first': first_sequence,
        'last': last_sequence,
        'sequences': in_sequences
    }
