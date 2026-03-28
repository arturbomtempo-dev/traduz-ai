const input = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const fileBadge = document.getElementById('file-badge');
const pdfNotice = document.getElementById('pdf-notice');
const area = document.getElementById('upload-area');
const form = document.getElementById('upload-form');
const btn = document.getElementById('submit-btn');

function updateFileDisplay(file) {
    if (!file) {
        return;
    }

    const ext = file.name.split('.').pop().toLowerCase();
    fileName.textContent = file.name;
    fileBadge.textContent = ext.toUpperCase();
    fileBadge.className = 'file-badge file-badge--' + ext;
    fileInfo.classList.add('visible');
    pdfNotice.classList.toggle('visible', ext === 'pdf');
    lucide.createIcons();
}

input.addEventListener('change', () => {
    if (input.files.length > 0) {
        updateFileDisplay(input.files[0]);
    }
});

area.addEventListener('dragover', (e) => {
    e.preventDefault();
    area.classList.add('drag-over');
});

area.addEventListener('dragleave', () => area.classList.remove('drag-over'));

area.addEventListener('drop', (e) => {
    e.preventDefault();
    area.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    
    if (files.length > 0) {
        const dt = new DataTransfer();
        dt.items.add(files[0]);
        input.files = dt.files;
        updateFileDisplay(files[0]);
    }
});

form.addEventListener('submit', () => {
    btn.classList.add('loading');
    btn.disabled = true;
});
