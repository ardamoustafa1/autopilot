import os, time, json, sqlite3, logging
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
TZ=ZoneInfo('Europe/Istanbul')
DRY_RUN=os.getenv('DRY_RUN','true').lower()!='false'
DB=ROOT/'state.sqlite3'
TEXT={
'combo': '''I thought I made an easy puzzle game.

Then I watched people struggle with it. 💀

One move can trigger an insane chain reaction.

Think you can beat it?

I built Combo Chain Blast solo.

🎮 Play free 👇
https://apps.apple.com/us/app/combo-chain-blast/id6817666697

#IndieGameDev #MobileGaming''',
'deste': '''You took a screenshot 3 months ago.

Now you need it.

Good luck finding it among 2,000 others. 💀

That's why I built Deste.

Search screenshots by the text inside them.

No cloud. No endless scrolling.

Free on iOS & Mac 👇
https://apps.apple.com/us/app/deste-smart-screenshots/id6822008867

#SwiftUI #IndieDev'''
}
SLOTS=[('combo','combo1.mp4'),('deste','deste.mp4'),('combo','combo2.mp4'),('deste','deste.mp4')]

def auth():
    names=['X_API_KEY','X_API_SECRET','X_ACCESS_TOKEN','X_ACCESS_TOKEN_SECRET']
    vals=[os.getenv(n) for n in names]
    if not all(vals): raise RuntimeError('Missing X credentials: '+', '.join(n for n,v in zip(names,vals) if not v))
    return OAuth1(*vals)

def check(r):
    if not r.ok: raise RuntimeError(f'X API {r.status_code}: {r.text[:700]}')
    return r.json()

def upload_video(path, oauth):
    url='https://upload.twitter.com/1.1/media/upload.json'
    size=path.stat().st_size
    result=check(requests.post(url,auth=oauth,data={'command':'INIT','total_bytes':size,'media_type':'video/mp4','media_category':'tweet_video'},timeout=45))
    media_id=result['media_id_string']
    with path.open('rb') as f:
        segment=0
        while chunk:=f.read(4*1024*1024):
            _append(url,oauth,media_id,segment,chunk)
            segment+=1
    result=check(requests.post(url,auth=oauth,data={'command':'FINALIZE','media_id':media_id},timeout=45))
    info=result.get('processing_info')
    for _ in range(30):
        if not info or info.get('state')=='succeeded': return media_id
        if info.get('state')=='failed': raise RuntimeError('Video processing failed: '+str(info))
        time.sleep(min(max(info.get('check_after_secs',2),1),15))
        result=check(requests.get(url,auth=oauth,params={'command':'STATUS','media_id':media_id},timeout=45))
        info=result.get('processing_info')
    raise TimeoutError('Video processing not finished')

def _append(url,oauth,media_id,segment,chunk):
    r=requests.post(url,auth=oauth,data={'command':'APPEND','media_id':media_id,'segment_index':segment},files={'media':('chunk',chunk,'application/octet-stream')},timeout=120)
    if not r.ok: raise RuntimeError(f'APPEND failed {r.status_code}: {r.text[:500]}')

def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    now=datetime.now(TZ)
    if now.minute not in (0,30):
        logging.info('Not a scheduled half-hour slot'); return
    # Absolute 2-hour rotation anchored at 18:00 Istanbul time.
    slot_index=((now.hour*2 + now.minute//30)-(18*2))%4
    app,video=SLOTS[slot_index]
    slot=now.strftime('%Y-%m-%d %H:%M')
    with sqlite3.connect(DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS posts(slot TEXT PRIMARY KEY, app TEXT, video TEXT, tweet_id TEXT, status TEXT)')
        if db.execute('SELECT 1 FROM posts WHERE slot=?',(slot,)).fetchone():
            logging.info('Already processed slot %s',slot); return
        path=ROOT/'videos'/video
        if not path.is_file(): raise FileNotFoundError(path)
        if DRY_RUN:
            logging.info('DRY RUN slot=%s app=%s video=%s text=%s',slot,app,video,TEXT[app]); return
        oauth=auth()
        media_id=upload_video(path,oauth)
        result=check(requests.post('https://api.x.com/2/tweets',auth=oauth,json={'text':TEXT[app],'media':{'media_ids':[media_id]}},timeout=45))
        tweet_id=result['data']['id']
        db.execute('INSERT INTO posts VALUES (?,?,?,?,?)',(slot,app,video,tweet_id,'posted'))
        db.commit()
        logging.info('Published %s %s tweet=%s',app,video,tweet_id)

if __name__=='__main__': main()
