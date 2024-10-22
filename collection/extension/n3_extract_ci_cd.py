import datetime
import os
import re
import pandas as pd
from pydriller import Git, Repository
import json

import const

# Jun 1, 2019
collection_period_start_date = datetime.datetime(2019, 6, 1, 0, 0, 0)
# May 31, 2021
collection_period_end_date = datetime.datetime(2021, 5, 31, 23, 59, 59)

# starts
# mocha: 22.2, jest: 42.9, jasmine: 15.6, karma: 11.9 (dep), puppeteer: 84.9 (not quite testing fw)
# nightwatch: 11.5, cypress: 45.2, playwright: 56.1, selenium-webdriver: 28.1
testing_frameworks = [
    'mocha', 'jest', 'jasmine', 'karma', 'puppeteer', 'nightwatch', 'cypress', 'playwright', 'selenium-webdriver'
]
ci_cd_tools = [
    'github_actions', 'circleci', 'travisci', 'appveyor', 'jenkins', 'gitlab', 'azure'
]


def create_df(d: list):
    columns = [
                  'repository', 'start_commits_total', 'end_commits_total', 'total_authors', 'package.json'
              ] + testing_frameworks + ci_cd_tools

    return pd.DataFrame(d, columns=columns)


def git_checkout(rdir: str, commit_hash: str) -> Git:
    gr = Git(rdir)
    gr.checkout(commit_hash)

    return gr


def get_repo_data(rdir: str, commit_hash: str):
    gr = git_checkout(rdir, commit_hash)

    commits = []
    for cm in gr.get_list_commits():
        commits.append(cm)

    return commits, gr.files()


def load_json_file(filepath: str):
    with open(filepath) as jf:
        return json.load(jf)


def load_json_file_from_commit(rdir: str, filepath: str, commit_hash: str):
    git_checkout(rdir, commit_hash)

    return load_json_file(filepath)


def is_file_modified(file: str, repo: str, rdir: str, before_hash: str, min_modifications: int):
    rname = repo.split('/')[1]
    full_dir = rdir + '/' + rname
    git_checkout(full_dir, before_hash)

    count = 0
    for commit in Repository('https://github.com/' + repo,
                             since=collection_period_start_date,
                             to=collection_period_end_date,
                             clone_repo_to=rdir,
                             filepath=file,
                             order=None,
                             ).traverse_commits():
        for m in commit.modified_files:
            if m.new_path is None or file != full_dir + '/' + m.new_path:
                continue

            if m.change_type.name == 'MODIFY':
                count += 1
                break
        if count >= min_modifications:
            return True
    return False


def count_file_modifications(file: str, repo: str, rdir: str, before_hash: str):
    rname = repo.split('/')[1]
    full_dir = rdir + '/' + rname
    git_checkout(full_dir, before_hash)

    count = 0
    for commit in Repository('https://github.com/' + repo,
                             since=collection_period_start_date,
                             to=collection_period_end_date,
                             clone_repo_to=rdir,
                             filepath=file,
                             order=None,
                             ).traverse_commits():
        for m in commit.modified_files:
            if m.new_path is None or file != full_dir + '/' + m.new_path:
                continue

            if m.change_type.name == 'MODIFY':
                count += 1
                break
    return count


df = pd.read_csv(const.DIR_EXTENSION + '/data/commits.csv')
data = create_df([])

for index, row in df.iterrows():
    parts = row['repository'].split('/')

    repo_base_dir = os.path.join(const.DIR_ROOT, 'collection/extension/data/repo', parts[0])
    repo_dir = os.path.join(repo_base_dir, parts[1])

    start_commits, start_commit_files = get_repo_data(repo_dir, row['start_commit_hash'])
    end_commits, end_commit_files = get_repo_data(repo_dir, row['end_commit_hash'])
    authors = set()
    for c in end_commits:
        authors.add(c.author.name)

    print('Repo #%d %s\n[start] commits: %d, files: %d\n[end] commits: %d, files: %d' % (
        index + 1, row['repository'],
        len(start_commits), len(start_commit_files),
        len(end_commits), len(end_commit_files)
    ))

    record = [
        row['repository'],
        len(start_commits),
        len(end_commits),
        len(authors),
    ]

    # extract testing
    dep_file_path = repo_dir + '/package.json'
    dep_file_found = True
    testing_fw_found = set()

    if dep_file_path not in end_commit_files or dep_file_path not in start_commit_files:
        print('No dependency file!')
        dep_file_found = False
    else:
        # repository is at end commit right now
        dep_file_json_end = load_json_file(dep_file_path)
        dep_file_json_start = load_json_file_from_commit(repo_dir, dep_file_path, row['start_commit_hash'])
        for dep_field in ['dependencies', 'devDependencies']:
            if dep_field in dep_file_json_end and dep_field in dep_file_json_start:
                for tfw in testing_frameworks:
                    if tfw in dep_file_json_end[dep_field] and tfw in dep_file_json_start[dep_field]:
                        testing_fw_found.add(tfw)

    record.append(1 if dep_file_found else 0)

    for fw in testing_frameworks:
        record.append(1 if fw in testing_fw_found else 0)

    # extract ci/cd
    ci_cd_patterns = {
        'github_actions': ['.github/workflows/(.)*.ya?ml'],
        'circleci': ['.circleci/(.)*.ya?ml', 'circle.ya?ml'],
        'travisci': ['.travis.ya?ml'],
        'appveyor': ['appveyor.ya?ml'],
        'jenkins': ['(.)*/?Jenkinsfile'],
        'gitlab': ['.gitlab-ci.ya?ml'],
        'azure': ['azure-pipelines.ya?ml'],
    }

    ci_cd_found = {}
    for t in ci_cd_tools:
        ci_cd_found[t] = -1

    for tool in ci_cd_patterns:
        for cf in start_commit_files:
            for pattern in ci_cd_patterns[tool]:
                regex = repo_dir + '/' + pattern
                matched = re.search(regex, cf, re.IGNORECASE)
                if (matched is not None) and (cf in end_commit_files):
                    count = count_file_modifications(cf, row['repository'], repo_base_dir, row['end_commit_hash'])
                    print('CI/CD file found [%d]: %s' % (count, cf.replace(repo_dir, '')))
                    ci_cd_found[tool] = count
                    break

    for cc in ci_cd_found:
        record.append(ci_cd_found[cc])

    tmp_df = create_df([record])
    data = pd.concat([data, tmp_df])
    data.to_csv('data/repositories_attributes.csv')

# azure config file:
# https://github.com/MicrosoftDocs/azure-devops-docs/issues/5258
