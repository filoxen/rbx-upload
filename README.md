# rbx-upload

Async Python client for (re)uploading and managing Roblox assets.

## Install

```bash
uv add rbx-upload
```

With CLI support:

```bash
uv add "rbx-upload[cli]"
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

### Batch upload

```python
from rbx_upload import RobloxClient, RbxAssetType, BatchUploadItem

items = [
    BatchUploadItem(image=img1, name="Shirt A", asset_type=RbxAssetType.SHIRT, group_id=67890),
    BatchUploadItem(image=img2, name="Shirt B", asset_type=RbxAssetType.SHIRT, group_id=67890),
    BatchUploadItem(image=img3, name="Pants A", asset_type=RbxAssetType.PANTS, group_id=67890),
]

async with RobloxClient(roblosecurity="...", publisher_user_id=12345) as client:
    result = await client.batch_upload(items)

    for item, upload in result.succeeded:
        print(f"{item.name}: asset_id={upload['asset_id']}")

    for item, error in result.failed:
        print(f"{item.name} failed: {error}")
```

### Error handling

```python
from rbx_upload import AuthError, RateLimitError, UploadError, AssetNotFoundError

try:
    result = await client.upload_clothing_image(...)
except AuthError:
    # Invalid or expired ROBLOSECURITY token
    ...
except RateLimitError:
    # Hit rate limit, back off and retry
    ...
except UploadError:
    # Upload operation timed out or failed
    ...
```

## CLI

Requires `pip install "rbx-upload[cli]"`. Set `ROBLOSECURITY` in your environment.

```bash
# Upload a clothing image
rbx-upload upload shirt.png --name "My Shirt" --group 67890 --publisher 12345

# Put an asset on sale
rbx-upload onsale 123456789 --name "My Shirt" --group 67890 --publisher 12345 --price 10
```

Run `rbx-upload --help` or `rbx-upload <command> --help` for all options.

## API

### `RobloxClient(roblosecurity, publisher_user_id, proxy=None)`

All methods are async.

| Method | Description |
|---|---|
| `asset_from_id(asset_id)` | Fetch asset info. Returns `ClothingAsset` for shirts/pants, `RbxAsset` otherwise. |
| `fetch_clothing_image(asset)` | Fetch raw PNG bytes for a clothing asset. |
| `upload_clothing_image(image, name, description, asset_type, group_id, max_attempts=10, poll_interval=1.0)` | Upload a clothing image. Returns `{"asset_id": int}`. |
| `batch_upload(items, max_attempts=10, poll_interval=1.0)` | Upload multiple items (2 at a time). Returns `BatchResult`. |
| `onsale_asset(asset_id, name, description, group_id, price=5)` | Put an asset on sale. |

`proxy` replaces `roblox.com` in all URLs.

### Exceptions

All exceptions inherit from `RbxError`.

| Exception | When raised |
|---|---|
| `AuthError` | Invalid/expired token or not authorized |
| `RateLimitError` | HTTP 429 from Roblox |
| `UploadError` | Upload operation timed out |
| `AssetNotFoundError` | Asset ID does not exist |
