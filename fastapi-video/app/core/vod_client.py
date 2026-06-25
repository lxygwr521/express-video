"""阿里云 VOD RPC 客户端 — 手动 HMAC-SHA1 签名

等价于 Node.js 的 @alicloud/pop-core RPCClient。
阿里云 VOD API 是 RPC 风格（GET/POST + 公共参数 + 签名），不是 REST。
"""

import hashlib
import hmac
import uuid
import base64
import urllib.parse
from datetime import datetime, timezone

import httpx
from app.config import settings

# VOD 服务端点
_ENDPOINT = "http://vod.cn-beijing.aliyuncs.com"
_API_VERSION = "2017-03-21"


def get_vod_client():
    """返回已配置签名方法的 HTTP 客户端（可复用连接池）"""
    return httpx.AsyncClient(base_url=_ENDPOINT, timeout=30.0)


def _sign(method: str, params: dict) -> str:
    """
    阿里云 POP API 签名 V1（HMAC-SHA1）

    签名步骤：
      1. 按参数名排序
      2. 构造规范化查询字符串（URL 编码）
      3. 构造待签名字符串：HTTPMethod + "&" + encodeURI("/") + "&" + encodeURI(规范化查询串)
      4. HMAC-SHA1(Secret + "&", 待签名字符串) → Base64
    """
    # 过滤掉 Signature 自身
    params = {k: v for k, v in params.items() if k != "Signature"}

    # 按 key 字典序排列
    sorted_keys = sorted(params.keys())
    # 构造规范化查询字符串（阿里云特殊 URL 编码：空格→%20，*→%2A，~→%7E）
    canon = "&".join(
        f"{_encode(k)}={_encode(str(params[k]))}" for k in sorted_keys
    )

    # 待签名字符串
    string_to_sign = f"{method}&{_encode('/')}&{_encode(canon)}"

    # HMAC-SHA1 签名
    secret = settings.ALIYUN_ACCESS_KEY_SECRET + "&"
    h = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha1)
    return base64.b64encode(h.digest()).decode()


def _encode(s: str) -> str:
    """阿里云 RPC URL 编码：先 urllib 编码，再替换特殊字符"""
    encoded = urllib.parse.quote(s, safe="")
    # 阿里云要求的特殊替换
    encoded = encoded.replace("+", "%20")
    encoded = encoded.replace("*", "%2A")
    encoded = encoded.replace("%7E", "~")
    return encoded


def _build_params(action: str, extra: dict | None = None) -> dict:
    """构造完整的请求参数（公共参数 + 业务参数 + 签名）"""
    params = {
        "Format": "JSON",
        "Version": _API_VERSION,
        "AccessKeyId": settings.ALIYUN_ACCESS_KEY_ID,
        "SignatureMethod": "HMAC-SHA1",
        "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SignatureVersion": "1.0",
        "SignatureNonce": uuid.uuid4().hex,
        "Action": action,
    }
    if extra:
        params.update(extra)

    # 计算签名并追加
    params["Signature"] = _sign("GET", params)
    return params


async def vod_request(action: str, params: dict | None = None) -> dict:
    """发送 VOD API 请求，返回 JSON 解析结果"""
    full_params = _build_params(action, params)
    async with get_vod_client() as client:
        resp = await client.get("/", params=full_params)
        resp.raise_for_status()
        data = resp.json()
        return data
