import json
import logging
import os
import time
import boto3

from moviepy.editor import AudioFileClip
from pymonad.either import Right, Left
from pytube import YouTube

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
    print(f"{func.__name__} took {elapsed_time:.2f} seconds.")
    return result


def get_secretsmanager_client():
    return boto3.client('secretsmanager')


def handler(event, context):
    logger.info(f"{event=}")
    result = (
        Right(event)
        .then(validate_method_and_path)
        .then(validate_api_key(get_secretsmanager_client))
        .then(parse_body)
        .then(validate_url_body_param)
        .then(download_audio_by_link)
        .either(
            process_early_exit,
            process_success
        )
    )

    logger.info(f"{result=}")
    return result


def download_audio_by_link(youtube_url):
    filename_prefix = time_and_log(video_title, youtube_url)
    mp4_path = f"/tmp/{filename_prefix}.mp4"
    mp3_path = f"/tmp/{filename_prefix}.mp3"

    time_and_log(download_audio, youtube_url, mp4_path)
    time_and_log(convert_mp4_to_mp3, mp4_path, mp3_path)

    return mp3_path


def parse_body(event):
    try:
        body = json.loads(event.get("body", '{}'))
        return Right(body)
    except json.JSONDecodeError:
        return Left(EarlyExitReasons.INVALID_JSON)


def process_early_exit(reason):
    match reason:
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


def process_success(data):
    logger.info("Processing success with data: %s", data)
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps({"success": "OK", "data": data}),
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


def load_api_key_from_secrets_manager():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='youtube-transcription-http-api-key')
    return response['SecretString']


if __name__ == "__main__":
    download_audio_by_link("https://www.youtube.com/watch?v=XGJNo8TpuVA")
