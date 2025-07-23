from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

basedir = Path(__file__).parent.parent


# BaseConfigクラスを作成する
class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY")
    # 画像アップロード先にapps/imagesを指定する
    UPLOAD_FOLDER = str(Path(basedir, "apps", "images"))
    MODEL_ARN = os.environ.get('MODEL_ARN')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')




# BaseConfigクラスを継承してLocalConfigクラスを作成する
class LocalConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'local.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True


# Test用の設定クラス
class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'testing.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = str(Path(basedir, "tests", "detector", "images"))


# config辞書にマッピングする
config = {
    "testing": TestingConfig,
    "local": LocalConfig,
}