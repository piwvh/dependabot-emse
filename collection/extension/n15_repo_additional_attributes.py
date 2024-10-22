import datetime
import os

import pandas as pd
from pydriller import Repository

import const
from collection.extension.util.general_util import write_large_csv
from collection.extension.util.git_util import git_checkout

repos = pd.read_csv(const.DIR_EXTENSION + '/data/available_repos.csv')

# # May 31, 2021
collection_period_end_date = datetime.datetime(2021, 5, 31, 23, 59, 59)


def get_repo_size(rdir: str) -> (int, str):
    command = f'git -C {rdir} count-objects -vH'

    output = os.popen(command).read()
    for line in output.split('\n'):
        line_parts = line.split(':')
        if line_parts[0] == 'size-pack':
            size_parts = line_parts[1].strip().split(' ')
            return size_parts[0], size_parts[1]

    return -1, ''


for idx, row in repos.iterrows():
    print('#%d %s' % (idx, row['repository']))

    repo_dir = str(os.path.join(const.DIR_ROOT, 'collection/extension/data/repo', row['repository']))

    try:
        first_commit_date = None
        for commit in Repository(repo_dir).traverse_commits():
            first_commit_date = commit.committer_date
            break

        last_commit = None
        for commit in Repository(repo_dir, to=collection_period_end_date, order='reverse').traverse_commits():
            last_commit = commit
            break
        gr = git_checkout(repo_dir, last_commit.hash)
        size, unit = get_repo_size(repo_dir)
    except:
        first_commit_date = ''
        size = -1
        unit = ''

    write_large_csv(
        const.DIR_EXTENSION + '/data/repositories_additional_attributes.csv',
        ['repository', 'first_commit_date', 'size', 'unit'],
        [{'repository': row['repository'], 'first_commit_date': first_commit_date, 'size': size, 'unit': unit}],
    )


additional_attrs = pd.read_csv(
    const.DIR_EXTENSION + '/data/repositories_additional_attributes.csv',
    parse_dates=['first_commit_date'],
)
sizes = []
ages = []
for idx, row in additional_attrs.iterrows():
    if row['size'] == -1:
        sizes.append(-1)
        ages.append(-1)
    else:
        if row['unit'] == 'KiB':
            sizes.append(round(row['size'] / 1024, 2))
        elif row['unit'] == 'GiB':
            sizes.append(row['size'] * 1024)
        elif row['unit'] == 'MiB':
            sizes.append(row['size'])
        else:
            raise Exception('Invalid unit')

        ages.append((collection_period_end_date - row['first_commit_date'].replace(tzinfo=None)).days)


attrs = pd.read_csv(const.DIR_EXTENSION + '/data/repositories_attributes.csv')
attrs.reset_index()
attrs['size'] = sizes
attrs['age'] = ages

del attrs['Unnamed: 0']

attrs.to_csv(const.DIR_EXTENSION + '/data/repositories_attributes.csv', index=False)
