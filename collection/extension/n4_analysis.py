import os

import pandas as pd

import const
from const import CSV_DATA

testing_frameworks = [
    'mocha', 'jest', 'jasmine', 'karma', 'nightwatch', 'cypress', 'playwright', 'selenium-webdriver'
]
ci_cd_tools = [
    'github_actions', 'circleci', 'travisci', 'appveyor', 'jenkins', 'gitlab', 'azure'
]

repo_vulnerability = pd.read_csv(CSV_DATA['pr_vulnerabilities'])
repo_attributes = pd.read_csv(os.path.join(const.DIR_ROOT, 'collection/extension/data/repositories_attributes.csv'))

merge_ratio = []
testing = []
ci_cd = []
num_prs = []

for index, row in repo_attributes.iterrows():
    records = repo_vulnerability.loc[repo_vulnerability['repository'] == row['repository']]

    closed_pr = sum(records['state'] == 'CLOSED')
    merged_pr = sum(records['state'] == 'MERGED')

    ratio = merged_pr / (merged_pr + closed_pr) if merged_pr + closed_pr > 0 else -1
    merge_ratio.append(ratio)

    has_testing = 0
    for fw in testing_frameworks:
        if row[fw] == 1:
            has_testing = 1
    testing.append(has_testing)

    has_ci_cd = 0
    for cc in ci_cd_tools:
        if row[cc] >= 12:
            has_ci_cd = 1
    ci_cd.append(has_ci_cd)

    num_prs.append(len(records))

# add columns
repo_attributes['merge_ratio'] = merge_ratio
repo_attributes['testing'] = testing
repo_attributes['ci_cd'] = ci_cd
repo_attributes['num_prs'] = num_prs

# filter
#repo_attributes = repo_attributes.loc[~repo_attributes['repository'].isin(exclude)]
repo_attributes = repo_attributes[repo_attributes['merge_ratio'] != -1]

# save
# repo_attributes.to_csv('data/attributes_analysis.csv')

# groups
g1 = repo_attributes[(repo_attributes['num_prs'] >= 1) & (repo_attributes['num_prs'] <= 2)]
g2 = repo_attributes[(repo_attributes['num_prs'] >= 3) & (repo_attributes['num_prs'] <= 4)]
g3 = repo_attributes[(repo_attributes['num_prs'] >= 5) & (repo_attributes['num_prs'] <= 10)]
g4 = repo_attributes[repo_attributes['num_prs'] >= 11]


print("total: %d, g1: %d, g2: %d, g3: %d, g4: %d\n" % (len(repo_attributes), len(g1), len(g2), len(g3), len(g4)))


def correlation_analysis(df):
    spearman = df.corr(method='spearman')
    print('ci/cd', spearman['merge_ratio']['ci_cd'])
    print('total_commits', spearman['merge_ratio']['end_commits_total'])
    print('total_authors', spearman['merge_ratio']['total_authors'])


def show_testing_analysis(df, col):
    with_testing = df[df['testing'] == 1]
    no_testing = df[df['testing'] == 0]

    m = df[col].mean()
    m1 = with_testing[col].mean()
    # m1 = (with_testing[col] / with_testing[col].sum()) * 100
    m2 = no_testing[col].mean()
    # m2 = (no_testing[col] / no_testing[col].sum()) * 100

    print("attribute:", col)
    print("total: %d, mean: %.2f" % (len(df), m))
    print("[with testing] total: %d, mean: %.2f" % (len(with_testing), m1))
    print("[no testing] total: %d, mean: %.2f" % (len(no_testing), m2))


def ci_cd_analysis(df, col):
    with_cicd = df[df['ci_cd'] == 1]
    no_cicd = df[df['ci_cd'] == 0]

    m1 = with_cicd[col].mean()
    m2 = no_cicd[col].mean()

    print("attribute:", col)
    print("[with CI/CD] total: %d, mean: %.2f" % (len(with_cicd), m1))
    print("[no CI/CD] total: %d, mean: %.2f" % (len(no_cicd), m2))


def final_analysis(df, col):
    with_ci_cd_testing = df[(df['ci_cd'] == 1) & (df['testing'] == 1)]
    no_ci_cd_testing = df[(df['ci_cd'] == 0) & (df['testing'] == 0)]

    m = df[col].mean()
    m1 = with_ci_cd_testing[col].mean()
    m2 = no_ci_cd_testing[col].mean()

    print("attribute:", col)
    print("total: %d, mean: %.2f" % (len(df), m))
    print("[with CI/CD & testing] total: %d, mean: %.2f" % (len(with_ci_cd_testing), m1))
    print("[no CI/CD & no testing] total: %d, mean: %.2f" % (len(no_ci_cd_testing), m2))


# print("---------------------------------")
# print("Correlation")
#
# print("total")
# correlation_analysis(repo_attributes)
# print("---------------------------------")
# print("g1")
# correlation_analysis(g1)
# print("---------------------------------")
# print("g2")
# correlation_analysis(g2)
# print("---------------------------------")
# print("g3")
# correlation_analysis(g3)
# print("---------------------------------")
# print("g4")
# correlation_analysis(g4)
# print("---------------------------------")
#


print('Testing')
show_testing_analysis(repo_attributes, 'merge_ratio')
print("---------------------------------")
print("g1")
show_testing_analysis(g1, 'merge_ratio')
print("---------------------------------")
print("g2")
show_testing_analysis(g2, 'merge_ratio')
print("---------------------------------")
print("g3")
show_testing_analysis(g3, 'merge_ratio')
print("---------------------------------")
print("g4")
show_testing_analysis(g4, 'merge_ratio')
print("---------------------------------")


print('CI/CD')
print("total")
ci_cd_analysis(repo_attributes, 'merge_ratio')
print("---------------------------------")
print("g1")
ci_cd_analysis(g1, 'merge_ratio')
print("---------------------------------")
print("g2")
ci_cd_analysis(g2, 'merge_ratio')
print("---------------------------------")
print("g3")
ci_cd_analysis(g3, 'merge_ratio')
print("---------------------------------")
print("g4")
ci_cd_analysis(g4, 'merge_ratio')
print("---------------------------------")


print('CI/CD & Testing')
print("total")
final_analysis(repo_attributes, 'merge_ratio')
print("---------------------------------")
print("g1")
final_analysis(g1, 'merge_ratio')
print("---------------------------------")
print("g2")
final_analysis(g2, 'merge_ratio')
print("---------------------------------")
print("g3")
final_analysis(g3, 'merge_ratio')
print("---------------------------------")
print("g4")
final_analysis(g4, 'merge_ratio')
print("---------------------------------")