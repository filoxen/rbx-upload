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
