from pydantic import BaseModel, ConfigDict, Field


class TelegramUser(BaseModel):
    id: int


class TelegramChat(BaseModel):
    id: int


class TelegramMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: int
    text: str | None = None
    chat: TelegramChat
    sender: TelegramUser = Field(alias="from")


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None
