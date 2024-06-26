#! /usr/bin/env python3
import argparse
import getpass
import json
from pathlib import Path
from typing import Optional, Dict
from collections import defaultdict

import requests

TOKEN_CACHE_FILE = Path(__file__).with_name('.token')
BASE = 'https://fsen.datendrehschei.be'
API_BASE = f'{BASE}/api/v1'


def headers(token: str) -> Dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def token_is_valid(token: str) -> bool:
    result = requests.get(API_BASE + '/user/me', headers=headers(token))
    return result.status_code == 200


def get_cached_token() -> Optional[str]:
    if not TOKEN_CACHE_FILE.is_file():
        return None
    token = TOKEN_CACHE_FILE.read_text()
    if not token_is_valid(token):
        return None
    return token


def get_token():
    if cached_token := get_cached_token():
        return cached_token
    status_code = 0
    response = None
    while status_code != 200:
        username = input('username for fsen.datendrehschei.be: ')
        password = getpass.getpass()
        response = requests.post(API_BASE + '/token', data={'username': username, 'password': password})
        status_code = response.status_code
    token = response.json()['access_token']
    TOKEN_CACHE_FILE.write_text(token)
    return token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--categories', choices=['finanzen', 'fsl', 'kontakt'], required=True, nargs='+')
    parser.add_argument('--financial-year-start')
    parser.add_argument('--permissions', action='store_true')
    args = parser.parse_args()
    token = get_token()
    data = get_fsdata(token)
    permissions = get_permissions(token)
    public_data = get_public_data()
    print('fs_id\tfs_name\taddresses', end='')
    if args.permissions:
        print('\tpermissions_json', end='')
    print('')
    for fs_id, fs_data in public_data['studentBodies'].items():
        fs_name = fs_data['name']
        financial_year_start = fs_data['financialYearStart']
        if financial_year_start == args.financial_year_start or not args.financial_year_start:
            address_set = set()
            for element in data[fs_id]['protected_data']['data']['email_addresses']:
                for category in args.categories:
                    if category in element['usages']:
                        address_set.add(element["address"])
            addresses = ",".join(sorted(address_set))
            permissions_json = json.dumps(permissions[fs_id])
            print(f'{fs_id}\t{fs_name}\t{addresses}', end='')
            if args.permissions:
                print(f'\t{permissions_json}', end='')
            print('')


def get_fsdata(token: str) -> Dict:
    response = requests.get(API_BASE + '/data', headers=headers(token))
    data = response.json()
    return data

def get_permissions(token: str) -> Dict:
    response = requests.get(API_BASE + '/user', headers=headers(token))
    data = response.json()
    data_for_fs = defaultdict(list)
    for username, data_for_user in data.items():
        for permission in data_for_user['permissions']:
            data_for_fs[permission['fs']].append({**permission, 'username': username})
    return data_for_fs


def get_public_data() -> Dict:
    response = requests.get(BASE + '/data/data.json')
    data = response.json()
    return data


if __name__ == '__main__':
    main()
