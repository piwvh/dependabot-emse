import os

import pandas as pd

import const
from collection.extension.util.general_util import write_file, write_csv
from collection.extension.util.git_util import git_checkout
from collection.extension.util.software_heritage_util import sh_get_revision, sh_get_directory, sh_get_raw_data

original_fixes = pd.read_csv(const.CSV_DATA['fixes_labels'])


def get_fix_commit(_repository: str, _package: str, _number: int):
    records = original_fixes[
        (original_fixes['repository'] == _repository) &
        (original_fixes['package'] == _package) &
        (original_fixes['number'] == _number)
        ]
    if records.empty:
        raise Exception('No fix commit found')

    return records.iloc[0]['commit_fix']


def get_dep_files_from_revision(rev_dir: dict, commit_hash: str) -> bool:
    dep_files = ['package.json', 'package-lock.json', 'yarn.lock', 'npm-shrinkwrap.json']
    file_found = False

    for di in rev_dir:
        if di['type'] == 'file' and di['name'] in dep_files:
            file_found = True
            sh_revision_path = const.DIR_EXTENSION + '/data/software_heritage/' + commit_hash
            if not os.path.isdir(sh_revision_path):
                os.makedirs(sh_revision_path)

            raw_data = sh_get_raw_data(di['target'])
            write_file(sh_revision_path + '/' + di['name'], raw_data)

    return file_found


# output csv
csv_fields = [
    'repository', 'package', 'ghsa', 'pr_number',
    'fix_commit', 'fixed_by', 'date', 'committer_date', 'source'
]
csv_data = []
csv_path = const.DIR_EXTENSION + '/data/all_fixes.csv'
write_csv(csv_path, csv_data, csv_fields)

fixes = pd.read_csv(const.CSV_DATA['fixes_labels_round_2'])

# filter: fixed
fixes = fixes[fixes['fixed'] == True]

print('Number of records:', len(fixes))
for index, row in fixes.iterrows():
    print('%s:%s [%d]' % (row['repository'], row['package'], row['number']), end='')

    fix_commit = get_fix_commit(row['repository'], row['package'], row['number'])

    print(' [#%s]' % (fix_commit[0:8],))

    repo_dir = os.path.join(const.DIR_ROOT, 'collection/extension/data/repo', row['repository'])

    try:
        gr = git_checkout(repo_dir, fix_commit)
        commit = gr.get_commit(fix_commit)

        csv_data.append([
            row['repository'], row['package'], row['ghsa'], row['number'],
            fix_commit, row['by'], commit.author_date, commit.committer_date, 'GITHUB'
        ])
        write_csv(csv_path, csv_data, csv_fields)
    except:
        print('\tFix commit not found. Checking software heritage...')
        revision = sh_get_revision(fix_commit)
        found = False

        if 'directory_url' in revision:
            directory = sh_get_directory(revision['directory_url'])
            found = get_dep_files_from_revision(directory, fix_commit)

        csv_data.append([
            row['repository'], row['package'], row['ghsa'], row['number'],
            fix_commit, row['by'], revision['date'], revision['committer_date'], 'SOFTWARE_HERITAGE' if found else ''
        ])
        write_csv(csv_path, csv_data, csv_fields)

