"""Maps keys recorded by vim to a printable representation"""


def to_bytes(kc):
    """Convert an integer to bytes."""
    return kc.to_bytes(2, 'big')


def to_int(kc):
    """Convert bytes to an integer."""
    return int(kc.hex(), 16)


# Vim records key presses using 1) a single byte or 2) a 0x80 byte
# followed by two bytes. Parse the single-bytes and double-bytes.
# For the returned list, all values are represented with two bytes
# (single bytes are padded).
def parse_keycodes(raw_keys):
    """
    Parse list of keypress bytes from raw keypress representation saved
    by vim's -w.
    """
    keycodes = []
    tmp = list(reversed(raw_keys))
    while tmp:
        b0 = tmp.pop()
        if b0 == 0x80:
            b1 = tmp.pop()
            b2 = tmp.pop()
            keycode = bytes((b1, b2))
        else:
            keycode = to_bytes(b0)
        keycodes.append(keycode)
    return keycodes


def to_raw_keys(keycodes):
    raw_keys = []
    for keycode in keycodes:
        if keycode[0] == 0:
            raw_keys.append(keycode[1])
        else:
            raw_keys.extend([0x80, keycode[0], keycode[1]])
    return bytes(raw_keys)


def parse_raw_keycode_reprs(
        raw_keycode_reprs: str,
        literal_lt='',
        literal_gt=''):
    if literal_lt and literal_gt:
        assert literal_lt != literal_gt
    keycodes = []
    multi_in_progress = False
    multi_keys = []
    for raw_keycode_repr in raw_keycode_reprs:
        if raw_keycode_repr == '<':
            multi_in_progress = True
            multi_keys.append(raw_keycode_repr)
        elif raw_keycode_repr == '>':
            multi_keys.append(raw_keycode_repr)
            multi_in_progress = False
            keycodes.append(''.join(multi_keys))
            multi_keys = []
        elif multi_in_progress:
            multi_keys.append(raw_keycode_repr)
        elif literal_lt and raw_keycode_repr == literal_lt:
            keycodes.append('<')
        elif literal_gt and raw_keycode_repr == literal_gt:
            keycodes.append('>')
        else:
            keycodes.append(raw_keycode_repr)
    return keycodes


# keystrokes that should not impact score (e.g., window focus)
IGNORED_KEYSTROKES = {
    b'\xfd\x35',  # (35) KE_IGNORE
    # Incidentally, CursorHold is triggered on GVIM move window
    b'\xfd\x60',  # (96) KE_CURSORHOLD Move Window (GVIM)
    b'\xfd\x61',  # (97) KE_NOP
    b'\xfd\x62',  # (98) KE_FOCUSGAINED Focus Gained (GVIM)
    b'\xfd\x63',  # (99) KE_FOCUSLOST Focus Lost (GVIM)
}

_KEYCODE_REPR_LOOKUP = {}
# Control characters
for x in range(32):
    _KEYCODE_REPR_LOOKUP[to_bytes(x)] = '<C-{}>'.format(chr(x + 64))
# Printable characters
for x in range(32, 127):
    _KEYCODE_REPR_LOOKUP[to_bytes(x)] = chr(x)
# Single byte fallback
for x in range(127, 256):
    _KEYCODE_REPR_LOOKUP[to_bytes(x)] = '<0x{:02x}>'.format(x)
# Specially named control characters and others
_KEYCODE_REPR_LOOKUP[to_bytes(9)] = '<Tab>'
_KEYCODE_REPR_LOOKUP[to_bytes(10)] = '<NL>'
_KEYCODE_REPR_LOOKUP[to_bytes(13)] = '<CR>'
_KEYCODE_REPR_LOOKUP[to_bytes(27)] = '<Esc>'
_KEYCODE_REPR_LOOKUP[to_bytes(127)] = '<Del>'

