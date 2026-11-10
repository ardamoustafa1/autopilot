import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
STATE = ROOT / 'state.json'
TZ = ZoneInfo('Europe/Istanbul')
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() != 'false'
# An exact post (text + video) is never automatically repeated.
# Additional original posts can be added to posts.json.

def credentials():
    keys = ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET']
    values = [os.getenv(key) for key in keys]
    if not all(values):
        raise RuntimeError('Missing environment variables: ' + ', '.join(k for k, v in zip(keys, values) if not v))
    return OAuth1(*values)

def api_result(response):
    if not response.ok:
        raise RuntimeError(f'X API error {response.status_code}: {response.text[:500]}')
    return response.json() if response.content else {}

def upload_video(path, oauth):
    # X media upload API endpoint; account access/credits and endpoint availability are required.
    url = 'https://upload.twitter.com/1.1/media/upload.json'
    size = path.stat().st_size
    init = api_result(requests.post(url, auth=oauth, data={
        'command': 'INIT', 'total_bytes': size, 'media_type': 'video/mp4',
        'media_category': 'tweet_video'}, timeout=45))
    media_id = init['media_id_string']
    with path.open('rb') as f:
        index = 0
        while True:
            chunk = f.read(4 * 1024 * 1024)
            if not chunk:
                break
            response = requests.post(url, auth=oauth, data={
                'command': 'APPEND', 'media_id': media_id, 'segment_index': index
            }, files={'media': ('segment', chunk, 'application/octet-stream')}, timeout=120)
            if not response.ok:
                raise RuntimeError(f'X upload APPEND failed {response.status_code}: {response.text[:500]}')
            index += 1
    result = api_result(requests.post(url, auth=oauth, data={'command': 'FINALIZE', 'media_id': media_id}, timeout=45))
    info = result.get('processing_info')
    for _ in range(60):
        if not info or info.get('state') == 'succeeded':
            return media_id
        if info.get('state') == 'failed':
            raise RuntimeError('X video processing failed: ' + str(info))
        time.sleep(min(max(int(info.get('check_after_secs', 3)), 1), 20))
        result = api_result(requests.get(url, auth=oauth, params={'command': 'STATUS', 'media_id': media_id}, timeout=45))
        info = result.get('processing_info')
    raise TimeoutError('X video processing timed out')

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    now = datetime.now(TZ)
    # GitHub Actions scheduled jobs may run late. Choose the last half-hour slot.
    slot_index = ((now.hour * 2 + now.minute // 30) - 36) % 4
    posts = json.loads((ROOT / 'posts.json').read_text(encoding='utf-8'))
    post = posts[slot_index]
    if not STATE.exists():
        STATE.write_text('{"published": {}}\n', encoding='utf-8')
    state = json.loads(STATE.read_text(encoding='utf-8'))
    published = state.setdefault('published', {})
    key = post['id']
    if key in published:
        logging.info('Skipped already published content: %s', key)
        return
    path = ROOT / 'videos' / post['video']
    if not path.is_file():
        raise FileNotFoundError(path)
    if DRY_RUN:
        logging.info('DRY RUN: would publish %s with %s (%s)', post['app'], post['video'], key)
        return
    if os.getenv('ENABLE_PUBLISHING', 'false').lower() != 'true':
        logging.info('Publishing disabled: set ENABLE_PUBLISHING=true after testing and reviewing content')
        return
    oauth = credentials()
    media_id = upload_video(path, oauth)
    result = api_result(requests.post('https://api.x.com/2/tweets', auth=oauth,
        json={'text': post['text'], 'media': {'media_ids': [media_id]}}, timeout=45))
    tweet_id = result['data']['id']
    published[key] = {'tweet_id': tweet_id, 'time': now.isoformat(), 'video': post['video']}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    logging.info('Published %s tweet ID %s', key, tweet_id)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.exception('AutoPilot failed')
        sys.exit(1)
