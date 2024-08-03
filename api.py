from flask import Flask, request, jsonify
from flask_cors import CORS
import inference

app = Flask(__name__)
CORS(app)

detector = inference.RestDetector('torchscript_model_0_66_49_wo_gl.pth')

@app.route('/uploadfile/', methods=['POST'])
def create_upload_file():
    file = request.files['file']
    emotion = detector.detect_emotion(file)
    print(f"Detected emotion: {emotion}")
    return jsonify({"emotion": emotion})

if __name__ == '__main__':
    app.run(debug=True)