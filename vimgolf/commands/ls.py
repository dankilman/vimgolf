import urllib.parse
from collections import namedtuple

from terminaltables import AsciiTable

from vimgolf import (
    LISTING_LIMIT,
    logger,
    GOLF_HOST,
    EXPANSION_PREFIX,
    Failure,
)
from vimgolf.challenge import get_stored_challenges, set_id_lookup
from vimgolf.html import (
    parse_html,
    get_elements_by_classname,
    get_elements_by_tagname,
    NodeType,
)
from vimgolf.utils import http_request, write, style, bool_to_mark

Listing = namedtuple('Listing', 'id name n_entries uploaded score answers')


def ls(page=None, limit=LISTING_LIMIT):
    logger.info('list_(%s, %s)', page, limit)
    stored_challenges = get_stored_challenges()
    try:
        url = GOLF_HOST
        if page is not None:
            url = urllib.parse.urljoin(GOLF_HOST, '/?page={}'.format(page))
        response = http_request(url)
        listings = extract_listings_from_page(
            page_html=response.body,
            limit=limit,
            stored_challenges=stored_challenges
        )
    except Failure:
        raise
    except Exception:
        logger.exception('challenge retrieval failed')
        write('The challenge list retrieval has failed', err=True, fg='red')
        raise Failure()

    table_rows = [['#', 'Name', 'Entries', 'ID', 'Submitted', 'Score', 'Answers']]
    for idx, listing in enumerate(listings):
        table_row = [
            '{}{} '.format(EXPANSION_PREFIX, idx + 1),
            listing.name,
            listing.n_entries,
            style(listing.id, fg='yellow'),
            bool_to_mark(listing.uploaded),
            listing.score if listing.score and listing.score > 0 else '-',
            listing.answers or '-',
        ]
        table_rows.append(table_row)

    write(AsciiTable(table_rows).table)

    id_lookup = {str(idx+1): listing.id for idx, listing in enumerate(listings)}
    set_id_lookup(id_lookup)


def extract_listings_from_page(page_html, limit, stored_challenges):
    nodes = parse_html(page_html)
    listings = []
    challenge_elements = get_elements_by_classname(nodes, 'challenge')
    for element in challenge_elements:
        if len(listings) >= limit:
            break
        anchor = get_elements_by_tagname(element.children, 'a')[0]
        href = anchor.get_attr('href')
        id_ = href.split('/')[-1]
        name = anchor.children[0].data
        n_entries = None
        for child in element.children:
            if child.node_type == NodeType.TEXT and 'entries' in child.data:
                n_entries = int([x for x in child.data.split() if x.isdigit()][0])
                break
        stored_challenge = stored_challenges.get(id_)
        stored_metadata = stored_challenge.metadata if stored_challenge else {}
        listing = Listing(
            id=id_,
            name=name,
            n_entries=n_entries,
            uploaded=stored_metadata.get('uploaded'),
            score=stored_metadata.get('best_score'),
            answers=stored_metadata.get('answers'),
        )
        listings.append(listing)
    return listings


def parse_list_spec(raw_spec):
    page_and_limit = raw_spec or ''
    spec = {}
    parts = page_and_limit.split(':')
    try:
        if len(parts) > 0 and parts[0]:
            spec['page'] = int(parts[0])
        if len(parts) > 1:
            spec['limit'] = int(parts[1])
    except Exception:
        pass
    return spec

