import sys
import requests
from tqdm import tqdm
import csv
import time
import json

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
    def query_string(owner, name):
        return """
        query { 
          repository(owner:"%(owner)s", name:"%(name)s") {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 1, since: "2019-06-01T00:00:00", until:"2020-06-01T00:00:00") {
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
        """ % {'owner': owner, 'name': name}

    def query_commits_search(self, owner, name, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_commits_search(owner, name, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(owner, name)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
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

    def query_commits(self):
        try:
            with open(PATH_REPOSITORIES_DATA['commit_meta'], 'w', encoding='utf-8') as output_file:
                writer = csv.writer(output_file)
                writer.writerow(['repository', 'commits'])
                meta = None
                logs = []
                try:
                    with open(PATH_REPOSITORIES_DATA['repo_meta'], 'r') as json_file:
                        meta = json.load(json_file)
                except IOError as err:
                    print(err)
                repo_name = []
                for repo in meta:
                    repo_name.append(tuple(repo['nameWithOwner'].split('/')))
                for repo in tqdm(repo_name):
                    self.query_commits_search(repo[0], repo[1])
                    try:
                        commit = self.response['data']['repository']['defaultBranchRef']['target']['history']['totalCount']
                        writer.writerow([repo[0] + '/' + repo[1], commit])
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
                except IOError as err:
                    print(err)
        except IOError as err:
            print(err)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = RepositoryRequest()
    requester.query_commits()
