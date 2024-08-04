const cameraVideoStream = document.getElementById('camera-stream');
const canvas = document.getElementById('canvas');
const canvasContext = canvas.getContext('2d');
const cameraResult = document.getElementById('camera-result');
const resultElement = document.getElementById('result'); // Added to reference the current mood element

if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia({ video: true })) {
    navigator.mediaDevices
        .getUserMedia({ video: true })
        .then((stream) => {
            cameraVideoStream.srcObject = stream;
            cameraVideoStream.play();
        });
}

let uploading = false;

function updateTextColor(emotion) {
    const colorMap = {
        Neutral: '#565676',
        Joy: '#dfad0a',
        Sadness: '#1443a7',
        Anger: '#b91e1e',
        Fear: 'purple',
        Disgust: 'green',
        Surprise: 'pink',
        Stressed: 'brown'
    };

    const color = colorMap[emotion] || '#565676'; // Default color if emotion not found
    cameraResult.style.color = color;
    resultElement.style.color = color;
}

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
            if (result.emotion) {
                console.log('Emotion:', result.emotion);
                cameraResult.innerText = `Camera mood: ${result.emotion}`;
                updateTextColor(result.emotion); // Update text color based on mood
            } else {
                cameraResult.innerText = ''; // Clear the cameraResult element
            }
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
    resultElement.innerText = `Current mood: ${result.emotion}`;
    updateTextColor(result.emotion); // Update text color based on mood
}

async function fetchCurrentTrack() {
    try {
        const response = await fetch('http://127.0.0.1:3000/current_track');

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        if (data.error) {
            console.error(data.error);
            return;
        }

        console.log(data);

        document.getElementById('album-cover').src = data.cover;
        document.getElementById('track-name').textContent = data.title;
        document.getElementById('artist-name').textContent = data.artist;
    } catch (error) {
        console.error('Error fetching current track:', error);
    }
}

window.onload = function() {
    fetchCurrentTrack();
    setInterval(fetchCurrentTrack, 500); // Fetch song info every 
};

document.addEventListener('DOMContentLoaded', function() {
    const playPauseBtn = document.getElementById('playPauseBtn');
    let isPlaying = false;

    playPauseBtn.addEventListener('click', function() {
        isPlaying = !isPlaying;

        if (isPlaying) {
            playPauseBtn.textContent = 'Pause';
            playPauseBtn.classList.add('pause-btn');
            playPauseBtn.classList.remove('play-btn');

            const response = fetch('http://127.0.0.1:3000/start_playback', {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }


        } else {
            playPauseBtn.textContent = 'Play';
            playPauseBtn.classList.add('play-btn');
            playPauseBtn.classList.remove('pause-btn');

        }
    });
});
