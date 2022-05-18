import base64

import boto3

from config import Config_is


def client_s3() -> object:
    s3_client = boto3.client('s3', aws_access_key_id=Config_is.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=Config_is.AWS_SECRET_ACCESS_KEY)
    return s3_client


def resource_s3() -> object:
    s3 = boto3.resource('s3', aws_access_key_id=Config_is.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=Config_is.AWS_SECRET_ACCESS_KEY)
    return s3


def delete_s3_object(path: str, bucket_name: str = Config_is.S3_BUCKET_NAME, s3_client: object = None) -> bool:
    """
    Delete an object from s3
    """
    if not s3_client:
        s3_client = client_s3()
    print(f"path is {path}")
    s3_client.delete_object(Bucket=bucket_name, Key=path)
    return True


def file_upload_obj_s3(s3_client: object, file, path: str) -> dict:
    """
    Upload files to s3
    """
    response = s3_client.upload_fileobj(file, Config_is.S3_BUCKET_NAME, path,
                                        ExtraArgs={'ContentType': file.content_type, 'ACL': 'public-read'})
    return response


def base64_uploader(s3_resource: object, file_is: object, image_type: str, file_path: str):
    """
    Upload base64 images to S3 bucket
    """
    obj = s3_resource.Object(Config_is.S3_BUCKET_NAME, file_path)
    obj.put(Body=base64.b64decode(file_is), ContentType=image_type, ACL='public-read')
    return True
