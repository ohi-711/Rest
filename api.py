from fastapi import FastAPI, UploadFile

import inference

app = FastAPI()

detector = inference.RestDetector('/Users/greatj/Downloads/torchscript_model_0_66_49_wo_gl.pth')

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    emotion = detector.detect_emotion(file.file)
    return {"emotion": emotion}