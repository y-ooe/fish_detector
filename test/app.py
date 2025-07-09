from flask import Flask, request, render_template
import tensorflow as tf
from keras.models import load_model
from keras.preprocessing import image
import numpy as np
import os

app = Flask(__name__)
model = load_model("keras_model.h5")
class_names = ["Tetris", "Sudoku", "2048", "Solitaire"]  # 例

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        img_file = request.files["image"]
        img_path = os.path.join("static", "upload.jpg")
        img_file.save(img_path)

        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        predictions = model.predict(img_array)
        pred_idx = np.argmax(predictions[0])
        result = f"{class_names[pred_idx]} ({predictions[0][pred_idx]*100:.2f}%)"

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
