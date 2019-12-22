import concurrent.futures
import json
import urllib.parse
from collections import namedtuple

from terminaltables import AsciiTable

from vimgolf import (
    logger,
    GOLF_HOST,
    MAX_REQUEST_WORKERS,
    LEADER_LIMIT,
    Failure,
)
from vimgolf.challenge import (
    expand_challenge_id,
    validate_challenge_id,
    show_challenge_id_error,
    get_challenge_url,
    Challenge,
)
from vimgolf.html import (
    parse_html,
    get_element_by_id,
    get_elements_by_classname,
    get_elements_by_tagname,
    get_text,
)
from vimgolf.utils import http_request, join_lines, write, bool_to_mark


def show(challenge_id, tracked=False):
    challenge_id = expand_challenge_id(challenge_id)
    logger.info('show(%s)', challenge_id)

    if not validate_challenge_id(challenge_id):
        show_challenge_id_error()
        raise Failure()

    try:
        fetched = fetch_challenge_spec_and_page(challenge_id)
        challenge = fetched['challenge']
        page_response = fetched['page']
        page_url = fetched['url']

        data = extract_data_from_page(page_response.body)
        name = data['name']
        description = data['description']
        leaders = data['leaders']

        challenge.update_metadata(name, description)

        start_file = challenge.in_text
        if not start_file.endswith('\n'):
            start_file += '\n'
        end_file = challenge.out_text
        if not end_file.endswith('\n'):
            end_file += '\n'

        separator = '-' * 50
        write(separator)
        write('{} ('.format(name), nl=False)
        write(challenge_id, fg='yellow', nl=False)
        write(')')
        write(separator)
        write(page_url)
        write(separator)
        write('Leaderboard', fg='green')
        if leaders:
            for leader in leaders[:LEADER_LIMIT]:
                write('{} {}'.format(leader.username.ljust(15), leader.score))
            if len(leaders) > LEADER_LIMIT:
                write('...')
        else:
            write('no entries yet', fg='yellow')
        write(separator)
        write(description)
        write(separator)
        write('Start File', fg='green')
        write(start_file, nl=False)
        write(separator)
        write('End File', fg='green')
        write(end_file, nl=False)
        write(separator)

        if tracked:
            write('Stats', fg='green')
            metadata = challenge.metadata
            write('Uploaded: {}'.format(metadata['uploaded']))
            write('Correct Solutions: {}'.format(metadata['correct']))
            write('Self Best Score: {}'.format(metadata['best_score']))
            answers = challenge.answers
            ignored_answer_suffix = 'ZQ'
            answer_rows = [['Keys', 'Correct', 'Submitted', 'Score', 'Timestamp']]
            for answer in answers:
                keys = ''.join(answer['keys'])
                if keys.endswith(ignored_answer_suffix):
                    continue
                answer_row = [
                    keys,
                    bool_to_mark(answer['correct']),
                    bool_to_mark(answer['uploaded']),
                    answer['score'],
                    answer['timestamp'],
                ]
                answer_rows.append(answer_row)
            if len(answer_rows) > 1:
                write(AsciiTable(answer_rows).table)
    except Failure:
        raise
    except Exception:
        logger.exception('challenge retrieval failed')
        write('The challenge retrieval has failed', err=True, fg='red')
        write('Please check the challenge ID on vimgolf.com', err=True, fg='red')
        raise Failure()


def fetch_challenge_spec_and_page(challenge_id):
    challenge = Challenge(challenge_id)
    challenge_spec = challenge.spec
    api_url = urllib.parse.urljoin(GOLF_HOST, '/challenges/{}.json'.format(challenge_id))
    page_url = get_challenge_url(challenge_id)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_REQUEST_WORKERS) as executor:
        requests = [page_url]
        if not challenge_spec:
            requests.append(api_url)
        results = executor.map(http_request, requests)
        page_response = next(results)
        if not challenge_spec:
            api_response = next(results)
            challenge_spec = json.loads(api_response.body)
            challenge.save(challenge_spec)
        else:
            challenge.load()
    return {
        'challenge': challenge,
        'page': page_response,
        'url': page_url
    }


def extract_data_from_page(page_html):
    nodes = parse_html(page_html)
    content_element = get_element_by_id(nodes, 'content')
    content_grid_7_element = get_elements_by_classname(content_element.children, 'grid_7')[0]
    name_h3 = get_elements_by_tagname(content_grid_7_element.children, 'h3')[0]
    name = join_lines(get_text([name_h3]).strip())
    description_p_element = get_elements_by_tagname(content_grid_7_element.children, 'p')[0]
    description = join_lines(get_text([description_p_element]).strip())
    content_grid_5_element = get_elements_by_classname(content_element.children, 'grid_5')[0]
    Leader = namedtuple('Leader', 'username score')
    leaders = []
    leaderboard_divs = get_elements_by_tagname(content_grid_5_element.children, 'div')
    for leaderboard_div in leaderboard_divs:
        user_h6 = get_elements_by_tagname(leaderboard_div.children, 'h6')[0]
        username_anchor = get_elements_by_tagname(user_h6.children, 'a')[1]
        username = get_text([username_anchor]).strip()
        if username.startswith('@'):
            username = username[1:]
        score_div = get_elements_by_tagname(leaderboard_div.children, 'div')[0]
        score = int(get_text([score_div]).strip())
        leader = Leader(username=username, score=score)
        leaders.append(leader)
    return {
        'name': name,
        'description': description,
        'leaders': leaders
    }
