import sys
import requests
from tqdm import tqdm
from datetime import timedelta
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
    def query_string(created, cursor):
        return """
        query { 
          search(type:REPOSITORY, 
          query:"language:javascript stars:>1 fork:false created:\\"%(created)s\\" pushed:\\"> 2019-05-31\\"",
           first:100, after: %(cursor)s) {
            pageInfo {
              endCursor
              hasNextPage
            } 
            repositoryCount
            nodes {
              ...on Repository {
                name
                nameWithOwner
                createdAt
                pushedAt
                updatedAt
                description
                forkCount
                stargazerCount
                resourcePath
                homepageUrl
                isArchived
                isDisabled
              }
            }
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """ % {'created': created, 'cursor': cursor}

    def query_repository_search(self, date, cursor, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_repository_search(date, cursor, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(date, cursor)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (date: {}, cursor: {}) failed: {}'.format(date, cursor, request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (date: {}, cursor: {}) failed: {}'.format(date, cursor, err))
            new_attempt(self.timeout_wait)
        except requests.exceptions.ConnectionError as err:
            print('query for (date: {}, cursor: {}) failed: {}'.format(date, cursor, err))
            new_attempt(self.connection_loss_wait)

    def query_repositories(self, start_date, end_date):
        meta = []
        logs = []
        days = (start_date - end_date).days
        for day in tqdm(range(days)):
            date = (start_date - timedelta(days=day)).strftime('%Y-%m-%d')
            has_next_page = True
            start_cursor = 'null'
            while has_next_page:
                self.query_repository_search(date, start_cursor)
                page_info = self.response['data']['search']['pageInfo']
                has_next_page = page_info['hasNextPage']
                if start_cursor == 'null':
                    repository_count = self.response['data']['search']['repositoryCount']
                    if repository_count > 1000:
                        logs.extend(['date: {}, repositoryCount: {}'.format(date, repository_count)])
                if has_next_page:
                    start_cursor = '"' + page_info['endCursor'] + '"'
                meta.extend(self.response['data']['search']['nodes'])
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
            with open(PATH_REPOSITORIES_DATA['meta'], 'w', encoding='utf-8') as output_file:
                json.dump(meta, output_file, ensure_ascii=False, indent=4)
        except IOError as err:
            print(err)
        try:
            with open(PATH_LOGS_DATA(os.path.basename(__file__)), 'w', encoding='utf-8') as logs_file:
                logs_file.write('\n'.join([' '.join(log) for log in logs]))
        except IOError as err:
            print(err)


if __name__ == '__main__':
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = RepositoryRequest()
    start_date = datetime.strptime('2019-05-31', '%Y-%m-%d').date()
    end_date = datetime.strptime('2008-01-01', '%Y-%m-%d').date()
    requester.query_repositories(start_date, end_date)
