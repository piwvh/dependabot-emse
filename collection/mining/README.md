## Scripts

* [repositories_meta.py](repositories_meta.py)
  * The script was used to obtain the initial list of candidate projects. These projects satisfy the following set of requirements:
      * JavaScript as the primary language;
      * Not a fork;
      * Starred;
      * At least a single commit to the repository after 2019/05/31;
  * Due to the limitations on the GitHub GraphQL API queries, the script retrieves a list of repositories that match the aforementioned description iteratively based on the date of creation. That is, for each day that belongs to the time-interval 2008/01/01 - 2019/05/31, the script queries the list of projects that match the description and were created on the selected date. If the number of such projects exceeds the limit on the answer size, the script prints an alert to the console but also to the log file generated from running it.
  * Information retrieved:
    * *name*: the name of the repository;
    * *nameWithOwner*: the repository's name with owner;
    * *createdAt*: the date and time when the repository was created;
    * *pushedAt*: the date and time when the repository was last pushed to;
    * *updatedAt*: the date and time when the repository was last updated;
    * *description*: the description of the repository;
    * *forkCount*: the number of forks there are of the repository in the whole network;
    * *stargazerCount*: the count of how many stargazers there are on the repository;
    * *resourcePath*: the HTTP path for the repository;
    * *homepageUrl*: the repository's URL;
    * *isArchived*: whether or not the repository is unmaintained;
    * *isDisabled*: whether or not the repository disabled.
  * <strong>usage</strong>: ```python repositories_meta.py```
  * <strong>output</strong>: [../data/repositories/repo_meta.json](../data/repositories/repo_meta.json)
  
* [commits_meta.py](commits_meta.py)
  * The script was used to perform a quick filter on the initial list of candidate projects ([../data/repositories/repo_meta.json](../data/repositories/repo_meta.json)). 
  * Recall one of the main requirements, active maintenance, which defines that each selected project must have at least a single commit for every month that belongs to the examination period. Since this period comprises exactly one year, the requirement implies that each selected project must also have at least 12 commits during this period. Based on this implication, we perform the preliminary filtering.
  * <strong>usage</strong>: ```python commits_meta.py```
  * <strong>output</strong>: [../data/repositories/commit_meta.csv](../data/repositories/commit_meta.csv)
  
* [commits_monthly.py](commit_monthly.py)
  * The script was used to retrieve the number of commits for each unique month of the examination period and the cumulative number of commits before the examination period for each selected project with at least 12 commits during the examination period ([../data/repositories/repo_meta.json](../data/repositories/repo_meta.json)).
  * <strong>usage</strong>: ```python commits_monthly.py```
  * <strong>output</strong>: [../data/repositories/commit_monthly.csv](../data/repositories/commit_monthly.csv)
  
* [activity_constraint_repositories.py](activity_constraint_repositories.py)
  * The script was used to identify which of the following constraints each selected projects satisfies:
    * Maturity at the start of the examination period (column ```before```);
    * Active maintenance during the examination period (column ```active```);
  * <strong>usage</strong>: ```python activity_constraint_repositories.py```
  * <strong>output</strong>: [../data/repositories/repo_meta_constraint_activity.csv](../data/repositories/repo_meta_constraint_activity.csv)
  
* [manifest.py](manifest.py)
  * The script was used to identify which of the selected projects that satisfy the activity and maturity constraints contained the manifest file (```package.json```) in the root of the repository at any point in time.
  * <strong>usage</strong>: ```python manifest.py```
  * <strong>output</strong>: [../data/repositories/repo_manifest.csv](../data/repositories/repo_manifest.csv)
  
* [manifest_constraint_repositories.py](manifest_constraint_repositories.py)
  * The script was used to construct a list of the selected projects that satisfy the activity, maturity, but also manifest constraints.
  * <strong>usage</strong>: ```python manifest.py```
  * <strong>output</strong>: [../data/repositories/repos_with_manifests.csv](../data/repositories/repos_with_manifests.csv)
  
