let cropper = null;
let currentCropImage = null;

function initCropper(imageUrl) {
  const modal = document.getElementById('cropperModal');
  const image = document.getElementById('cropperImage');
  
  // Set the image source
  image.src = imageUrl;
  
  // Destroy existing cropper if any
  if (cropper) {
    cropper.destroy();
  }
  
  // Show modal
  modal.style.display = 'flex';
  
  // Initialize cropper after image loads
  image.onload = function() {
    cropper = new Cropper(image, {
      aspectRatio: 3 / 4, // Standard book cover ratio
      viewMode: 1,
      autoCropArea: 0.8,
      responsive: true,
      guides: true,
      highlight: true,
      cropBoxMovable: true,
      cropBoxResizable: true,
      toggleDragModeOnDblclick: true,
    });
  };
}

function saveCroppedImage() {
  if (!cropper) return;
  
  const canvas = cropper.getCroppedCanvas({
    maxWidth: 800,
    maxHeight: 1066,
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high',
  });
  
  // Convert canvas to blob and create form data
  canvas.toBlob(function(blob) {
    const formData = new FormData();
    formData.append('image', blob, 'cropped-cover.png');
    
    // Create a temporary file input to simulate file upload
    const dataTransfer = new DataTransfer();
    const file = new File([blob], 'cropped-cover.png', { type: 'image/png' });
    dataTransfer.items.add(file);
    
    // Set the file input
    const fileInput = document.querySelector('input[name="cover_file"]');
    fileInput.files = dataTransfer.files;
    
    // Update preview
    const reader = new FileReader();
    reader.onload = function(e) {
      document.getElementById('coverPreview').src = e.target.result;
      document.getElementById('coverPreview').style.display = 'block';
    };
    reader.readAsDataURL(blob);
    
    closeCropper();
  }, 'image/png');
}

function closeCropper() {
  const modal = document.getElementById('cropperModal');
  modal.style.display = 'none';
  if (cropper) {
    cropper.destroy();
    cropper = null;
  }
}

// Listen for cover file input changes
document.addEventListener('DOMContentLoaded', function() {
  const coverInput = document.querySelector('input[name="cover_file"]');
  
  if (coverInput) {
    coverInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(evt) {
          initCropper(evt.target.result);
        };
        reader.readAsDataURL(file);
      }
    });
  }
});