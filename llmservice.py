import json
import boto3
from logger import logger


# Bedrock client
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

# Generate LLM Response

async def generate_reply(prompt: str):

    logger.info("Calling Claude LLM")

    try:
        # request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        # call Bedrock
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        # parse response
        result = json.loads(response["body"].read())

        logger.info("LLM response received")

        return result["content"][0]["text"]

    except Exception:
        logger.exception("Bedrock call failed")
        raise