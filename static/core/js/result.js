function downloadTxt(el) {
    const text = document.querySelector('.translation-text').value;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });

    const a = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(blob),
        download: el.dataset.filename,
    });
    a.click();
    URL.revokeObjectURL(a.href);
}

document.querySelector('.btn-accent[data-filename]')?.addEventListener('click', function () {
    downloadTxt(this);
});
