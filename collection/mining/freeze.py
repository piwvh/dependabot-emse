import csv
import shutil
import sys
import glob
import pandas as pd
import subprocess
import itertools
from pathlib import Path
from tqdm import tqdm
from ast import literal_eval
sys.path.append('..')
from finder import *  # noqa: E402
from attributes.continuous_integration import main as ci_main  # noqa: E402


def load_update_commits():
    upd_commits = pd.read_csv(PATH_REPOSITORIES_DATA['security_updates_commits'], index_col=False)
    upd_commits['files'] = upd_commits['files'].apply(literal_eval)
    return upd_commits


def load_update_vulnerabilities():
    upd_vulns = pd.read_csv(PATH_REPOSITORIES_DATA['pr_vulnerabilities'], index_col=False)
    upd_vulns['vulnerabilities'] = upd_vulns['vulnerabilities'].apply(literal_eval)
    return upd_vulns


def associate_commits_with_vulns():
    upd_commits = load_update_commits()
    upd_vulns = load_update_vulnerabilities()
    merged = upd_commits.merge(upd_vulns, how='inner', on=['repository', 'number', 'url', 'state'])
    return merged


def checkout(path, sha):
    command = 'git reset --hard {0}'.format(sha)
    if 'DEBUG' in os.environ:
        print(command)
    process = subprocess.Popen(
        command, cwd=path, shell=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    process.wait()
    if process.returncode != 0:
        print('Failed to execute {0}'.format(command))
        return False
    else:
        return True


if __name__ == '__main__':
    projects = pd.read_csv(PATH_REPOSITORIES_DATA['dependabot_filtered_repos'], index_col=False)['repository'].tolist()
    try:
        projects.remove('hull/hull-connectors')
    except ValueError as err:
        print(err)
    df_updates = associate_commits_with_vulns()
    if not os.path.exists(DIR_FREEZE):
        os.makedirs(DIR_CLONED, exist_ok=True)
    with open(PATH_REPOSITORIES_DATA['commit_ci'], 'w') as ci_file:
        writer = csv.writer(ci_file)
        writer.writerow(['repository', 'oid', 'ci', 'actions'])
        for project in tqdm(projects):
            slug = project.split('/')
            owner = slug[0]
            name = slug[1]
            files = df_updates[df_updates['repository'] == project]['files'].to_list()
            dependency_files = []
            for file in list(itertools.chain.from_iterable(files)):
                if file.split('/')[-1] in ['package.json', 'package-lock.json', 'yarn.lock']:
                    dependency_files.append(file)
            dependency_files = list(set(dependency_files))
            dependency_dirs = []
            for file in dependency_files:
                if len(file.split('/')) > 1:
                    dependency_dirs.append(os.path.dirname(file))
            dependency_dirs = list(set(dependency_dirs))
            dependency_files = []
            for dependency_dir in dependency_dirs:
                dependency_files.append(os.path.join(dependency_dir, 'package.json'))
                dependency_files.append(os.path.join(dependency_dir, 'package-lock.json'))
                dependency_files.append(os.path.join(dependency_dir, 'yarn.lock'))
                dependency_files.append(os.path.join(dependency_dir, 'npm-shrinkwrap.json'))
            dependency_files.append('package.json')
            dependency_files.append('package-lock.json')
            dependency_files.append('yarn.lock')
            dependency_files.append('npm-shrinkwrap.json')
            with open(os.path.join(DIR_NETWORK, owner + '@' + name + '.txt'), 'r') as network_file:
                    network_graph = network_file.readlines()
            network_graph = [x.strip() for x in network_graph]
            commits = []
            for line in network_graph:
                if line[0] == '*':
                    sha = line.replace('*', '').replace('|', '').replace('/', '').replace('\\', '').replace(' ', '').split(',')[0]
                    commits.append(sha)
            for index, row in df_updates[df_updates['repository'] == project].iterrows():
                commits.append(row['parent_oid'])
                if row['state'] == 'MERGED':
                    commits.append(row['merged_oid'])
            commits = list(set(commits))
            path_repository_clone = os.path.join(DIR_CLONED, owner, name)
            for commit in commits:
                if checkout(path_repository_clone, commit):
                    path_repository_commit = os.path.join(DIR_FREEZE, owner, name, commit)
                    if not os.path.exists(os.path.join(path_repository_commit)):
                        os.makedirs(os.path.join(path_repository_commit), exist_ok=True)
                    for file in dependency_files:
                        file_path_cloned = os.path.join(path_repository_clone, file)
                        file_path_frozen = os.path.join(path_repository_commit, file)
                        if os.path.exists(file_path_cloned):
                            if not os.path.exists(os.path.dirname(file_path_frozen)):
                                os.makedirs(os.path.join(os.path.dirname(file_path_frozen)), exist_ok=True)
                            shutil.copy(file_path_cloned, file_path_frozen)
                    md_files = []
                    for path in Path(path_repository_clone).rglob('package.json'):
                        file_path_cloned = str(path)
                        file_path_frozen = str(path).replace(path_repository_clone, path_repository_commit)
                        if not os.path.exists(file_path_frozen):
                            if not os.path.exists(os.path.dirname(file_path_frozen)):
                                os.makedirs(os.path.join(os.path.dirname(file_path_frozen)), exist_ok=True)
                            os.replace(file_path_cloned, file_path_frozen)
                    for file_instance in os.listdir(path_repository_clone):
                        if file_instance.endswith(".md"):
                            md_files.append(file_instance)
                    for md_file in md_files:
                        if md_file.lower() == 'readme.md':
                            shutil.copy(os.path.join(path_repository_clone, md_file), os.path.join(path_repository_commit, 'README.md'))
                    has_ci = ci_main.run(None, path_repository_clone, None)
                    has_actions = os.path.exists(os.path.join(path_repository_clone, '.github', 'workflows'))
                    writer.writerow([project, commit, has_ci, has_actions])
            try:
                shutil.rmtree(path_repository_clone)
            except OSError as e:
                print("Error: %s : %s" % (path_repository_clone, e.strerror))


