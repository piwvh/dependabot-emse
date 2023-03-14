import json
import sys
from tqdm import tqdm
import pandas as pd

sys.path.append('..')
from finder import *


if __name__ == '__main__':
    repo_names = pd.read_csv(PATH_REPOSITORIES_DATA['engineered_repos'], index_col=False)['repository'].to_list()
    dependabot_projects = []
    for repo in tqdm(repo_names):
        try:
            with open(os.path.join(DIR_PRS_FILTERED, repo.replace('/', '@') + '.json'), 'r', encoding='utf-8') as json_file:
                has_other = False
                has_dependabot = False
                prs = json.load(json_file)
                for pr in prs:
                    try:
                        if pr['author']['resourcePath'] == '/apps/dependabot':
                            has_dependabot = True
                        elif pr['author']['resourcePath'] in ['/apps/renovate', '/renovate-bot']:
                            has_other = True
                        elif pr['author']['resourcePath'] == '/apps/greenkeeper':
                            has_other = True
                        elif pr['author']['resourcePath'] == '/apps/dependabot-preview':
                            has_other = True
                        elif pr['author']['resourcePath'] == '/snyk-bot':
                            has_other = True
                    except TypeError:
                        pass  # deleted user
                if has_dependabot & (not has_other):
                    dependabot_projects.append(repo)
        except IOError:
            pass
    df_dependabot_projects = pd.DataFrame({'repository': dependabot_projects})
    df_dependabot_projects.to_csv(PATH_REPOSITORIES_DATA['dependabot_repos'], index=False)
