from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import pytz

app = Flask(__name__)

##########################################################あいうえお
#データベース構築
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:140286TakaHiro@localhost/site4db_6'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://site4user:140286TakaHiro@localhost/site4db_6'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://site4user:140286TakaHiro@localhost/site4db_7'
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='thread', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname=db.Column(db.Text, nullable=False)
    password=db.Column(db.Text, nullable=False)
    posts = db.relationship('Post', backref='user', lazy=True)

with app.app_context():
    db.create_all()

##########################################################
#ログイン設定
app.config['SECRET_KEY'] = 'hiroki-secret-key'
from flask_login import LoginManager
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from flask_login import current_user
import hashlib

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def hash_password(password):
    hash_object = hashlib.sha256()
    hash_object.update(password.encode('utf-8'))
    hashed_password = hash_object.hexdigest()
    return hashed_password

def get_nickname():
    if current_user.is_authenticated:
        nickname = current_user.nickname
    else:
        nickname = "ログインしていません"
    return nickname

@app.route('/login', methods=['GET', 'POST'])
def login():
    nickname=get_nickname()
    if request.method == 'POST':
        #認証
        user = User.query.filter_by(nickname=request.form['nickname']).first()
        if user and user.password == hash_password(request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        else:
            good_or_bad="nicknameかpasswordが間違っています。"
    elif request.method == 'GET':
        good_or_bad="新規にスレッドを作る場合やスレッドに投稿する場合はログインが必要です"
    return render_template('login.html', good_or_bad=good_or_bad, nickname=nickname)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    nickname=get_nickname()
    if request.method == 'POST':
        # サインアップ
        user = User.query.filter_by(nickname=request.form['nickname']).first()
        if user:
            already_used_or_not='すでに使われているnicknameです'
        else:
            #Userテーブルへ
            nickname = request.form['nickname']
            password = hash_password(request.form['password'])
            new_user = User(nickname=nickname, password=password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    elif request.method == 'GET':
        already_used_or_not='他のサービスで使っているパスワードや名前などは絶対に使用しないでください。'
    return render_template('signup.html', already_used_or_not=already_used_or_not, nickname=nickname)

##########################################################
#メインの関数
def post_thread(comment, thread_id):
    current_time = datetime.utcnow()
    current_time_japan = current_time.astimezone(pytz.timezone('Asia/Tokyo'))
    new_post = Post(content=comment, thread_id=thread_id, user_id=current_user.id, time=current_time_japan)
    db.session.add(new_post)
    db.session.commit()

import html
def sanitizing_text(text):
    processed_text = str(html.escape(text)).replace("\n", "<br>")
    return processed_text

@app.route('/')
def home():
    nickname=get_nickname()
    #Threadテーブルから
    threads = Thread.query.all()
    return render_template('home.html', threads=threads, nickname=nickname)

@app.route('/thread/new', methods=['GET', 'POST'])
@login_required
def new_thread():
    nickname=get_nickname()
    if request.method == 'POST':
        #Threadテーブルへ
        title = request.form['title']
        new_thread = Thread(title=title)
        db.session.add(new_thread)
        db.session.commit()
        #Postテーブルへ
        comment = request.form['comment']
        post_thread(comment, new_thread.id)
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('new_thread.html', nickname=nickname)

@app.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def view_thread(thread_id):
    nickname=get_nickname()
    if request.method == 'POST':
        #ログインしているのか
        if current_user.is_authenticated:
            #Postテーブルへ
            comment = request.form['comment']
            comment=sanitizing_text(comment)
            post_thread(comment, thread_id)
        else:
            return redirect(url_for('login'))  
    elif request.method == 'GET':
        pass
    #Threadテーブル、Postテーブルから
    thread = Thread.query.get(thread_id)
    posts = Post.query.filter_by(thread_id=thread_id)
    posts_with_nicknames = [(post, post.user.nickname) for post in posts]
    return render_template('thread.html', thread=thread, posts_with_nicknames=posts_with_nicknames, nickname=nickname)
    
##########################################################
#実行
if __name__ == '__main__':
    app.run(debug=True)


