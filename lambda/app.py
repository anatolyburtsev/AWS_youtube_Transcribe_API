import json
import logging
import os
import time
from datetime import datetime

import boto3

from moviepy.editor import AudioFileClip
from pymonad.either import Right, Left
from pymonad.tools import curry
from pytube import YouTube
from openai import OpenAI

from validations import validate_url_body_param, validate_method_and_path, EarlyExitReasons, validate_api_key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def time_and_log(func, *args, **kwargs):
    """
    Measures and logs the time taken to execute a given function.

    :param func: Function to be executed.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: The return value of the function.
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time
    logger.info(f"{func.__name__} took {elapsed_time:.2f} seconds.")
    return result


def get_secretsmanager_client():
    return boto3.client('secretsmanager', region_name=os.environ["AWS_REGION"])


def get_dynamodb_resource():
    return boto3.resource("dynamodb")


def handler(event, context):
    logger.info(f"{event=}")
    initial_context = {'event': event}

    result = (
        Right(initial_context)
        .then(validate_method_and_path)
        .then(validate_api_key(get_secretsmanager_client))
        .then(parse_body)
        .then(validate_url_body_param)
        .then(download_audio_by_link(get_dynamodb_resource))
        .then(transcribe_audio(get_secretsmanager_client, get_dynamodb_resource))
        .either(
            process_early_exit,
            process_success
        )
    )

    logger.info(f"{result=}")
    return result


def get_file_size_in_mb(file_path):
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)
    return size_mb


@curry(3)
def transcribe_audio(get_secretsmanager, get_dynamodb, context):
    try:
        if context.get("transcript"):
            return Right(context)

        audio_file_path = context.get("mp4_path")
        secretsmanager_client = get_secretsmanager()

        secret_value = secretsmanager_client.get_secret_value(SecretId='youtube-transcription-openai-key')
        openai_key = json.loads(secret_value['SecretString'])['key']

        openai_client = OpenAI(api_key=openai_key)

        with open(audio_file_path, "rb") as audio_file:
            transcript = time_and_log(
                openai_client.audio.transcriptions.create, model="whisper-1",
                file=audio_file
            )
            context["transcript"] = transcript.text

            cache_transcription(get_dynamodb, context)
            return Right(context)

    except Exception as e:
        logger.error(f"Error: {e}")
        return Left(EarlyExitReasons.INTERNAL_SERVER_ERROR)


def get_cached_transcription(get_dynamodb, youtube_url):
    table = get_dynamodb().Table('youtube_transcribes')
    response = table.get_item(Key={'youtube_url': youtube_url})
    return dict(response.get('Item')) if response.get("Item") else None


def cache_transcription(get_dynamodb, context):
    table = get_dynamodb().Table('youtube_transcribes')
    table.put_item(Item={
        'youtube_url': context.get("youtube_url"),
        'transcript': context.get("transcript"),
        'video_title': context.get("video_title"),
        'date': datetime.now().strftime('%Y-%m-%d')
    })


@curry(2)
def download_audio_by_link(get_dynamodb, context):
    youtube_url = context.get("youtube_url")
    cached_item = get_cached_transcription(get_dynamodb, youtube_url)
    if cached_item:
        logger.info(f"Cache hit for {youtube_url}")
        logger.info(f"{cached_item=}")
        logger.info(f"Before: {context=}")
        context.update(cached_item)
        logger.info(f"After: {context=}")
        return Right(cached_item)

    filename_prefix = time_and_log(video_title, youtube_url)
    mp4_path = f"/tmp/{filename_prefix}.mp4"

    time_and_log(download_audio, youtube_url, mp4_path)
    logger.info(f"mp4 file size: {get_file_size_in_mb(mp4_path)} Mb")

    context["video_title"] = filename_prefix
    context["mp4_path"] = mp4_path
    return Right(context)


def parse_body(context):
    try:
        event = context.get("event")
        body = json.loads(event.get("body", '{}'))
        context["body"] = body
        return Right(context)
    except json.JSONDecodeError:
        return Left(EarlyExitReasons.INVALID_JSON)


def process_early_exit(reason):
    match reason:
        case EarlyExitReasons.HEALTH_CHECK:
            response = {"statusCode": 200, "body": json.dumps({"success": "OK"})}
        case EarlyExitReasons.OPTION_PRE_FLIGHT:
            response = {"statusCode": 200, "body": json.dumps({"success": "OK"})}
        case EarlyExitReasons.INVALID_JSON:
            response = {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid JSON in request"})
            }
        case EarlyExitReasons.INVALID_INPUT:
            response = {"statusCode": 400, "body": json.dumps(
                {"message": "Invalid input: URL is required and must be a valid YouTube URL"})}
        case EarlyExitReasons.INTERNAL_SERVER_ERROR:
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error"})
            }
        case EarlyExitReasons.INVALID_API_KEY:
            response = {
                "statusCode": 401,
                "body": json.dumps({"message": "Invalid API key"})
            }
        case EarlyExitReasons.NOT_FOUND:
            response = {
                "statusCode": 404,
                "body": json.dumps({"message": "Not found"})
            }
        case _:
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": "Unknown error"})
            }

    return {
        "isBase64Encoded": False,
        "headers": {"Content-Type": "application/json"},
        **response
    }


def process_success(context):
    transcript = context.get("transcript")
    logger.info("Processing success with data: %s", transcript)
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps({"success": "OK", "transcript": transcript}),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Content-Type": "application/json",
        },
    }


def video_title(youtube_url: str) -> str:
    """
    Retrieve the title of a YouTube video.

    Examples
    --------
    >>> title = video_title("https://www.youtube.com/watch?v=SampleVideoID")
    >>> print(title)
    'Sample Video Title'
    """
    video_youtube = YouTube(youtube_url)
    return video_youtube.title


def download_audio(youtube_url: str, download_path: str) -> None:
    """
    Download the audio from a YouTube video.

    Examples
    --------
    >>> download_audio("https://www.youtube.com/watch?v=SampleVideoID", "path/to/save/audio.mp4")
    """
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.filter(only_audio=True)[0]
    folder_path, filename = os.path.split(download_path)

    audio_stream.download(output_path=folder_path, filename=filename)


def convert_mp4_to_mp3(input_path: str, output_path: str) -> None:
    """
    Convert an audio file from mp4 format to mp3.

    Examples
    --------
    >>> convert_mp4_to_mp3("path/to/audio.mp4", "path/to/audio.mp3")
    """
    audio_clip = AudioFileClip(input_path)
    audio_clip.write_audiofile(output_path, codec="mp3")


if __name__ == "__main__":
    # download_audio_by_link("https://www.youtube.com/watch?v=XGJNo8TpuVA")
    transcribe_audio(get_secretsmanager_client, "/tmp/The New Stack and Ops for AI.mp3")
