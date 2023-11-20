random_string=$(openssl rand -base64 20)
echo $random_string
aws secretsmanager create-secret --name youtube-transcription-http-api-key --secret-string "{\"http-api-key\":\"$random_string\"}"

