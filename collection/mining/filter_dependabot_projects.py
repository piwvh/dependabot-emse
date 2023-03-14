import sys
import pandas as pd
from tqdm import tqdm
import json

sys.path.append('..')
from finder import *  # noqa: E402


if __name__ == '__main__':
    repos_with_other = set()
    repo_names = pd.read_csv(PATH_REPOSITORIES_DATA['dependabot_repos'], index_col=False)['repository'].tolist()
    clear_repos = []
    for repo in tqdm(repo_names):
        with open(os.path.join(DIR_UPDATES, repo.replace('/', '@') + '.json'), 'r', encoding='utf-8') as json_file:
            raw_prs = json.load(json_file)
            for pr in raw_prs:
                title = pr['title']
                ecosystem = None
                try:
                    files = pr['files']['nodes']
                    for file in files:
                        if ecosystem is not None:
                            break
                        for key, arr in ECOSYSTEM_MAPPING.items():
                            if ecosystem is not None:
                                break
                            for value in arr:
                                if value in file['path']:
                                    ecosystem = key
                                    break
                except TypeError:
                    ecosystem = 'unknown'
                if ecosystem == 'unknown':
                    ecosystem = 'npm'
                if ecosystem is None:  # special case, cannot be retrieved with GraphQL API, done manually
                    if (repo == 'sitespeedio/sitespeed.io') & (pr['number'] == '2562'):
                        ecosystem = 'rubygems'
                    else:
                        ecosystem = 'npm'
                if ecosystem != 'npm':
                    repos_with_other.add(repo)
    for repo in repo_names:
        if not (repo in repos_with_other):
            clear_repos.append(repo)
    df_dependabot_projects_clear = pd.DataFrame({'repository': clear_repos})
    df_dependabot_projects_clear.to_csv(PATH_REPOSITORIES_DATA['dependabot_filtered_repos'], index=False)
