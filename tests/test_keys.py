import pytest

from vimgolf.keys import Keys, parse_raw_keycode_reprs, normalize_keycode_repr


def test_keys():
    cases = [
        (b'\x5a\x5a', ['Z', 'Z']),
        (b'\x80\x6b\x31\x5a\x5a', ['<F1>', 'Z', 'Z']),
        (b'\x1b\x18\x0e\x0d', ['<Esc>', '<C-X>', '<C-N>', '<CR>']),
    ]
    for raw_keys, keycode_reprs in cases:
        keys_from_raw_keys = Keys.from_raw_keys(raw_keys)
        keys_from_keycode_reprs = Keys.from_keycode_reprs(keycode_reprs)
        for keys in [keys_from_raw_keys, keys_from_keycode_reprs]:
            assert keys.raw_keys == raw_keys
            assert keys.keycode_reprs == keycode_reprs


def test_parse_raw_keycode_reprs():
    cases = [
        ('<C-V>G$A;<Esc><C-E>xZZ', [
            '<C-V>', 'G', '$', 'A', ';', '<Esc>', '<C-E>', 'x', 'Z', 'Z',
        ]),
        ('#Yp<C-A>l11.GONew t<C-N><C-N>.<CR><Esc>ZZ', [
            '#', 'Y', 'p', '<C-A>', 'l', '1', '1', '.', 'G', 'O', 'N', 'e', 'w', ' ',
            't', '<C-N>', '<C-N>', '.', '<CR>', '<Esc>', 'Z', 'Z',
        ]),
        ('i# <Esc>fiswa<Esc>A #<CR><Esc>31i#<Esc>yykPZZ', [
            'i', '#', ' ', '<Esc>', 'f', 'i', 's', 'w', 'a', '<Esc>', 'A', ' ', '#',
            '<CR>', '<Esc>', '3', '1', 'i', '#', '<Esc>', 'y', 'y', 'k', 'P', 'Z', 'Z',
        ]),
        ('$<C-V>G$I"<Esc>gvA<C-@>ZZ', [
            '$', '<C-V>', 'G', '$', 'I', '"', '<Esc>', 'g', 'v', 'A', '<C-@>', 'Z', 'Z',
        ]),
        ('cw(<C-R><C-O>")<Esc>w.w.ZZ', [
            'c', 'w', '(', '<C-R>', '<C-O>', '"', ')', '<Esc>', 'w', '.', 'w', '.', 'Z', 'Z',
        ]),
    ]
    for raw_keycode_reprs, expected in cases:
        assert parse_raw_keycode_reprs(raw_keycode_reprs) == expected


def test_parse_raw_keycode_reprs_literal_lt_and_gt():
    literal_lt = '{'
    literal_gt = '}'
    cases = [
        ('<CR>{}CR{}<CR>'.format(literal_lt, literal_gt), [
            '<CR>', '<', 'C', 'R', '>', '<CR>'
        ])
    ]
    for raw_keycode_reprs, expected in cases:
        assert parse_raw_keycode_reprs(
            raw_keycode_reprs,
            literal_lt=literal_lt,
            literal_gt=literal_gt
        ) == expected


def test_assert_literal_lt_and_gt_not_the_same():
    with pytest.raises(AssertionError):
        parse_raw_keycode_reprs('', literal_lt='1', literal_gt='1')


def test_keys_from_raw_keycode_reprs():
    keys = Keys.from_raw_keycode_reprs(
        raw_keycode_reprs='{ZZ}',
        literal_lt='{',
        literal_gt='}'
    )
    assert keys.keycode_reprs == ['<', 'Z', 'Z', '>']


def test_keycode_repr_normalization():
    assert normalize_keycode_repr('<cr>') == '<CR>'
    assert normalize_keycode_repr('<Z') == '<Z'
    assert normalize_keycode_repr('z>') == 'z>'
    test_case = 'zZ<cr><cR><Cr><esc><c-A><C-z>'
    keys = Keys.from_raw_keycode_reprs(test_case, literal_lt=None, literal_gt=None)
    assert keys.keycode_reprs == [
        'z', 'Z', '<CR>', '<CR>', '<CR>', '<Esc>', '<C-A>', '<C-Z>'
    ]
