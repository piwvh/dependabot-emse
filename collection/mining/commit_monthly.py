import sys
import requests
from tqdm import tqdm
import csv
import time
import json
import dateutil.relativedelta as rel
import pandas as pd
import numpy as np

sys.path.append('..')
from finder import *  # noqa: E402
from config import *  # noqa: E402
from token_management import TokenManagerGraphQL  # noqa: E402


class RepositoryRequest:

    def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
        self.error_code_wait = error_code_wait
        self.timeout_wait = timeout_wait
        self.connection_loss_wait = connection_loss_wait
        self.response = None

    @staticmethod
    def query_string_strict_bound(owner, name, since, until):
        return """
        query { 
          repository(owner:"%(owner)s", name:"%(name)s") {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 1, since: "%(since)s", until:"%(until)s") {
                    totalCount
                  }
                }
              }
            }
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """ % {'owner': owner, 'name': name, 'since': since, 'until': until}

    @staticmethod
    def query_string_relax_bound(owner, name, until):
        return """
            query { 
              repository(owner:"%(owner)s", name:"%(name)s") {
                defaultBranchRef {
                  target {
                    ... on Commit {
                      history(first: 1, until:"%(until)s") {
                        totalCount
                      }
                    }
                  }
                }
              }
              rateLimit {
                remaining
                resetAt
              }
            }
            """ % {'owner': owner, 'name': name, 'until': until}

    def query_commits_monthly(self, owner, name, since, until, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_commits_monthly(owner, name, since, until, level + 1)
            if level == 0:
                print('success!')

        try:
            if since is not None:
                request = requests.post(url='https://api.github.com/graphql',
                                        json={'query': self.query_string_strict_bound(owner, name, since, until)},
                                        headers={"Authorization": "Token " + manager.get_active_token()},
                                        timeout=10)
            else:
                request = requests.post(url='https://api.github.com/graphql',
                                        json={'query': self.query_string_relax_bound(owner, name, until)},
                                        headers={"Authorization": "Token " + manager.get_active_token()},
                                        timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name: {}, since: {}, until: {}) failed: {}'.format(owner, name, since,
                                                                                                until,
                                                                                                request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name: {}, since: {}, until: {}) failed: {}'.format(owner, name, since,
                                                                                            until,
                                                                                            err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name: {}, since: {}, until: {}) failed: {}'.format(owner, name, since,
                                                                                            until,
                                                                                            err))
            new_attempt(self.connection_loss_wait)

    def query_commits(self):
        commit_meta = pd.read_csv(PATH_REPOSITORIES_DATA['commit_meta'], index_col=False)
        commit_meta = commit_meta[commit_meta['commits'] >= 12]
        try:
            with open(PATH_REPOSITORIES_DATA['commit_monthly'], 'w', encoding='utf-8') as output_file:
                writer = csv.writer(output_file)
                writer.writerow(['repository',
                                 'before_0',
                                 'month_0',
                                 'month_1',
                                 'month_2',
                                 'month_3',
                                 'month_4',
                                 'month_5',
                                 'month_6',
                                 'month_7',
                                 'month_8',
                                 'month_9',
                                 'month_10',
                                 'month_11'])
                repo_name = list(commit_meta['repository'])
                start = '2019-06-01'
                end = '2019-07-01'
                for repo in tqdm(repo_name):
                    slug = repo.split('/')
                    owner = slug[0]
                    name = slug[1]
                    row = [repo]
                    self.query_commits_monthly(owner, name, None, start + 'T00:00:00')
                    try:
                        commit = self.response['data']['repository']['defaultBranchRef']['target']['history'][
                            'totalCount']
                        row.append(commit)
                    except TypeError as err:
                        row.append(None)
                        print("failed to retrieve totalCount: {}".format(err))
                    try:
                        rate_info = self.response['data']['rateLimit']
                        manager.update_state(rate_info)
                    except TypeError as err:
                        print("failed to retrieve rateLimit: {}".format(err))
                    for month in range(12):
                        since = datetime.strftime(datetime.strptime(start, '%Y-%m-%d') +
                                                  rel.relativedelta(months=month), '%Y-%m-%d') + 'T00:00:00'
                        until = datetime.strftime(datetime.strptime(end, '%Y-%m-%d') +
                                                  rel.relativedelta(months=month), '%Y-%m-%d') + 'T00:00:00'
                        self.query_commits_monthly(owner, name, since, until)
                        try:
                            commit = self.response['data']['repository']['defaultBranchRef']['target']['history']['totalCount']
                            row.append(commit)
                        except TypeError as err:
                            row.append(None)
                            print("failed to retrieve totalCount: {}".format(err))
                        except KeyError as err:
                            row.append(None)
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
                    writer.writerow(row)
        except IOError as err:
            print(err)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = RepositoryRequest()
    requester.query_commits()
