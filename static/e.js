const cameraVideoStream = document.getElementById('camera-stream');
const canvas = document.getElementById('canvas');
const canvasContext = canvas.getContext('2d');
const cameraResult = document.getElementById('camera-result');

if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia({ video: true })) {
    navigator.mediaDevices
        .getUserMedia({ video: true })
        .then((stream) => {
            cameraVideoStream.srcObject = stream;
            cameraVideoStream.play();
        });
}

let uploading = false;

function captureImage() {
    if (uploading) return; // Prevent multiple requests

    uploading = true;

    // Set canvas dimensions to match video dimensions
    canvas.width = cameraVideoStream.videoWidth;
    canvas.height = cameraVideoStream.videoHeight;

    // Draw the video frame to the canvas
    canvasContext.drawImage(cameraVideoStream, 0, 0);

    // Convert canvas to a Blob and send it to the backend
    canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('file', blob, 'snapshot.png');

        try {
            const response = await fetch('http://127.0.0.1:3000/emotioninference', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const result = await response.json();
            console.log('Emotion:', result.emotion); // Log the emotion returned by the backend
            cameraResult.innerText = `Camera mood: ${result.emotion}`;
        } catch (error) {
            console.error('Error:', error);
        } finally {
            uploading = false; // Allow next upload
        }
    });
}

setInterval(captureImage, 5000);

async function analyzeEmotion() {
    const userInput = document.getElementById('userInput').value;

    const response = await fetch('http://127.0.0.1:3000/analyze_text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: userInput }),
    });

    const result = await response.json();
    document.getElementById('result').innerText = `Current mood: ${result.emotion}`;
}
