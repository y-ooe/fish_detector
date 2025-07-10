from apps.app import db
from apps.auth.forms import SignUpForm, LoginForm
from apps.auth.models import User
from flask import Blueprint, redirect, render_template, url_for, flash, request
from flask_login import login_user, login_required, logout_user

# Blueprintでauthアプリを生成する
auth = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@auth.route("/")
def index():
    return render_template("auth/index.html")


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    """ユーザー登録"""
    form = SignUpForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )

        # メールアドレスの重複チェック
        if user.is_dupulicate_email():
            flash("このメールアドレスはすでに登録されています。")
            return render_template("auth/signup.html", form=form)

        db.session.add(user)
        db.session.commit()

        login_user(user)

        # GETパラメータにnextキーが存在し、値がない場合はユーザーの一覧ページへリダイレクト
        next_ = request.args.get("next")
        if next_ is None or next_.startswith("/"):
            next_ = url_for("detector.index")    
        return redirect(next_)

    return render_template("auth/signup.html", form=form)

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is not None and user.verify_password(form.password.data):
            login_user(user)    
            return redirect(url_for("detector.index"))

        flash("メールアドレスまたはパスワードが間違っています。")
    return render_template("auth/login.html", form=form)