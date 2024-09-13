import json
import logging
import os
import sys
import time
import uuid
import requests
import streamlit as st
from azure.identity import DefaultAzureCredential

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="[%(asctime)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
logger = logging.getLogger(__name__)

SPEECH_ENDPOINT = st.secrets["Azure_Avatar"]["SPEECH_ENDPOINT"]
PASSWORDLESS_AUTHENTICATION = False
API_VERSION = "2024-04-15-preview"
SUBSCRIPTION_KEY = st.secrets["Azure_Avatar"]["SUBSCRIPTION_KEY"]

def _create_job_id():
    return str(uuid.uuid4())

def _authenticate():
    if PASSWORDLESS_AUTHENTICATION:
        credential = DefaultAzureCredential()
        token = credential.get_token('https://cognitiveservices.azure.com/.default')
        return {'Authorization': f'Bearer {token.token}'}
    else:
        return {'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY}

def submit_synthesis(text_input):
    job_id = _create_job_id()
    url = f'{SPEECH_ENDPOINT}/avatar/batchsyntheses/{job_id}?api-version={API_VERSION}'
    header = {
        'Content-Type': 'application/json'
    }
    header.update(_authenticate())

    payload = {
        'synthesisConfig': {
            "voice": 'en-US-JennyMultilingualNeural',
        },
        "inputKind": "plainText",
        "inputs": [
            {
                "content": text_input,
            },
        ],
        "avatarConfig": {
            "customized": False,
            "talkingAvatarCharacter": 'Lisa',
            "talkingAvatarStyle": 'casual-sitting',
            "videoFormat": "mp4",
            "videoCodec": "h264",
            "subtitleType": "soft_embedded",
            "backgroundColor": "#FFFFFFFF",
        }
    }

    response = requests.put(url, json.dumps(payload), headers=header)
    if response.status_code < 400:
        logger.info(f'Batch avatar synthesis job submitted successfully. Job ID: {response.json()["id"]}')
        return job_id
    else:
        logger.error(f'Failed to submit batch avatar synthesis job: [{response.status_code}], {response.text}')
        return None

def get_synthesis(job_id):
    url = f'{SPEECH_ENDPOINT}/avatar/batchsyntheses/{job_id}?api-version={API_VERSION}'
    header = _authenticate()

    response = requests.get(url, headers=header)
    if response.status_code < 400:
        if response.json()['status'] == 'Succeeded':
            logger.info(f'Job succeeded. Download URL: {response.json()["outputs"]["result"]}')
            return response.json()['outputs']['result']
        logger.info(f'Job status: {response.json()["status"]}')
        return response.json()['status']
    else:
        logger.error(f'Failed to get batch synthesis job: {response.text}')
        return None

def download_video(url):
    logger.info(f'Attempting to download video from {url}')
    response = requests.get(url)
    if response.status_code == 200:
        filename = f"avatar_video_{uuid.uuid4()}.mp4"
        with open(filename, "wb") as f:
            f.write(response.content)
        logger.info(f'Video downloaded successfully to {filename}')
        return filename
    else:
        logger.error(f"Failed to download video: {response.status_code}")
        return None

def generate_avatar_video(text_input):
    logger.info(f'Generating avatar video for text: "{text_input}"')
    job_id = submit_synthesis(text_input)
    if job_id is None:
        return "Failed to submit job"

    while True:
        status = get_synthesis(job_id)
        if isinstance(status, str) and status.startswith('http'):  # It's the download URL
            logger.info('Batch avatar synthesis job succeeded')
            video_path = download_video(status)
            if video_path:
                logger.info(f'Video generated and downloaded: {video_path}')
                return video_path
            else:
                logger.error('Failed to download video')
                return "Failed to download video"
        elif status == 'Failed':
            logger.error('Batch avatar synthesis job failed')
            return "Job failed"
        else:
            logger.info(f'Batch avatar synthesis job is still running, status [{status}]')
            time.sleep(5)