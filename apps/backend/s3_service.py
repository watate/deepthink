import asyncio
import json

import boto3

from config import get_settings


def _client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_api,
        aws_access_key_id=settings.s3_api_access_key_id,
        aws_secret_access_key=settings.s3_api_secret,
    )


async def save_tree(tree_id: str, tree_data: dict) -> None:
    def _put():
        settings = get_settings()
        _client().put_object(
            Bucket=settings.s3_bucket,
            Key=f"trees/{tree_id}.json",
            Body=json.dumps(tree_data),
            ContentType="application/json",
        )

    await asyncio.to_thread(_put)


async def load_tree(tree_id: str) -> dict | None:
    def _get():
        settings = get_settings()
        try:
            resp = _client().get_object(
                Bucket=settings.s3_bucket,
                Key=f"trees/{tree_id}.json",
            )
            return json.loads(resp["Body"].read())
        except _client().exceptions.NoSuchKey:
            return None

    return await asyncio.to_thread(_get)


async def list_trees() -> list[dict]:
    def _list():
        settings = get_settings()
        client = _client()
        result = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=settings.s3_bucket, Prefix="trees/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".json"):
                    body = client.get_object(Bucket=settings.s3_bucket, Key=key)
                    data = json.loads(body["Body"].read())
                    result.append(data)
        return result

    return await asyncio.to_thread(_list)


async def delete_tree(tree_id: str) -> None:
    def _delete():
        settings = get_settings()
        _client().delete_object(
            Bucket=settings.s3_bucket,
            Key=f"trees/{tree_id}.json",
        )

    await asyncio.to_thread(_delete)
