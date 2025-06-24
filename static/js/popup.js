document.addEventListener('DOMContentLoaded', function() {
    // Get all meme images
    const memeImages = document.querySelectorAll('.meme-image');
    const popup = document.getElementById('imagePopup');
    const popupImage = document.getElementById('popupImage');
    const closeBtn = document.querySelector('.close-btn');
    
    // Add click event to each meme image
    memeImages.forEach(image => {
        image.addEventListener('click', function() {
            // Set the popup image source to the clicked image's source
            popupImage.src = this.src;
            
            // Show the popup with fade-in animation
            popup.style.display = 'flex';
            popup.classList.add('fade-in');
        });
    });
    
    // Close popup when clicking the close button
    closeBtn.addEventListener('click', function() {
        popup.style.display = 'none';
    });
    
    // Close popup when clicking outside the image
    popup.addEventListener('click', function(e) {
        if (e.target === popup) {
            popup.style.display = 'none';
        }
    });
    
    // Close popup when pressing Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && popup.style.display === 'flex') {
            popup.style.display = 'none';
        }
    });
});