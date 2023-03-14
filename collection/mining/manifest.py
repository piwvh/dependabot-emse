import sys
import requests
from tqdm import tqdm
import csv
import time
import json
import pandas as pd

sys.path.append('..')
from finder import *  # noqa: E402
from config import *  # noqa: E402
from token_management import TokenManagerGraphQL  # noqa: E402


def parse_time(time_string):
    return datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')


class RepositoryRequest:

    def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
        self.error_code_wait = error_code_wait
        self.timeout_wait = timeout_wait
        self.connection_loss_wait = connection_loss_wait
        self.response = None

    @staticmethod
    def query_string(owner, name, file):
        return """
        query { 
          repository(owner:"%(owner)s", name:"%(name)s") { 
            defaultBranchRef{
              target {
                ...on Commit{
                  history(first:1, until:"2020-06-01T00:00:00Z", path: "%(file)s"){
                    nodes {
                      authoredDate
                    }
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
        """ % {'owner': owner, 'name': name, 'file': file}

    def query_file(self, owner, name, file, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_file(owner, name, file, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(owner, name, file)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name: {}, file: {}) failed: {}'.format(owner, name, file,
                                                                                    request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name: {}, file: {}) failed: {}'.format(owner, name, file, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name: {}, file: {}) failed: {}'.format(owner, name, file, err))
            new_attempt(self.connection_loss_wait)

    def query_manifests(self, files):
        repos = pd.read_csv(PATH_REPOSITORIES_DATA['repo_constraint_activity'], index_col=False)
        active = repos['active']
        before = repos['before']
        repo_constraint_activity = repos[active & before]
        repo_names = repo_constraint_activity['repository'].tolist()
        try:
            with open(PATH_REPOSITORIES_DATA['repo_manifest'], 'w', encoding='utf-8') as output_file:
                writer = csv.writer(output_file)
                row_names = ['repository']
                row_names.extend(files)
                writer.writerow(row_names)
                for repo in tqdm(repo_names):
                    row = [repo]
                    slug = repo.split('/')
                    owner = slug[0]
                    name = slug[1]
                    for manifest in files:
                        self.query_file(owner, name, manifest)
                        try:
                            history = self.response['data']['repository']['defaultBranchRef']['target']['history'][
                                'nodes']
                            if not history:
                                row.append(False)
                            else:
                                row.append(True)
                            rate_info = self.response['data']['rateLimit']
                            manager.update_state(rate_info)
                        except TypeError as err:
                            print("failed (owner: {}, name: {}, file: {}): {}".format(owner, name, manifest, err))
                            manager.decrease_remaining()
                        except KeyError as err:
                            print("failed (owner: {}, name: {}, file: {}): {}".format(owner, name, manifest, err))
                            manager.decrease_remaining()
                    writer.writerow(row)
        except IOError:
            print(IOError)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = RepositoryRequest()
    files = ['package.json']
    requester.query_manifests(files)
