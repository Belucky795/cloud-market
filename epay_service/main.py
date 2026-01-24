"""
易支付服务 - 全局插件
提供支付接口服务，供其他插件调用
"""
import hashlib
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode

# 全局配置存储
_config: Dict[str, Any] = {}
_initialized = False


def register(bot=None, config: dict = None):
    """插件注册时调用"""
    global _config, _initialized
    if config:
        _config = config
        _initialized = True
        print(f"💳 易支付服务已初始化: API={_config.get('api_url', '未配置')}")


def unregister(bot=None):
    """插件卸载时调用"""
    global _config, _initialized
    _config = {}
    _initialized = False
    print("💳 易支付服务已停止")


def on_config_change(new_config: dict):
    """配置变更时调用"""
    global _config
    _config = new_config
    print(f"💳 易支付配置已更新: API={_config.get('api_url', '未配置')}")


# ============== 对外提供的服务接口 ==============

def is_configured() -> bool:
    """检查支付服务是否已配置"""
    return bool(_config.get('api_url') and _config.get('pid') and _config.get('key'))


def get_config() -> Dict[str, Any]:
    """获取当前配置（脱敏）"""
    return {
        'api_url': _config.get('api_url', ''),
        'pid': _config.get('pid', ''),
        'configured': is_configured()
    }


def _generate_sign(params: dict, key: str) -> str:
    """生成签名"""
    # 按字母顺序排序参数
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    # 拼接参数字符串
    param_str = '&'.join([f"{k}={v}" for k, v in sorted_params if v])
    # 拼接密钥
    sign_str = param_str + key
    # MD5签名
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest()


def _verify_sign(params: dict, sign: str, key: str) -> bool:
    """验证签名"""
    check_params = {k: v for k, v in params.items() if k != 'sign' and k != 'sign_type'}
    expected_sign = _generate_sign(check_params, key)
    return expected_sign.lower() == sign.lower()


async def create_payment(
    order_no: str,
    amount: float,
    name: str = "商品购买",
    pay_type: str = "alipay",
    notify_url: Optional[str] = None,
    return_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建支付订单
    
    Args:
        order_no: 商户订单号
        amount: 支付金额（元）
        name: 商品名称
        pay_type: 支付方式 (alipay/wxpay)
        notify_url: 异步通知地址（可选，使用配置中的默认值）
        return_url: 同步跳转地址（可选，使用配置中的默认值）
    
    Returns:
        {
            'success': bool,
            'pay_url': str,  # 支付链接
            'qr_code': str,  # 二维码内容
            'error': str     # 错误信息
        }
    """
    if not is_configured():
        return {'success': False, 'error': '支付服务未配置'}
    
    api_url = _config['api_url'].rstrip('/')
    pid = _config['pid']
    key = _config['key']
    
    params = {
        'pid': pid,
        'type': pay_type,
        'out_trade_no': order_no,
        'notify_url': notify_url or _config.get('notify_url', ''),
        'return_url': return_url or _config.get('return_url', ''),
        'name': name,
        'money': f"{amount:.2f}",
    }
    
    # 生成签名
    params['sign'] = _generate_sign(params, key)
    params['sign_type'] = 'MD5'
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 请求API获取支付链接
            resp = await client.post(f"{api_url}/mapi.php", data=params)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 1:
                    return {
                        'success': True,
                        'pay_url': data.get('payurl', ''),
                        'qr_code': data.get('qrcode', ''),
                        'trade_no': data.get('trade_no', '')
                    }
                else:
                    return {'success': False, 'error': data.get('msg', '创建订单失败')}
            else:
                return {'success': False, 'error': f'API请求失败: {resp.status_code}'}
                
    except Exception as e:
        return {'success': False, 'error': f'请求异常: {str(e)}'}


def get_payment_url(
    order_no: str,
    amount: float,
    name: str = "商品购买",
    pay_type: str = "alipay",
    notify_url: Optional[str] = None,
    return_url: Optional[str] = None
) -> Optional[str]:
    """
    获取支付页面URL（同步方法，直接跳转）
    
    Returns:
        支付页面URL，失败返回None
    """
    if not is_configured():
        return None
    
    api_url = _config['api_url'].rstrip('/')
    pid = _config['pid']
    key = _config['key']
    
    params = {
        'pid': pid,
        'type': pay_type,
        'out_trade_no': order_no,
        'notify_url': notify_url or _config.get('notify_url', ''),
        'return_url': return_url or _config.get('return_url', ''),
        'name': name,
        'money': f"{amount:.2f}",
    }
    
    params['sign'] = _generate_sign(params, key)
    params['sign_type'] = 'MD5'
    
    return f"{api_url}/submit.php?{urlencode(params)}"


async def query_order(order_no: str) -> Dict[str, Any]:
    """
    查询订单状态
    
    Returns:
        {
            'success': bool,
            'status': str,  # TRADE_SUCCESS / TRADE_CLOSED / WAIT_BUYER_PAY
            'trade_no': str,
            'error': str
        }
    """
    if not is_configured():
        return {'success': False, 'error': '支付服务未配置'}
    
    api_url = _config['api_url'].rstrip('/')
    pid = _config['pid']
    key = _config['key']
    
    params = {
        'act': 'order',
        'pid': pid,
        'out_trade_no': order_no,
    }
    params['sign'] = _generate_sign(params, key)
    params['sign_type'] = 'MD5'
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{api_url}/api.php", params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 1:
                    return {
                        'success': True,
                        'status': data.get('status', 'UNKNOWN'),
                        'trade_no': data.get('trade_no', ''),
                        'money': data.get('money', '0'),
                        'trade_status': data.get('trade_status', '')
                    }
                else:
                    return {'success': False, 'error': data.get('msg', '查询失败')}
            else:
                return {'success': False, 'error': f'API请求失败: {resp.status_code}'}
                
    except Exception as e:
        return {'success': False, 'error': f'请求异常: {str(e)}'}


def verify_notify(params: dict) -> bool:
    """
    验证异步通知签名
    
    Args:
        params: 回调参数字典
    
    Returns:
        签名是否有效
    """
    if not is_configured():
        return False
    
    sign = params.get('sign', '')
    return _verify_sign(params, sign, _config['key'])
