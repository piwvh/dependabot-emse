import os

import pandas as pd

import const
from collection.extension.util.general_util import write_csv
from collection.extension.util.git_util import git_checkout

fixes_df = pd.read_csv(const.DIR_EXTENSION + '/data/manual_fixes_inspired.csv')
inspired_df = fixes_df[fixes_df['inspired'] == 1]

inspired_data = []
for index, row in inspired_df.iterrows():
    print(row['fix_commit'])

    data = [row['repository'], row['package'], row['fix_commit']]
    repo_dir = os.path.join(const.DIR_EXTENSION, 'data/repo', row['repository'])
    try:
        gr = git_checkout(repo_dir, row['fix_commit'])
        commit = gr.get_commit(row['fix_commit'])
        data.append(commit.msg)
    except:
        # hrtg
        data.append('')

    inspired_data.append(data)


write_csv(const.DIR_EXTENSION + '/data/manual_fixes_inspired_commit_messages.csv', inspired_data, [
    'repository', 'package', 'fix_commit', 'commit_message'
])