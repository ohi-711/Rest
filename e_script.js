const cameraVideoStream = document.getElementById('camera-stream');
const canvas = document.getElementById('canvas');
const canvasContext = canvas.getContext('2d');

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
            const response = await fetch('http://127.0.0.1:5000/uploadfile/', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const result = await response.json();
            console.log('Emotion:', result.emotion); // Log the emotion returned by the backend
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

    const response = await fetch('http://127.0.0.1:5000/analyze_text', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: userInput }),
    });

    const result = await response.json();
    document.getElementById('result').innerText = `Current mood: ${result.emotion}`;
}
