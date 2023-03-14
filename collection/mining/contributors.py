import sys
import json
from tqdm import tqdm
import pandas as pd
import csv

sys.path.append('..')
from finder import *  # noqa: E402

if __name__ == '__main__':
    repo_names = pd.read_csv(PATH_REPOSITORIES_DATA['engineered_repos'])['repository'].to_list()
    contributors_project = dict()
    contributors_org = dict()
    contributor_names = set()
    for repo in tqdm(repo_names):
        slug = repo.split('/')
        org = slug[0]
        project = slug[1]
        try:
            with open(os.path.join(DIR_PRS_FILTERED, repo.replace('/', '@') + '.json'), 'r') as json_file:
                prs = json.load(json_file)
                for pr in prs:
                    try:
                        contributor = (pr['author']['resourcePath'])
                        contributor_names.add(contributor)
                        if contributor in contributors_project:
                            contributors_project[contributor].add(project)
                        else:
                            contributors_project[contributor] = set()
                            contributors_project[contributor].add(project)
                        if contributor in contributors_org:
                            contributors_org[contributor].add(org)
                        else:
                            contributors_org[contributor] = set()
                            contributors_org[contributor].add(org)
                    except TypeError:
                        pass  # deleted account
        except IOError as err:
            pass  # no PRs
    contributor_final = dict()
    for name in tqdm(contributor_names):
        projects = len(contributors_project[name])
        orgs = len(contributors_org[name])
        contributor_final[name] = (projects, orgs)
    contributor_final = {k: v for k, v in sorted(contributor_final.items(), key=lambda item: item[1][1], reverse=True)}
    try:
        with open(PATH_REPOSITORIES_DATA['contributors'], 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['contributor', 'projects', 'orgs'])
            for key, value in contributor_final.items():
                writer.writerow([key, value[0], value[1]])
    except IOError as err:
        print(err)



