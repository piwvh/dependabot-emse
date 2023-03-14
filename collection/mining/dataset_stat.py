import sys
import pandas as pd
import json
from tqdm import tqdm
import time
import requests
from statistics import mean, median
from datetime import datetime

sys.path.append('..')
from token_management import TokenManagerGraphQL  # noqa: E402
from finder import *  # noqa: E402
from config import *  # noqa: E402


def compute_statistic(data):
    return min(data), max(data), median(data), mean(data)


def parse_time(time_string):
    return datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')


def _license(df_projects, df_reaper):
    return compute_statistic(df_projects.merge(df_reaper, how='left', on=['repository'])['license'].to_list())


def _documentation(df_projects, df_reaper):
    return compute_statistic(df_projects.merge(df_reaper, how='left', on=['repository'])['documentation'].to_list())


def _tests(df_projects, df_reaper):
    return compute_statistic(df_projects.merge(df_reaper, how='left', on=['repository'])['unit_test'].to_list())


def _ci(df_projects, df_reaper):
    return compute_statistic(df_projects.merge(df_reaper, how='left', on=['repository']
                                               )['continuous_integration'].to_list())


def _commits_before(df_projects, df_commits):
    return compute_statistic(df_projects.merge(df_commits, how='left', on=['repository'])['before_0'].to_list())


def _commits_during(df_projects, df_commits):
    return compute_statistic(df_projects.merge(df_commits, how='left', on=['repository'])['commits'].to_list())


def _forks(repositories):
    forks = []
    with open(PATH_REPOSITORIES_DATA['repo_meta'], 'r') as json_file:
        repositories = json.load(json_file)
    for repository in tqdm(repositories):
        if repository['nameWithOwner'] in dependabot_projects_names:
            forks.append(repository['forkCount'])
    return compute_statistic(forks)


def _stars(repositories):
    stars = []
    with open(PATH_REPOSITORIES_DATA['repo_meta'], 'r') as json_file:
        repositories = json.load(json_file)
    for repository in tqdm(repositories):
        if repository['nameWithOwner'] in dependabot_projects_names:
            stars.append(repository['stargazerCount'])
    return compute_statistic(stars)


def _age(repositories, today):
    age = []
    with open(PATH_REPOSITORIES_DATA['repo_meta'], 'r') as json_file:
        repositories = json.load(json_file)
    for repository in tqdm(repositories):
        if repository['nameWithOwner'] in dependabot_projects_names:
            age.append((today - parse_time(repository["createdAt"])).days)
    return compute_statistic(age)


def _contributors_api(repositories):
    class RepositoryRequest:

        def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
            self.error_code_wait = error_code_wait
            self.timeout_wait = timeout_wait
            self.connection_loss_wait = connection_loss_wait
            self.response = None

        @staticmethod
        def query_string(owner, name):
            return """
            query { 
              repository(owner:"%(owner)s", name:"%(name)s") {
                collaborators(first:1) {
                  totalCount
                }
              }
              rateLimit {
                remaining
                resetAt
              }
            }
            """ % {'owner': owner, 'name': name}

        def query_contributor_search(self, owner, name, level=0):
            def new_attempt(_time):
                time.sleep(_time)
                self.query_contributor_search(owner, name, level + 1)
                if level == 0:
                    print('success!')

            try:
                request = requests.post(url='https://api.github.com/graphql',
                                        json={'query': self.query_string(owner, name)},
                                        headers={"Authorization": "Token " + manager.get_active_token()},
                                        timeout=10)
                if request.status_code == 200:
                    print(self.response)
                    self.response = request.json()
                else:
                    print('query for (owner: {}, name: {}) failed: {}'.format(owner, name, request.status_code))
                    new_attempt(self.error_code_wait)
            except requests.exceptions.Timeout as err:
                print('query for (owner: {}, name: {}) failed: {}'.format(owner, name, err))
                new_attempt(self.timeout_wait)
            except requests.exceptions.ConnectionError as err:
                print('query for (owner: {}, name: {}) failed: {}'.format(owner, name, err))
                new_attempt(self.connection_loss_wait)

        def query_contributors(self, all_contributors, repo_names):
            logs = []
            for repo_name in tqdm(repo_names):
                repo = repo_name.split('/')
                print(repo)
                self.query_contributor_search(repo[0], repo[1])
                try:
                    local_contributor_count = self.response['data']['repository']['collaborators']['totalCount']
                    all_contributors.append(local_contributor_count)
                except TypeError as err:
                    logs.append(repo[0] + '/' + repo[1])
                    print("failed to retrieve totalCount: {}".format(err))
                except KeyError as err:
                    logs.append(repo[0] + '/' + repo[1])
                    print("failed to retrieve totalCount: {}".format(err))
                try:
                    rate_info = self.response['data']['rateLimit']
                    manager.update_state(rate_info)
                except TypeError as err:
                    print("failed to retrieve rateLimit: {}".format(err))
                    manager.decrease_remaining()
                except KeyError as err:
                    print("failed to retrieve rateLimit: {}".format(err))
                    manager.decrease_remaining()
            try:
                with open(PATH_LOGS_DATA(os.path.basename(__file__)), 'w', encoding='utf-8') as logs_file:
                    logs_file.write('\n'.join([' '.join(log) for log in logs]))
            except IOError:
                print('failed to write logs')
    contributors = []
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = RepositoryRequest()
    requester.query_contributors(contributors, repositories)
    return compute_statistic(contributors)


