import httpx
import json
import logging

logger = logging.getLogger(__name__)

class VOSClient:
    """
    VOS3000 API 客户端
    
    规范：
    - 接口格式采用 JSON 定义
    - 采用 UTF-8 格式编码
    - 接口采用 POST 方式提交至 VOS3000 WEB 服务
    - 对于接口返回码，非0表示失败
    - HTML 头部信息 Content-Type 设置为 text/html;charset-UTF-8
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=timeout)
        logger.info(f"VOS Client initialized for {self.base_url}")
    
    def path_url(self, path: str) -> str:
        """构建完整的 API URL"""
        if not path.startswith('/'):
            path = '/' + path
        return f"{self.base_url}{path}"
    
    def post(self, path: str, payload: dict = None) -> dict:
        """
        发送 POST 请求到 VOS3000
        
        Args:
            path: API 路径
            payload: 请求参数（字典格式）
            
        Returns:
            dict: 响应数据，包含 retCode 字段
                - retCode = 0: 成功
                - retCode != 0: 失败，exception 字段包含错误信息
        """
        url = self.path_url(path)
        
        # 按照 VOS3000 规范设置请求头
        headers = {
            "Content-Type": "text/html;charset=UTF-8"
        }
        
        # 确保 payload 不为空
        payload = payload or {}
        
        try:
            # 将 payload 转换为 JSON，确保 UTF-8 编码
            json_data = json.dumps(payload, ensure_ascii=False)
            
            logger.debug(f"VOS Request: {path}, Payload: {json_data}")
            
            # 发送 POST 请求
            response = self.client.post(
                url,
                content=json_data.encode('utf-8'),
                headers=headers
            )
            
            # 检查 HTTP 状态码
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查返回码
            ret_code = result.get('retCode', -999)
            if ret_code != 0:
                logger.warning(
                    f"VOS API returned error: {path}, "
                    f"retCode={ret_code}, "
                    f"exception={result.get('exception', 'Unknown error')}"
                )
            else:
                logger.debug(f"VOS Response: {path}, retCode=0 (Success)")
            
            return result
            
        except httpx.HTTPStatusError as e:
            # HTTP 错误（4xx, 5xx）
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"VOS HTTP Error: {path}, {error_msg}")
            return {
                "retCode": -1,
                "exception": error_msg
            }
            
        except httpx.TimeoutException as e:
            # 超时错误
            error_msg = f"Request timeout: {str(e)}"
            logger.error(f"VOS Timeout: {path}, {error_msg}")
            return {
                "retCode": -2,
                "exception": error_msg
            }
            
        except httpx.NetworkError as e:
            # 网络错误
            error_msg = f"Network error: {str(e)}"
            logger.error(f"VOS Network Error: {path}, {error_msg}")
            return {
                "retCode": -3,
                "exception": error_msg
            }
            
        except json.JSONDecodeError as e:
            # JSON 解析错误
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error(f"VOS JSON Error: {path}, {error_msg}")
            return {
                "retCode": -4,
                "exception": error_msg
            }
            
        except Exception as e:
            # 其他未知错误
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"VOS Unknown Error: {path}, {error_msg}", exc_info=True)
            return {
                "retCode": -99,
                "exception": error_msg
            }
    
    def is_success(self, result: dict) -> bool:
        """
        检查 API 调用是否成功
        
        Args:
            result: API 响应结果
            
        Returns:
            bool: retCode 为 0 时返回 True，否则返回 False
        """
        return result.get('retCode', -999) == 0
    
    def get_error_message(self, result: dict) -> str:
        """
        获取错误信息
        
        Args:
            result: API 响应结果
            
        Returns:
            str: 错误信息，如果成功则返回空字符串
        """
        if self.is_success(result):
            return ""
        
        ret_code = result.get('retCode', -999)
        exception = result.get('exception', 'Unknown error')
        return f"retCode={ret_code}, {exception}"
    
    def call_api(self, path: str, payload: dict = None) -> dict:
        """
        call_api 是 post 方法的别名，方便统一调用
        """
        return self.post(path, payload)
    
    def __del__(self):
        """清理资源"""
        try:
            self.client.close()
        except:
            pass
