from dataclasses import dataclass, field
import time
import uuid


@dataclass
class LocalLambdaContext:
    function_name: str = "my_lambda_function"
    memory_limit_in_mb: int = 128
    timeout_ms: int = 3000
    function_version: str = "$LATEST"
    invoked_function_arn: str = field(init=False)
    aws_request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    log_group_name: str = field(init=False)
    log_stream_name: str = field(init=False)
    identity: object = None
    client_context: object = None
    _start_time: float = field(default_factory=time.time, init=False)

    def __post_init__(self):
        self.invoked_function_arn = (
            f"arn:aws:lambda:ap-northeast-1:123456789012:function:{self.function_name}"
        )
        self.log_group_name = f"/aws/lambda/{self.function_name}"
        self.log_stream_name = (
            f"{time.strftime('%Y/%m/%d')}/[$LATEST]{uuid.uuid4().hex}"
        )

    def get_remaining_time_in_millis(self) -> int:
        elapsed_ms = int((time.time() - self._start_time) * 1000)
        return max(self.timeout_ms - elapsed_ms, 0)
