import datetime
import os
import pandas as pd

from pydriller import Repository

import const


def create_df(d: list):
    return pd.DataFrame(d, columns=[
        'repository', 'start_commit_hash', 'start_commit_date', 'end_commit_hash', 'end_commit_date'
    ])


# Jun 1, 2019
collection_period_start_date = datetime.datetime(2019, 6, 1, 0, 0, 0)
# May 31, 2021
collection_period_end_date = datetime.datetime(2021, 5, 31, 23, 59, 59)

df = pd.read_csv(const.DIR_EXTENSION + '/data/available_repos.csv')

data = create_df([])
counter = 0

# some of the projects:
# 1. do not have the commit we are looking for
# 2. are private

exclude = [
    'applitools/eyes.sdk.javascript1'
]

for index, row in df.iterrows():
    counter += 1
    print('Repo #%d: %s' % (counter, row['repository']))

    if row['repository'] in exclude:
        print('Excluded')
        continue

    parts = row['repository'].split('/')
    repo_dir = os.path.join(const.DIR_ROOT, 'collection/extension/data/repo', parts[0])
    if not os.path.isdir(repo_dir):
        os.mkdir(repo_dir)

    start_commit = None
    for commit in Repository('https://github.com/' + row['repository'],
                             since=collection_period_start_date,
                             clone_repo_to=repo_dir,
                             order=None,
                             ).traverse_commits():
        start_commit = commit
        break

    end_commit = None
    for commit in Repository('https://github.com/' + row['repository'],
                             to=collection_period_end_date,
                             clone_repo_to=repo_dir,
                             order='reverse',
                             ).traverse_commits():
        end_commit = commit
        break

    if start_commit is None or end_commit is None:
        print('! Required commits not found for %s' % row['repository'])
        continue

    tmp_df = create_df([
        [row['repository'], start_commit.hash, str(start_commit.author_date),
         end_commit.hash, str(end_commit.author_date)]
    ])
    data = pd.concat([data, tmp_df])
    data.to_csv(const.DIR_EXTENSION + '/data/commits.csv')

