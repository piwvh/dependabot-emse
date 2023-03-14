import sys
import csv
import requests
from tqdm import tqdm
import time
import pandas as pd
import json

sys.path.append('..')
from finder import *  # noqa: E402
from config import *  # noqa: E402
from token_management import TokenManagerGraphQL, TokenManagerRestApi  # noqa: E402


class CommitRequest:
    def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
        self.error_code_wait = error_code_wait
        self.timeout_wait = timeout_wait
        self.connection_loss_wait = connection_loss_wait
        self.response = None

    @staticmethod
    def query_string(repository, oid):
        return 'https://api.github.com/repos/{}/commits/{}'.format(repository, oid)

    def query_update(self, repository, oid, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_update(repository, oid, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.get(url=self.query_string(repository, oid),
                                   headers={"Authorization": "Token " + manager.get_active_token(),
                                            "Accept": "application/vnd.github.v3.raw"},
                                   timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (repository {}, oid: {}) failed: {}'.format(repository, oid, request.status_code))
                second_manager.decrease_remaining()
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (repository {}, oid: {}) failed: {}'.format(repository, oid, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (repository {}, oid: {}) failed: {}'.format(repository, oid, err))
            new_attempt(self.connection_loss_wait)


class RepositoryRequest:

    def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
        self.error_code_wait = error_code_wait
        self.timeout_wait = timeout_wait
        self.connection_loss_wait = connection_loss_wait
        self.response = None

    @staticmethod
    def query_string(owner, name, number):
        return """
        query { 
          repository(owner:"%(owner)s", name:"%(name)s"){
            pullRequest(number:%(number)s) {
              timeline(first:100) {
                edges {
                  node {
                    __typename
                    ... on HeadRefForcePushedEvent {
                      beforeCommit {
                        oid
                        pushedDate
                        parents(first:1) {
                          nodes {
                            oid
                            pushedDate
                          }
                        }
                      }
                      actor{
                        login
                        resourcePath
                      }
                    }
                  }
                }
              }
              state
              commits(first:100) {
                nodes {
                  commit {
                    oid
                    pushedDate
                    author {
                      name
                    }
                    parents(first:1) {
                      nodes{
                        oid
                        pushedDate
                      }
                    }
                  }
                }
              }
              mergeCommit {
                oid
              }
              files(first:100) {
                nodes {
                  path
                }
              }
            }
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """ % {'owner': owner, 'name': name, 'number': number}

    def query_update(self, owner, name, number, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_update(owner, name, number, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(owner, name, number)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (owner: {}, name {}, number: {}) failed: {}'.format(owner, name, number,
                                                                                     request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (owner: {}, name {}, number: {}) failed: {}'.format(owner, name, number, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (owner: {}, name {}, number: {}) failed: {}'.format(owner, name, number, err))
            new_attempt(self.connection_loss_wait)

    def query_updates_all(self):
        with open(PATH_REPOSITORIES_DATA['security_updates_commits'], 'w') as output:
            writer = csv.writer(output)
            writer.writerow([
                'repository',
                'number',
                'url',
                'parent_oid',
                'parent_time',
                'commit_oid',
                'commit_time',
                'final_oid',
                'final_time',
                'rebased',
                'state',
                'merged_oid',
                'closed_by_bot',
                'closed_case',
                'superseded_by',
                'created_at',
                'closed_at',
                'files'
            ])
            repo_names = pd.read_csv(PATH_REPOSITORIES_DATA['dependabot_filtered_repos'],
                                     index_col=False)['repository'].tolist()
            logs = []
            for repo in tqdm(repo_names):
                slug = repo.split('/')
                owner = slug[0]
                name = slug[1]
                try:
                    with open(os.path.join(DIR_UPDATES, repo.replace('/', '@') + '.json'), 'r',
                              encoding='utf-8') as json_file:
                        all_prs = json.load(json_file)
                        for pr in all_prs:
                            number = pr['number']
                            state = pr['state']
                            created_at = pr['createdAt']
                            closed_at = pr['closedAt']
                            closed_by_bot = False  # whether it was Dependabot who closed the pull request
                            closed_case = 0  # default case: closed by non-Dependabot
                            superseded_by = None
                            url = 'https://github.com/{}/pull/{}'.format(repo, pr['number'])
                            if state == 'CLOSED':
                                closer = None  # individual behind the close event
                                #  identify the individual behind the close event
                                for node in pr['timeline']['edges']:
                                    if (node['node']['__typename']) == 'ClosedEvent':
                                        try:
                                            closer = node['node']['actor']['resourcePath']
                                            break
                                        except TypeError:  # deleted user
                                            break
                                closed_by_bot = closer == '/apps/dependabot'
                                if closed_by_bot:
                                    for comment in pr['comments']['nodes']:
                                        # manual upgrade
                                        if 'up-to-date now, so this is no longer needed' in comment['bodyText']:
                                            closed_case = 1
                                            break
                                        # dependency removal
                                        elif 'no longer a dependency, so this is no longer needed' in\
                                                comment['bodyText']:
                                            closed_case = 2
                                            break
                                        # can not be updated to non-vulnerable version
                                        elif 'no longer updatable, so this is no longer needed' in\
                                                comment['bodyText']:
                                            closed_case = 3
                                            break
                                        # superseded by a newer security update
                                        elif 'Superseded by' in comment['bodyText']:
                                            closed_case = 4
                                            superseded_by = comment['bodyText'].split('#')[1].split('.')[0]
                                            break
                                        # closed using user in-comment command
                                        elif 'OK, I won\'t notify you' in comment['bodyText']:
                                            closed_case = 5
                                            break
                                        # anomaly case/unknown
                                        else:
                                            closed_case = 6
                            self.query_update(owner, name, number)
                            try:
                                rate_info = self.response['data']['rateLimit']
                                manager.update_state(rate_info)
                            except TypeError as err:
                                print("rate-failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number,
                                                                                                 err))
                                manager.decrease_remaining()
                                logs.append(
                                    "rate-failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number,
                                                                                               err))
                            except KeyError as err:
                                print("rate-failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number,
                                                                                                 err))
                                manager.decrease_remaining()
                                logs.append(
                                    "rate-failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number,
                                                                                               err))
                            try:
                                rebased = False
                                if state == 'MERGED':
                                    merged_oid = self.response['data']['repository']['pullRequest']\
                                        ['mergeCommit']['oid']
                                else:
                                    merged_oid = None
                                for timeline_edge in self.response['data']['repository']\
                                        ['pullRequest']['timeline']['edges']:
                                    if timeline_edge['node']['__typename'] == 'HeadRefForcePushedEvent':
                                        before_commit = timeline_edge['node']['beforeCommit']
                                        parent_oid = before_commit['parents']['nodes'][0]['oid']
                                        parent_time = before_commit['parents']['nodes'][0]['pushedDate']
                                        commit_oid = before_commit['oid']
                                        commit_time = before_commit['pushedDate']
                                        rebased = True
                                        break
                                for commit_node in self.response['data']['repository']['pullRequest']\
                                        ['commits']['nodes']:
                                    commit = commit_node['commit']
                                    try:
                                        author = commit['author']['name']
                                        if author == 'dependabot[bot]':
                                            if not rebased:
                                                parent_oid = commit['parents']['nodes'][0]['oid']
                                                parent_time = commit['parents']['nodes'][0]['pushedDate']
                                                commit_oid = commit['oid']
                                                commit_time = commit['pushedDate']
                                            final_oid = commit['oid']
                                            final_time = commit['pushedDate']
                                            break
                                    except TypeError:  # deleted user
                                        author = commit['author']['name']
                                if not rebased:
                                    files = []
                                    for file_node in self.response['data']['repository']['pullRequest']\
                                                                  ['files']['nodes']:
                                        file = file_node['path']
                                        files.append(file)
                                else:
                                    second_requester.query_update(repo, commit_oid)
                                    second_manager.decrease_remaining()
                                    files = []
                                    for file_node in second_requester.response['files']:
                                        file = file_node['filename']
                                        files.append(file)
                                writer.writerow([
                                    repo,
                                    number,
                                    url,
                                    parent_oid,
                                    parent_time,
                                    commit_oid,
                                    commit_time,
                                    final_oid,
                                    final_time,
                                    rebased,
                                    state,
                                    merged_oid,
                                    closed_by_bot,
                                    closed_case,
                                    superseded_by,
                                    created_at,
                                    closed_at,
                                    files
                                ])
                            except TypeError as err:
                                print("failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number, err))
                                manager.decrease_remaining()
                                logs.append(
                                    "failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number, err))
                            except KeyError as err:
                                print("failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number, err))
                                manager.decrease_remaining()
                                logs.append(
                                    "failed (owner: {}, name: {}, number: {}): {}".format(owner, name, number, err))
                except IOError as err:
                    print(err)
            try:
                with open(PATH_LOGS_DATA(os.path.basename(__file__)), 'w') as logs_file:
                    for log in logs:
                        logs_file.write("%s\n" % log)
            except IOError as err:
                print(err)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(GITHUB_TOKENS[0:3])
    second_manager = TokenManagerRestApi(GITHUB_TOKENS[3:])
    requester = RepositoryRequest()
    second_requester = CommitRequest()
    requester.query_updates_all()
