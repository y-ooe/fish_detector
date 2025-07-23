const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('fileElem');

// ブラウザのデフォルト動作を抑制
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
    });
});

// ハイライト表示
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => {
        dropArea.classList.add('dragover');
    });
});

// ハイライト解除
['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => {
        dropArea.classList.remove('dragover');
    });
});

// ドロップ時の処理
dropArea.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
});

// ファイル選択ボタンからのアップロード
fileInput.addEventListener('change', e => {
    if (fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
    }
});

// アップロード処理
function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    // CSRFトークンをmetaタグから取得
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch('/upload', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => response.text())
        .then(data => {
            alert("アップロード完了: " + data);
        })
        .catch(error => {
            alert("エラーが発生しました");
            console.error(error);
        });
}

