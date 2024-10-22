import json
import os

from pyarn import lockfile

from collection.extension.util.general_util import get_package_version_history


def yarn_file_to_json(file_path: str):
    return json.loads(lockfile.Lockfile.from_file(file_path).to_json())


def get_package_version_from_dep_file(package: str, json_file: dict):
    for key in ['dependencies', 'devDependencies']:
        if key not in json_file:
            continue

        if package in json_file[key]:
            return json_file[key][package]

    return None


def get_package_version_from_lock_file(package: str, lock_file_type: str, file_content: dict):
    if file_content is None:
        return None

    if lock_file_type == 'yarn.lock':
        for key in file_content:
            # special case example: "package@v1, package@v2"
            packages = key.split(',')
            for p in packages:
                p = p.strip()
                parts = p.rsplit('@', 1)
                if len(parts) == 2 and parts[0] == package:
                    return file_content[key]['version']
    else:
        if 'dependencies' in file_content and package in file_content['dependencies']:
            return file_content['dependencies'][package]['version']

    return None


def get_package_versions(package: str) -> list:
    versions = []
    for item in get_package_version_history(package):
        versions.append(item['version'])

    return versions


def semver_coerce(ver: str):
    command = f'docker run dependabot_node:1.0.0 bash -c "node semver.js coerce \'{ver}\'"'
    output = os.popen(command).read()

    json_output = json.loads(output)

    return json_output['output']['version'] if json_output['output'] is not None else None


def semver_min_satisfying(versions: list, criteria: str):
    version_str = ' '.join(versions)

    command = f'docker run dependabot_node:1.0.0 bash -c "node semver.js minSatisfying {version_str} \'{criteria}\'"'
    output = os.popen(command).read()

    json_output = json.loads(output)

    return json_output['output'].strip() if json_output['output'] is not None else None
