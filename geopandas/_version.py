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
    # these strings will be replaced by git during git-archive.
    # setup.py/versioneer.py will grep for the variable names, so they must
    # each be defined on a line of their own. _version.py will just call
    # get_keywords().
    git_refnames = "$Format:%d$"
    git_full = "$Format:%H$"
    git_date = "$Format:%ci$"
    keywords = {"refnames": git_refnames, "full": git_full, "date": git_date}
    return keywords


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
    # these strings are filled in when 'setup.py versioneer' creates _version.py
    cfg = VersioneerConfig()
    cfg.VCS = "git"
    cfg.style = "pep440"
    cfg.tag_prefix = "v"
    cfg.parentdir_prefix = "geopandas-"
    cfg.versionfile_source = "geopandas/_version.py"
    cfg.verbose = False
    return cfg


class NotThisMethod(Exception):
    """Exception raised if a method is not valid for the current scenario."""


LONG_VERSION_PY: Dict[str, str] = {}
HANDLERS: Dict[str, Dict[str, Callable]] = {}


def register_vcs_handler(vcs: str, method: str) ->Callable:
    """Create decorator to mark a method as the handler of a VCS."""
    def decorate(f):
        """Store f in HANDLERS[vcs][method]."""
        if vcs not in HANDLERS:
            HANDLERS[vcs] = {}
        HANDLERS[vcs][method] = f
        return f
    return decorate


def run_command(commands: List[str], args: List[str], cwd: Optional[str]=
    None, verbose: bool=False, hide_stderr: bool=False, env: Optional[Dict[
    str, str]]=None) ->Tuple[Optional[str], Optional[int]]:
    """Call the given command(s)."""
    assert isinstance(commands, list)
    p = None
    for c in commands:
        try:
            dispcmd = str([c] + args)
            # remember shell=False, so use git.cmd on windows, not just git
            p = subprocess.Popen([c] + args, cwd=cwd, env=env,
                                 stdout=subprocess.PIPE,
                                 stderr=(subprocess.PIPE if hide_stderr
                                         else None))
            break
        except EnvironmentError:
            e = sys.exc_info()[1]
            if e.errno == errno.ENOENT:
                continue
            if verbose:
                print("unable to run %s" % dispcmd)
                print(e)
            return None, None
    else:
        if verbose:
            print("unable to find command, tried %s" % (commands,))
        return None, None
    stdout = p.communicate()[0].strip().decode()
    if p.returncode != 0:
        if verbose:
            print("unable to run %s (error)" % dispcmd)
            print("stdout was %s" % stdout)
        return None, p.returncode
    return stdout, p.returncode


def versions_from_parentdir(parentdir_prefix: str, root: str, verbose: bool
    ) ->Dict[str, Any]:
    """Try to determine the version from the parent directory name.

    Source tarballs conventionally unpack into a directory that includes both
    the project name and a version string. We will also support searching up
    two directory levels for an appropriately named parent directory
    """
    rootdirs = []

    for i in range(3):
        dirname = os.path.basename(root)
        if dirname.startswith(parentdir_prefix):
            return {"version": dirname[len(parentdir_prefix):],
                    "full-revisionid": None,
                    "dirty": False, "error": None, "date": None}
        else:
            rootdirs.append(root)
            root = os.path.dirname(root)

    if verbose:
        print("Tried directories %s but none started with prefix %s" %
              (str(rootdirs), parentdir_prefix))
    raise NotThisMethod("rootdir doesn't start with parentdir_prefix")


