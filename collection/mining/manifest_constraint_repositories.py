import sys
import pandas as pd

sys.path.append('..')
from finder import *  # noqa: E402

if __name__ == '__main__':
    manifests = pd.read_csv(PATH_REPOSITORIES_DATA['repo_manifest'], index_col=False)
    has_manifest = manifests['package.json']
    constrained = pd.DataFrame({'repository': manifests[has_manifest]['repository']})
    constrained.to_csv(PATH_REPOSITORIES_DATA['repos_with_manifests'], index=False)