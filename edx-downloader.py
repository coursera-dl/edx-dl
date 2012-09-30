#!/usr/bin/env python3
import os, pprint, sys, math, urllib.request, urllib.parse, http.cookiejar, shutil, json
from datetime import timedelta, datetime, time
EDX_HOMEPAGE = 'https://www.edx.org'
LOGIN_API = 'https://www.edx.org/login'
save_path = 'temp'
user_email = sys.argv[1]
user_pswd = sys.argv[2]

#Get Token
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)
response = opener.open(EDX_HOMEPAGE)
set_cookie = {}
for cookie in cj:
    set_cookie[cookie.name] = cookie.value

#Login
post_data = urllib.parse.urlencode({
            'email' : user_email,
            'password' : user_pswd,
            'remember' : False
            }).encode('utf-8')
request = urllib.request.Request(LOGIN_API, post_data)
request.add_header('User-Agent', 'edX-downloader/0.01')
request.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
request.add_header('Content-Type', 'application/x-www-form-urlencoded;charset=utf-8')
request.add_header('Referer', EDX_HOMEPAGE)
request.add_header('X-Requested-With', 'XMLHttpRequest')
request.add_header('X-CSRFToken', set_cookie.get('csrftoken', ''))
response = urllib.request.urlopen(request)
resp = json.loads(response.read().decode(encoding = 'utf-8'))
if not resp.get('success', False):
    print('Wrong Email or Password.', file = sys.stderr)
    exit(2)
    