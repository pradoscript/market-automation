from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Subscriber(Base):
    __tablename__ = "subscribers"

    chat_id: Mapped[int] = mapped_column(primary_key=True)