_KEYCODE_REPR_LOOKUP.update({
    b'k1': '<F1>',
    b'k2': '<F2>',
    b'k3': '<F3>',
    b'k4': '<F4>',
    b'k5': '<F5>',
    b'k6': '<F6>',
    b'k7': '<F7>',
    b'k8': '<F8>',
    b'k9': '<F9>',
    b'k;': '<F10>',
    b'F1': '<F11>',
    b'F2': '<F12>',
    b'F3': '<F13>',
    b'F4': '<F14>',
    b'F5': '<F15>',
    b'F6': '<F16>',
    b'F7': '<F17>',
    b'F8': '<F18>',
    b'F9': '<F19>',

    b'%1': '<Help>',
    b'&8': '<Undo>',
    b'#2': '<S-Home>',
    b'*7': '<S-End>',
    b'K1': '<kHome>',
    b'K4': '<kEnd>',
    b'K3': '<kPageUp>',
    b'K5': '<kPageDown>',
    b'K6': '<kPlus>',
    b'K7': '<kMinus>',
    b'K8': '<kDivide>',
    b'K9': '<kMultiply>',
    b'KA': '<kEnter>',
    b'KB': '<kPoint>',
    b'KC': '<k0>',
    b'KD': '<k1>',
    b'KE': '<k2>',
    b'KF': '<k3>',
    b'KG': '<k4>',
    b'KH': '<k5>',
    b'KI': '<k6>',
    b'KJ': '<k7>',
    b'KK': '<k8>',
    b'KL': '<k9>',

    b'kP': '<PageUp>',
    b'kN': '<PageDown>',
    b'kh': '<Home>',
    b'@7': '<End>',
    b'kI': '<Insert>',
    b'kD': '<Del>',
    b'kb': '<BS>',

    b'ku': '<Up>',
    b'kd': '<Down>',
    b'kl': '<Left>',
    b'kr': '<Right>',
    b'#4': '<S-Left>',
    b'%i': '<S-Right>',

    b'kB': '<S-Tab>',
    b'\xffX': '<C-@>',

    # Escaped literal 0x80
    b'\xfeX': '<0x80>',

    # "These rarely-used modifiers should be combined with the next
    #  stroke (like <S-Space>), but let's put them here for now"
    b'\xfc\x02': '<S->',
    b'\xfc\x04': '<C->',
    b'\xfc\x06': '<C-S->',
    b'\xfc\x08': '<A->',
    b'\xfc\x0a': '<A-S->',
    b'\xfc\x0c': '<C-A->',
    b'\xfc\x0e': '<C-A-S->',
    b'\xfc\x10': '<M->',
    b'\xfc\x12': '<M-S->',
    b'\xfc\x14': '<M-C->',
    b'\xfc\x16': '<M-C-S->',
    b'\xfc\x18': '<M-A->',
    b'\xfc\x1a': '<M-A-S->',
    b'\xfc\x1c': '<M-C-A->',
    b'\xfc\x1e': '<M-C-A-S->',

    b'\xfd\x04': '<S-Up>',
    b'\xfd\x05': '<S-Down>',
    b'\xfd\x06': '<S-F1>',
    b'\xfd\x07': '<S-F2>',
    b'\xfd\x08': '<S-F3>',
    b'\xfd\x09': '<S-F4>',
    b'\xfd\x0a': '<S-F5>',
    b'\xfd\x0b': '<S-F6>',
    b'\xfd\x0c': '<S-F7>',
    b'\xfd\x0d': '<S-F9>',
    b'\xfd\x0e': '<S-F10>',
    b'\xfd\x0f': '<S-F10>',
    b'\xfd\x10': '<S-F11>',
    b'\xfd\x11': '<S-F12>',
    b'\xfd\x12': '<S-F13>',
    b'\xfd\x13': '<S-F14>',
    b'\xfd\x14': '<S-F15>',
    b'\xfd\x15': '<S-F16>',
    b'\xfd\x16': '<S-F17>',
    b'\xfd\x17': '<S-F18>',
    b'\xfd\x18': '<S-F19>',
    b'\xfd\x19': '<S-F20>',
    b'\xfd\x1a': '<S-F21>',
    b'\xfd\x1b': '<S-F22>',
    b'\xfd\x1c': '<S-F23>',
    b'\xfd\x1d': '<S-F24>',
    b'\xfd\x1e': '<S-F25>',
    b'\xfd\x1f': '<S-F26>',
    b'\xfd\x20': '<S-F27>',
    b'\xfd\x21': '<S-F28>',
    b'\xfd\x22': '<S-F29>',
    b'\xfd\x23': '<S-F30>',
    b'\xfd\x24': '<S-F31>',
    b'\xfd\x25': '<S-F32>',
    b'\xfd\x26': '<S-F33>',
    b'\xfd\x27': '<S-F34>',
    b'\xfd\x28': '<S-F35>',
    b'\xfd\x29': '<S-F36>',
    b'\xfd\x2a': '<S-F37>',
    b'\xfd\x2b': '<Mouse>',
    b'\xfd\x2c': '<LeftMouse>',
    b'\xfd\x2d': '<LeftDrag>',
    b'\xfd\x2e': '<LeftRelease>',
    b'\xfd\x2f': '<MiddleMouse>',
    b'\xfd\x30': '<MiddleDrag>',
    b'\xfd\x31': '<MiddleRelease>',
    b'\xfd\x32': '<RightMouse>',
    b'\xfd\x33': '<RightDrag>',
    b'\xfd\x34': '<RightRelease>',

    b'\xfd\x4b': '<ScrollWheelUp>',
    b'\xfd\x4c': '<ScrollWheelDown>',
    b'\xfd\x4d': '<ScrollWheelRight>',
    b'\xfd\x4e': '<ScrollWheelLeft>',
    b'\xfd\x4f': '<kInsert>',
    b'\xfd\x50': '<kDel>',
    b'\xfd\x55': '<C-Left>',
    b'\xfd\x56': '<C-Right>',
    b'\xfd\x57': '<C-Home>',
    b'\xfd\x58': '<C-End>',
})

