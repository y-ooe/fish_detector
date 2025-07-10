from pathlib import Path
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

from apps.config import config

# SQLAlchemyをインスタンス化
db = SQLAlchemy()
csrf = CSRFProtect()

login_manager = LoginManager()

# login_view属性に未ログイン時にリダイレクトするエンドポイントを指定する
login_manager.login_view = "auth.signup"

# login_message属性にログイン後に表示するメッセージを指定する
# ここでは何も表示しないよう空を指定する
login_manager.login_message = ""

def create_app(config_key):
    app = Flask(__name__)

    app.config.from_object(config[config_key])

    csrf.init_app(app)

    # SQLAlchemyアプリと連携する
    db.init_app(app)
    # Migrateアプリと連携する
    Migrate(app, db)
    # login_managerをアプリと連携する
    login_manager.init_app(app)

    # # カスタムエラー画面を登録する
    # app.register_error_handler(404, page_not_found)
    # app.register_error_handler(500, internal_server_error)

    from apps.auth import views as auth_views
    from apps.detector import views as dt_views

    # register_blueprintを使いviewsのcrudをアプリへ登録する
    app.register_blueprint(auth_views.auth, url_prefix="/auth")
    app.register_blueprint(dt_views.dt)


    return app

# 登録したエンドポイント名の関数を作成し、404や500が発生した際に指定した際に指定したhtmlを返す
# def page_not_found(e):
#     """404 Not Foun"""
#     return render_template('404.html'), 404

# def internal_server_error(e):
#     """500 Internal Server Error"""
#     return render_template('500.html'), 500