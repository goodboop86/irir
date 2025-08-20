import inspect
import logging
from functools import wraps
import asyncio

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Utils:
    logger = logging.getLogger(__name__)

    @staticmethod
    def broad_enable(target):
        true_values = {"true", "True", "on", "yes", "1", True, 1}
        return target in true_values

    # --- Async trace decorator ---
    @staticmethod
    def async_trace(func):
        """
        非同期メソッドの呼び出しとその完了をログに記録するデコレータ。
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # クラス名とメソッド名を取得
            # Check if args[0] is an instance of a class before accessing __class__
            class_name = (
                args[0].__class__.__name__
                if args and hasattr(args[0], "__class__")
                else "Function"
            )
            method_name = func.__name__

            Utils.logger.info(f"Async Method '{class_name}.{method_name}' called.")

            try:
                result = await func(*args, **kwargs)
                Utils.logger.info(
                    f"Async Method '{class_name}.{method_name}' completed successfully."
                )
                return result
            except Exception as e:
                Utils.logger.error(
                    f"Async Method '{class_name}.{method_name}' failed with error: {e}"
                )
                raise

        return wrapper

    # --- Combined trace decorator ---
    @classmethod
    def trace(cls, func):
        """
        同期関数または非同期関数をトレースするデコレータ。
        """
        if inspect.iscoroutinefunction(func):
            return cls.async_trace(func)
        else:
            # Define the synchronous wrapper here
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # クラス名とメソッド名を取得
                class_name = (
                    args[0].__class__.__name__
                    if args and hasattr(args[0], "__class__")
                    else "Function"
                )
                method_name = func.__name__

                Utils.logger.info(f"Method '{class_name}.{method_name}' called.")

                try:
                    result = func(*args, **kwargs)
                    Utils.logger.info(
                        f"Method '{class_name}.{method_name}' completed successfully."
                    )
                    return result
                except Exception as e:
                    Utils.logger.error(
                        f"Method '{class_name}.{method_name}' failed with error: {e}"
                    )
                    raise

            return sync_wrapper
