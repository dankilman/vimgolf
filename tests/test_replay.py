import os
import tempfile

from vimgolf import play


def test():
    with tempfile.TemporaryDirectory() as d:
        infile = os.path.join(d, 'infile')
        logfile = os.path.join(d, 'logfile')
        with open(infile, 'w') as f:
            f.write('input content')
        with open(logfile, 'w') as f:
            f.write('ihello')
        play.replay_single(infile, logfile)
