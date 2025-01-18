// ダークモード管理
const toggleDarkMode = () => {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
};

// ドラッグ&ドロップ処理
const setupDragAndDrop = () => {
    const dropZone = document.querySelector('.upload-form');
    const fileInput = document.getElementById('pdf_file');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    dropZone.addEventListener('dragenter', () => dropZone.classList.add('drag-over'));
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {
        dropZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            updateFileName(file.name);
        } else {
            showError('PDFファイルのみアップロード可能です');
        }
    });
};

// ファイル名表示の更新
const updateFileName = (fileName) => {
    const fileNameDisplay = document.querySelector('.file-name');
    if (fileNameDisplay) {
        fileNameDisplay.textContent = fileName;
    }
};

// エラーメッセージ表示
const showError = (message) => {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    document.querySelector('.upload-form').appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
};

// プログレスバー管理
class ProgressBar {
    constructor() {
        this.progressContainer = document.createElement('div');
        this.progressContainer.className = 'progress-container';
        this.progressBar = document.createElement('div');
        this.progressBar.className = 'progress-bar';
        this.progressContainer.appendChild(this.progressBar);
        
        this.statusText = document.createElement('div');
        this.statusText.className = 'status-text';
        this.progressContainer.appendChild(this.statusText);
    }

    show() {
        const form = document.querySelector('.upload-form');
        form.appendChild(this.progressContainer);
    }

    update(progress, status) {
        this.progressBar.style.width = `${progress}%`;
        if (status) {
            this.statusText.textContent = status;
        }
    }

    hide() {
        this.progressContainer.remove();
    }
}

// フォーム送信の処理
const handleFormSubmit = async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const file = formData.get('pdf_file');
    
    if (!file || file.size === 0) {
        showError('ファイルを選択してください');
        return;
    }

    const progress = new ProgressBar();
    progress.show();
    progress.update(0, '変換を開始しています...');

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('変換に失敗しました');
        }

        const result = await response.text();
        document.querySelector('main').innerHTML = result;
        setupEventListeners(); // イベントリスナーの再設定

    } catch (error) {
        showError(error.message);
    } finally {
        progress.hide();
    }
};

// イベントリスナーの設定
const setupEventListeners = () => {
    // ファイル選択時の処理
    const fileInput = document.getElementById('pdf_file');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                updateFileName(file.name);
            }
        });
    }

    // フォーム送信の処理
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
};

// 初期化処理
document.addEventListener('DOMContentLoaded', () => {
    // ダークモードの初期設定
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    if (savedDarkMode) {
        document.body.classList.add('dark-mode');
    }

    setupDragAndDrop();
    setupEventListeners();
});
