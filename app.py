# Flask 웹 프레임워크, 문자열 템플릿, 폼처리, 리다이렉트를 사용
from flask import Flask, render_template_string, request, redirect, url_for
import json # 줄바꿈/특수문자 포함 본문을 안전하게 파일에 저장하기 위해 사용(JSON Lines)

# Flask 앱 객체 생성
app = Flask(__name__)

# 글을 저장할 파일 경로
FILE_PATH = 'posts.txt'

# 💜함수: 글 목록 불러오기(제목 + 내용)
def load_posts():
    # post.txt를 한 줄씩 읽어서 JSON으로 파싱해서 [{'title':..., 'content':...},...] 형태로 반환
    # 📌 하위호환: 
    # - 과거 사용하였던 '제목|||내용' 혁ㅅㄱ의 라인도 자동 인식하여 읽어옴
    # - 이후 수정/삭제/새 글 작성 시엔 JSONL로 저장됨.
    try:
        #파일을 읽고 줄마다 리스트로 만들어서 반환
        posts = []
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            posts = []
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                # 1) 우선 JSONL 시도
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and 'title' in obj and 'content' in obj:
                        posts.append({'title': obj['title'], 'content': obj['content']})
                        continue
                except json.JSONDecodeError:
                    pass
                
                # 2) 구형 '제목|||내용' 포멧 fallback (처음 구분자만 분리)
                parts = line.split('|||', 1)
                if len(parts) == 2:
                    title, content = parts
                    posts.append({'title': title, 'content': content})
            return posts
    except FileNotFoundError:
        # 파일이 없으면 빈 리스트 반환
        return []
    # ✅ open(): 파일열기
    # ✅ readlines(): 줄 단위로 읽기
    # ✅ strip(): 줄 끝 개행 문자 제거
    # ✅ try/except: 파일이 없을 경우 대비

# 💜함수: 글 추가 저장하기
def save_post(title, content):
    # 새 글 한건을 JSON 한 줄로 저장.
    # - ensure_ascii=False: 한글이 \uXXXX로 꺠지지 않게 
    # - 내용 안의 줄바꿈은 팔일에 \n으로 안전하게 기록됨
    with open(FILE_PATH, 'a', encoding='utf-8') as f:
        # f.write(f"{title}|||{content}\n") 하단의 JSON 코드로 변경
        f.write(json.dumps({'title': title, 'content': content}, ensure_ascii=False) + '\n')
# ✅ 'a' 모드: 파일 끝에 내용을 "추가"
# ✅  write(): 글 내용 + 줄바꿈 저장

# 💜글 전체 다시 저장 (수정/삭제 후), 항상 JSON Lines 형식으로 덮어씀
def save_all_posts(posts):
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        for p in posts:
            # f.write(f"{p['title']}|||{p['content']}\n") 하단의 JSON 코드로 변경
            f.write(json.dumps({'title': p['title'], 'content': p['content']}, ensure_ascii=False) + '\n')

# 홈 주소 / -> 게시판으로 리다이렉트
@app.route('/')
def home():
    # 하드코딩('/board') 대신 url_for 사용 -> 경로/오타에 강함
    return redirect(url_for('board')) # 글 목록 페이지로 이동

# 게시판 목록페이지 /board
@app.route('/board')
def board():
    posts = load_posts() # 파일에서 글 목록 불러오기
    return render_template_string('''
        <h2>📝 나의 게시판</h2>
        <a href = "/create">글쓰기</a>
        <ul>
        {% for post in posts %}
            <li>
                <a href="/detail/{{ loop.index0 }}">{{ post.title }}</a>
            </li> 
        {% endfor %}
        </ul>                                  
''', posts=posts) # 글 목록을 템플릿에 넘겨줌
# ✅ render_template_string() : HTML을 직접 문자열로 사용
# ✅ {% for %}: Jinja 템플릿 반복문
# ✅ {{ post }}: 반복되는 글 내용 출력


