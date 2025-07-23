from flask import Blueprint, request, render_template, current_app, send_from_directory, redirect, url_for
from flask_login import login_required, current_user

from apps.app import db
from apps.detector.models import UserImage
from apps.auth.models import User
from apps.detector.forms import UploadImageForm

import uuid
from pathlib import Path
import boto3
import os
from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
import h5py


dt = Blueprint("detector", __name__, template_folder="templates")

# # モデル修正（1度だけ実行）
# f = h5py.File("keras_model.h5", mode="r+")
# model_config_string = f.attrs.get("model_config")
# if b'"groups": 1,' in model_config_string:
#     f.attrs.modify("model_config", model_config_string.replace(b'"groups": 1,', b""))
#     f.flush()
# f.close()

# # モデルとラベルをグローバルに読み込む
# tm_model = load_model("keras_model.h5", compile=False)
# tm_labels = [line.strip() for line in open("labels.txt", "r").readlines()]

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

    # デフォルトはTeachableMachineに設定
    engine = request.args.get("engine", "teachable")  

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
            image_path=image_uuid_filename
        )
        
        db.session.add(user_image)
        db.session.commit()

        # # エンジンに応じてリダイレクト先を変更する
        # if engine == "teachable":
        #     return redirect(url_for("detector.predict"))
        # else:
        #     return redirect(url_for("detector.detect"))

        return redirect(url_for("detector.detect"))

    return render_template("detector/upload.html", form=form, engine=engine)


# Rekognitionでの物体検知
@dt.route("/detect", methods=["GET"])
@login_required
def detect():
    # 最新のユーザー画像を取得
    user_image = (
        db.session.query(UserImage)
        .filter_by(user_id=current_user.id)
        .order_by(UserImage.id.desc())
        .first()
    )

    if not user_image:
        return render_template("detector/detect.html", message="画像が登録されていません")

    # ファイルパスを取得
    local_path = Path(current_app.config["UPLOAD_FOLDER"]) / user_image.image_path

    # S3へアップロード
    s3 = boto3.client("s3")
    bucket_name = current_app.config["S3_BUCKET_NAME"]
    s3_key = f"user_images/{user_image.image_path}"
    s3.upload_file(str(local_path), bucket_name, s3_key)

    # Rekognition呼び出し
    rekognition = boto3.client("rekognition", region_name="us-east-1")
    model_arn = current_app.config["MODEL_ARN"]

    response = rekognition.detect_custom_labels(
        Image={"S3Object": {"Bucket": bucket_name, "Name": s3_key}},
        ProjectVersionArn=model_arn,
        MinConfidence=70
    )

    print("Rekognition response:", response)

    labels = response.get("CustomLabels", [])

    return render_template(
        "detector/result.html",
        image_url=s3_key,
        labels=labels
    )


# TeachableMachineでの物体検知
@dt.route("/predict", methods=["GET"])
@login_required
def predict():

    pass
    # 最新画像を取得
    user_image = (
        db.session.query(UserImage)
        .filter_by(user_id=current_user.id)
        .order_by(UserImage.id.desc())
        .first()
    )

    # if not user_image:
    #     return render_template("detector/result.html", message="画像が登録されていません")

    # Disable scientific notation for clarity
    np.set_printoptions(suppress=True)

    # # hack to change model config from keras 2->3 compliant
    # f = h5py.File("keras_model.h5", mode="r+")
    # model_config_string = f.attrs.get("model_config")
    # if model_config_string.find('"groups": 1,') != -1:
    #     model_config_string = model_config_string.replace('"groups": 1,', '')
    #     f.attrs.modify('model_config', model_config_string)
    #     f.flush()
    #     model_config_string = f.attrs.get("model_config")
    #     assert model_config_string.find('"groups": 1,') == -1
    # f.close()

    # # モデル読み込み
    # model = load_model("keras_model.h5", compile=False)

    # # Load the labels
    # class_names = open("labels.txt", "r").readlines()

    # Create the array of the right shape to feed into the keras model
    # The 'length' or number of images you can put into the array is
    # determined by the first position in the shape tuple, in this case 1
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    # 画像パス
    image_path = Path(current_app.config["UPLOAD_FOLDER"]) / user_image.image_path
    image = Image.open(image_path).convert("RGB")

    # resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

    # turn the image into a numpy array
    image_array = np.asarray(image)

    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

    # Load the image into the array
    data[0] = normalized_image_array

    # 予測の実行
    prediction = tm_model.predict(data)
    index = np.argmax(prediction)
    class_name = tm_labels[index]
    confidence_score = float(prediction[0][index])

    # Print prediction and confidence score
    print("Class:", class_name[2:], end="")
    print("Class:", class_name, end="")
    print("Confidence Score:", confidence_score)

    # 結果を1件分返却
    result = [{"label": class_name, "confidence": confidence_score}]

    return render_template(
        "detector/result.html",
        image_url=user_image.image_path,
        labels=result
    )