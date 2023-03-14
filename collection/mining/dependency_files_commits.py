import sys
import csv
from ast import literal_eval
import requests
from tqdm import tqdm
import time
import pandas as pd
import json
import itertools

sys.path.append('..')
from finder import *  # noqa: E402
from config import *  # noqa: E402
from token_management import TokenManagerGraphQL, TokenManagerRestApi  # noqa: E402


class HistoryRequest:

    def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
        self.error_code_wait = error_code_wait
        self.timeout_wait = timeout_wait
        self.connection_loss_wait = connection_loss_wait
        self.response = None

    @staticmethod
    def query_string_since(owner, name, path, since, cursor):
        return """
        query { 
          repository(owner: "%(owner)s", name: "%(name)s") {
            defaultBranchRef{
              target {
                ...on Commit{
                    history(first:100, path: "%(path)s", since: "%(since)s", after: %(cursor)s){
                    nodes {
                      abbreviatedOid
                      oid
                      authoredDate
                      pushedDate
                    }
                    pageInfo {
                      endCursor
                      hasNextPage
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
        """ % {'owner': owner, 'name': name, 'path': path, 'since': since, 'cursor': cursor}

    @staticmethod
    def query_string_before(owner, name, path, before):
        return """
        query { 
          repository(owner: "%(owner)s", name: "%(name)s") {
            defaultBranchRef{
              target {
                ...on Commit{
                    history(first:1, path: "%(path)s", until: "%(before)s"){
                    nodes {
                      abbreviatedOid
                      oid
                      authoredDate
                      pushedDate
                    }
                    pageInfo {
                      endCursor
                      hasNextPage
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
        """ % {'owner': owner, 'name': name, 'path': path, 'before': before}

    def query_commits_since_per_path_per_repo(self, owner, name, path, since, cursor, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_commits_since_per_path_per_repo(owner, name, path, since, cursor, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string_since(owner, name, path, since, cursor)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name: {}, path: {}, since: {}, cursor: {}) failed: {}'.format(
                    owner, name, path, since, cursor, request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name: {}, path: {}, since: {}, cursor: {}) failed: {}'.format(
                owner, name, path, since, cursor, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name: {}, path: {}, since: {}, cursor: {}) failed: {}'.format(
                owner, name, path, since, cursor, err))
            new_attempt(self.connection_loss_wait)

    def query_commits_before_per_path_per_repo(self, owner, name, path, before, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_commits_before_per_path_per_repo(owner, name, path, before, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string_before(owner, name, path, before)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name: {}, path: {}, before: {}) failed: {}'.format(
                    owner, name, path, before, request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name: {}, path: {}, before: {}) failed: {}'.format(
                owner, name, path, before, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name: {}, path: {}, before: {}) failed: {}'.format(
                owner, name, path, before, err))
            new_attempt(self.connection_loss_wait)

    def query_commits_all(self):
        upd_commits = pd.read_csv(PATH_REPOSITORIES_DATA['security_updates_commits'], index_col=False)
        upd_commits['files'] = upd_commits['files'].apply(literal_eval)
        repo_names = pd.read_csv(PATH_REPOSITORIES_DATA['dependabot_filtered_repos'],
                                 index_col=False)['repository'].tolist()
        logs = []
        exam = '2019-06-01T00:00:00Z'
        with open(PATH_REPOSITORIES_DATA['manifest_commits'], 'w') as output:
            writer = csv.writer(output)
            writer.writerow([
                'repository',
                'path',
                'abbreviated_oid',
                'oid',
                'authored',
                'pushed'
            ])
            for repo in tqdm(repo_names):
                slug = repo.split('/')
                owner = slug[0]
                name = slug[1]
                filtered_files = []
                all_files = upd_commits[upd_commits['repository'] == repo]['files'].to_list()
                for file in list(itertools.chain.from_iterable(all_files)):
                    if file.split('/')[-1] in ['package.json', 'package-lock.json', 'yarn.lock', 'npm-shrinkwrap.json']:
                        filtered_files.append(file)
                filtered_files = list(set(filtered_files))
                all_dirs = set()
                for file in filtered_files:
                    all_dirs.add(os.path.dirname(file))
                for direct in all_dirs:
                    if not (os.path.join(direct, 'package.json') in filtered_files):
                        filtered_files.append(os.path.join(direct, 'package.json'))
                for file in filtered_files:
                    has_next_page = True
                    start_cursor = 'null'
                    while has_next_page:
                        self.query_commits_since_per_path_per_repo(owner, name, file, exam, start_cursor)
                        try:
                            page_info = self.response['data']['repository']['defaultBranchRef']['target']['history']\
                                ['pageInfo']
                            has_next_page = page_info['hasNextPage']
                            if has_next_page:
                                start_cursor = '"' + page_info['endCursor'] + '"'
                            local_commits = self.response['data']['repository']['defaultBranchRef']['target']\
                                ['history']['nodes']
                            for commit in local_commits:
                                writer.writerow([
                                    repo,
                                    file,
                                    commit['abbreviatedOid'],
                                    commit['oid'],
                                    commit['authoredDate'],
                                    commit['pushedDate']
                                ])
                            rate_info = self.response['data']['rateLimit']
                            manager.update_state(rate_info)
                        except TypeError as err:
                            print("failed since (owner: {}, name: {}, path: {}, cursor: {}): {}".format(owner, name, file,
                                                                                                        start_cursor, err))
                            has_next_page = False
                            manager.decrease_remaining()
                            logs.append("failed since (owner: {}, name: {}, path: {}, cursor: {}): {}".format(
                                owner, name, file, start_cursor, err))
                        except KeyError as err:
                            print("failed since (owner: {}, name: {}, path: {}, cursor: {}): {}".format(owner, name, file,
                                                                                                        start_cursor, err))
                            has_next_page = False
                            manager.decrease_remaining()
                            logs.append("failed since (owner: {}, name: {}, path: {}, cursor: {}): {}".format(
                                owner, name, file, start_cursor, err))
                    self.query_commits_before_per_path_per_repo(owner, name, file, exam)
                    try:
                        local_commits = self.response['data']['repository']['defaultBranchRef']['target']\
                            ['history']['nodes']
                        for commit in local_commits:
                            writer.writerow([
                                repo,
                                file,
                                commit['abbreviatedOid'],
                                commit['oid'],
                                commit['authoredDate'],
                                commit['pushedDate']
                            ])
                        rate_info = self.response['data']['rateLimit']
                        manager.update_state(rate_info)
                    except TypeError as err:
                        print("failed before (owner: {}, name: {}, path: {}): {}".format(owner, name, file, err))
                        manager.decrease_remaining()
                        logs.append("failed before (owner: {}, name: {}, path: {}, cursor: {}): {}".format(
                            owner, name, file, start_cursor, err))
                    except KeyError as err:
                        print("failed before (owner: {}, name: {}, path: {}): {}".format(owner, name, file,
                                                                                                    err))
                        manager.decrease_remaining()
                        logs.append("failed before(owner: {}, name: {}, path: {}): {}".format(
                            owner, name, file, err))
        try:
            with open(PATH_LOGS_DATA(os.path.basename(__file__)), 'w') as logs_file:
                for log in logs:
                    logs_file.write("%s\n" % log)
        except IOError as err:
            print(err)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = HistoryRequest()
    requester.query_commits_all()
