from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_video_id(url):
    """Extract the video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([^&?/]+)',
        r'(?:embed/|v%3D|vi%2F)([^%&?/]+)',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    """Get the transcript of a YouTube video."""
    try:
        # Get the list of available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        logger.info(f"Available transcripts: {[tr.language_code for tr in transcript_list]}")
        
        # Try to get the manually created English transcript first
        try:
            logger.info("Trying to get the manually created transcript")
            transcript = transcript_list.find_manually_created_transcript(['en', 'en-US'])
            logger.info(f"Found manually created transcript in {transcript.language_code}")
            return ' '.join([entry['text'] for entry in transcript.fetch()])
        except Exception as e:
            logger.warning(f"Could not get manually created transcript: {str(e)}")
        
        # Try to get any English transcript
        try:
            logger.info("Trying to get any English transcript")
            transcript = transcript_list.find_transcript(['en', 'en-US'])
            logger.info(f"Found transcript in {transcript.language_code}")
            return ' '.join([entry['text'] for entry in transcript.fetch()])
        except Exception as e:
            logger.warning(f"Could not get English transcript: {str(e)}")
        
        # If no English transcript is found, try to get the first available transcript
        try:
            logger.info("Trying to get the first available transcript")
            for transcript in transcript_list:
                logger.info(f"Using transcript in {transcript.language_code}")
                return ' '.join([entry['text'] for entry in transcript.fetch()])
        except Exception as e:
            logger.warning(f"Could not get any transcript: {str(e)}")
            
        # If all else fails, try the direct method
        try:
            logger.info("Trying direct transcript retrieval")
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            return ' '.join([entry['text'] for entry in transcript_data])
        except Exception as e:
            logger.warning(f"Direct transcript retrieval failed: {str(e)}")
            
        return None
    except Exception as e:
        logger.error(f"Error getting transcript: {str(e)}")
        return None

def summarize_transcript(transcript):
    """Summarize the transcript using OpenAI API."""
    try:
        logger.info(f"Sending transcript of length {len(transcript)} to OpenAI")
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You summarize transcripts of YouTube videos and output the summary as if it is a very short article itself. Do not mention the video title or the video URL or the transcript itself in the summary. Do not include any other text than the summary."
                },
                {
                    "role": "user",
                    "content": f"Please summarize this transcript: {transcript}"
                }
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1
        )
        logger.info("Successfully received response from OpenAI")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in summarize_transcript: {str(e)}")
        return str(e)

@app.route('/summarize', methods=['POST'])
def summarize_video():
    """Endpoint to summarize a YouTube video."""
    logger.info(f"Received request: {request.method} {request.path}")
    try:
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        if not data or 'youtube_url' not in data:
            logger.warning("Missing youtube_url in request")
            return jsonify({'error': 'YouTube URL is required'}), 400
            
        youtube_url = data['youtube_url']
        logger.info(f"Processing URL: {youtube_url}")
        
        video_id = extract_video_id(youtube_url)
        if not video_id:
            logger.warning(f"Invalid YouTube URL: {youtube_url}")
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        logger.info(f"Extracted video ID: {video_id}")
        transcript = get_transcript(video_id)
        
        if not transcript:
            logger.warning(f"No transcript available for video: {video_id}")
            return jsonify({'error': 'No transcript available for this video'}), 404
        
        logger.info("Got transcript, summarizing...")
        summary = summarize_transcript(transcript)
        
        logger.info("Returning summary to client")
        return jsonify({'summary': summary})
    except Exception as e:
        logger.error(f"Error in /summarize endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': f"Server error: {str(e)}"}), 500

# Add a simple test endpoint
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

if __name__ == '__main__':
    logger.info("Starting Flask server")
    # Use host='0.0.0.0' to make the server externally visible
    app.run(debug=True, host='0.0.0.0', port=5001) 