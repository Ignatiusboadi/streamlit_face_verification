// camera_script.js

document.addEventListener('DOMContentLoaded', function () {
    const enrollButton = document.getElementById('enroll-take-pic-btn');
    const verifyButton = document.getElementById('verify-take-pic-btn');

    // Function to access the camera and capture an image
    function accessCameraAndCapturePicture(storeId) {
        navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();

            video.addEventListener('loadeddata', () => {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const context = canvas.getContext('2d');
                context.drawImage(video, 0, 0, canvas.width, canvas.height);

                const imageData = canvas.toDataURL('image/jpeg');

                const imageStoreInput = document.querySelector(`#${storeId} input`);
                imageStoreInput.value = imageData;
                const event = new Event('input', { bubbles: true });
                imageStoreInput.dispatchEvent(event);

                stream.getTracks().forEach(track => track.stop());
            });
        }).catch(err => {
            console.error("Error accessing the camera: ", err);
        });
    }

    if (enrollButton) {
        enrollButton.addEventListener('click', function () {
            accessCameraAndCapturePicture('enroll-image-store');
        });
    }

    if (verifyButton) {
        verifyButton.addEventListener('click', function () {
            accessCameraAndCapturePicture('verify-image-store');
        });
    }
});
