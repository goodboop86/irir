from dataclasses import dataclass


@dataclass
class RegisterLambdaEvent:
    AWS_PROFILE: str
    AWS_SECRET_MANAGER__SECRET_NAME: str
    AWS_SECRET_MANAGER__SECRET_KEY_NAME: str
    AWS_S3__BUCKET_NAME: str
    AWS_REGION_NAME: str
    AWS_DYNAMODB__TARGET_TABLE: str
    YYYYMMDD: str
    WORK_DIR: str
    ENV: str
