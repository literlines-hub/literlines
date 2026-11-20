"""곧은 한 줄 - 인스타그램 자동 게시 (Instagram API with Instagram Login, 페이스북 페이지 불필요)

GitHub Actions에서 매시간 실행됨.
schedule.json에서 '승인됨(approved: true)'이고 게시 시각(한국 시간)이 지난 게시물만 올림.
토큰은 GitHub Secret 'IG_TOKEN'에서만 읽음 (파일이나 로그에 절대 남기지 않음).
"""
import json, os, sys, time, datetime, urllib.request, urllib.parse
IG_API="https://graph.instagram.com/v23.0"; FB_API="https://graph.facebook.com/v23.0"
API=IG_API
IG_USER_ID=os.environ.get("IG_USER_ID","").strip() or (json.load(open("config.json")).get("ig_user_id","") if os.path.exists("config.json") else "").strip()
TOKEN=os.environ.get("IG_TOKEN","").strip()
REPO=os.environ.get("GITHUB_REPOSITORY","")       # 예: hyegang/gotgeun-hanjul
BRANCH=os.environ.get("GITHUB_REF_NAME","main")
DRY=os.environ.get("DRY_RUN","")=="1"
KST=datetime.timezone(datetime.timedelta(hours=9))
def call(method,path,params,api=None):
    params=dict(params,access_token=TOKEN); data=urllib.parse.urlencode(params).encode()
    url=f"{api or API}/{path}"
    req=urllib.request.Request(url+("?"+data.decode() if method=="GET" else ""),data=None if method=="GET" else data,method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors="replace").replace(TOKEN,"***"); raise SystemExit(f"API 오류 {e.code}: {body}")
def wait_ready(cid):
    for _ in range(30):
        st=call("GET",cid,{"fields":"status_code"}).get("status_code")
        if st=="FINISHED": return
        if st in("ERROR","EXPIRED"): raise SystemExit(f"미디어 처리 실패: {st}")
        time.sleep(5)
    raise SystemExit("미디어 처리 시간 초과")
def find_user():
    """토큰 종류에 맞춰 API 주소와 인스타 계정 ID를 찾음.
    - 인스타그램 로그인 토큰: graph.instagram.com /me
    - 통합 로그인(시스템 사용자) 토큰: graph.facebook.com + 비즈니스 포트폴리오의 인스타 계정"""
    global API
    if IG_USER_ID:
        for api in (FB_API, IG_API):
            try:
                me=call("GET",IG_USER_ID,{"fields":"id,username"},api); API=api; return IG_USER_ID, me.get("username")
            except SystemExit as e: err=e
        raise err
    try:
        me=call("GET","me",{"fields":"user_id,username"},IG_API); API=IG_API; return me["user_id"], me.get("username")
    except SystemExit: pass
    API=FB_API
    try:
        for pg in call("GET","me/accounts",{"fields":"instagram_business_account{id,username}"}).get("data",[]):
            ig=pg.get("instagram_business_account")
            if ig: return ig["id"], ig.get("username")
    except SystemExit: pass
    try: bizs=call("GET","me/businesses",{"fields":"id"}).get("data",[])
    except SystemExit: bizs=[]
    for b in bizs:
        for edge in ("instagram_accounts","owned_instagram_accounts"):
            try:
                d=call("GET",f"{b['id']}/{edge}",{"fields":"id,username"}).get("data",[])
                if d: return d[0]["id"], d[0].get("username")
            except SystemExit: pass
    raise SystemExit("인스타 계정 ID를 찾지 못했어요. config.json의 ig_user_id에 계정 ID(17841로 시작)를 넣어 주세요.")
SHA=os.environ.get("GITHUB_SHA","")
def media_url(folder,f):
    if f.endswith(".mp4"):  # 영상은 올바른 형식(video/mp4)으로 내려주는 jsDelivr CDN 사용 (커밋 고정)
        return f"https://cdn.jsdelivr.net/gh/{REPO}@{SHA or BRANCH}/posts/{folder}/{f}"
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/posts/{folder}/{f}"
def wait_ready_long(cid):
    for _ in range(60):
        st=call("GET",cid,{"fields":"status_code"}).get("status_code")
        if st=="FINISHED": return
        if st in("ERROR","EXPIRED"): raise SystemExit(f"영상 처리 실패: {st}")
        time.sleep(10)
    raise SystemExit("영상 처리 시간 초과")