@register_vcs_handler('git', 'get_keywords')
def git_get_keywords(versionfile_abs: str) ->Dict[str, str]:
    """Extract version information from the given file."""
    # the code embedded in _version.py can just fetch the value of these
    # keywords. When used from setup.py, we don't want to import _version.py,
    # so we do it with a regexp instead. This function is not used from
    # _version.py.
    keywords = {}
    try:
        f = open(versionfile_abs, "r")
        for line in f.readlines():
            if line.strip().startswith("git_refnames ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["refnames"] = mo.group(1)
            if line.strip().startswith("git_full ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["full"] = mo.group(1)
            if line.strip().startswith("git_date ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["date"] = mo.group(1)
        f.close()
    except EnvironmentError:
        pass
    return keywords


@register_vcs_handler('git', 'keywords')
def git_versions_from_keywords(keywords: Dict[str, str], tag_prefix: str,
    verbose: bool) ->Dict[str, Any]:
    """Get version information from git keywords."""
    if not keywords:
        raise NotThisMethod("no keywords at all, weird")
    date = keywords.get("date")
    if date is not None:
        # git-2.2.0 added "%cI", which expands to an ISO-8601 format
        date = date.strip().replace(" ", "T", 1).replace(" ", "", 1)
    refnames = keywords["refnames"].strip()
    if refnames.startswith("$Format"):
        if verbose:
            print("keywords are unexpanded, not using")
        raise NotThisMethod("unexpanded keywords, not a git-archive tarball")
    refs = set([r.strip() for r in refnames.strip("()").split(",")])
    # starting in git-1.8.3, tags are listed as "tag: foo-1.0" instead of
    # just "foo-1.0". If we see a "tag: " prefix, prefer those.
    TAG = "tag: "
    tags = set([r[len(TAG):] for r in refs if r.startswith(TAG)])
    if not tags:
        # Either we're using git < 1.8.3, or there really are no tags. We use
        # a heuristic: assume all version tags have a digit. The old git %d
        # expansion behaves like git log --decorate=short and strips out the
        # refs/heads/ and refs/tags/ prefixes that would let us distinguish
        # between branches and tags. By ignoring refnames without digits, we
        # filter out many common branch names like "release" and
        # "stabilization", as well as "HEAD" and "master".
        tags = set([r for r in refs if re.search(r'\d', r)])
        if verbose:
            print("discarding '%s', no digits" % ",".join(refs - tags))
    if verbose:
        print("likely tags: %s" % ",".join(sorted(tags)))
    for ref in sorted(tags):
        # sorting will prefer e.g. "2.0" over "2.0rc1"
        if ref.startswith(tag_prefix):
            r = ref[len(tag_prefix):]
            if verbose:
                print("picking %s" % r)
            return {"version": r,
                    "full-revisionid": keywords["full"].strip(),
                    "dirty": False, "error": None,
                    "date": date}
    # no suitable tags, so version is "0+unknown", but full hex is still there
    if verbose:
        print("no suitable tags, using unknown + full revision id")
    return {"version": "0+unknown",
            "full-revisionid": keywords["full"].strip(),
            "dirty": False, "error": "no suitable tags", "date": None}


@register_vcs_handler('git', 'pieces_from_vcs')
def git_pieces_from_vcs(tag_prefix: str, root: str, verbose: bool, runner:
    Callable=run_command) ->Dict[str, Any]:
    """Get version from 'git describe' in the root of the source tree.

    This only gets called if the git-archive 'subst' keywords were *not*
    expanded, and _version.py hasn't already been rewritten with a short
    version string, meaning we're inside a checked out source tree.
    """
    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]

    out, rc = runner(GITS, ["rev-parse", "--git-dir"], cwd=root,
                     hide_stderr=True)
    if rc != 0:
        if verbose:
            print("Directory %s not under git control" % root)
        raise NotThisMethod("'git rev-parse --git-dir' returned error")

    # if there is a tag matching tag_prefix, this yields TAG-NUM-gHEX[-dirty]
    # if there isn't one, this yields HEX[-dirty] (no NUM)
    describe_out, rc = runner(GITS, ["describe", "--tags", "--dirty",
                                     "--always", "--long",
                                     "--match", "%s*" % tag_prefix],
                              cwd=root)
    # --long was added in git-1.5.5
    if describe_out is None:
        raise NotThisMethod("'git describe' failed")
    describe_out = describe_out.strip()
    full_out, rc = runner(GITS, ["rev-parse", "HEAD"], cwd=root)
    if full_out is None:
        raise NotThisMethod("'git rev-parse' failed")
    full_out = full_out.strip()

    pieces = {}
    pieces["long"] = full_out
    pieces["short"] = full_out[:7]  # maybe improved later
    pieces["error"] = None

    # parse describe_out. It will be like TAG-NUM-gHEX[-dirty] or HEX[-dirty]
    # TAG might have hyphens.
    git_describe = describe_out

    # look for -dirty suffix
    dirty = git_describe.endswith("-dirty")
    pieces["dirty"] = dirty
    if dirty:
        git_describe = git_describe[:git_describe.rindex("-dirty")]

    # now we have TAG-NUM-gHEX or HEX

    if "-" in git_describe:
        # TAG-NUM-gHEX
        mo = re.search(r'^(.+)-(\d+)-g([0-9a-f]+)$', git_describe)
        if not mo:
            # unparseable. Maybe git-describe is misbehaving?
            pieces["error"] = ("unable to parse git-describe output: '%s'"
                               % describe_out)
            return pieces

        # tag
        full_tag = mo.group(1)
        if not full_tag.startswith(tag_prefix):
            if verbose:
                fmt = "tag '%s' doesn't start with prefix '%s'"
                print(fmt % (full_tag, tag_prefix))
            pieces["error"] = ("tag '%s' doesn't start with prefix '%s'"
                               % (full_tag, tag_prefix))
            return pieces
        pieces["closest-tag"] = full_tag[len(tag_prefix):]

        # distance: number of commits since tag
        pieces["distance"] = int(mo.group(2))

        # commit: short hex revision ID
        pieces["short"] = mo.group(3)

    else:
        # HEX: no tags
        pieces["closest-tag"] = None
        count_out, rc = runner(GITS, ["rev-list", "HEAD", "--count"],
                               cwd=root)
        pieces["distance"] = int(count_out)  # total number of commits

    # commit date: see ISO-8601 comment in git_versions_from_keywords()
    date = runner(GITS, ["show", "-s", "--format=%ci", "HEAD"],
                  cwd=root)[0].strip()
    pieces["date"] = date.strip().replace(" ", "T", 1).replace(" ", "", 1)

    return pieces


def plus_or_dot(pieces: Dict[str, Any]) ->str:
    """Return a + if we don't already have one, else return a ."""
    if "+" in pieces.get("closest-tag", ""):
        return "."
    return "+"


def render_pep440(pieces: Dict[str, Any]) ->str:
    """Build up version string, with post-release "local version identifier".

    Our goal: TAG[+DISTANCE.gHEX[.dirty]] . Note that if you
    get a tagged build and then dirty it, you'll get TAG+0.gHEX.dirty

    Exceptions:
    1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty]
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"] or pieces["dirty"]:
            rendered += plus_or_dot(pieces)
            rendered += "%d.g%s" % (pieces["distance"], pieces["short"])
            if pieces["dirty"]:
                rendered += ".dirty"
    else:
        # exception #1
        rendered = "0+untagged.%d.g%s" % (pieces["distance"],
                                          pieces["short"])
        if pieces["dirty"]:
            rendered += ".dirty"
    return rendered


def render_pep440_branch(pieces: Dict[str, Any]) ->str:
    """TAG[[.dev0]+DISTANCE.gHEX[.dirty]] .

    The ".dev0" means not master branch. Note that .dev0 sorts backwards
    (a feature branch will appear "older" than the master branch).

    Exceptions:
    1: no tags. 0[.dev0]+untagged.DISTANCE.gHEX[.dirty]
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"] or pieces["dirty"]:
            rendered += ".dev0"
            rendered += plus_or_dot(pieces)
            rendered += "%d.g%s" % (pieces["distance"], pieces["short"])
            if pieces["dirty"]:
                rendered += ".dirty"
    else:
        # exception #1
        rendered = "0"
        if pieces["distance"] or pieces["dirty"]:
            rendered += ".dev0"
            rendered += "+untagged.%d.g%s" % (pieces["distance"],
                                              pieces["short"])
            if pieces["dirty"]:
                rendered += ".dirty"
    return rendered


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
