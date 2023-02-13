from typing import Any
from pydantic import BaseModel, Field
from firefly.enum import ContentType, MediaType


def find_by_id(array: list[Any], id: int) -> Any:
    for item in array:
        assert hasattr(item, 'id')
        if item.id == id:
            return item
    return None


class SettingsModel(BaseModel):
    pass


class FolderField(SettingsModel):
    name: str
    mode: str | None = None
    format: str | None = None
    order: str | None = None
    filter: str | None = None


class FolderSettings(SettingsModel):
    id: int = Field(...)
    name: str = Field(...)
    color: str = Field(...)
    fields: list[FolderField] = Field(default_factory=list)
    links: list[Any] = Field(default_factory=list)


class ViewSettings(SettingsModel):
    id: int = Field(...)
    name: str = Field(...)
    position: int = Field(...)
    folders: list[int] = Field(default_factory=list)
    states: list[int] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    separator: bool = False


class AcceptModel(SettingsModel):
    folders: list[int] | None = Field(
        None,
        title="Folders",
        description="List of folder IDs",
    )
    content_types: list[ContentType] | None = Field(
        title="Content types",
        description="List of content types that are accepted. "
        "None means all types are accepted.",
        default_factory=lambda: [ContentType.VIDEO],
    )
    media_types: list[MediaType] | None = Field(
        title="Media types",
        description="List of media types that are accepted. "
        "None means all types are accepted.",
        default_factory=lambda: [MediaType.FILE],
    )


class PlayoutChannelSettings(SettingsModel):
    id: int = Field(...)
    name: str = Field(...)
    fps: float = Field(25.0)
    plugins: list[str] = Field(default_factory=list)
    solvers: list[str] = Field(default_factory=list)
    day_start: tuple[int, int] = Field((7, 0))
    rundown_columns: list[str] = Field(default_factory=list)
    fields: list[FolderField] = Field(default_factory=list)
    send_action: int | None = None
    scheduler_accepts: AcceptModel = Field(default_factory=AcceptModel)
    rundown_accepts: AcceptModel = Field(default_factory=AcceptModel)


class StorageSettings(SettingsModel):
    id: int = Field(...)
    name: str = Field(...)
    paht: str | None = Field(None)


class Settings(SettingsModel):
    folders: list[FolderSettings] = Field(default_factory=list)
    views: list[ViewSettings] = Field(default_factory=list)
    metatypes: dict[str, Any] = Field(default_factory=dict)
    cs: dict[str, Any] = Field(default_factory=dict)
    playout_channels: list[PlayoutChannelSettings] = Field(default_factory=list)
    server_url: str | None = Field(None, title="Server URL")
    storages: list[StorageSettings] = Field(default_factory=list)

    def get_folder(self, id_folder: int) -> FolderSettings:
        return find_by_id(self.folders, id_folder)

    def get_view(self, id_view: int) -> ViewSettings:
        return find_by_id(self.views, id_view)

    def get_playout_channel(self, id_channel: int) -> PlayoutChannelSettings:
        return find_by_id(self.playout_channels, id_channel)

    def get_storage(self, id_storage: int) -> StorageSettings:
        return find_by_id(self.storages, id_storage)

    def update(self, data: dict[str, Any]) -> None:
        new_settings = Settings(**data)
        for key in new_settings.dict().keys():
            if key in self.dict().keys():
                setattr(self, key, getattr(new_settings, key))
