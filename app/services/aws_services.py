import base64
import boto3

from config import Config_is


class AmazonServices:
    def __init__(self):
        self.s3_client = boto3.client('s3', aws_access_key_id=Config_is.AWS_ACCESS_KEY_ID,
                                      aws_secret_access_key=Config_is.AWS_SECRET_ACCESS_KEY)
        self.s3_resource = boto3.resource('s3', aws_access_key_id=Config_is.AWS_ACCESS_KEY_ID,
                                          aws_secret_access_key=Config_is.AWS_SECRET_ACCESS_KEY)

    def delete_s3_object(self, path: str) -> bool:
        """
        Delete an object from s3
        """
        self.s3_client.delete_object(Bucket=Config_is.S3_BUCKET_NAME, Key=path)
        return True

    def file_upload_obj_s3(self, file, path: str) -> dict:
        """
        Upload files to s3
        """
        response = self.s3_client.upload_fileobj(file, Config_is.S3_BUCKET_NAME, path,
                                                 ExtraArgs={'ContentType': file.content_type, 'ACL': 'public-read'})
        return response

    def base64_uploader(self, file_is: object, image_type: str, file_path: str) -> bool:
        """
        Upload base64 images to S3 bucket
        """
        s3_obj = self.s3_resource.Object(Config_is.S3_BUCKET_NAME, file_path)
        s3_obj.put(Body=base64.b64decode(file_is), ContentType=image_type, ACL='public-read')
        return True