def _contributors_reaper(df_projects, df_reaper):
    return compute_statistic(df_projects.merge(df_reaper, how='left', on=['repository'])['community'].to_list())


def _dependabot_prs(repositories):
    dependabot_prs = []
    for repo in tqdm(repositories):
        try:
            with open(os.path.join(DIR_UPDATES, repo.replace('/', '@') + '.json'), 'r', encoding='utf-8') as json_file:
                local_dependabot_prs = 0
                prs = json.load(json_file)
                for pr in prs:
                    local_dependabot_prs += 1
        except IOError:
            pass
        dependabot_prs.append(local_dependabot_prs)
    return compute_statistic(dependabot_prs)


if __name__ == '__main__':
    today = parse_time('2019-06-01T00:00:00Z')
    reaper_data = pd.read_csv(os.path.join(DIR_REAPER, 'data', 'results.csv'), index_col=False)
    commit_info = pd.read_csv(PATH_REPOSITORIES_DATA['commit_monthly'], index_col=False)
    commit_meta_info = pd.read_csv(PATH_REPOSITORIES_DATA['commit_meta'], index_col=False)
    dependabot_projects = pd.read_csv(PATH_REPOSITORIES_DATA['dependabot_filtered_repos'], index_col=False)
    dependabot_projects_names = dependabot_projects['repository'].to_list()
    # stats
    license_stat = _license(dependabot_projects, reaper_data)
    test_stat = _tests(dependabot_projects, reaper_data)
    ci_stat = _ci(dependabot_projects, reaper_data)
    documentation_stat = _documentation(dependabot_projects, reaper_data)
    commits_before_stat = _commits_before(dependabot_projects, commit_info)
    commits_during_stat = _commits_during(dependabot_projects, commit_meta_info)
    forks_stat = _forks(dependabot_projects_names)
    age_stat = _age(dependabot_projects_names, today)
    stars_stat = _stars(dependabot_projects_names)
    contributors_stat = _contributors_reaper(dependabot_projects, reaper_data)
    dependabot_prs_stat = _dependabot_prs(dependabot_projects_names)
    # dataframe
    headers = ['min', 'max', 'median', 'mean']
    all_rows = [license_stat,
                test_stat,
                ci_stat,
                documentation_stat,
                commits_before_stat,
                commits_during_stat,
                forks_stat,
                age_stat,
                stars_stat,
                contributors_stat,
                dependabot_prs_stat]
    df_statistic = pd.DataFrame(columns=headers, data=all_rows)
    df_statistic['feature'] = pd.Series(['license',
                                         'tests',
                                         'ci',
                                         'documentation',
                                         'commits before',
                                         'commits during',
                                         'forks',
                                         'age',
                                         'stars',
                                         'contributors',
                                         'dependabot prs'])
    df_statistic.set_index('feature', inplace=True)
    df_statistic.to_csv(PATH_REPOSITORIES_DATA['statistic'], index=True)


