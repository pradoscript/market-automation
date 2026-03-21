import logging

from sqlalchemy.orm import Session

from app.models.subscriber_model import Subscriber

logger = logging.getLogger(__name__)


class SubscriberRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, chat_id: int) -> None:
        if not self._db.get(Subscriber, chat_id):
            self._db.add(Subscriber(chat_id=chat_id))
            self._db.commit()
            logger.info("Subscriber added: chat_id=%s", chat_id)

    def remove(self, chat_id: int) -> None:
        sub = self._db.get(Subscriber, chat_id)
        if sub:
            self._db.delete(sub)
            self._db.commit()
            logger.info("Subscriber removed: chat_id=%s", chat_id)

    def get_all(self) -> list[int]:
        return [s.chat_id for s in self._db.query(Subscriber).all()]
