import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from rbx_upload import RbxAssetType, RobloxClient
from rbx_upload.models import ClothingAsset, RbxAsset

SHIRT_ASSET_ID = 127203169647575
SHIRT_TEMPLATE_ID = 80789317092375
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client():
    roblosecurity = os.environ["ROBLOSECURITY"]
    return RobloxClient(roblosecurity=roblosecurity, publisher_user_id=0)


# ---------------------------------------------------------------------------
# _get_shirt_template_id_from_xml  (pure, no HTTP)
# ---------------------------------------------------------------------------


def test_get_shirt_template_id_from_xml():
    root = ET.parse(FIXTURES / "shirt.xml").getroot()
    assert RobloxClient._get_shirt_template_id_from_xml(root) == SHIRT_TEMPLATE_ID


def test_get_shirt_template_id_missing_url_tag():
    root = ET.fromstring("<root><other>data</other></root>")
    with pytest.raises(ValueError, match="<url> tag"):
        RobloxClient._get_shirt_template_id_from_xml(root)


def test_get_shirt_template_id_empty_url_tag():
    root = ET.fromstring("<root><url></url></root>")
    with pytest.raises(ValueError, match="did not contain any text"):
        RobloxClient._get_shirt_template_id_from_xml(root)


# ---------------------------------------------------------------------------
# asset_from_id  (live HTTP)
# ---------------------------------------------------------------------------


async def test_asset_from_id_returns_clothing_asset(client):
    async with client:
        asset = await client.asset_from_id(SHIRT_ASSET_ID)
    assert isinstance(asset, ClothingAsset)
    assert asset.asset_id == SHIRT_ASSET_ID
    assert asset.asset_type == RbxAssetType.SHIRT


# ---------------------------------------------------------------------------
# fetch_clothing_image  (live HTTP)
# ---------------------------------------------------------------------------


async def test_fetch_clothing_image_returns_png(client):
    async with client:
        shirt = await client.asset_from_id(SHIRT_ASSET_ID)
        image = await client.fetch_clothing_image(shirt)
    assert isinstance(image, bytes)
    assert image[:4] == b"\x89PNG"
