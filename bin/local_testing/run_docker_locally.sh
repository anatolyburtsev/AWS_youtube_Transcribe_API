docker build . -t yt_tr
docker run -p 9000:8080 -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_ACCESS_KEY_ID -e AWS_REGION=us-east-1 yt_tr