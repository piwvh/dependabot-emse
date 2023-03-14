import sys
from tqdm import tqdm
import pandas as pd
import requests
import csv
import json
import time

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
    def query_string(owner, name, cursor):
        return """
        query { 
          repository(owner:"%(owner)s", name:"%(name)s") {
            stargazers(first:100, after: %(cursor)s) {
              edges {
                starredAt
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """ % {'owner': owner, 'name': name, 'cursor': cursor}

    def query_stars_per_repo(self, owner, name, cursor, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_stars_per_repo(owner, name, cursor, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(owner, name, cursor)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name {}, cursor: {}) failed: {}'.format(owner, name, cursor,
                                                                                     request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name {}, cursor: {}) failed: {}'.format(owner, name, cursor, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name {}, cursor: {}) failed: {}'.format(owner, name, cursor, err))
            new_attempt(self.connection_loss_wait)

    def query_stars_all(self):
        repos = pd.read_csv(PATH_REPOSITORIES_DATA['dependabot_filtered_repos'], index_col=False)
        repo_names = repos['repository'].tolist()
        logs = []
        for repo in tqdm(repo_names):
            stars = []
            slug = repo.split('/')
            owner = slug[0]
            name = slug[1]
            has_next_page = True
            start_cursor = 'null'
            while has_next_page:
                self.query_stars_per_repo(owner, name, start_cursor)
                try:
                    page_info = self.response['data']['repository']['stargazers']['pageInfo']
                    has_next_page = page_info['hasNextPage']
                    if has_next_page:
                        start_cursor = '"' + page_info['endCursor'] + '"'
                    stars.extend(self.response['data']['repository']['stargazers']['edges'])
                    rate_info = self.response['data']['rateLimit']
                    manager.update_state(rate_info)
                except TypeError as err:
                    print("failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))
                    has_next_page = False
                    manager.decrease_remaining()
                    logs.append("failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))
                except KeyError as err:
                    print("failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))
                    has_next_page = False
                    manager.decrease_remaining()
                    logs.append("failed (owner: {}, name: {}, cursor: {}): {}".format(owner, name, start_cursor, err))
            if stars:
                try:
                    with open(os.path.join(PATH_REPOSITORIES_DATA['dir_stars'], repo.replace('/', '@') + '.json'), 'w',
                              encoding='utf-8') as output_file:
                        json.dump(stars, output_file, ensure_ascii=False, indent=4)
                except IOError as err:
                    print(err)
        try:
            with open(PATH_LOGS_DATA(os.path.basename(__file__)), 'w') as logs_file:
                writer = csv.writer(logs_file)
                for log in logs:
                    writer.writerow([log])
        except IOError as err:
            print(err)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = RepositoryRequest()
    requester.query_stars_all()
