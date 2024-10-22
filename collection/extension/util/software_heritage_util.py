import requests

from collection.extension.util.tokens import Tokens

# https://archive.softwareheritage.org/oidc/profile/#tokens
token_list = [
'eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJhMTMxYTQ1My1hM2IyLTQwMTUtODQ2Ny05MzAyZjk3MTFkOGEifQ.eyJpYXQiOjE3Mjc4ODA0NDksImp0aSI6IjM0ODlkY2ZkLWQ4YWItNDA3NS1hNDViLWVkZGUxZTgyMjc1OCIsImlzcyI6Imh0dHBzOi8vYXV0aC5zb2Z0d2FyZWhlcml0YWdlLm9yZy9hdXRoL3JlYWxtcy9Tb2Z0d2FyZUhlcml0YWdlIiwiYXVkIjoiaHR0cHM6Ly9hdXRoLnNvZnR3YXJlaGVyaXRhZ2Uub3JnL2F1dGgvcmVhbG1zL1NvZnR3YXJlSGVyaXRhZ2UiLCJzdWIiOiJkOWEwNjM0Ni0zYTZmLTQzMTktYWIyMC1jMWU4YWE4ZTkyMjYiLCJ0eXAiOiJPZmZsaW5lIiwiYXpwIjoic3doLXdlYiIsInNlc3Npb25fc3RhdGUiOiJlNzk3OWFkMC0xNWVlLTQ4NWItYjc0Ni1hODVkMzg5Yjc1ZjYiLCJzY29wZSI6Im9wZW5pZCBvZmZsaW5lX2FjY2VzcyBwcm9maWxlIGVtYWlsIn0.xKgmI1rqlHn872VNgpCIjgGx72nPlrjub-nMkxQuF2k',
'eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJhMTMxYTQ1My1hM2IyLTQwMTUtODQ2Ny05MzAyZjk3MTFkOGEifQ.eyJpYXQiOjE3Mjc4ODAzNTIsImp0aSI6IjEzMGUxZTNiLTBiZGQtNDJhMy05YmEzLWY2NmVjOTA2OTA5ZSIsImlzcyI6Imh0dHBzOi8vYXV0aC5zb2Z0d2FyZWhlcml0YWdlLm9yZy9hdXRoL3JlYWxtcy9Tb2Z0d2FyZUhlcml0YWdlIiwiYXVkIjoiaHR0cHM6Ly9hdXRoLnNvZnR3YXJlaGVyaXRhZ2Uub3JnL2F1dGgvcmVhbG1zL1NvZnR3YXJlSGVyaXRhZ2UiLCJzdWIiOiI1M2UzZTgyMi04YTNhLTRlN2UtOTQ4Zi1mOWJjYWMwOGYxYTAiLCJ0eXAiOiJPZmZsaW5lIiwiYXpwIjoic3doLXdlYiIsInNlc3Npb25fc3RhdGUiOiIzYTAyZjRlNS0yYmNjLTRjMWYtYjhhNy1iYzM0YTUxMzQzNTQiLCJzY29wZSI6Im9wZW5pZCBvZmZsaW5lX2FjY2VzcyBwcm9maWxlIGVtYWlsIn0.Ze5L9EUBJQ43UCdx58Er6O8lYcfD5Pub18RR_uKaLMM',
]
tokens = Tokens(token_list)


def sh_get(url: str):
    token = tokens.next()
    headers = {
        'Authorization': f'Bearer {token}',
    }

    print('GET: ' + url)
    response = requests.get(url, headers=headers)
    tokens.update(token, int(response.headers['X-RateLimit-Remaining']), int(response.headers['X-RateLimit-Reset']))
    if response.status_code == 403:
        return sh_get(url)

    return response


def sh_get_revision(git_hash: str):
    sh_url = 'https://archive.softwareheritage.org/api/1/revision/' + git_hash
    response = sh_get(sh_url)

    return response.json()


def sh_get_directory(directory_url: str):
    response = sh_get(directory_url)

    return response.json()


def sh_get_raw_data(git_hash: str):
    sh_url = f'https://archive.softwareheritage.org/api/1/content/sha1_git:{git_hash}/raw/'

    return sh_get(sh_url).text
