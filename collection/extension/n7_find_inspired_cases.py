import pandas as pd
from packaging.version import parse as parse_version

import const
from collection.extension.util.general_util import create_df, append_row_to_df, str_to_date
from collection.extension.util.npm_util import semver_coerce, get_package_versions, semver_min_satisfying

# for each fix, we might have multiple records in this dataset, per each pull request concerning that fix:
# fix1, pr#1
# fix1, pr#2
# ...
fixes_details = pd.read_csv(const.DIR_EXTENSION + '/data/manual_fixes_details.csv')
print('All records:', len(fixes_details))

# lock file fixes
lockfile_fixes = fixes_details[~fixes_details.lock_file_fix_version.isnull()]
print('Lockfile fixes records:', len(lockfile_fixes))

lockfile_fixes_df = create_df(columns=[
    'repository', 'package', 'fix_commit', 'lock_file_fix_version',
    'latest_stable_version', 'pr_version', 'pr_number', 'pr_date',
    'fix_date', 'pr_fix_diff', 'inspired'
])


for index, row in lockfile_fixes.iterrows():
    print('%d %s — %s [#%s]' % (index, row['repository'], row['package'], row['fix_commit'][0:8]))

    pr_date = str_to_date(row['pr_date'], _format='%Y-%m-%dT%H:%M:%S%z')
    fix_date = str_to_date(row['fix_date'], _format='%Y-%m-%d %H:%M:%S%z')
    delta = fix_date - pr_date
    if delta.days < 0:
        continue

    pr_fix_diff = str(delta.days) + "," + str(delta.seconds // 3600)

    lockfile_fix_version = parse_version(row['lock_file_fix_version'])
    pr_version = parse_version(row['pr_version'])
    latest_stable_version = parse_version(row['latest_stable_version'])
    latest_version = parse_version(row['latest_version'])

    inspired = None

    # like 6.0.0-next.3e165448
    if not hasattr(lockfile_fix_version, 'major'):
        continue

    print('(%s, %s, %s)' % (lockfile_fix_version, pr_version, latest_stable_version))

    if lockfile_fix_version == pr_version and lockfile_fix_version != latest_stable_version and lockfile_fix_version != latest_version:
        inspired = True
    else:
        inspired = False

    data = [
        row['repository'], row['package'], row['fix_commit'],
        row['lock_file_fix_version'],
        row['latest_stable_version'],
        row['pr_version'],
        row['pr_number'],
        row['pr_date'],
        row['fix_date'],
        pr_fix_diff,
        inspired,
    ]
    lockfile_fixes_df = append_row_to_df(lockfile_fixes_df, data)

lockfile_fixes_df.to_csv(const.DIR_EXTENSION + '/data/lockfile_fixes.csv')

# dep file fixes
dep_file_fixes = fixes_details[~fixes_details.dep_file_fix_version.isnull()]
print('Dependency file fixes records:', len(dep_file_fixes))

dep_file_fixes_df = create_df(columns=[
    'repository', 'package', 'fix_commit', 'dep_file_fix_version',
    'min_satisfying_version', 'latest_stable_version', 'pr_version', 'pr_number',
    'pr_date', 'fix_date', 'pr_fix_diff', 'inspired'
])

for index, row in dep_file_fixes.iterrows():
    print('%d %s — %s [#%s]' % (index, row['repository'], row['package'], row['fix_commit'][0:8]))

    dep_file_fix_version_coerced = parse_version(semver_coerce(row['dep_file_fix_version']))
    if dep_file_fix_version_coerced is None:
        print('Coerced is none:', row['dep_file_fix_version'])
        continue

    ms = semver_min_satisfying(get_package_versions(row['package']), row['dep_file_fix_version'])
    if ms is None:
        print('Min satisfying version not found')
        exit()

    pr_date = str_to_date(row['pr_date'], _format='%Y-%m-%dT%H:%M:%S%z')
    fix_date = str_to_date(row['fix_date'], _format='%Y-%m-%d %H:%M:%S%z')
    delta = fix_date - pr_date
    if delta.days < 0:
        continue

    pr_fix_diff = str(delta.days) + "," + str(delta.seconds // 3600)

    min_satisfying_version = parse_version(ms)
    pr_version = parse_version(row['pr_version'])
    latest_stable_version = parse_version(row['latest_stable_version'])
    latest_version = parse_version(row['latest_version'])

    inspired = None

    # like 6.0.0-next.3e165448
    if not hasattr(dep_file_fix_version_coerced, 'major'):
        continue

    print('(%s [%s] -> %s, %s, %s)' % (
        dep_file_fix_version_coerced, row['dep_file_fix_version'],
        min_satisfying_version, pr_version, latest_stable_version
    ))

    if ((dep_file_fix_version_coerced == pr_version or min_satisfying_version == pr_version)
            and dep_file_fix_version_coerced != latest_stable_version and dep_file_fix_version_coerced != latest_version
            and min_satisfying_version != latest_stable_version and min_satisfying_version != latest_version):
        inspired = True
    else:
        inspired = False

    data = [
        row['repository'], row['package'], row['fix_commit'],
        row['dep_file_fix_version'],
        min_satisfying_version,
        row['latest_stable_version'],
        row['pr_version'],
        row['pr_number'],
        row['pr_date'],
        row['fix_date'],
        pr_fix_diff,
        inspired,
    ]
    dep_file_fixes_df = append_row_to_df(dep_file_fixes_df, data)

dep_file_fixes_df.to_csv(const.DIR_EXTENSION + '/data/dep_file_fixes.csv')


def fix_time(row):
    time = None
    if row['inspired'] == 1:
        time = row['inspire_time']
    else:
        time = row['min_fix_time']

    return int(time.split(',')[0])
