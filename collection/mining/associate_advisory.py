import sys
import execjs
import pandas as pd
import csv
from tqdm import tqdm
import json

sys.path.append('..')
from finder import *  # noqa: E402


class SemVer:
    def __init__(self):
        self.semver = execjs.compile(
            """
            const semver = require('semver');
            function satisfies(x, y) {
                return semver.intersects(x, y);
            }
            """
        )

    def satisfies(self, version, constraint):
        return self.semver.call("satisfies", version, constraint)


def parse_time(time_string):
    return datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')


if __name__ == '__main__':
    repos_with_other = set()
    semver = SemVer()
    repo_names = pd.read_csv(PATH_REPOSITORIES_DATA['dependabot_filtered_repos'], index_col=False)['repository'].tolist()
    advisories = pd.read_csv(PATH_GITHUB_ADVISORIES['modified'],
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
    npm_mask = advisories['ecosystem'] == 'NPM'
    advisories = advisories[npm_mask]
    with open(PATH_REPOSITORIES_DATA['pr_vulnerabilities'], 'w') as output:
        writer = csv.writer(output)
        writer.writerow(['repository',
                         'number',
                         'url',
                         'date',
                         'state',
                         'package',
                         'from',
                         'to',
                         'vulnerabilities',
                         'severities',
                         'maximal_severity'])
        for repo in tqdm(repo_names):
            with open(os.path.join(DIR_UPDATES, repo.replace('/', '@') + '.json'), 'r', encoding='utf-8') as json_file:
                raw_prs = json.load(json_file)
                for pr in raw_prs:
                    url = 'https://github.com/{}/pull/{}'.format(repo, pr['number'])
                    vulnerability_severity = []
                    vulnerability_ghsa = []
                    title = pr['title']
                    created_at = parse_time(pr['createdAt'])
                    title_lower_case = title.lower()
                    bump_index = title_lower_case.find('bump', 0)
                    title_filtered = title[bump_index:]
                    title_words = title_filtered.split(' ')
                    try:
                        package = title_words[1]
                        from_version = title_words[3]
                        to_version = title_words[5]
                    except IndexError:  # https://github.com/ForestAdmin/lumber/pull/402
                        package = 'acorn'
                        from_version = '5.7.3'
                        to_version = '5.7.4'
                    # special cases: wrong 'from_version' in title due to modifications imposed on transitive deps
                    if (repo == 'CatalysmsServerManager/7-days-to-die-server-manager') & (str(pr['number']) == '48'):
                        from_version = '5.7.3'
                    elif (repo == 'parcel-bundler/parcel') & (str(pr['number']) == '4330'):
                        from_version = '7.1.0'
                    elif (repo == 'Giveth/feathers-giveth') & (str(pr['number']) == '167'):
                        from_version = '7.1.0'
                    elif (repo == 'instacart/Snacks') & (str(pr['number']) == '401'):
                        from_version = '5.5.0'
                    elif (repo == 'gladly-team/tab') & (str(pr['number']) == '746'):
                        from_version = '5.5.3'
                    elif (repo == 'serverless/plugins') & (str(pr['number']) == '315'):
                        from_version = '5.7.3'
                    elif (repo == 'Viglino/ol-ext') & (str(pr['number']) == '429'):
                        from_version = '6.0.4'
                    elif (repo == 'gaearon/react-hot-loader') & (pr['number'] == '1436'):
                        from_version = '5.7.3'
                    time_mask = advisories['publishedAt'] <= created_at
                    package_mask = advisories['package'] == package
                    concerned_advisories = advisories[time_mask & package_mask]
                    for index, advisory in concerned_advisories.iterrows():
                        constraint = advisory['vulnerableVersionRange'].replace(',', '')
                        patched = '>= ' + advisory['firstPatchedVersion']
                        # minimist special case
                        if (package == 'minimist') & (to_version == '1.2.2'):
                            if semver.satisfies(from_version, constraint) & semver.satisfies('1.2.3', patched):
                                vulnerability_severity.append(advisory['severity'])
                                vulnerability_ghsa.append(advisory['ghsa'])
                        # ws special case
                        elif (package == 'ws') & (from_version == '1.1.5'):
                            if semver.satisfies(to_version, '>3.3.0'):
                                if parse_time(pr['createdAt']) <= parse_time("2019-12-09T23:59:59Z"):
                                    if advisory['ghsa'] == 'GHSA-5v72-xg48-5rpm':
                                        vulnerability_severity.append(advisory['severity'])
                                        vulnerability_ghsa.append(advisory['ghsa'])
                        # kind-of special case
                        elif package == 'kind-of':
                            if semver.satisfies(from_version, '<=6.0.2'):
                                if semver.satisfies(to_version, '>6.0.2'):
                                    if parse_time(pr['createdAt']) <= parse_time("2020-11-06T23:59:59Z"):
                                        if advisory['ghsa'] == 'GHSA-6c8f-qphg-qjgp':
                                            vulnerability_severity.append(advisory['severity'])
                                            vulnerability_ghsa.append(advisory['ghsa'])
                        else:
                            if semver.satisfies(from_version, constraint) & semver.satisfies(to_version, patched):
                                vulnerability_severity.append(advisory['severity'])
                                vulnerability_ghsa.append(advisory['ghsa'])
                    maximal_severity = 0
                    for severity in vulnerability_severity:
                        if severity == 'LOW':
                            maximal_severity = max(maximal_severity, 1)
                        elif severity == 'MODERATE':
                            maximal_severity = max(maximal_severity, 2)
                        elif severity == 'HIGH':
                            maximal_severity = max(maximal_severity, 3)
                        elif severity == 'CRITICAL':
                            maximal_severity = max(maximal_severity, 4)
                    if maximal_severity == 0:
                        maximal_severity = None
                    elif maximal_severity == 1:
                        maximal_severity = 'LOW'
                    elif maximal_severity == 2:
                        maximal_severity = 'MODERATE'
                    elif maximal_severity == 3:
                        maximal_severity = 'HIGH'
                    elif maximal_severity == 4:
                        maximal_severity = 'CRITICAL'
                    writer.writerow([repo,
                                     pr['number'],
                                     url,
                                     pr['createdAt'],
                                     pr['state'],
                                     package,
                                     from_version,
                                     to_version,
                                     vulnerability_ghsa,
                                     vulnerability_severity,
                                     maximal_severity])

