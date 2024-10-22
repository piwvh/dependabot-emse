import csv
import datetime
import json
import os
from typing import Optional

import pandas
from packaging.version import parse as parse_version, Version
import pandas as pd


def load_file(filepath: str):
    with open(filepath) as f:
        return f.readlines()


def load_json_file(filepath: str):
    with open(filepath) as jf:
        return json.load(jf)


def write_file(filepath: str, content: str):
    with open(filepath, "w") as text_file:
        text_file.write(content)


def get_package_version_history(package: str) -> list:
    command = f'docker run node:21.2.0 bash -c "npm view {package} time --json"'
    output = os.popen(command).read()

    versions = []
    for key, value in json.loads(output).items():
        if key in ['modified', 'created']:
            continue
        versions.append({'version': key, 'date': value})

    #sorted(versions, key=lambda x: x['date'])

    return versions


def get_package_latest_version(package: str, target_date: datetime.datetime):
    version_history = get_package_version_history(package)

    latest_version = version_history[0]
    latest_stable_version = None
    for ver in version_history:
        if str_to_date(ver['date']).timestamp() > target_date.timestamp():
            break

        try:
            ver_parsed = parse_version(ver['version'])
            if not ver_parsed.is_devrelease and not ver_parsed.is_prerelease and (
                    latest_stable_version is None or ver_parsed > parse_version(latest_stable_version['version'])):
                latest_stable_version = ver
            if ver_parsed > parse_version(latest_version['version']):
                latest_version = ver
        except:
            continue

    return latest_version, latest_stable_version


def compare_versions(version1_str, version2_str):
    v1 = Version(version1_str)
    v2 = Version(version2_str)

    if v1.major != v2.major:
        return 'major'
    # Compare minor versions
    elif v1.minor != v2.minor:
        return 'minor'
    # Compare patch versions
    elif v1.micro != v2.micro:
        return 'patch'
    else:
        return ''


# G 2020-01-22 15:51:10-03:00 -> %Y-%m-%d %H:%M:%S%z
# SE 2019-09-12T17:16:59+05:00 -> %Y-%m-%dT%H:%M:%S%z
def str_to_date(s: str, _format: str = '%Y-%m-%dT%H:%M:%S.%fZ') -> Optional[datetime.datetime]:
    if s is None or s == '':
        return None

    return datetime.datetime.strptime(s, _format)


def write_csv(filepath: str, data: list, header: list):
    with open(filepath, 'w') as f:
        write = csv.writer(f)
        write.writerow(header)
        write.writerows(data)


def create_file(path: str, text: str):
    with open(path, "w") as text_file:
        text_file.write(text)


def write_large_csv(filename: str, fields: list, data: list):
    created = False
    if not os.path.isfile(filename):
        create_file(filename, '')
        created = True

    with open(filename, 'a') as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fields
        )

        if created:
            writer.writeheader()
        writer.writerows(data)



def merge_csv(*paths: str):
    output = None
    for path in paths:
        df = pandas.read_csv(path)
        if output is None:
            output = df
        else:
            output = pandas.concat([output, df], ignore_index=True)

    return output


def create_df(columns: list, data: list = None):
    return pd.DataFrame(data, columns=columns)


def append_row_to_df(data: pd.DataFrame, row: list):
    return pd.concat([data, create_df(list(data.columns), [row])]).reset_index(drop=True)


def get_max_severity(severity_list) -> str:
    for sev in ['CRITICAL', 'HIGH', 'MODERATE', 'LOW']:
        if sev in severity_list:
            return sev

    raise Exception('Invalid severity list')