_KEYCODE_LOOKUP = {v: k for k, v in _KEYCODE_REPR_LOOKUP.items()}
_KEYCODE_REPR_NORMALIZED = {k.lower(): k for k in _KEYCODE_LOOKUP}


def get_keycode_repr(keycode):
    if keycode in _KEYCODE_REPR_LOOKUP:
        key = _KEYCODE_REPR_LOOKUP[keycode]
    else:
        # Show unknown keycodes as hex codes surrounded by brackets.
        key = ''.join('\\x{:02x}'.format(kc) for kc in keycode)
        key = '[' + key + ']'
    return key


def normalize_keycode_repr(keycode_repr):
    if not (keycode_repr.startswith('<') and keycode_repr.endswith('>')):
        return keycode_repr
    return _KEYCODE_REPR_NORMALIZED[keycode_repr.lower()]


def get_keycode(keycode_repr):
    return _KEYCODE_LOOKUP[keycode_repr]


# A naive approach for a key sequence that will save buffer content and quit
# regardless of the current state.
# It's certainly not robust, as edge cases can fail it,
# but for practical vimgolf inputs, failures should be rare enough.
_REPLAY_QUIT_KEYCODE_REPRS = '<Esc><Esc><Esc>:<C-U>wqall<CR>'
REPLAY_QUIT_RAW_KEYS = to_raw_keys([
    get_keycode(kr) for kr in
    parse_raw_keycode_reprs(_REPLAY_QUIT_KEYCODE_REPRS)
])


class Keys:
    def __init__(self, raw_keys, keycodes, keycode_reprs):
        # raw keypress representation saved by vim's -w
        self.raw_keys = raw_keys
        # list of parsed keycode byte strings
        self.keycodes = keycodes
        # list of human-readable key strings
        self.keycode_reprs = keycode_reprs

    @property
    def score(self):
        return len(self.keycodes)

    @classmethod
    def from_raw_keys(cls, raw_keys):
        keycodes = parse_keycodes(raw_keys)
        keycodes = [keycode for keycode in keycodes if keycode not in IGNORED_KEYSTROKES]
        keycode_reprs = [get_keycode_repr(keycode) for keycode in keycodes]
        return Keys(
            raw_keys=raw_keys,
            keycodes=keycodes,
            keycode_reprs=keycode_reprs,
        )

    @classmethod
    def from_keycode_reprs(cls, keycode_reprs):
        keycode_reprs = [normalize_keycode_repr(kr) for kr in keycode_reprs]
        keycodes = [get_keycode(keycode_repr) for keycode_repr in keycode_reprs]
        raw_keys = to_raw_keys(keycodes)
        return Keys(
            raw_keys=raw_keys,
            keycodes=keycodes,
            keycode_reprs=keycode_reprs
        )

    @classmethod
    def from_raw_keycode_reprs(cls, raw_keycode_reprs, literal_lt, literal_gt):
        return cls.from_keycode_reprs(parse_raw_keycode_reprs(
            raw_keycode_reprs=raw_keycode_reprs,
            literal_lt=literal_lt,
            literal_gt=literal_gt,
        ))
