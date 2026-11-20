#!/usr/bin/env python3
"""Publishes the oldest due, unposted post in queue/ to Instagram and the Facebook Page.
Runs in GitHub Actions. Env: META_PAGE_TOKEN (secret), FB_PAGE_ID, IG_USER_ID, GITHUB_REPOSITORY.
Flow: render slides -> commit + push images (public raw URLs) -> post via Meta Graph API -> log in posted.json.
"""
import datetime, glob, json, os, subprocess, sys, time, urllib.parse, urllib.request
from render import render

API = 'https://graph.facebook.com/v21.0'
TOKEN, PAGE, IG = os.environ['META_PAGE_TOKEN'], os.environ['FB_PAGE_ID'], os.environ['IG_USER_ID']
REPO = os.environ.get('GITHUB_REPOSITORY', 'moonkengi/zareya-social')
FORCE = os.environ.get('FORCE_POST', '')  # optional: a queue date to post now

def call(path, data=None, method='POST'):
    data = dict(data or {}, access_token=TOKEN)
    if method == 'GET':
        req = urllib.request.Request(f'{API}/{path}?{urllib.parse.urlencode(data)}')
    else:
        req = urllib.request.Request(f'{API}/{path}', data=urllib.parse.urlencode(data).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f'Meta API error on {path}: {e.read().decode()}')

def git(*a): subprocess.run(['git', *a], check=True)

def wait_ready(cid):
    for _ in range(30):
        st = call(cid, {'fields': 'status_code'}, 'GET').get('status_code')
        if st == 'FINISHED': return
        if st == 'ERROR': sys.exit(f'Instagram could not process container {cid}')
        time.sleep(5)

def post_instagram(urls, caption):
    if len(urls) == 1:
        cid = call(f'{IG}/media', {'image_url': urls[0], 'caption': caption})['id']
    else:
        kids = [call(f'{IG}/media', {'image_url': u, 'is_carousel_item': 'true'})['id'] for u in urls]
        for k in kids: wait_ready(k)
        cid = call(f'{IG}/media', {'media_type': 'CAROUSEL', 'children': ','.join(kids), 'caption': caption})['id']
    wait_ready(cid)
    return call(f'{IG}/media_publish', {'creation_id': cid})['id']

def post_facebook(urls, caption):
    if len(urls) == 1:
        return call(f'{PAGE}/photos', {'url': urls[0], 'caption': caption})['id']
    ids = [call(f'{PAGE}/photos', {'url': u, 'published': 'false'})['id'] for u in urls]
    data = {'message': caption}
    for i, pid in enumerate(ids): data[f'attached_media[{i}]'] = json.dumps({'media_fbid': pid})
    return call(f'{PAGE}/feed', data)['id']

def main():
    log = json.load(open('posted.json')) if os.path.exists('posted.json') else {}
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date().isoformat()
    due = [f for f in sorted(glob.glob('queue/*.json'))
           if os.path.basename(f)[:10] not in log and (os.path.basename(f)[:10] <= today or os.path.basename(f)[:10] == FORCE)]
    if FORCE: due = [f for f in due if os.path.basename(f)[:10] == FORCE]
    if not due:
        print('Nothing due today.'); return
    f = due[0]; key = os.path.basename(f)[:10]; post = json.load(open(f))
    files = render(post, f'images/{key}')
    git('config', 'user.name', 'zareya-bot'); git('config', 'user.email', 'bot@zareya.co.ke')
    git('add', 'images'); git('commit', '-m', f'Images for {key}'); git('push')
    sha = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    urls = [f'https://raw.githubusercontent.com/{REPO}/{sha}/{p}' for p in files]
    time.sleep(10)
    ig = post_instagram(urls, post['caption'])
    fb = post_facebook(urls, post['caption'])
    log[key] = {'instagram': ig, 'facebook': fb, 'posted_at': datetime.datetime.utcnow().isoformat() + 'Z'}
    json.dump(log, open('posted.json', 'w'), indent=1)
    git('add', 'posted.json'); git('commit', '-m', f'Posted {key}'); git('push')
    print(f'Posted {key}: IG {ig}, FB {fb}')
    with open(os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null'), 'a') as s:
        s.write(f'Posted {key} ({post.get("pillar")}). IG media {ig}, FB post {fb}\n')

if __name__ == '__main__':
    main()
