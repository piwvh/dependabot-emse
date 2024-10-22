import requests

from collection.extension.util.tokens import Tokens

token_list = ['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']

tokens = Tokens(token_list)


def github_get(url: str):
    token = tokens.next()
    headers = {
        'Authorization': f'token {token}',
    }

    response = requests.get(url, headers=headers)
    tokens.update(token, int(response.headers['X-RateLimit-Remaining']), int(response.headers['X-RateLimit-Reset']))
    if response.status_code == 403:
        return github_get(url)

    return response


def http_repository_exists(repo: str):
    github_url = f'https://api.github.com/repos/{repo}'
    response = github_get(github_url)
    body = response.json()

    return response.status_code == 200 and 'id' in body

