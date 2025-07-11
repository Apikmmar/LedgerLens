document.addEventListener('DOMContentLoaded', function () {
  const uploadForm = document.getElementById('uploadForm');
  const fileInput = document.getElementById('fileInput');
  const fileInputPresigned = document.getElementById('fileInputPresigned');
  const statusDiv = document.getElementById('status');

  if (uploadForm) {
    uploadForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      const file = fileInput.files[0];
      const submitButton = e.target.querySelector('button[type="submit"]');

      if (!file) {
        showStatus('Please select a file first.', 'error');
        return;
      }

      if (!file.type.startsWith('image/')) {
        showStatus('Please select a valid image file.', 'error');
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        showStatus('File size must be less than 10MB.', 'error');
        return;
      }

      showStatus('Uploading and processing...', 'processing');
      submitButton.disabled = true;
      submitButton.classList.add('loading');

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('/', {
          method: 'POST',
          body: formData
        });

        const result = await response.text();

        if (response.ok) {
          showStatus('✅ ' + result, 'success');
        } else {
          showStatus('❌ ' + result, 'error');
        }
      } catch (error) {
        showStatus('❌ Upload failed: ' + error.message, 'error');
      } finally {
        submitButton.disabled = false;
        submitButton.classList.remove('loading');
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (file) {
        const fileSize = (file.size / (1024 * 1024)).toFixed(2);
        showStatus(`Selected: ${file.name} (${fileSize} MB)`, 'processing');
      }
    });
  }

  if (fileInputPresigned) {
    fileInputPresigned.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (file) {
        const fileSize = (file.size / (1024 * 1024)).toFixed(2);
        showStatus(`Selected: ${file.name} (${fileSize} MB)`, 'processing');
      }
    });
  }

  // Presigned upload function
  window.uploadWithPresigned = async function () {
    const file = fileInputPresigned?.files[0];
    const button = event.target;

    if (!file) {
      showStatus('Please select a file first.', 'error');
      return;
    }

    if (!file.type.startsWith('image/')) {
      showStatus('Please select a valid image file.', 'error');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      showStatus('File size must be less than 10MB.', 'error');
      return;
    }

    button.disabled = true;
    button.classList.add('loading');
    showStatus('Generating pre-signed URL...', 'processing');

    try {
      const res = await fetch('/presign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, type: file.type })
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || 'Failed to get pre-signed URL');

      const { url, key } = data;

      showStatus('Uploading to S3...', 'processing');

      const uploadRes = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file
      });

      if (uploadRes.ok) {
        showStatus('✅ Upload successful! Processing...', 'processing');

        const processRes = await fetch('/process', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ key })
        });

        if (processRes.ok) {
          showStatus('✅ Receipt processed successfully!', 'success');
        } else {
          showStatus('⚠️ Upload successful but processing failed', 'error');
        }
      } else {
        throw new Error('Upload to S3 failed');
      }
    } catch (error) {
      showStatus('❌ Error: ' + error.message, 'error');
    } finally {
      button.disabled = false;
      button.classList.remove('loading');
    }
  };

  // Drag and drop support
  setupDragAndDrop();
});

// Utilities
function showStatus(message, type) {
  const statusDiv = document.getElementById('status');
  if (!statusDiv) return;

  statusDiv.textContent = message;
  statusDiv.className = type;
  statusDiv.style.display = 'block';

  if (type === 'success') {
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 5000);
  }
}

function setupDragAndDrop() {
  const fileInputs = document.querySelectorAll('input[type="file"]');

  fileInputs.forEach(input => {
    const container = input.closest('.container');
    if (!container) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      container.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
      }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      container.addEventListener(eventName, () => container.classList.add('highlight'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      container.addEventListener(eventName, () => container.classList.remove('highlight'), false);
    });

    container.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        input.files = files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, false);
  });
}

console.log('✅ upload.js loaded successfully');
