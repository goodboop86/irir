import inspect
import logging
from functools import wraps

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Utils:
    logger = logging.getLogger(__name__)

    @staticmethod
    def broad_enable(target):
        true_values = {"true", "True", "on", "yes", True, 1}
        return target in true_values
    

    def trace(func):
        """
        メソッドの呼び出しとその完了をログに記録するデコレータ。
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # クラス名とメソッド名を取得
            class_name = args[0].__class__.__name__ if args else "Function"
            method_name = func.__name__

            Utils.logger.info(f"Method '{class_name}.{method_name}' called.")
            
            try:
                result = func(*args, **kwargs)
                # logger.info(f"Method '{class_name}.{method_name}' completed successfully.")
                return result
            except Exception as e:
                logger.error(f"Method '{class_name}.{method_name}' failed with error: {e}")
                raise

        return wrapper

