import base64
import hashlib
import hmac
import json
import requests
import time
import urllib.parse


class DiscoverTextApi():
    API_VERSION = "v1"
    BASE_URL = "https://api.discovertext.com"

    def __init__(self, credential_file=None,
                 api_key=None, api_secret=None, hostname=None,
                 username=None, password=None, api_base_url=None):

        if (credential_file):
            with open(credential_file) as credential_file_handle:
                credentials = json.load(credential_file_handle)
                self._api_key = credentials["api_key"]
                self._api_secret = credentials["api_secret"]
                self._hostname = credentials["hostname"]
                if "username" in credentials:
                    self._username = credentials["username"]
                if "password" in credentials:
                    self._password = credentials["password"]
        else:
            self._api_key = api_key
            self._api_secret = api_secret
            self._hostname = hostname
            self._username = username
            self._password = password

        self._jwt_token = None
        self._jwt_token_renewal = 0
        self._jwt_token_exp = 0

        if not self._api_key:
            raise "missing api key"
        if not self._api_secret:
            raise "missing api secret key"
        if not self._hostname:
            raise "missing hostname"

        base_url = DiscoverTextApi.BASE_URL if not api_base_url else api_base_url
        self._api_base_url = f'{base_url}/api/{DiscoverTextApi.API_VERSION}'

    def _check_jwt(self):
        if not self._jwt_token or self._jwt_token_renewal == 0:
            raise "no token issued"
        if self._jwt_token_exp < int(time.time()):
            raise "expired token"

    def _check_renew(self):
        self._check_jwt()
        if self._jwt_token_renewal < int(time.time()):
            self.renew_token()

    def _get_request_response(self, response):
        if not response:
            raise "no response"
        response.raise_for_status()
        return response.text

    def _send_get(self, request_url, query_params=None, check_credentials=True):
        if check_credentials:
            self._check_renew()
        request_headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {self._jwt_token}'
        }
        response = requests.get(url=request_url,
                                params=query_params,
                                headers=request_headers
                                )
        return self._get_request_response(response)

    def _send_post(self, request_url, post_data=None, query_params=None, check_credentials=True):
        if check_credentials:
            self._check_renew()
        request_headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {self._jwt_token}'
        }
        response = requests.post(url=request_url,
                                 json=json.dumps(post_data),
                                 params=query_params,
                                 headers=request_headers
                                 )
        return self._get_request_response(response)

    def _set_token_and_renewal(self, token):
        self._jwt_token = token
        # set token renewal to now + 6 minutes... gives us a 4 minute window
        self._jwt_token_exp = int(time.time()) + 600
        self._jwt_token_renewal = int(time.time()) + 360

    def login(self, username=None, password=None):
        '''
        login the user and get the initial JWT

        https://api.discovertext.com/Docs/GettingStarted/Authentication
        '''
        login_username = self._username if username is None else username
        login_password = self._password if password is None else password
        if not login_username:
            raise "Username not set"
        if not login_password:
            raise "Password not set"
        nonce = int(time.time())
        sig_string = f'{self._api_key}:{self._hostname}:{login_username}:{login_password}:{nonce}'
        message = bytes(sig_string, 'utf-8')
        secret = bytes(self._api_secret, 'utf-8')
        signature = base64.b64encode(
            hmac.new(secret, message, digestmod=hashlib.sha256).digest()).decode('utf-8')

        request_url = f'{self._api_base_url}/login'
        request_data = {
            "apiKey": self._api_key,
            "hostname": self._hostname,
            "username": login_username,
            "password": login_password,
            "nonce": nonce,
            "signature": signature
        }

        response = requests.post(url=request_url, json=request_data)
        response.raise_for_status()
        self._set_token_and_renewal(response.text)

    def get_oauth_authorize_url(self, redirect_url):
        request_url = f'{self._api_base_url}/login/oauth'
        formatted_redirect_uri = urllib.parse.quote(redirect_url, safe='')
        return f'{request_url}?response_type=code&client_id={self._api_key}&redirect_uri={formatted_redirect_uri}&scope=read&hostname={self._hostname}'

    def get_oauth_access_token_url(self, auth_code, redirect_url):
        request_url = f'{self._api_base_url}/login/token'
        response = requests.get(url=request_url,
                                params={
                                    "client_id": self._api_key,
                                    "client_secret": self._api_secret,
                                    "grant_type": "authorization_code",
                                    "code": auth_code,
                                    "redirect_uri": redirect_url
                                })
        response.raise_for_status()
        response_item = response.json
        self._set_token_and_renewal(response.json["token"])

    def renew_token(self):
        request_url = f'{self._api_base_url}/login/renew'
        request_headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {self._jwt_token}'
        }
        response = requests.get(url=request_url,
                                headers=request_headers
                                )
        response.raise_for_status()
        self._set_token_and_renewal(response.text)

    def get_unit_types(self):
        request_url = f'{self._api_base_url}/system/unitTypes'
        return json.loads(self._send_get(request_url))

    def get_projects(self, offset=0, limit=20):
        request_url = f'{self._api_base_url}/projects'
        return json.loads(self._send_get(request_url, {
            "offset": offset,
            "limit": limit
        }))

    def get_project_archives(self, project_id, offset=0, limit=20):
        request_url = f'{self._api_base_url}/projects/{project_id}/archives'
        return json.loads(self._send_get(request_url, {
            "offset": offset,
            "limit": limit
        }))

    def get_archive(self, archive_id):
        request_url = f'{self._api_base_url}/archives/{archive_id}'
        return json.loads(self._send_get(request_url, {}))

    def get_archive_units(self, archive_id, offset=0, limit=20, include_metadata=True):
        request_url = f'{self._api_base_url}/archives/{archive_id}/units'
        params = {
            "offset": offset,
            "limit": limit,
            "includeMetadata": "true" if include_metadata else "false"
        }
        return json.loads(self._send_get(request_url, params))

    def get_project_buckets(self, project_id, offset=0, limit=20):
        request_url = f'{self._api_base_url}/projects/{project_id}/buckets'
        return json.loads(self._send_get(request_url, {
            "offset": offset,
            "limit": limit
        }))

    def get_bucket(self, bucket_id):
        request_url = f'{self._api_base_url}/buckets/{bucket_id}'
        return json.loads(self._send_get(request_url, {}))

    def get_bucket_units(self, bucket_id, offset=0, limit=20, include_metadata=True):
        request_url = f'{self._api_base_url}/buckets/{bucket_id}/units'
        params = {
            "offset": offset,
            "limit": limit,
            "includeMetadata": "true" if include_metadata else "false"
        }
        return json.loads(self._send_get(request_url, params))

    def get_codeset_listing(self, offset=0, limit=20):
        request_url = f'{self._api_base_url}/codesets'
        params = {
            "offset": offset,
            "limit": limit
        }
        return json.loads(self._send_get(request_url, params))

    def get_codeset_item(self, codeset_id):
        request_url = f'{self._api_base_url}/codesets/{codeset_id}'
        return json.loads(self._send_get(request_url, {}))

    def get_codeset_data(self, codeset_id, offset=0, limit=20):
        request_url = f'{self._api_base_url}/codesets/{codeset_id}/data'
        params = {
            "offset": offset,
            "limit": limit
        }
        return json.loads(self._send_get(request_url, params))
