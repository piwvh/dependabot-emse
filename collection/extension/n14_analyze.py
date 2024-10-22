import pandas as pd
from packaging.version import Version

import const
from collection.extension.util.general_util import compare_versions

all_fixes = pd.read_csv(const.DIR_EXTENSION + '/data/all_fixes_versions.csv')
all_fixes['version_diff'] = all_fixes.apply(lambda r: compare_versions(r['vulnerable_version'], r['pr_version']) , axis=1)

print(all_fixes)

print(len(all_fixes[all_fixes['version_diff'] == 'major']))
print(len(all_fixes[all_fixes['version_diff'] == 'minor']))
print(len(all_fixes[all_fixes['version_diff'] == 'patch']))

xx = all_fixes.groupby(['fixed_by', 'version_diff'], as_index=False)['repository'].count().rename(
    columns={'repository': 'count'})

by_bot = xx[xx['fixed_by'] == 'bot']
by_bot['percentage'] = 100 * by_bot['count'] / 2662

by_human = xx[xx['fixed_by'] == 'human']
by_human['percentage'] = 100 * by_human['count'] / 1507

print(by_bot)
print(by_human)