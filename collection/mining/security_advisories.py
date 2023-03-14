import sys
import csv
import requests
import time
import pandas as pd

sys.path.append('..')
from token_management import TokenManagerGraphQL  # noqa: E402
from finder import *  # noqa: E402
from config import *  # noqa: E402


class AdvisoryRequest:
    def __init__(self, error_code_wait=1, timeout_wait=2, connection_loss_wait=60):
        self.error_code_wait = error_code_wait
        self.timeout_wait = timeout_wait
        self.connection_loss_wait = connection_loss_wait
        self.response = None
        self.advisories = []

    @staticmethod
    def query_string(cursor):
        return """
            query {
              securityAdvisories(orderBy: {field: PUBLISHED_AT, direction: DESC}, first: 100, after: %(cursor)s) {
                pageInfo {
                  hasNextPage
                  endCursor
                }
                nodes {
                  identifiers {
                    type
                    value
                  }
                  summary
                  publishedAt
                  updatedAt
                  severity
                  vulnerabilities (first:100) {
                    nodes {
                      firstPatchedVersion {
                        identifier
                      }
                      package {
                        ecosystem
                        name
                      }
                      severity
                      vulnerableVersionRange
                    }
                  }
                }
              }
              rateLimit {
                remaining
                resetAt
              }
            }
        """ % {'cursor': cursor}

    def query_advisory_page(self, cursor, level=0):
        def new_attempt(_time):
            time.sleep(_time)
            self.query_advisory_page(cursor, level + 1)
            if level == 0:
                print('success!')

        try:
            request = requests.post(url='https://api.github.com/graphql',
                                    json={'query': self.query_string(cursor)},
                                    headers={"Authorization": "Token " + manager.get_active_token()},
                                    timeout=10)
            if request.status_code == 200:
                self.response = request.json()
            else:
                print('query for (cursor: {}) failed: {}'.format(cursor, request.status_code))
                new_attempt(self.error_code_wait)
        except requests.exceptions.Timeout as err:
            print('query for (cursor: {}) failed: {}'.format(cursor, err))
        except requests.exceptions.ConnectionError as err:
            print('query for (cursor: {}) failed: {}'.format(cursor, err))
            new_attempt(self.connection_loss_wait)

    def query_advisories_all(self):
        logs = []
        has_next_page = True
        start_cursor = 'null'
        while has_next_page:
            self.query_advisory_page(start_cursor)
            try:
                page_info = self.response['data']['securityAdvisories']['pageInfo']
                has_next_page = page_info['hasNextPage']
                if has_next_page:
                    start_cursor = '"' + page_info['endCursor'] + '"'
                self.advisories.extend(self.response['data']['securityAdvisories']['nodes'])
                rate_info = self.response['data']['rateLimit']
                manager.update_state(rate_info)
            except TypeError as err:
                print("failed (cursor: {}): {}".format(start_cursor, err))
                has_next_page = False
                manager.decrease_remaining()
                logs.append("failed ( cursor: {}): {}".format(start_cursor, err))
            except KeyError as err:
                print("failed (cursor: {}): {}".format(start_cursor, err))
                has_next_page = False
                manager.decrease_remaining()
                logs.append("failed (cursor: {}): {}".format(start_cursor, err))
        print('{} advisories retrieved from https://github.com/advisories at {}'.format(len(self.advisories),
                                                                                        datetime.now()))
        logs.append('{} advisories retrieved from https://github.com/advisories at {}'.format(len(self.advisories),
                                                                                              datetime.now()))
        try:
            with open(PATH_LOGS_DATA(os.path.basename(__file__)), 'w') as logs_file:
                for log in logs:
                    logs_file.write("%s\n" % log)
        except IOError as err:
            print(err)


def json_to_csv(advisories_json):
    try:
        with open(PATH_GITHUB_ADVISORIES['raw'], 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["package",
                             "ecosystem",
                             "severity",
                             "cve",
                             "ghsa",
                             "summary",
                             "publishedAt",
                             "updatedAt",
                             "firstPatchedVersion",
                             "vulnerableVersionRange"])
            for advisory_report in advisories_json:
                cve = None
                ghsa = None
                identifiers = advisory_report['identifiers']
                summary = advisory_report['summary']
                for identifier in identifiers:
                    if identifier['type'] == 'GHSA':
                        ghsa = identifier['value']
                    elif identifier['type'] == 'CVE':
                        cve = identifier['value']
                published_at = advisory_report['publishedAt']
                updated_at = advisory_report['updatedAt']
                for vulnerability in advisory_report['vulnerabilities']['nodes']:
                    if vulnerability['firstPatchedVersion'] is not None:
                        first_patched_version = vulnerability['firstPatchedVersion']['identifier']
                    else:
                        first_patched_version = None
                    package = vulnerability['package']['name']
                    ecosystem = vulnerability['package']['ecosystem']
                    severity = vulnerability['severity']
                    vulnerable_version_range = vulnerability["vulnerableVersionRange"]
                    writer.writerow([package,
                                     ecosystem,
                                     severity,
                                     cve,
                                     ghsa,
                                     summary,
                                     published_at,
                                     updated_at,
                                     first_patched_version,
                                     vulnerable_version_range])
    except IOError:
        print("I/O error")


def filter_advisories():
    advisories = pd.read_csv(PATH_GITHUB_ADVISORIES['raw'],
                             index_col=False,
                             dtype={
                                 "package": str,
                                 "ecosystem": str,
                                 "severity": str,
                                 "cve": str,
                                 "ghsa": str,
                                 "summary": str,
                                 "publishedAt": str,
                                 "updatedAt": str,
                                 "firstPatchedVersion": str,
                                 "vulnerableVersionRange": str
                             }).assign(
        publishedAt=lambda d: pd.to_datetime(d['publishedAt'], infer_datetime_format=True),
        updatedAt=lambda d: pd.to_datetime(d['updatedAt'], infer_datetime_format=True)
    )
    mask_malicious_1 = advisories['firstPatchedVersion'].isnull()
    mask_malicious_2 = advisories['summary'].str.contains('Malicious Package')
    advisories_filtered = advisories[(~mask_malicious_1) & (~mask_malicious_2)]
    advisories_filtered.to_csv(PATH_GITHUB_ADVISORIES['filtered'], index=False)


if __name__ == "__main__":
    manager = TokenManagerGraphQL(GITHUB_TOKENS)
    requester = AdvisoryRequest()
    requester.query_advisories_all()
    json_to_csv(requester.advisories)
    filter_advisories()
