from flask import Blueprint, render_template, current_app, send_from_directory, redirect, url_for
from flask_login import login_required, current_user

from apps.app import db
from apps.detector.models import UserImage
from apps.auth.models import User
from apps.detector.forms import UploadImageForm

import uuid
from pathlib import Path


dt = Blueprint("detector", __name__, template_folder="templates")

# Topページ
@dt.route("/")
def index():
    user_images = (
        db.session.query(User, UserImage)
        .join(UserImage)
        .filter(User.id == UserImage.user_id)
        .all()
    )

    return render_template("detector/index.html", user_images=user_images)

@dt.route("/images/<path:filename>")
def image_file(filename):
    """
    画像ファイルを返す
    :param filename: 画像ファイル名
    :return: 画像ファイル
    """
    # UPLOAD_FOLDERで指定したディレクトリから画像ファイルを取得する
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)

@dt.route("/upload", methods=["GET", "POST"])
@login_required
def upload_image():
    """
    画像アップロードページ
    :return: アップロードページのHTML
    """
    form = UploadImageForm()

    if form.validate_on_submit():
        # 画像ファイルを保存する
        file = form.image.data
        # ファイル名をUUIDで生成する
        ext = Path(file.filename).suffix
        image_uuid_filename = str(uuid.uuid4()) + ext

        # 画像を保存する
        file.save(
            Path(current_app.config["UPLOAD_FOLDER"], image_uuid_filename)
        )

        # DBに保存する
        user_image = UserImage(
            user_id=current_user.id, 
            mage_path=image_uuid_filename
        )
        db.session.add(user_image)
        db.session.commit()

        return redirect(url_for("detector.index"))

    return render_template("detector/upload.html", form=form)

