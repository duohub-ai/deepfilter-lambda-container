import json
import os
import logging
from pydub import AudioSegment
from df.enhance import enhance, load_audio, save_audio

# Import the modules
from modules.init import load_deepfilter_model
from modules.s3 import fetch_file_from_s3, upload_file_to_s3
from modules.file import create_file_entry, fetch_file_from_dynamodb

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Define global variables for the model and state
model = None
df_state = None

def clean_audio(input_file: str, output_file: str, model, df_state) -> bool:
    """Clean a single audio file using DeepFilter."""
    try:
        temp_wav = input_file
        if not input_file.endswith('.wav'):
            audio = AudioSegment.from_file(input_file)
            temp_wav = input_file.replace(os.path.splitext(input_file)[1], '_temp.wav')
            audio.export(temp_wav, format="wav")

        audio, _ = load_audio(temp_wav, sr=df_state.sr())
        enhanced = enhance(model, df_state, audio)

        # Ensure the output file has only one extension
        output_file = os.path.splitext(output_file)[0] + '.wav'
        save_audio(output_file, enhanced, df_state.sr())
        
        if temp_wav != input_file:
            os.remove(temp_wav)

        logger.info(f"Enhanced audio saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error cleaning audio file {input_file}: {str(e)}")
        return False

def lambda_handler(event, context):
    global model, df_state
    logger.info("Lambda function started")
    logger.info(f"Event: {event}")

    # Parse AppSync event
    if 'arguments' in event:
        # This is an AppSync request
        arguments = event['arguments']
        file_id = arguments.get('input', {}).get('fileID')
    else:
        # Fallback for direct Lambda invocation
        file_id = event.get('fileID')

    region = os.environ.get('AWS_REGION')

    if not file_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'message': 'fileID is required in the request'
            })
        }

    file_metadata = fetch_file_from_dynamodb(file_id)
    if not file_metadata:
        return {
            'statusCode': 404,
            'body': json.dumps({
                'success': False,
                'message': f'File with ID {file_id} not found in DynamoDB'
            })
        }

    user_id = file_metadata.get('userID', {}).get('S')
    if not user_id:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'User ID is missing in file metadata'
            })
        }

    file_key = file_metadata.get('key', {}).get('S')
    if not file_key:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'File key is missing in DynamoDB record'
            })
        }

    file_content = fetch_file_from_s3(file_key, region)
    if not file_content:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'Failed to fetch file from S3'
            })
        }

    input_file_path = f"/tmp/{file_key.split('/')[-1]}"
    with open(input_file_path, 'wb') as f:
        f.write(file_content)

    model, df_state = load_deepfilter_model(model, df_state)

    # Convert to WAV and enhance
    input_basename = os.path.splitext(os.path.basename(input_file_path))[0]
    wav_output_path = f"/tmp/enhanced_{input_basename}.wav"
    if not clean_audio(input_file_path, wav_output_path, model, df_state):
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'Error enhancing the audio file'
            })
        }

    # Convert WAV to MP3
    mp3_output_path = f"/tmp/enhanced_{input_basename}.mp3"

    try:
        audio = AudioSegment.from_wav(wav_output_path)
        audio.export(mp3_output_path, format="mp3")
        logger.info(f"Converted enhanced audio to MP3: {mp3_output_path}")
    except Exception as e:
        logger.error(f"Error converting WAV to MP3: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'Error converting enhanced audio to MP3'
            })
        }

    # Upload MP3 file to S3 with the new path structure
    corrected_filename = f"enhanced_{input_basename}.mp3"
    s3_key = f"{user_id}/enhanced/{corrected_filename}"
    if not upload_file_to_s3(mp3_output_path, s3_key, region, corrected_filename):
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'Error uploading the cleaned MP3 file to S3'
            })
        }

    file_size = os.path.getsize(mp3_output_path)
    file_length = len(audio) / 1000  # Length in seconds
    new_file_entry = create_file_entry(corrected_filename)

    # Clean up temporary files
    try:
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
        if os.path.exists(wav_output_path):
            os.remove(wav_output_path)
        if os.path.exists(mp3_output_path):
            os.remove(mp3_output_path)
    except Exception as e:
        logger.warning(f"Error while cleaning up temporary files: {str(e)}")
        # Continue execution even if cleanup fails

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'message': 'File fetched, enhanced, converted to MP3, and new entry created successfully',
            'newFileID': new_file_entry['id']['S']
        })
    }
