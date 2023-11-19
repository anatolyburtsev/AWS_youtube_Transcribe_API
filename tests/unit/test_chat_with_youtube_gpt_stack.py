import aws_cdk as core
import aws_cdk.assertions as assertions

from chat_with_youtube_gpt.chat_with_youtube_gpt_stack import ChatWithYoutubeGptStack

# example tests. To run these tests, uncomment this file along with the example
# resource in chat_with_youtube_gpt/chat_with_youtube_gpt_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ChatWithYoutubeGptStack(app, "chat-with-youtube-gpt")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
