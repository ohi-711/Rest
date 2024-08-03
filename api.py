from flask import Flask, request, jsonify
import inference

app = Flask(__name__)

detector = inference.RestDetector('torchscript_model_0_66_49_wo_gl.pth')

@app.route('/uploadfile/', methods=['POST'])
def create_upload_file():
    file = request.files['file']
    emotion = detector.detect_emotion(file)
    return jsonify({"emotion": emotion})

if __name__ == '__main__':
    app.run(debug=True)