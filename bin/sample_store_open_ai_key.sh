openai_key=""
aws secretsmanager create-secret --name youtube-transcription-openai-key --secret-string "{\"key\":\"$openai_key\"}"

