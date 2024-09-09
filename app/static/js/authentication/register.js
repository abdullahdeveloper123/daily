/**
 * Handles file uploads for a specific input field.
 * @param {string} inputId - The ID of the file input element.
 * @param {string} containerId - The ID of the container where files will be displayed.
 * @param {string} warningId - The ID of the warning element for file limit.
 * @param {string} typeWarningId - The ID of the warning element for file type.
 * @param {Array<string>} acceptedTypes - List of accepted MIME types for the file input.
 * @param {number} maxSize - The maximum file size in bytes for the files.
 */
function handleFileUpload(inputId, containerId, warningId, typeWarningId, acceptedTypes, maxSize) {
    const fileInput = document.getElementById(inputId);
    const fileContainer = document.getElementById(containerId);
    const warning = document.getElementById(warningId);
    const typeWarning = document.getElementById(typeWarningId);

    fileInput.addEventListener('change', function(event) {
        const files = event.target.files;
        const currentFiles = fileContainer.children.length;

        // Hide all warnings initially
        warning.style.display = 'none';
        typeWarning.style.display = 'none';

        // Check if more than three files are selected
        if (files.length + currentFiles > 3) {
            warning.style.display = 'block'; // Show file limit warning
            event.target.value = ''; // Clear the input
            return;
        }

        Array.from(files).forEach(file => {
            // Check if file size exceeds the limit
            if (file.size > maxSize) {
                // Show alert for file size limit
                alert(` please upload file lower than ${maxSize / (1024 * 1024)} MB.`);
                event.target.value = ''; // Clear the input
                return;
            }

            // Check if file type is acceptable
            if (!acceptedTypes.includes(file.type)) {
                typeWarning.textContent = 'File type not acceptable. Please upload a file of the correct type.'; // Update type warning message
                typeWarning.style.display = 'block'; // Show type warning
                event.target.value = ''; // Clear the input
                return;
            }

            // Create file preview element
            const fileWrapper = document.createElement('div');
            fileWrapper.classList.add('file-wrapper');

            let fileElement;

            // Handle image files
            if (file.type.startsWith('image/')) {
                fileElement = document.createElement('img');
                fileElement.src = URL.createObjectURL(file);
            }
            // Handle video files
            else if (file.type.startsWith('video/')) {
                fileElement = document.createElement('video');
                fileElement.src = URL.createObjectURL(file);
                fileElement.controls = true; // Add controls for videos
            }
            // Handle document files
            else {
                fileElement = document.createElement('span');
                fileElement.textContent = file.name; // Display file name for documents
            }

            // Create remove icon
            const removeIcon = document.createElement('div');
            removeIcon.classList.add('remove-icon');
            removeIcon.textContent = 'x';
            removeIcon.addEventListener('click', function() {
                fileWrapper.remove(); // Remove the file when icon is clicked
            });

            fileWrapper.appendChild(fileElement);
            fileWrapper.appendChild(removeIcon);
            fileContainer.appendChild(fileWrapper);
        });
    });
}

// Initialize file upload handlers with size limits
handleFileUpload('imageInput', 'imageContainer', 'imageWarning', 'imageTypeWarning', ['image/jpeg', 'image/png', 'image/gif'], 1 * 1024 * 1024); // 10 MB for images
handleFileUpload('videoInput', 'videoContainer', 'videoWarning', 'videoTypeWarning', ['video/mp4', 'video/webm', 'video/ogg'], 100 * 1024 * 1024); // 100 MB for videos
handleFileUpload('docInput', 'docContainer', 'docWarning', 'docTypeWarning', ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'], 50 * 1024 * 1024); // 50 MB for documents
