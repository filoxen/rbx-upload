# rbx-upload

Async Python client for (re)uploading and managing Roblox assets.

## Install

```bash
uv add rbx-upload
```

## Usage

```python
from rbx_upload import RobloxClient, RbxAssetType

async with RobloxClient(
    roblosecurity="...",
    publisher_user_id=12345,
) as client:

    # Fetch asset info
    asset = await client.asset_from_id(127203169647575)

    # Fetch raw PNG bytes for a clothing asset
    image = await client.fetch_clothing_image(asset)

    # Upload a clothing image
    result = await client.upload_clothing_image(
        image=image,
        name="My Shirt",
        description="",
        asset_type=RbxAssetType.SHIRT,
        group_id=67890,
    )

    # Put an asset on sale
    await client.onsale_asset(
        asset_id=result["asset_id"],
        name="My Shirt",
        description="",
        group_id=67890,
        price=5,
    )
```

## API

### `RobloxClient(roblosecurity, publisher_user_id, proxy=None)`

All methods are async

| Method | Description |
|---|---|
| `asset_from_id(asset_id)` | Fetch asset info. Returns `ClothingAsset` for shirts/pants, `RbxAsset` otherwise. |
| `fetch_clothing_image(asset)` | Fetch raw PNG bytes for a clothing asset. |
| `upload_clothing_image(image, name, description, asset_type, group_id)` | Upload a clothing image. Returns `{"asset_id": int}`. |
| `onsale_asset(asset_id, name, description, group_id, price=5)` | Put an asset on sale. |

`proxy` replaces `roblox.com` in all URLs
