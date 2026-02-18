from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal


class RbxAssetType(IntEnum):
    IMAGE = 1
    SHIRT = 11
    PANTS = 12


ClothingAssetType = Literal[
    RbxAssetType.SHIRT,
    RbxAssetType.PANTS,
]
CreatorType = Literal["User", "Group"]


class RbxError(Exception):
    """Base exception for all rbx-upload errors."""
    pass


class AuthError(RbxError):
    """Raised when authentication fails or the ROBLOSECURITY token is invalid."""
    pass


class RateLimitError(RbxError):
    """Raised when hitting Roblox rate limits (HTTP 429)."""
    pass


class UploadError(RbxError):
    """Raised when an asset upload fails."""
    pass


class AssetNotFoundError(RbxError):
    """Raised when an asset cannot be found."""
    pass


class RbxCreator:
    def __init__(self, creator_id: int, username: str, creator_type: CreatorType):
        self.creator_id = creator_id
        self.username = username
        self.creator_type = creator_type


class RbxAsset:
    def __init__(
        self,
        asset_id: int,
        creator: RbxCreator,
        name: str,
        description: str,
        asset_type: RbxAssetType,
    ) -> None:
        self.asset_id = asset_id
        self.name = name
        self.description = description
        self.creator = creator
        self.asset_type = asset_type


class ClothingAsset(RbxAsset):
    def __init__(
        self,
        asset_id: int,
        creator: RbxCreator,
        name: str,
        description: str,
        asset_type: ClothingAssetType,
    ) -> None:
        super().__init__(
            asset_id=asset_id,
            creator=creator,
            name=name,
            description=description,
            asset_type=asset_type,
        )


@dataclass
class BatchUploadItem:
    image: bytes
    name: str
    asset_type: RbxAssetType
    group_id: int
    description: str = ""


@dataclass
class BatchResult:
    succeeded: list[tuple[BatchUploadItem, dict]] = field(default_factory=list)
    failed: list[tuple[BatchUploadItem, Exception]] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return len(self.failed) == 0
