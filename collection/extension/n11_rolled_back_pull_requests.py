import datetime
import os

import pandas as pd
from pydriller import Repository, Commit

import const
from collection.extension.util.git_util import git_checkout


def is_rollback(target_commit: Commit, current_commit: Commit):
    if target_commit.author_date >= current_commit.author_date:
        return False

    target_changes = set()
    current_changes = set()

    for mod in current_commit.modified_files:
        current_changes.add((mod.filename, mod.source_code, mod.change_type))

    for mod in target_commit.modified_files:
        target_changes.add((mod.filename, mod.source_code, mod.change_type))

    return target_changes == current_changes


original_fixes = pd.read_csv(const.CSV_DATA['fixes_labels'])
collection_period_end_date = datetime.datetime(2021, 5, 31, 23, 59, 59)


def get_fix_commit_hash(_repository: str, _package: str, _number: int):
    records = original_fixes[
        (original_fixes['repository'] == _repository) &
        (original_fixes['package'] == _package) &
        (original_fixes['number'] == _number)
        ]
    if records.empty:
        raise Exception('No fix commit found')

    return records.iloc[0]['commit_fix']


fixes = pd.read_csv(const.CSV_DATA['fixes_labels_round_2'])
# filter: fixed by bot
fixed_by_bot = fixes[(fixes['by'] == 'bot') & (fixes['fixed'] == True)]

for index, row in fixed_by_bot.iterrows():
    print('%s : %s [%d]' % (row['repository'], row['package'], row['number']), end='')

    fix_commit_hash = get_fix_commit_hash(row['repository'], row['package'], row['number'])

    print(' [#%s]' % (fix_commit_hash[0:8],))

    repo_dir = os.path.join(const.DIR_ROOT, 'collection/extension/data/repo', row['repository'])

    try:
        gr = git_checkout(repo_dir, 'HEAD')
        fix_commit = gr.get_commit(fix_commit_hash)
        for commit in Repository(repo_dir,
                                 since=fix_commit.author_date,
                                 to=collection_period_end_date
                                 ).traverse_commits():
            if(is_rollback(fix_commit, commit)):
                print('Rollback found: %s -> %s' % (fix_commit.hash, commit.hash))
    except Exception as er:
        print('Skip...', er)
