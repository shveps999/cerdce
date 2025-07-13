"""
Модуль для управления сообщениями бота
"""

from .start_messages import StartMessages
from .user_messages import UserMessages
from .post_messages import PostMessages
from .feed_messages import FeedMessages
from .moderation_messages import ModerationMessages
from .callback_messages import CallbackMessages
from .notification_messages import NotificationMessages
from .common_messages import CommonMessages

__all__ = [
    "StartMessages",
    "UserMessages", 
    "PostMessages",
    "FeedMessages",
    "ModerationMessages",
    "CallbackMessages",
    "NotificationMessages",
    "CommonMessages"
] 