(function(){
    const params = new URLSearchParams(window.location.search || '');
    const token = params.get('token') || '';
    const btn = document.getElementById('confirmBtn');
    const message = document.getElementById('formMessage');
    const passwordInput = document.getElementById('password');
    const apiBase = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? 'http://localhost:3000'
        : 'https://azure-service-tags-tracker-dev.vercel.app';

    function showMessage(text, kind='error'){
        if (!message) return;
        message.textContent = text;
        message.className = `form-message ${kind}`;
        message.style.display = 'block';
    }

    if (!token){
        showMessage('Missing or invalid link. Please request a new upgrade email.');
        if (btn) btn.disabled = true;
        return;
    }

    btn?.addEventListener('click', async () => {
        const password = (passwordInput?.value || '').trim();
        if (!password){
            showMessage('Password is required.', 'error');
            return;
        }
        btn.disabled = true;
        btn.textContent = 'Activating...';
        message.style.display = 'none';
        try {
            const res = await fetch(`${apiBase}/api/upgrade_confirm`, {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ token, password })
            });
            const data = await res.json();
            if (res.ok && data.success){
                showMessage('Premium activated! You can close this tab and continue.', 'success');
                if (data.token) {
                    try { window.localStorage.setItem('auth_token', data.token); } catch(_) {}
                }
            } else {
                showMessage(data.error || 'Could not activate premium.');
            }
        } catch(err){
            console.error(err);
            showMessage('Request failed. Please try again.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Activate Premium';
        }
    });
})();
