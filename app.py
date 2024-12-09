import os
from flask import Flask, request, send_file, jsonify
import torchaudio
from df import enhance, init_df

app = Flask(__name__)

# Initialize the DeepFilterNet model
model, df_state, _ = init_df()

@app.route('/clean', methods=['POST'])
def clean_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    input_path = os.path.join('/tmp', audio_file.filename)
    audio_file.save(input_path)
    
    output_path = os.path.join('/tmp', f'cleaned_{audio_file.filename}')
    
    waveform, sample_rate = torchaudio.load(input_path)
    cleaned_waveform = enhance(model, df_state, waveform, sample_rate)
    torchaudio.save(output_path, cleaned_waveform, sample_rate)
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
