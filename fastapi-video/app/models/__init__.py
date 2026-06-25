"""导入所有模型 — SQLAlchemy 在调用 create_all() 或查询时需要先 import 模型"""

from app.models.base import Base
from app.models.user import User
from app.models.video import Video
from app.models.subscribe import Subscribe
from app.models.videocomment import Videocomment
from app.models.videolike import Videolike
from app.models.collect import Collect
from app.models.conversation import Conversation
from app.models.message import Message

__all__ = [
    "Base",
    "User",
    "Video",
    "Subscribe",
    "Videocomment",
    "Videolike",
    "Collect",
    "Conversation",
    "Message",
]
