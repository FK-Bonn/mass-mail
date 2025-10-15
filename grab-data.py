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


def get_open_request(fs_id: str, afsg_requests: list[dict], semester_filter: Optional[str]) -> str:
    if not semester_filter:
        return ''
    for request in afsg_requests:
        if request['fs'] == fs_id and request['semester'] == semester_filter and request['status'] in ('EINGEREICHT', 'GESTELLT'):
            return request['request_id']


def has_no_request(fs_id: str, afsg_requests: list[dict], semester_filter: Optional[str]) -> bool:
    if not semester_filter:
        return False
    for request in afsg_requests:
        if request['fs'] == fs_id and request['semester'] == semester_filter:
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--categories', choices=['finanzen', 'fsl', 'kontakt'], required=True, nargs='+')
    parser.add_argument('--financial-year-start')
    parser.add_argument('--open-afsg')
    parser.add_argument('--no-afsg')
    parser.add_argument('--permissions', action='store_true')
    args = parser.parse_args()
    token = get_token()
    data = get_fsdata(token)
    permissions = get_permissions(token)
    afsg_requests = get_afsg_requests()
    print('fs_id\tfs_name\taddresses', end='')
    if args.permissions:
        print('\tpermissions_json', end='')
    if args.open_afsg:
        print('\trequest_id', end='')
    print('')
    for fs_id, fs_data in data.items():
        fs_name = fs_data['base']['data']['name']
        financial_year_start = fs_data['base']['data']['financial_year_start']
        open_request = get_open_request(fs_id, afsg_requests, args.open_afsg)
        no_request = has_no_request(fs_id, afsg_requests, args.no_afsg)
        include_this_fs = (financial_year_start == args.financial_year_start or not args.financial_year_start)
        include_this_fs = include_this_fs and (not args.open_afsg or open_request)
        include_this_fs = include_this_fs and (not args.no_afsg or no_request)
        if include_this_fs:
            address_set = set()
            for element in fs_data['protected']['data']['email_addresses']:
                for category in args.categories:
                    if category in element['usages']:
                        address_set.add(element["address"])
            addresses = ",".join(sorted(address_set))
            permissions_json = json.dumps(permissions[fs_id])
            print(f'{fs_id}\t{fs_name}\t{addresses}', end='')
            if args.permissions:
                print(f'\t{permissions_json}', end='')
            if args.open_afsg:
                print(f'\t{open_request}', end='')
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
        if username == 'finanzreferat':
            continue
        full_name = data_for_user['full_name']
        for permission in data_for_user['permissions']:
            data_for_fs[permission['fs']].append({**permission, 'username': username, 'full_name': full_name})
    return data_for_fs


def get_afsg_requests() -> list[dict]:
    response = requests.get(BASE + '/api/v1/payout-request/afsg')
    data = response.json()
    return data


if __name__ == '__main__':
    main()
