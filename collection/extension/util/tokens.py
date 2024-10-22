import datetime
import time


class Tokens:
    tokens_state = {}

    def __init__(self, tokens):
        for t in tokens:
            self.tokens_state[t] = {'remaining': 1, 'reset': (datetime.datetime.now() + datetime.timedelta(days=1)).timestamp()}

    def next(self) -> str:
        while True:
            min_wait = 999
            for token_id, state in self.tokens_state.items():
                if state['remaining'] > 0 or datetime.datetime.now() > datetime.datetime.fromtimestamp(state['reset']):
                    return token_id

                wait = (datetime.datetime.fromtimestamp(state['reset']) - datetime.datetime.now()).seconds
                if wait < min_wait:
                    min_wait = wait

            print("Waiting for %d seconds..." % (min_wait + 1))
            time.sleep(min_wait + 1)

    def update(self, token_id: str, remaining: int, reset: int):
        self.tokens_state[token_id]['remaining'] = remaining
        self.tokens_state[token_id]['reset'] = reset
