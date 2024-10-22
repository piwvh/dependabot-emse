import math

import pandas as pd

import const

fixes_records = pd.read_csv(const.DIR_EXTENSION + '/data/manual_fixes.csv')
lockfile_fixes = pd.read_csv(const.DIR_EXTENSION + '/data/lockfile_fixes.csv')
dep_file_fixes = pd.read_csv(const.DIR_EXTENSION + '/data/dep_file_fixes.csv')

column_lockfile_fix = []
column_dep_file_fix = []
column_lockfile_inspired = []
column_dep_file_inspired = []
column_inspired = []
column_fix_time = []
for index, row in fixes_records.iterrows():
    lockfile_records = lockfile_fixes[
        (lockfile_fixes['repository'] == row['repository']) &
        (lockfile_fixes['package'] == row['package']) &
        (lockfile_fixes['fix_commit'] == row['fix_commit'])
    ]
    lockfile_inspired_records = lockfile_records[
        lockfile_records['inspired'] == True
    ]
    column_lockfile_fix.append(1 if len(lockfile_records) > 0 else 0)
    column_lockfile_inspired.append(1 if len(lockfile_inspired_records) > 0 else 0)

    dep_file_records = dep_file_fixes[
        (dep_file_fixes['repository'] == row['repository']) &
        (dep_file_fixes['package'] == row['package']) &
        (dep_file_fixes['fix_commit'] == row['fix_commit'])
    ]
    dep_file_inspired_records = dep_file_records[
        dep_file_records['inspired'] == True
    ]
    column_dep_file_fix.append(1 if len(dep_file_records) > 0 else 0)
    column_dep_file_inspired.append(1 if len(dep_file_inspired_records) > 0 else 0)

    column_inspired.append(1 if len(lockfile_inspired_records) > 0 or len(dep_file_inspired_records) > 0 else 0)

    fix_time = None
    if len(lockfile_inspired_records) > 0:
        fix_time = lockfile_inspired_records.iloc[0]['pr_fix_diff']
    elif len(dep_file_inspired_records) > 0:
        fix_time = dep_file_inspired_records.iloc[0]['pr_fix_diff']

    # non-inspired case
    if fix_time is None:
        fix_time_hour = 0
        for _, r in lockfile_records.iterrows():
            parts = r['pr_fix_diff'].split(',')
            t = int(parts[0]) * 24 + int(parts[1])
            if t >= fix_time_hour:
                fix_time_hour = t
                fix_time = r['pr_fix_diff']
        for _, r in dep_file_records.iterrows():
            parts = r['pr_fix_diff'].split(',')
            t = int(parts[0]) * 24 + int(parts[1])
            if t >= fix_time_hour:
                fix_time_hour = t
                fix_time = r['pr_fix_diff']

    column_fix_time.append(fix_time)


fixes_records['dep_file_fix'] = column_dep_file_fix
fixes_records['lockfile_fix'] = column_lockfile_fix
fixes_records['dep_file_inspired'] = column_dep_file_inspired
fixes_records['lockfile_inspired'] = column_lockfile_inspired
fixes_records['inspired'] = column_inspired
fixes_records['fix_time'] = column_fix_time

fixes_records.to_csv(const.DIR_EXTENSION + '/data/manual_fixes_inspired.csv')
