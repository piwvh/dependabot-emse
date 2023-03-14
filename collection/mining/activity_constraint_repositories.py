import sys
import pandas as pd

sys.path.append('..')
from finder import *  # noqa: E402

if __name__ == '__main__':
    commit_monthly = pd.read_csv(PATH_REPOSITORIES_DATA['commit_monthly'], index_col=False)
    month_0 = commit_monthly['month_0'] > 0
    month_1 = commit_monthly['month_1'] > 0
    month_2 = commit_monthly['month_2'] > 0
    month_3 = commit_monthly['month_3'] > 0
    month_4 = commit_monthly['month_4'] > 0
    month_5 = commit_monthly['month_5'] > 0
    month_6 = commit_monthly['month_6'] > 0
    month_7 = commit_monthly['month_7'] > 0
    month_8 = commit_monthly['month_8'] > 0
    month_9 = commit_monthly['month_9'] > 0
    month_10 = commit_monthly['month_10'] > 0
    month_11 = commit_monthly['month_11'] > 0
    active = month_0 & month_1 & month_2 & month_3 & month_4 & month_5 & month_6 & month_7 & month_8 & month_9 & \
             month_10 & month_11
    before = commit_monthly['before_0'] > 99
    constrained = pd.DataFrame({'repository': commit_monthly['repository'], 'before': before, 'active': active})
    constrained.to_csv(PATH_REPOSITORIES_DATA['repo_constraint_activity'], index=False)