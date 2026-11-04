const verifyForm = document.getElementById('verify-form');
const scanForm = document.getElementById('scan-form');
const claimInput = document.getElementById('t');
const urlInput = document.getElementById('u');
const claimCount = document.getElementById('claim-count');

function showNotice(target, message, isError = false) {
    const notice = document.createElement('p');
    notice.className = isError ? 'notice notice-error' : 'notice';
    notice.textContent = message;
    target.replaceChildren(notice);
}

async function submitSafely(form, result, button, loadingText, action) {
    if (form.dataset.busy === 'true') return;

    const buttonText = button.textContent;
    form.dataset.busy = 'true';
    form.setAttribute('aria-busy', 'true');
    button.disabled = true;
    button.textContent = loadingText;

    try {
        await action();
    } catch {
        showNotice(result, 'That check could not be completed. Please try again.', true);
    } finally {
        form.dataset.busy = 'false';
        form.removeAttribute('aria-busy');
        button.disabled = false;
        button.textContent = buttonText;
    }
}

function clearValidationMessage(result) {
    if (result.querySelector('.notice-error')) result.replaceChildren();
}

claimInput.addEventListener('input', () => {
    claimCount.value = `${claimInput.value.length} / 2,000`;
    clearValidationMessage(document.getElementById('r1'));
});

urlInput.addEventListener('input', () => {
    clearValidationMessage(document.getElementById('r2'));
});

claimInput.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        verifyForm.requestSubmit();
    }
});

verifyForm.addEventListener('submit', event => {
    event.preventDefault();
    const result = document.getElementById('r1');
    const button = verifyForm.querySelector('button[type="submit"]');

    if (!claimInput.value.trim()) {
        showNotice(result, 'Enter a claim or statement to check.', true);
        claimInput.focus();
        return;
    }

    submitSafely(verifyForm, result, button, 'Checking...', () => window.verify());
});

scanForm.addEventListener('submit', event => {
    event.preventDefault();
    const result = document.getElementById('r2');
    const button = scanForm.querySelector('button[type="submit"]');
    const value = urlInput.value.trim();

    if (!value) {
        showNotice(result, 'Enter a website address to scan.', true);
        urlInput.focus();
        return;
    }

    try {
        const candidate = /^[a-z][a-z\d+.-]*:\/\//i.test(value) ? value : `https://${value}`;
        const parsed = new URL(candidate);
        if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.hostname) throw new Error();
    } catch {
        showNotice(result, 'Enter a valid web address, such as example.com.', true);
        urlInput.focus();
        return;
    }

    submitSafely(scanForm, result, button, 'Scanning...', () => window.scan());
});