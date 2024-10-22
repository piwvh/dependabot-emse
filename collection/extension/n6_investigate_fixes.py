import os

import pandas as pd

import const
from collection.extension.util.general_util import str_to_date, write_csv, load_json_file, \
    get_package_latest_version
from collection.extension.util.git_util import load_json_file_from_commit
from collection.extension.util.npm_util import get_package_version_from_dep_file, yarn_file_to_json, \
    get_package_version_from_lock_file

# output csv
csv_fields = [
    'repository', 'package', 'ghsa', 'fix_commit',
    'dep_file_fix_version', 'lock_file_fix_version',
    'latest_version', 'latest_stable_version',
    'pr_version', 'vulnerable_version',
    'fix_date', 'latest_version_date', 'latest_stable_version_date',
    'pr_date', 'pr_number', 'lock_file_type'
]
csv_data = []
csv_path = const.DIR_EXTENSION + '/data/manual_fixes_details.csv'
write_csv(csv_path, csv_data, csv_fields)

lock_files = ['package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock']

security_updates = pd.read_csv(const.CSV_DATA['pr_vulnerabilities'])
fixes = pd.read_csv(const.DIR_EXTENSION + '/data/manual_fixes.csv')

# filter
fixes = fixes[~fixes.source.isnull()]
fixes = fixes[~fixes.fix_commit_hash.isnull()]
# fixes = fixes[~fixes.fix_commit_parent.isnull()]

# remove duplicate rows
# fixes = fixes.drop_duplicates()

print('Number of records:', len(fixes))

no_pr_found = 0
for index, row in fixes.iterrows():
    package = row['package']
    print('[%d] %s : %s [#%s]' % (index, row['repository'], row['package'], row['fix_commit'][0:8]))

    repo_dir = os.path.join(const.DIR_ROOT, 'collection/extension/data/repo', row['repository'])

    row_data = [row['repository'], package, row['ghsa'], row['fix_commit']]

    if row['source'] == 'GITHUB':
        dep_file_path = repo_dir + '/package.json'
        try:
            json_dep_file, commit = load_json_file_from_commit(repo_dir, dep_file_path, row['fix_commit'])
        except:
            print('\tDep file not found (G)')
            continue

        fix_date = commit.committer_date if commit.committer_date > commit.author_date else commit.author_date
        lock_file_base_path = repo_dir
    else:  # software heritage
        sh_path = const.DIR_EXTENSION + '/data/software_heritage/' + row['fix_commit']
        dep_file_path = sh_path + '/package.json'
        try:
            json_dep_file = load_json_file(dep_file_path)
        except:
            print('\tDep file not found (S)')
            continue

        author_date = str_to_date(row['date'], '%Y-%m-%dT%H:%M:%S%z')
        committer_date = str_to_date(row['committer_date'], '%Y-%m-%dT%H:%M:%S%z')
        fix_date = committer_date if committer_date > author_date else author_date
        lock_file_base_path = sh_path

    # lock file
    lock_file_type = None
    json_lock_file = None
    for lf in lock_files:
        lock_file_path = lock_file_base_path + '/' + lf
        if os.path.isfile(lock_file_path):
            try:
                json_lock_file = load_json_file(lock_file_path) if lf != 'yarn.lock' else yarn_file_to_json(lock_file_path)
                lock_file_type = lf
                break
            except:
                print('\tInvalid lock file:', lock_file_path)

    dep_file_fix_version = get_package_version_from_dep_file(package, json_dep_file)

    latest_version, latest_stable_version = get_package_latest_version(package, fix_date)

    lock_file_fix_version = get_package_version_from_lock_file(package, lock_file_type, json_lock_file)

    # find previous security update prs
    prs = security_updates[
        (security_updates['repository'] == row['repository']) &
        (security_updates['package'] == package) &
        (security_updates['state'] != 'MERGED')
    ]
    if prs.empty:
        print('\tNo PR found')
        no_pr_found += 1
        continue
    # if len(prs) > 1:
    #     print('\tMore than one PR was found: %d' % (len(prs),))

    for i, pr in prs.iterrows():
        csv_data.append(row_data + [
            dep_file_fix_version, lock_file_fix_version,
            latest_version['version'], latest_stable_version['version'],
            pr['to'], pr['from'],
            fix_date, latest_version['date'], latest_stable_version['date'],
            pr['date'], pr['number'], lock_file_type
        ])
        write_csv(csv_path, csv_data, csv_fields)

print('No PR found for %d records' % (no_pr_found,))
# remove duplicates
# we might have same record with different GHSA (GitHub Security Advisories)
# fixes_details = pd.read_csv(csv_path)
# fixes_details = fixes_details.drop_duplicates()
# fixes_details.to_csv(csv_path)
