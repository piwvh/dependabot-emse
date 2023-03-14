import os
from datetime import datetime

DIR_ROOT = os.path.dirname(os.path.abspath(__file__))

DIR_DATA = os.path.join(DIR_ROOT, 'data')

DIR_REPOSITORIES = os.path.join(DIR_DATA, 'repositories')

DIR_PRS = os.path.join(DIR_DATA, 'pull_requests')

DIR_UPDATES = os.path.join(DIR_DATA, 'security_updates')

DIR_CLONED = os.path.join(os.path.dirname(DIR_ROOT), 'cloned3')

DIR_NETWORK = os.path.join(DIR_DATA, 'network')

DIR_FREEZE = os.path.join(os.path.dirname(DIR_ROOT), 'frozen')

DIR_GITHUB = os.path.join(DIR_DATA, 'github')

DIR_PRS_FILTERED = os.path.join(DIR_DATA, 'pull_requests_filtered')

DIR_LOGS = os.path.join(DIR_ROOT, 'logs')

DIR_RESULTS = os.path.join(DIR_ROOT, 'results')

DIR_REAPER = os.path.join(DIR_ROOT, 'reaper')

DIR_VULNERABILITY_FIXES = os.path.join(DIR_ROOT, 'vulnerability_fixes')

KNOWN_BOTS = ['/apps/dependabot',
              '/apps/dependabot-preview',
              '/snyk-bot',
              '/apps/renovate',
              '/renovate-bot',
              '/apps/greenkeeper']


def PATH_LOGS_DATA(file_name):
    return os.path.join(DIR_LOGS, file_name.replace(".py", "@") + datetime.now().strftime("%Y%m%d%H%M%S") + ".txt")


PATH_REPOSITORIES_DATA = {
    'repo_meta': os.path.join(DIR_REPOSITORIES, 'repo_meta.json'),
    'commit_meta': os.path.join(DIR_REPOSITORIES, 'commit_meta.csv'),
    'commit_monthly': os.path.join(DIR_REPOSITORIES, 'commit_monthly.csv'),
    'repo_constraint_activity': os.path.join(DIR_REPOSITORIES, 'repo_meta_constraint_activity.csv'),
    'repo_constraint_prs': os.path.join(DIR_REPOSITORIES, 'repo_meta_constraint_prs.csv'),
    'repo_manifest': os.path.join(DIR_REPOSITORIES, 'repo_manifest.csv'),
    'repo_stars': os.path.join(DIR_REPOSITORIES, 'repo_stars.csv'),
    'contributors': os.path.join(DIR_REPOSITORIES, 'contributors.csv'),
    'repos_with_manifests': os.path.join(DIR_REPOSITORIES, 'repos_with_manifests.csv'),
    'engineered_repos': os.path.join(DIR_REPOSITORIES, 'engineered.csv'),
    'dependabot_repos': os.path.join(DIR_REPOSITORIES, 'dependabot.csv'),
    'dependabot_filtered_repos': os.path.join(DIR_REPOSITORIES, 'dependabot_filtered.csv'),
    'statistic': os.path.join(DIR_REPOSITORIES, 'dataset_statistic.csv'),
    'pr_vulnerabilities': os.path.join(DIR_REPOSITORIES, 'pr_vulnerabilities.csv'),
    'pr_vulnerabilities2': os.path.join(DIR_REPOSITORIES, 'pr_vulnerabilities_old_2.csv'),
    'security_updates_commits': os.path.join(DIR_REPOSITORIES, 'security_updates_commits.csv'),
    'manifest_commits': os.path.join(DIR_REPOSITORIES, 'manifest_commits.csv'),
    'manifest_commits_times': os.path.join(DIR_REPOSITORIES, 'manifest_commits_times.csv'),
    'commit_logs': os.path.join(DIR_REPOSITORIES, 'commit_logs2.csv'),
    'commit_ci': os.path.join(DIR_REPOSITORIES, 'commit_ci.csv'),
    'commit_ci2': os.path.join(DIR_REPOSITORIES, 'commit_ci2.csv'),
    'commit_ci3': os.path.join(DIR_REPOSITORIES, 'commit_ci3.csv'),
    'commit_ci4': os.path.join(DIR_REPOSITORIES, 'commit_ci4.csv'),
    'workspace_presence': os.path.join(DIR_REPOSITORIES, 'workspace_presence.csv'),
    'workspace_presence_per_commit': os.path.join(DIR_REPOSITORIES, 'workspace_presence_per_commit.csv'),
    'workspace_paths': os.path.join(DIR_REPOSITORIES, 'workspace_paths.csv')
}

PATH_VULNERABILITY_FIXES = {
    'validation': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'validation.csv'),
    'validation2': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'validation2.csv'),
    'fixes': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'fixes.csv'),
    'fixes_labels': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'fixes_labels.csv'),
    'fixes_labels_reduced': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'fixes_labels_reduced.csv'),
    'fixes_labels_round_2': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'fixes_labels_round_2.csv'),
    # hamid
    'fixes_labels_round_2_updated': os.path.join(DIR_ROOT, 'hamid', 'data', 'fixes_labels_round_2_updated.csv'),
    'fixes_commits_times': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'fixes_commits_times.csv'),
    'stage_1_second_rater': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'second_rater', 'stage_1.csv'),
    'stage_1_second_rater_true': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'second_rater', 'stage_1_true.csv'),
    'stage_1_second_rater_doc': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'second_rater', 'stage_1.docx'),
    'stage_2_second_rater': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'second_rater', 'stage_2.csv'),
    'stage_2_second_rater_true': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'second_rater', 'stage_2_true.csv'),
    'stage_2_second_rater_2': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'second_rater', 'stage_2_rater_2.csv'),
    'stage_2_second_rater_doc': os.path.join(DIR_VULNERABILITY_FIXES, 'data', 'second_rater', 'stage_2.docx'),
}

PATH_GITHUB_ADVISORIES = {
    'raw': os.path.join(DIR_GITHUB, 'security_advisories.csv'),
    'filtered': os.path.join(DIR_GITHUB, 'security_advisories_filtered.csv'),
    'modified': os.path.join(DIR_GITHUB, 'security_advisories_modified.csv')
}

ECOSYSTEM_MAPPING = {
    'npm': ['package-lock.json', 'package.json', 'yarn.lock', 'npm-shrinkwrap.json'],
    'maven': ['pom.xml'],
    'dotnet': ['.csproj', '.vbproj', '.nuspec', '.vcxproj', '.fsproj', 'packages.config'],
    'composer': ['composer.json', 'composer.lock'],
    'pip': ['requirements.txt', 'pipfile', 'pipfile.lock', 'setup.py', '.txt'],
    'rubygems': ['Gemfile.lock', 'Gemfile', '.gemspec'],
}

FEATURES_SUBSET = ['continuous_integration',
                   'community',
                   'documentation',
                   'history',
                   'license',
                   'unit_test']

FEATURES_FULL = ['architecture',
                 'continuous_integration',
                 'community',
                 'documentation',
                 'history',
                 'license',
                 'management',
                 'unit_test']

GITHUB_TOKENS = ['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']