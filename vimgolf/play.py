import filecmp
import json
import os
import urllib.parse

from vimgolf import logger, PLAY_VIMRC_PATH, GOLF_HOST, INSPECT_VIM_PATH
from vimgolf.challenge import get_challenge_url
from vimgolf.keys import Keys
from vimgolf.utils import write, input_loop, http_request
from vimgolf.vim import vim


def play(challenge, workspace):
    logger.info('play(...)')

    infile = os.path.join(workspace, 'in')
    if challenge.in_extension:
        infile += challenge.in_extension
    outfile = os.path.join(workspace, 'out')
    if challenge.out_extension:
        outfile += challenge.out_extension
    logfile = os.path.join(workspace, 'log')
    with open(outfile, 'w') as f:
        f.write(challenge.out_text)

    write('Launching vimgolf session', fg='yellow')
    main_loop(challenge, infile, logfile, outfile)
    write('Thanks for playing!', fg='green')


def main_loop(challenge, infile, logfile, outfile):
    while True:
        with open(infile, 'w') as f:
            f.write(challenge.in_text)

        play_result = play_single(
            infile=infile,
            logfile=logfile,
            outfile=outfile,
        )

        raw_keys = play_result['raw_keys']
        keycode_reprs = play_result['keycode_reprs']
        correct = play_result['correct']
        score = play_result['score']

        write('Here are your keystrokes:', fg='green')
        for keycode_repr in keycode_reprs:
            color = 'magenta' if len(keycode_repr) > 1 else None
            write(keycode_repr, fg=color, nl=False)
        write()

        if correct:
            write('Success! Your output matches.', fg='green')
            write('Your score:', fg='green')
        else:
            write('Uh oh, looks like your entry does not match the desired output.', fg='red')
            write('Your score for this failed attempt:', fg='red')
        write(score)

        menu_loop_result = menu_loop(
            challenge=challenge,
            correct=correct,
            infile=infile,
            outfile=outfile,
            raw_keys=raw_keys
        )

        if challenge.id:
            challenge.add_answer(
                keys=keycode_reprs,
                score=score,
                correct=correct,
                uploaded=menu_loop_result['uploaded'],
            )

        if menu_loop_result['should_quit']:
            break


def play_single(infile, logfile, outfile):
    vim(play_args(infile, logfile), check=True)
    correct = filecmp.cmp(infile, outfile)
    with open(logfile, 'rb') as _f:
        keys = Keys.from_raw_keys(_f.read())
    return {
        'correct': correct,
        'keycode_reprs': keys.keycode_reprs,
        'raw_keys': keys.raw_keys,
        'score': keys.score,
    }


def replay(infile, logfile, mappingfile):
    vim(replay_args(infile, logfile, mappingfile), check=True)


def inspect(inspect_pairs_path):
    vim(inspect_args(inspect_pairs_path), check=True)


def base_args():
    return [
        '-Z',  # restricted mode, utilities not allowed
        '-n',  # no swap file, memory only editing
        '--noplugin',  # no plugins
        '-i', 'NONE',  # don't load .viminfo (e.g., has saved macros, etc.)
        '+0',  # start on line 0
        '-u', PLAY_VIMRC_PATH,  # vimgolf .vimrc
        '-U', 'NONE',  # don't load .gvimrc
    ]


def play_args(infile, logfile):
    return base_args() + [
        '-W', logfile,  # keylog file (overwrites existing)
        infile,
    ]


def replay_args(infile, logfile, mappingfile):
    return base_args() + [
        '-S', mappingfile,
        '-s', logfile,  # keylog will call mapping
        infile,
    ]


def inspect_args(inspect_pairs_path):
    return base_args() + [
        '-S', INSPECT_VIM_PATH,
        '-S', inspect_pairs_path,
    ]


def menu_loop(
        challenge,
        correct,
        infile,
        outfile,
        raw_keys):
    upload_eligible = challenge.id and challenge.compliant and challenge.api_key
    uploaded = False
    while True:
        # Generate the menu items inside the loop since it can change across iterations
        # (e.g., upload option can be removed)
        menu = []
        if not correct:
            menu.append(('d', 'Show diff'))
        if upload_eligible and correct:
            menu.append(('w', 'Upload result'))
        menu.append(('r', 'Retry the current challenge'))
        menu.append(('q', 'Quit vimgolf'))
        valid_codes = [x[0] for x in menu]
        for opt in menu:
            write('[{}] {}'.format(*opt), fg='yellow')
        selection = input_loop('Choice> ')
        if selection not in valid_codes:
            write('Invalid selection: {}'.format(selection), err=True, fg='red')
        elif selection == 'd':
            diff_args = ['-d', '-n', infile, outfile]
            vim(diff_args)
        elif selection == 'w':
            success = upload_result(challenge.id, challenge.api_key, raw_keys)
            if success:
                write('Uploaded entry!', fg='green')
                leaderboard_url = get_challenge_url(challenge.id)
                write('View the leaderboard: {}'.format(leaderboard_url), fg='green')
                uploaded = True
                upload_eligible = False
            else:
                write('The entry upload has failed', err=True, fg='red')
                message = 'Please check your API key on vimgolf.com'
                write(message, err=True, fg='red')
        else:
            break
    should_quit = selection == 'q'
    if not should_quit:
        write('Retrying vimgolf challenge', fg='yellow')
    return {
        'should_quit': should_quit,
        'uploaded': uploaded,
    }


def upload_result(challenge_id, api_key, raw_keys):
    logger.info('upload_result(...)')
    success = False
    try:
        url = urllib.parse.urljoin(GOLF_HOST, '/entry.json')
        data_dict = {
            'challenge_id': challenge_id,
            'apikey':       api_key,
            'entry':        raw_keys,
        }
        data = urllib.parse.urlencode(data_dict).encode()
        response = http_request(url, data=data)
        message = json.loads(response.body)
        if message.get('status') == 'ok':
            success = True
    except Exception:
        logger.exception('upload failed')
    return success
