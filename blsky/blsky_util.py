import subprocess


def git_commit_tle(commit_path):
    """
    Not used (see beast_tle_update.sh instead)
    """
    cmd = f"git -C {commit_path} commit -am 'updating csv to repo.'"
    subprocess.call(cmd, shell=True)
    cmd = f"git -C {commit_path} push origin main"
    subprocess.call(cmd, shell=True)


def find_tle_commit(this_date=None):
    tcommit = {}
    for line in subprocess.check_output(['git', 'log']).decode().split('\n'):
        if line.startswith('commit'):
            this_commit = line.split()[1]
            tcommit[this_commit] = {}
        elif line.startswith('    '):
            tcommit[this_commit]['msg'] = line.strip()
        elif len(line):
            key = line.split(':')[0]
            msg = ':'.join(line.split(':')[1:])
            tcommit[this_commit][key] = msg.strip()
    return tcommit
