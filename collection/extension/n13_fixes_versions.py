import os

import pandas as pd
from pydriller import Git

import const
from collection.extension.util.general_util import str_to_date, write_csv, get_package_latest_version

# output csv
csv_fields = [
    'repository', 'package', 'ghsa', 'fix_commit', 'fixed_by',
    'latest_version', 'latest_stable_version',
    'pr_version', 'vulnerable_version',
    'fix_date', 'latest_version_date', 'latest_stable_version_date',
    'pr_date', 'pr_number'
]
csv_data = []
csv_path = const.DIR_EXTENSION + '/data/all_fixes_versions.csv'
write_csv(csv_path, csv_data, csv_fields)

security_updates = pd.read_csv(const.CSV_DATA['pr_vulnerabilities'])
all_fixes = pd.read_csv(const.DIR_EXTENSION + '/data/all_fixes.csv')

# filter
all_fixes = all_fixes[~all_fixes.source.isnull()]
all_fixes = all_fixes[~all_fixes.fix_commit.isnull()]

# remove duplicate rows
# fixes = fixes.drop_duplicates()

print('Number of records:', len(all_fixes))

for index, row in all_fixes.iterrows():
    package = row['package']
    print('[%d] %s : %s [#%s]' % (index, row['repository'], row['package'], row['fix_commit'][0:8]))

    repo_dir = os.path.join(const.DIR_ROOT, 'collection/extension/data/repo', row['repository'])

    if row['source'] == 'GITHUB':
        gr = Git(repo_dir)
        commit = gr.get_commit(row['fix_commit'])
        fix_date = commit.committer_date if commit.committer_date > commit.author_date else commit.author_date
    else:  # software heritage
        author_date = str_to_date(row['date'], '%Y-%m-%dT%H:%M:%S%z')
        committer_date = str_to_date(row['committer_date'], '%Y-%m-%dT%H:%M:%S%z')
        fix_date = committer_date if committer_date > author_date else author_date

    latest_version, latest_stable_version = get_package_latest_version(package, fix_date)

    # find previous security update prs
    prs = security_updates[
        (security_updates['repository'] == row['repository']) &
        (security_updates['package'] == package) &
        (security_updates['number'] == row['pr_number'])
        ]
    if prs.empty:
        print('\tNo PR found')
        continue
    if len(prs) > 1:
        print('\tMore than one PR was found: %d' % (len(prs),))
        print(prs)

    pr = prs.iloc[0]
    csv_data.append([
        row['repository'], package, row['ghsa'], row['fix_commit'], row['fixed_by'],
        latest_version['version'], latest_stable_version['version'],
        pr['to'], pr['from'],
        fix_date, latest_version['date'], latest_stable_version['date'],
        pr['date'], pr['number']
    ])
    write_csv(csv_path, csv_data, csv_fields)