# 💜 📝 글 작성 페이지 / create
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # strip은 선택사항: 제목 잎뒤 공백 제거, 본문은 줄바꿈 유지가 목적이라 그대로 저장
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '') # 폼에서 글 내용 가져오기
        save_post(title, content) # 파일에 저장
        return redirect(url_for('board')) # 목록으로 이동
    
    # GET 요청: 글쓰기 폼 보여줌
    return render_template_string(''' 
        <h2>✏️ 글 작성</h2>
        <form method="post">
            제목: <input type="text" name="title" required><br><br>
            내용: <br>
            <textarea name="content" rows="8" cols="70" required></textarea><br>
            <button type="submit">저장</button>
        </form>
        <a href="{{board_url}}">목록으로</a>   
    ''', board_url=url_for('board'))
# ✅ request.method: GET인지 POST인지 확인
# ✅ request.form['content']: 사용자가 입력한 내용

# 💜 글 상세보기(여기서 ✏️수정, ❌삭제로 변경)
# <div></div> 내부에 edit, delete 는 함수 이름
@app.route('/detail/<int:index>')
def detail(index):
    posts = load_posts()
    if 0 <= index < len(posts):
        post = posts[index]
        return render_template_string('''
            <h2>📝 {{ post.title }}</h2>
            <!-- 🔹pre + white-space:pre-wrap 으로 줄바꿈/공박을 그대로 표시 -->
            <pre style="white-space: pre-wrap; font-family:inherit;">{{ post.content }}</pre>
                          
            <div style="display:flex; gap:10px; margin-top: 10px;">
                <a href="{{ url_for('edit', index=index) }}">
                <button type="button">✏️수정</button></a>
                <!-- 🔹삭제는 POST로 안전하게 -->
                <form method="post" action="{{ url_for('delete', index=index) }}" onsubmit="return confirm('정말 삭제할까요?');">
                    <button type="submit" style="background:#ff4d4f; color:white;">❌삭제</button>
                </form>
            </div>
            
            <p><a href = "/board">목록으로</a></p>
        ''', post=post, index=index)
    return "글이 존재하지 않습니다.", 404


# 💜 글 수정하기 / 새로운 라우트 추가: /edit/<int:index>
@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit(index):
    # 수정: 기존 값으로 폼 채워주고, 저장 시 덮어쓰기
    posts = load_posts()
    if not (0 <= index < len(posts)):
        return "글이 존재하지 않습니다", 404
    
    if request.method == 'POST':
        posts[index] = {
            'title': request.form['title'],
            'content': request.form['content']
        }
        save_all_posts(posts)
        return redirect(f'/detail/{index}')
          
    
    # GET 요청: 기존 글 데이터 폼에 미리 채워서 보여줌
    post = posts[index]
    return render_template_string('''
        <h2>✏️ 글 수정</h2>
        <form method = "post">
            제목: <input type="text" name="title" value="{{post.title}}" required><br><br>
            내용: <br>
            <textarea name="content" rows="6" cols="60" required>{{ post.content }}</textarea><br>
            <button type="submit">수정 완료</button>
        </form>
        <p><a href="/detail/{{ index }}">뒤로</a></p>  
    ''', post=post, index=index)

# 💜❌ 글 삭제기능
@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    # 삭제: 상세에서만 POST로 호출
    posts = load_posts()
    if 0 <= index < len(posts):
        del posts[index]
        save_all_posts(posts)
    return redirect('/board')

# 🖥️ 서버실행
if __name__ ==  '__main__':
    app.run(debug=True)
# ✅ __name__ == '__main__': 파이썬 파일 직접 실행할 때만 작동
# ✅ debug=True: 실시간 코드 변경 감지 + 에러 확인

######################
# 정리
# /create: 글 입력-> 파일 저장
# /board: 파일에서 글 읽어서 목록 출력
# posts.txt: 글이 실제로 저장되는 텍스트 파일
