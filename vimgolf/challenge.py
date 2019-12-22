import datetime
import json
import os
import re
import urllib.parse

from vimgolf import (
    VIMGOLF_ID_LOOKUP_PATH,
    EXPANSION_PREFIX,
    GOLF_HOST,
    VIMGOLF_CHALLENGES_PATH,
)
from vimgolf.utils import write, http_request, format_


def validate_challenge_id(challenge_id):
    return challenge_id is not None and re.match(r'[\w\d]{24}', challenge_id)


def show_challenge_id_error():
    write('Invalid challenge ID', err=True, fg='red')
    write('Please check the ID on vimgolf.com', err=True, fg='red')


def get_id_lookup():
    id_lookup = {}
    if os.path.exists(VIMGOLF_ID_LOOKUP_PATH):
        with open(VIMGOLF_ID_LOOKUP_PATH, 'r') as f:
            id_lookup = json.load(f)
    return id_lookup


def set_id_lookup(id_lookup):
    with open(VIMGOLF_ID_LOOKUP_PATH, 'w') as f:
        json.dump(id_lookup, f, indent=2)


def expand_challenge_id(challenge_id):
    if challenge_id.startswith(EXPANSION_PREFIX):
        challenge_id = get_id_lookup().get(challenge_id[1:], challenge_id)
    return challenge_id


def get_challenge_url(challenge_id):
    return urllib.parse.urljoin(GOLF_HOST, '/challenges/{}'.format(challenge_id))


def get_stored_challenges():
    result = {}
    for d in os.listdir(VIMGOLF_CHALLENGES_PATH):
        full_path = os.path.join(VIMGOLF_CHALLENGES_PATH, d)
        if not os.path.isdir(full_path):
            continue
        result[d] = Challenge(d)
    return result


class Challenge:
    def __init__(
            self,
            id,
            in_text=None,
            out_text=None,
            in_extension=None,
            out_extension=None,
            compliant=None,
            api_key=None):
        self.in_text = in_text
        self.out_text = out_text
        self.in_extension = in_extension
        self.out_extension = out_extension
        self.id = id
        self.compliant = compliant
        self.api_key = api_key

    def load_or_download(self):
        if self.spec:
            return self.load()
        else:
            return self.download()

    def load(self):
        self.load_from_spec(self.spec)
        return self

    def download(self):
        url = urllib.parse.urljoin(GOLF_HOST, '/challenges/{}.json'.format(self.id))
        response = http_request(url)
        challenge_spec = json.loads(response.body)
        self.save(challenge_spec)
        return self

    def load_from_spec(self, challenge_spec):
        in_text = format_(challenge_spec['in']['data'])
        out_text = format_(challenge_spec['out']['data'])
        in_type = challenge_spec['in']['type']
        out_type = challenge_spec['out']['type']
        # Sanitize and add leading dot
        in_extension = '.{}'.format(re.sub(r'[^\w-]', '_', in_type))
        out_extension = '.{}'.format(re.sub(r'[^\w-]', '_', out_type))
        self.in_text = in_text
        self.out_text = out_text
        self.in_extension = in_extension
        self.out_extension = out_extension

    @property
    def dir(self):
        return os.path.join(VIMGOLF_CHALLENGES_PATH, self.id)

    @property
    def spec_path(self):
        return os.path.join(self.dir, 'spec.json')

    @property
    def in_path(self):
        return os.path.join(self.dir, 'in{}'.format(self.in_extension))

    @property
    def out_path(self):
        return os.path.join(self.dir, 'out{}'.format(self.out_extension))

    @property
    def answers_path(self):
        return os.path.join(self.dir, 'answers.jsonl')

    @property
    def metadata_path(self):
        return os.path.join(self.dir, 'metadata.json')

    def save(self, spec):
        self.load_from_spec(spec)
        self._ensure_dir()
        with open(self.in_path, 'w') as f:
            f.write(self.in_text)
        with open(self.out_path, 'w') as f:
            f.write(self.out_text)
        with open(self.spec_path, 'w') as f:
            json.dump(spec, f)

    def add_answer(self, keys, correct, score, uploaded):
        self._ensure_dir()
        with open(self.answers_path, 'a') as f:
            f.write('{}\n'.format(json.dumps({
                'keys': keys,
                'correct': correct,
                'score': score,
                'uploaded': uploaded,
                'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            })))

    @property
    def answers(self):
        if not os.path.exists(self.answers_path):
            return []
        result = []
        with open(self.answers_path) as f:
            for raw_answer in f:
                result.append(json.loads(raw_answer))
        return sorted(result, key=lambda a: a['timestamp'])

    @property
    def spec(self):
        if not os.path.exists(self.spec_path):
            return {}
        with open(self.spec_path) as f:
            return json.load(f)

    @property
    def metadata(self):
        if not os.path.exists(self.metadata_path):
            return {}
        with open(self.metadata_path) as f:
            return json.load(f)

    def update_metadata(self, name=None, description=None):
        self._ensure_dir()
        uploaded = 0
        correct = 0
        stub_score = 10 ** 10
        best_score = stub_score
        for answer in self.answers:
            if answer['uploaded']:
                uploaded += 1
            if answer['correct']:
                correct += 1
                best_score = min(best_score, answer['score'])
        current_metadata = self.metadata
        current_metadata.update({
            'id': self.id,
            'url': get_challenge_url(self.id),
            'uploaded': uploaded,
            'correct': correct,
            'best_score': best_score if best_score != stub_score else -1,
        })
        if name:
            current_metadata['name'] = name
        if description:
            current_metadata['description'] = description
        with open(self.metadata_path, 'w') as f:
            json.dump(current_metadata, f)

    def _ensure_dir(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir, exist_ok=True)
