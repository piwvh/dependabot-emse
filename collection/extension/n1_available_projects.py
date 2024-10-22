import pandas as pd

from collection.extension.util.github_util import http_repository_exists
from const import CSV_DATA


def create_df(data: list):
    return pd.DataFrame(data, columns=['repository'])


vulnerabilities = pd.read_csv(CSV_DATA['pr_vulnerabilities'], index_col=False)
repositories = vulnerabilities['repository'].unique()

df = create_df([])
for repo in repositories:
    if http_repository_exists(repo) is True:
        df = pd.concat([df, create_df([repo])])
        print("Exists:", repo)
        df.to_csv('data/available_repos.csv')
