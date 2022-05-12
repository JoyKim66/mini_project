from pymongo import MongoClient
import datetime
import jwt
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# 코딩 시작

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb+srv://test:sparta@cluster0.m2th4.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.dbsparta


@app.route('/')
def login():
    return render_template("login.html")


@app.route('/index')
def main():
    posts = list(db.posts.find({}, {"_id": False}).sort("num", -1))
    return render_template("index.html", posts=posts)


@app.route('/save_movie', methods=['POST'])
def save_movie():
    # 정보 저장하기
    url_receive = request.form["url_give"]
    actor_receive = request.form["actor_give"]
    director_receive = request.form["director_give"]
    date_receive = request.form["date_give"]
    comment_receive = request.form["comment_give"]

    movie_list = list(db.posts.find({}, {"_id": False}).sort("num", -1).limit(1))
    if movie_list == []:
        count = 0
    else:
        count = movie_list[0]["num"] + 1

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    image = soup.select_one('meta[property="og:image"]')['content']
    title = soup.select_one('meta[property="og:title"]')['content']

    doc = {
        "image": image,
        "title": title,
        "actor": actor_receive,
        "director": director_receive,
        "date": date_receive,
        "comment": comment_receive,
        "num": count,
        "like": 0
    }
    db.posts.insert_one(doc)
    return jsonify({'result': 'success', 'msg': '저장'})


@app.route("/posts/del", methods=["POST"])
def delete():
    num_receive = request.form['num_give']
    db.posts.delete_one({'num': int(num_receive)})
    return jsonify({'msg': '삭제 완료!'})


@app.route("/post/like", methods=["POST"])
def edit():
    num_receive = request.form['num_give']
    post_likes = db.posts.find_one({'num': int(num_receive)})['like']
    likes = post_likes + 1
    db.posts.update_one({'num': int(num_receive)}, {'$set': {'like': likes}})

    return jsonify(likes=likes)

    # 회원가입 DB에 저장


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": ""  # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


# 중복체크 기능
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/index/check', methods=['POST'])
def address_check():
    title_receive = request.form['title_give']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(title_receive, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    title = soup.select_one('meta[property="og:title"]')['content']

    return jsonify({'result': 'success', 'title': title})

@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
