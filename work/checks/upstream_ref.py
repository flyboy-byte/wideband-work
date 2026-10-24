"""The git ref holding upstream's files (mck1117/wideband master). A working copy has a local `master`; a fresh clone of
the fork has only `origin/master` (equal to upstream's, kept so). $WB_UPSTREAM_REF overrides."""
import os, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def upstream_ref():
    for ref in [os.environ.get('WB_UPSTREAM_REF', ''), 'master', 'origin/master', 'upstream/master']:
        if ref and subprocess.run(['git', '-C', REPO, 'rev-parse', '--verify', '-q', ref + '^{commit}'],
                                  capture_output=True).returncode == 0:
            return ref
    raise SystemExit('no upstream ref: fetch master (git fetch origin master) or set WB_UPSTREAM_REF')
