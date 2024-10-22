import os

import pandas as pd

import const
from collection.extension.util.general_util import write_csv
from collection.extension.util.git_util import git_checkout

df1 = pd.read_csv(const.DIR_EXTENSION + '/data/manual_fixes_inspired_commit_messages_h.csv')
df2 = pd.read_csv(const.DIR_EXTENSION + '/data/manual_fixes_inspired_commit_messages_a.csv')
df3 = pd.read_csv(const.DIR_EXTENSION + '/data/manual_fixes_inspired_commit_messages_e.csv')


def get_labels(row):
    if not isinstance(row['label'], str):
        labels = []
    else:
        parts = row['label'].split('+')
        labels = [p.strip() for p in parts if p != '']

    return labels


def are_identical(list1, list2, list3):
    return set(list1) == set(list2) == set(list3)


# total = 0
# disagreement = 0
# for i in range(len(df1)):
#     if pd.isnull(df1.iloc[i]['commit_message']):
#         continue
#
#     total += 1
#
#     labels1 = get_labels(df1.iloc[i])
#     labels2 = get_labels(df2.iloc[i])
#     labels3 = get_labels(df3.iloc[i])
#
#     if len(labels1) == 0 and len(labels2) == 0 and len(labels3) == 0:
#         continue
#
#     if len(labels1) == 0 and len(labels2) == 1 and labels2[0] == 'empty' and len(labels3) == 1 and labels3[0] == 'empty':
#         continue
#
#     if len(labels1) == 0 and len(labels2) == 0 and len(labels3) == 1 and labels3[0] == 'other':
#         continue
#     if are_identical(labels1, labels2, labels3):
#         continue
#
#     print('H:', labels1, '\nA:', labels2, '\nE:', labels3)
#     print('\n[%s:%s]\n\n%s' % (df1.iloc[i]['repository'], df1.iloc[i]['package'], df1.iloc[i]['commit_message']))
#     print('==============================================================================')
#     disagreement += 1
#
# print('Total: %d, Disagreement: %.2f' % (total, 100 * disagreement / total))



total = 0
label_dependencies = 0
label_security = 0
label_dependabot = 0
for i in range(len(df1)):
    total += 1
    for l in get_labels(df1.iloc[i]):
        if l == 'dependencies':
            label_dependencies += 1
        elif l == 'security':
            label_security += 1
        elif l == 'dependabot':
            label_dependabot += 1

print(total)
print('dependencies: %d (%.2f), security: %d (%f), dependabot: %d (%f)' % (
    label_dependencies, label_dependencies / total,
    label_security, label_security / total,
    label_dependabot, label_dependencies / total
))
