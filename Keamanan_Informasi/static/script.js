document.addEventListener('DOMContentLoaded', function() {
    const embedSection = document.getElementById('embedSection');
    const detectSection = document.getElementById('detectSection');
    const showEmbedButton = document.getElementById('showEmbedFormBtn');
    const showDetectButton = document.getElementById('showDetectFormBtn');
    
    window.showForm = function(formName) {
        if (formName === 'embed') {
            if (embedSection) embedSection.style.display = 'block';
            if (detectSection) detectSection.style.display = 'none';
            if (showEmbedButton) showEmbedButton.classList.add('active');
            if (showDetectButton) showDetectButton.classList.remove('active');
        } else if (formName === 'detect') {
            if (embedSection) embedSection.style.display = 'none';
            if (detectSection) detectSection.style.display = 'block';
            if (showEmbedButton) showEmbedButton.classList.remove('active');
            if (showDetectButton) showDetectButton.classList.add('active');
        }
    }

    if (showEmbedButton) {
        showEmbedButton.addEventListener('click', function() {
            window.showForm('embed');
        });
    }

    if (showDetectButton) {
        showDetectButton.addEventListener('click', function() {
            window.showForm('detect');
        });
    }

    
});