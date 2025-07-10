document.getElementById('uploadForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const fileInput = document.getElementById('fileInput');
  const file = fileInput.files[0];
  const statusDiv = document.getElementById('status');
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

async function uploadWithPresigned() {
  const fileInput = document.getElementById("fileInputPresigned");
  const file = fileInput.files[0];
  const button = event.target;

  if (!file) {
    showStatus("Please select a file first.", 'error');
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
  showStatus("Generating pre-signed URL...", 'processing');

  try {
    const res = await fetch("/presign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, type: file.type })
    });

    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.error || 'Failed to get pre-signed URL');
    }

    const { url, key } = data;

    showStatus("Uploading to S3...", 'processing');

    const uploadRes = await fetch(url, {
      method: "PUT",
      headers: { "Content-Type": file.type },
      body: file
    });

    if (uploadRes.ok) {
      showStatus("✅ Upload successful! Processing...", 'processing');
      
      // Trigger Lambda processing
      const processRes = await fetch("/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: key })
      });
      
      if (processRes.ok) {
        showStatus("✅ Receipt processed successfully!", 'success');
      } else {
        showStatus("⚠️ Upload successful but processing failed", 'error');
      }
    } else {
      throw new Error('Upload to S3 failed');
    }
  } catch (error) {
    showStatus("❌ Error: " + error.message, 'error');
  } finally {
    button.disabled = false;
    button.classList.remove('loading');
  }
}

// Utility function to show status messages
function showStatus(message, type) {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = message;
  statusDiv.className = type;
  statusDiv.style.display = 'block';
  
  // Auto-hide success messages after 5 seconds
  if (type === 'success') {
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 5000);
  }
}

// File input change handlers for better UX
document.getElementById('fileInput').addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (file) {
    const fileSize = (file.size / (1024 * 1024)).toFixed(2);
    showStatus(`Selected: ${file.name} (${fileSize} MB)`, 'processing');
  }
});

document.getElementById('fileInputPresigned').addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (file) {
    const fileSize = (file.size / (1024 * 1024)).toFixed(2);
    showStatus(`Selected: ${file.name} (${fileSize} MB)`, 'processing');
  }
});

// Drag and drop functionality
function setupDragAndDrop() {
  const fileInputs = document.querySelectorAll('input[type="file"]');
  
  fileInputs.forEach(input => {
    const container = input.closest('.container');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      container.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
      container.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
      container.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
      container.classList.add('highlight');
    }
    
    function unhighlight(e) {
      container.classList.remove('highlight');
    }
    
    container.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
      const dt = e.dataTransfer;
      const files = dt.files;
      
      if (files.length > 0) {
        input.files = files;
        const event = new Event('change', { bubbles: true });
        input.dispatchEvent(event);
      }
    }
  });
}

// Initialize drag and drop when page loads
document.addEventListener('DOMContentLoaded', setupDragAndDrop);