* [pull_requests.py](pull_requests.py)
  * The script was used to retrieve the meta information on all the pull requests that belong to the group of the [engineered projects](../data/repositories/engineered.csv).
  * Information retrieved:
    * *resourcePath*: the HTTP path for the pull request;
    * *checksResourcePath*: the HTTP path for the checks of the pull request;
    * *number*: the pull request number;
    * *author*: the actor who authored the pull request;
      * *login*: the username of the actor;
      * *resourcePath*: the HTTP path for this actor;
      * *url*: the HTTP URL for this actor;
    * *authorAssociation*: author's [association](https://docs.github.com/en/graphql/reference/enums#commentauthorassociation) with the repository;
    * *title*: the pull request title;
    * *bodyText*: the body rendered to text;
    * *labels*: the list of labels associated with the pull request (the first 100);
      * *name*: the label name;
      * *description*: the description of the label;
    * *createdAt*: the date and time when the pull request was created;
    * *closed*: ```true``` if the pull request is closed;
    * *state*: the [state](https://docs.github.com/en/graphql/reference/enums#pullrequeststate) of the pull request;
    * *closedAt*: the date and time when the pull request was closed;
    * *publishedAt* the date and time when the pull request was published at;
    * *mergeable* whether or not the pull request can be merged based on the existence of merge conflicts;
    * *mergedBy* the actor who merged the pull request;
      * *login*: the username of the actor;
      * *resourcePath*: the HTTP path for this actor;
      * *url*: the HTTP URL for this actor;
  * <strong>usage</strong>: ```python pull_requests.py```
  * <strong>output</strong>: [../data/pull_requests/.](../data/pull_requests)
  
* [filter_pull_requests.py](filter_pull_requests.py)
  * The script was used to filter out the pull requests that were created outside of the examination period.
  * <strong>usage</strong>: ```python filter_pull_requests.py```
  * <strong>output</strong>: [../data/pull_requests_filtered/.](../data/pull_requests_filtered)
  
* [contributors.py](contributors.py)
  * The script was used to identify the unique resource paths for the contributors that have created the final set of the collected pull requests.
  * Additionally, performs the count for each unique user resource to identify the number of [considered repositories](../data/repositories/engineered.csv) and organizations this subject has committed to
  * <strong>usage</strong>: ```python contributors.py```
  * <strong>output</strong>: [../data/repositories/contributors.csv](../data/repositories/contributors.csv)
  
* [dependabot_projects.py](dependabot_projects.py)
  * The script was used to identify the set of [engineered projects](../data/repositories/engineered.csv) that have a received at least a single Dependabot Security Update during the examination period and no pull requests of other known dependency management bots.
  * <strong>usage</strong>: ```python dependabot_projects.py```
  * <strong>output</strong>: [../data/repositories/dependabot.csv](../data/repositories/dependabot.csv)
  
* [security_updates.py](security_updates.py)
  * The script was used to retrieve additional information concerning the Dependabot Security Updates of [considered projects](../data/repositories/dependabot.csv).
  * Additional information retrieved:
    * the *actor that closed* the associated pull request
      * *login*: the username of the actor;
      * *resourcePath*: the HTTP path for this actor;
    * for the first 100 comments associated with this security update, i.e., pull request
      * *author of the comment*;
        * *login*: the username of the actor;
        * *resourcePath*: the HTTP path for this actor;
      * *bodyText*: the body rendered to text;
      * *createdAt*: the date and time when the comment was created;
  * <strong>usage</strong>: ```python security_updates.py```
  * <strong>output</strong>: [../data/security_updates/.](../data/security_updates)
  
* [filter_dependabot_projects.py](filter_dependabot_projects.py)
  * The script was used to filter out the projects with Dependabot Security Updates that target the ecosystems other than npm/yarn.
  * <strong>usage</strong>: ```python filter_dependabot_projects.py```
  * <strong>output</strong>: [../data/repositories/dependabot_filtered.csv](../data/repositories/dependabot_filtered.csv)
  
* [dataset_stat.py](dataset_stat.py)
  * The script was used to compute the characteristics of the [selected projects](../data/repositories/dependabot_filtered.csv).
  * Specifically, *min.*, *max.*, *median*, and *mean* for:
    * Number of forks;
    * Number of stars;
    * Number of core contributors;
    * Number of Dependabot Security Updates;
    * Number of commits before the examination period;
    * Number of commits during the examination period;
  * <strong>usage</strong>: ```python dataset_stat.py```
  * <strong>output</strong>: [../data/repositories/dataset_statistic.csv](../data/repositories/dataset_statistic.csv)
    
* [security_advisories.py](security_advisories.py)
  * The script was used to retrieve the security advisory records from GitHub Advisory Database.
  * Stores all of security advisories but also separately filters out the advisories that concern the intentionally malicious packages.
  * <strong>usage</strong>: ```python security_advisories.py```
  * <strong>output</strong>: [../data/github/security_advisories.csv](../data/github/security_advisories.csv), [../data/github/security_advisories_filtered.csv](../data/github/security_advisories_filtered.csv)
  
* [associate_advisory.py](associate_advisory.py)
  * The script used to associate each Dependabot Security Update with the vulnerabilities they target based on the title of the pull request.
  * Utilizes the [modified records of security advisories](../data/github/security_advisories_modified.csv) (see Appendix A in the report).
  * The script is made to account for special cases in both the security advisories and misleading pull request titles.
  * <strong>usage</strong>: ```python associate_advisory.py```
  * <strong>output</strong>: [../data/repositories/pr_vulnerabilities.csv](../data/repositories/pr_vulnerabilities.csv)
  
* [security_updates_commits.py](security_updates_commits.py)
  * The script was used to retrieve the further information on the concerned Dependabot Security Updates. In particular, the in-depth information on the commits associated with it.
  * This information includes:
    * the repository name (with owner);
    * the pull request number;
    * the url to access the pull request;
    * the oid of the parent commit based on which Dependabot has generated the first commit for this security update;
    * the date and time the parent commit was authored;
    * the oid of the first commit Dependabot has generated for this security update;
    * the date and time the first commit Dependabot has generated for this security update was authored;
    * the oid of the most recent commit Dependabot has generated for this security update;
    * the date and time the most recent commit Dependabot has generated for this security update was authored;
    * whether the associated security update was rebased by Dependabot in any point in time (the first commit oid =/ the most recent commit oid);
    * the [state](https://docs.github.com/en/graphql/reference/enums#pullrequeststate) of the associated pull request at the moment of information retrieval;
    * the oid of the commit resulted from merged the associated pull request;
    * whether or not the associated pull request was closed by Dependabot itself or not;
    * the case of closing pull request event. one of seven:
      * *0*: closed by non-Dependabot;
      * *1*: manual upgrade;
      * *2*: dependency removal;
      * *3*: can not be updated to non-vulnerable version;
      * *4*: superseded by a newer security update;
      * *5*: closed using user in-comment command;
      * *6*: anomaly/unknown/unexpected case;
    * the number of the pull request the security update was superseded by;
    * the date and time the associated pull request was created at;
    * the date and time the associated pull request was closed at;
    * the names of the files modified by the first commit Dependabot has generated for this security update;
  * <strong>usage</strong>: ```python security_updates_commits.py```
  * <strong>output</strong>: [../data/repositories/security_updates_commits.csv](../data/repositories/security_updates_commits.csv)
  
* [stars.py](stars.py)
  * The script was used to retrieve the stargazer information for each [selected project](../data/repositories/dependabot_filtered.csv).
  * <strong>usage</strong>: ```python stars.py```
  * <strong>output</strong>: [../data/repositories/stars/.](../data/repositories/stars)
  
* [network.py](network.py)
  * The script was used to retrieve the network graph for each [selected project](../data/repositories/dependabot_filtered.csv).
  * <strong>usage</strong>: ```python network.py```
  * <strong>output</strong>: [../data/network/.](../data/network)
  
* [dependency_files_commits.py](dependency_files_commits.py)
  * The script was used to retrieve the oid's of the commits that upgrade the dependency files for each [selected project](../data/repositories/dependabot_filtered.csv).
  * <strong>usage</strong>: ```python dependency_files_commits.py```
  * <strong>output</strong>: [../data/repositories/manifest_commits.csv](../data/repositories/manifest_commits.csv)

* [freeze.py](freeze.py)
  * The script was used to locally store the state (representation) of the dependency files for each retrieved [commit](../data/repositories/manifest_commits.csv) that updates the dependency files.
  * Additionally stores the state of the README.md files and identifies whether the CI files are deployed at the repository.
  * <strong>usage</strong>: ```python freeze.py```
  * <strong>output</strong>: [../data/repositories/commits_ci.csv](../data/repositories/commit_ci.csv)