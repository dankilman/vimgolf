vimgolf (fork)
==============

This project contains a [vimgolf](https://www.vimgolf.com/) client written in Python.

The user interface is similar to the [official vimgolf client](https://github.com/igrigorik/vimgolf),
with a few additions inspired by [vimgolf-finder](https://github.com/kciter/vimgolf-finder).

This forked version of [dstein64/vimgolf](https://github.com/dstein64/vimgolf) contains the following
additional features:

- Use locally cached version of challenge when running `vimgolf put`, if one exists.
- Keep local version of challenges and track all entered solutions in 
  `$XDG_DATA_HOME/vimgolf/challenges`.
- Update `vimgolf ls` to show output in a table.
- Update `vimgolf ls` to show whether a challenge was already submitted and 
  what is the best score achieved for it so far (only applies to challenges submitted through
  this client).
- `vimgolf show` will display additional information about previously entered solutions 
  to the given challenge.
  Specifically, for each entered solution, it will display the key sequence entered, whether
  it was correct, whether it was submitted to vimgolf.com, what score did it achieve and when
  was it entered.
- new `vimgolf inspect` command to inspect provided solutions, step by step.
  (use `<C-J>` and `<C-K>` in the inspect window to move between steps)

Installation
------------

#### Requirements

- Python 3.5 or greater

#### Install
Currently, the fork is not published to pypi, so you need to clone it first.

```sh
$ git clone https://github.com/dankilman/vimgolf.git
$ cd vimgolf
$ pip3 install .
```

Usage
-----

#### Launch

```sh
$ vimgolf
```

#### Commands

```text
Usage: vimgolf [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  config   configure your vimgolf.com credentials
  inspect  inspect behaviour of a key sequence applied to challenge
  local    launch local challenge
  ls       list vimgolf.com challenges (spec syntax: [PAGE][:LIMIT])
  put      launch vimgolf.com challenge
  show     show vimgolf.com challenge
  version  display the version number
```

`CHALLENGE_ID` can be a 24-character ID from vimgolf.com, or a plus-prefixed ID corresponding to the
last invocation of `vimgolf ls`. For example, a `CHALLENGE_ID` of `+6` would correspond to the
sixth challenge presented in the most recent call to `vimgolf ls`.

Demo
----

<p align="center">
  <img width="850" src="https://github.com/dankilman/vimgolf/blob/master/screencast.svg">
</p>

License
-------

The source code has an [MIT License](https://en.wikipedia.org/wiki/MIT_License).

See [LICENSE](https://github.com/dankilman/vimgolf/blob/master/LICENSE).