def publish_reel(post):
    uid,uname=find_user()
    caption=open(os.path.join("posts",post["folder"],"caption.txt"),encoding="utf-8").read()
    c=call("POST",f"{uid}/media",{"media_type":"REELS","video_url":media_url(post["folder"],post.get("video","reel.mp4")),"caption":caption,"share_to_feed":"true"})
    wait_ready_long(c["id"]); res=call("POST",f"{uid}/media_publish",{"creation_id":c["id"]}); return res["id"], uname
THREADS_TOKEN=os.environ.get("THREADS_TOKEN","").strip()
def publish_threads(post):
    """스레드: 캡션 첫 부분(한글 문장)을 글로 게시"""
    if not THREADS_TOKEN: print("THREADS_TOKEN 없음: 스레드 건너뜀"); return None
    text=open(os.path.join("posts",post["folder"],post.get("threads_file","threads.txt")),encoding="utf-8").read().strip()[:500]
    def tcall(method,path,params):
        params=dict(params,access_token=THREADS_TOKEN); data=urllib.parse.urlencode(params).encode()
        req=urllib.request.Request(f"https://graph.threads.net/v1.0/{path}",data=data if method=="POST" else None,method=method)
        if method=="GET": req=urllib.request.Request(f"https://graph.threads.net/v1.0/{path}?{data.decode()}")
        try:
            with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
        except urllib.error.HTTPError as e: raise SystemExit("스레드 API 오류 %s: %s"%(e.code,e.read().decode(errors="replace").replace(THREADS_TOKEN,"***")))
    me=tcall("GET","me",{"fields":"id,username"})
    c=tcall("POST",f"{me['id']}/threads",{"media_type":"TEXT","text":text}); time.sleep(5)
    r=tcall("POST",f"{me['id']}/threads_publish",{"creation_id":c["id"]}); print("스레드 게시 완료:",r["id"]); return r["id"]
def publish(post):
    if post.get("type")=="reel": return publish_reel(post)
    uid,uname=find_user()
    base=f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/posts/{post['folder']}"
    caption=open(os.path.join("posts",post["folder"],"caption.txt"),encoding="utf-8").read()
    children=[]
    for f in post.get("slides",["slide1.jpg","slide2.jpg","slide3.jpg"]):
        c=call("POST",f"{uid}/media",{"image_url":f"{base}/{f}","is_carousel_item":"true"}); wait_ready(c["id"]); children.append(c["id"])
    car=call("POST",f"{uid}/media",{"media_type":"CAROUSEL","children":",".join(children),"caption":caption}); wait_ready(car["id"])
    res=call("POST",f"{uid}/media_publish",{"creation_id":car["id"]})
    return res["id"], uname
def main():
    sched=json.load(open("schedule.json",encoding="utf-8")); now=datetime.datetime.now(KST); changed=False
    for p in sched["posts"]:
        if p.get("posted_id") or not p.get("approved"): continue
        due=datetime.datetime.fromisoformat(p["time_kst"]).replace(tzinfo=KST)
        if due>now: continue
        if DRY: print("[테스트] 게시 예정:",p["folder"]); continue
        if not TOKEN: raise SystemExit("IG_TOKEN 시크릿이 없습니다")
        mid,user=publish(p); p["posted_id"]=mid; p["posted_at"]=now.isoformat(timespec="minutes"); changed=True
        if p.get("threads"):
            try: p["threads_id"]=publish_threads(p)
            except SystemExit as e: print(e)
        print(f"게시 완료: {p['folder']} → @{user} (media {mid})")
        break   # 한 번 실행에 하나만
    if changed: json.dump(sched,open("schedule.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    else: print("지금 올릴 게시물 없음")
if __name__=="__main__": main()
