"""Git implementation of _version.py."""
import errno
import os
import re
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple
import functools


def get_keywords() ->Dict[str, str]:
    """Get the keywords needed to look up the version information."""
    pass


class VersioneerConfig:
    """Container for Versioneer configuration parameters."""
    VCS: str
    style: str
    tag_prefix: str
    parentdir_prefix: str
    versionfile_source: str
    verbose: bool


def get_config() ->VersioneerConfig:
    """Create, populate and return the VersioneerConfig() object."""
    pass


class NotThisMethod(Exception):
    """Exception raised if a method is not valid for the current scenario."""


LONG_VERSION_PY: Dict[str, str] = {}
HANDLERS: Dict[str, Dict[str, Callable]] = {}


def register_vcs_handler(vcs: str, method: str) ->Callable:
    """Create decorator to mark a method as the handler of a VCS."""
    pass


def run_command(commands: List[str], args: List[str], cwd: Optional[str]=
    None, verbose: bool=False, hide_stderr: bool=False, env: Optional[Dict[
    str, str]]=None) ->Tuple[Optional[str], Optional[int]]:
    """Call the given command(s)."""
    pass


def versions_from_parentdir(parentdir_prefix: str, root: str, verbose: bool
    ) ->Dict[str, Any]:
    """Try to determine the version from the parent directory name.

    Source tarballs conventionally unpack into a directory that includes both
    the project name and a version string. We will also support searching up
    two directory levels for an appropriately named parent directory
    """
    pass


@register_vcs_handler('git', 'get_keywords')
def git_get_keywords(versionfile_abs: str) ->Dict[str, str]:
    """Extract version information from the given file."""
    pass


@register_vcs_handler('git', 'keywords')
def git_versions_from_keywords(keywords: Dict[str, str], tag_prefix: str,
    verbose: bool) ->Dict[str, Any]:
    """Get version information from git keywords."""
    pass


@register_vcs_handler('git', 'pieces_from_vcs')
def git_pieces_from_vcs(tag_prefix: str, root: str, verbose: bool, runner:
    Callable=run_command) ->Dict[str, Any]:
    """Get version from 'git describe' in the root of the source tree.

    This only gets called if the git-archive 'subst' keywords were *not*
    expanded, and _version.py hasn't already been rewritten with a short
    version string, meaning we're inside a checked out source tree.
    """
    pass


def plus_or_dot(pieces: Dict[str, Any]) ->str:
    """Return a + if we don't already have one, else return a ."""
    pass


def render_pep440(pieces: Dict[str, Any]) ->str:
    """Build up version string, with post-release "local version identifier".

    Our goal: TAG[+DISTANCE.gHEX[.dirty]] . Note that if you
    get a tagged build and then dirty it, you'll get TAG+0.gHEX.dirty

    Exceptions:
    1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty]
    """
    pass


def render_pep440_branch(pieces: Dict[str, Any]) ->str:
    """TAG[[.dev0]+DISTANCE.gHEX[.dirty]] .

    The ".dev0" means not master branch. Note that .dev0 sorts backwards
    (a feature branch will appear "older" than the master branch).

    Exceptions:
    1: no tags. 0[.dev0]+untagged.DISTANCE.gHEX[.dirty]
    """
    pass


def pep440_split_post(ver: str) ->Tuple[str, Optional[int]]:
    """Split pep440 version string at the post-release segment.

    Returns the release segments before the post-release and the
    post-release version number (or -1 if no post-release segment is present).
    """
    pass


def render_pep440_pre(pieces: Dict[str, Any]) ->str:
    """TAG[.postN.devDISTANCE] -- No -dirty.

    Exceptions:
    1: no tags. 0.post0.devDISTANCE
    """
    pass


def render_pep440_post(pieces: Dict[str, Any]) ->str:
    """TAG[.postDISTANCE[.dev0]+gHEX] .

    The ".dev0" means dirty. Note that .dev0 sorts backwards
    (a dirty tree will appear "older" than the corresponding clean one),
    but you shouldn't be releasing software with -dirty anyways.

    Exceptions:
    1: no tags. 0.postDISTANCE[.dev0]
    """
    pass


def render_pep440_post_branch(pieces: Dict[str, Any]) ->str:
    """TAG[.postDISTANCE[.dev0]+gHEX[.dirty]] .

    The ".dev0" means not master branch.

    Exceptions:
    1: no tags. 0.postDISTANCE[.dev0]+gHEX[.dirty]
    """
    pass


def render_pep440_old(pieces: Dict[str, Any]) ->str:
    """TAG[.postDISTANCE[.dev0]] .

    The ".dev0" means dirty.

    Exceptions:
    1: no tags. 0.postDISTANCE[.dev0]
    """
    pass


def render_git_describe(pieces: Dict[str, Any]) ->str:
    """TAG[-DISTANCE-gHEX][-dirty].

    Like 'git describe --tags --dirty --always'.

    Exceptions:
    1: no tags. HEX[-dirty]  (note: no 'g' prefix)
    """
    pass


def render_git_describe_long(pieces: Dict[str, Any]) ->str:
    """TAG-DISTANCE-gHEX[-dirty].

    Like 'git describe --tags --dirty --always -long'.
    The distance/hash is unconditional.

    Exceptions:
    1: no tags. HEX[-dirty]  (note: no 'g' prefix)
    """
    pass


def render(pieces: Dict[str, Any], style: str) ->Dict[str, Any]:
    """Render the given version pieces into the requested style."""
    pass


def get_versions() ->Dict[str, Any]:
    """Get version information or return default if unable to do so."""
    pass
