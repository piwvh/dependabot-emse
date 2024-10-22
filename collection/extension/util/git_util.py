from pydriller import Git, Repository

from collection.extension.util.general_util import load_json_file


def git_checkout(rdir: str, commit_hash: str) -> Git:
    gr = Git(rdir)
    gr.checkout(commit_hash)

    return gr


def load_json_file_from_commit(rdir: str, filepath: str, commit_hash: str):
    gr = git_checkout(rdir, commit_hash)
    commit = gr.get_commit(commit_hash)

    return load_json_file(filepath), commit


def get_commits_after(repo_path, start_commit_hash):
    commits_after = []
    for commit in Repository(repo_path, from_commit=start_commit_hash).traverse_commits():
        commits_after.append(commit)

    return commits_after
