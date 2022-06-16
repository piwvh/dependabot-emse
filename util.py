import pandas as pd
from const import *


def load_advisory_database():
    database = pd.read_csv(CSV_DATA['security_advisories_modified'],
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
    npm_mask = database['ecosystem'] == 'NPM'
    return database[npm_mask]
