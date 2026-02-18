import asyncio
import json
import uuid
import xml.etree.ElementTree

import httpx

from .models import ClothingAsset, RbxAsset, RbxAssetType, RbxCreator


class RateLimitError(Exception):
    """Raised when hitting Roblox rate limits (HTTP 429)."""

    pass


class RobloxClient:
    def __init__(
        self,
        roblosecurity: str,
        publisher_user_id: int,
        proxy: str | None = None,
    ):
        self._roblosecurity = roblosecurity
        self._publisher_user_id = publisher_user_id
        self._proxy = proxy
        self._http = httpx.AsyncClient()

        self._fetch_headers = {
            "Cookie": f".ROBLOSECURITY={roblosecurity}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        self._csrf_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
            "Referer": "https://create.roblox.com/",
            "Origin": "https://create.roblox.com",
        }
        self._csrf_cookies = {".ROBLOSECURITY": roblosecurity}

    def _proxy_url(self, url: str) -> str:
        if not self._proxy:
            return url
        return url.replace("roblox.com", self._proxy)

    async def _get_csrf_token(self) -> str:
        url = self._proxy_url("https://apis.roblox.com/assets/user-auth/v1/assets")
        response = await self._http.post(
            url, cookies=self._csrf_cookies, headers=self._csrf_headers
        )
        csrf = response.headers.get("X-CSRF-TOKEN")
        if not csrf:
            raise httpx.HTTPStatusError(
                "Failed to retrieve X-CSRF-TOKEN.",
                request=response.request,
                response=response,
            )
        return csrf

    async def _economy_request(self, asset_id: int) -> httpx.Response:
        url = self._proxy_url(
            f"https://economy.roblox.com/v2/assets/{asset_id}/details"
        )
        return await self._http.get(url, headers=self._fetch_headers)

    async def _asset_delivery_request(self, asset_id: int) -> httpx.Response:
        url = self._proxy_url(
            f"https://assetdelivery.roblox.com/v1/asset/?id={asset_id}"
        )
        return await self._http.get(
            url, headers=self._fetch_headers, follow_redirects=True
        )

    async def _get_asset_xml(self, asset: RbxAsset) -> xml.etree.ElementTree.Element:
        response = await self._asset_delivery_request(asset.asset_id)
        response.raise_for_status()
        content = response.content.decode("utf-8")
        return xml.etree.ElementTree.fromstring(content)

    @staticmethod
    def _get_shirt_template_id_from_xml(root: xml.etree.ElementTree.Element) -> int:
        url_element = root.find(".//url")
        if url_element is None:
            raise ValueError("XML did not contain a <url> tag.")
        url = url_element.text
        if not url:
            raise ValueError("<url> tag did not contain any text.")
        return int(url.split("id=")[1])

    async def asset_from_id(self, asset_id: int) -> RbxAsset:
        """Fetch asset information from Roblox by asset ID."""
        response = await self._economy_request(asset_id)
        response.raise_for_status()
        asset_info = response.json()
        creator_info = asset_info["Creator"]
        creator = RbxCreator(
            creator_id=creator_info["Id"],
            username=creator_info["Name"],
            creator_type=creator_info["CreatorType"],
        )
        asset_type_id = asset_info["AssetTypeId"]
        if asset_type_id in (RbxAssetType.SHIRT, RbxAssetType.PANTS):
            return ClothingAsset(
                asset_id=asset_info["AssetId"],
                creator=creator,
                name=asset_info["Name"],
                description=asset_info["Description"],
                asset_type=asset_type_id,
            )
        return RbxAsset(
            asset_id=asset_info["AssetId"],
            creator=creator,
            name=asset_info["Name"],
            description=asset_info["Description"],
            asset_type=asset_type_id,
        )

    async def fetch_clothing_image(self, asset: ClothingAsset) -> bytes:
        """Fetch the image data for a clothing asset."""
        xml_root = await self._get_asset_xml(asset)
        template_id = self._get_shirt_template_id_from_xml(xml_root)
        image = await self._asset_delivery_request(template_id)
        image.raise_for_status()
        return image.content

    async def upload_clothing_image(
        self,
        image: bytes,
        name: str,
        description: str,
        asset_type: RbxAssetType,
        group_id: int,
    ) -> dict:
        """Upload a clothing image to Roblox and return the operation result."""
        csrf = await self._get_csrf_token()
        upload_url = self._proxy_url(
            "https://apis.roblox.com/assets/user-auth/v1/assets"
        )
        meta = {
            "displayName": name,
            "description": description,
            "assetType": asset_type,
            "creationContext": {
                "creator": {"groupId": group_id},
                "expectedPrice": 10,
            },
        }
        upload_headers = {
            "X-CSRF-TOKEN": csrf,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://create.roblox.com/",
            "Origin": "https://create.roblox.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        response = await self._http.post(
            upload_url,
            files={
                "request": (None, json.dumps(meta), "application/json"),
                "fileContent": ("clothing_upload", image, "image/png"),
            },
            headers=upload_headers,
            cookies=self._csrf_cookies,
        )

        if response.status_code == 429:
            raise RateLimitError("Rate limit hit during upload")

        response.raise_for_status()
        data = response.json()

        operation_id = data.get("operationId")
        if operation_id:
            for _ in range(10):
                await asyncio.sleep(1)
                op_response = await self._http.get(
                    self._proxy_url(
                        f"https://apis.roblox.com/assets/user-auth/v1/operations/{operation_id}"
                    ),
                    headers={"X-CSRF-TOKEN": csrf},
                    cookies=self._csrf_cookies,
                )
                op_response.raise_for_status()
                op_data = op_response.json()
                if op_data.get("done"):
                    if op_data.get("response", {}).get("assetId"):
                        return {"asset_id": op_data["response"]["assetId"]}
                    return op_data

        return data

    async def onsale_asset(
        self,
        asset_id: int,
        name: str,
        description: str,
        group_id: int,
        price: int = 5,
    ) -> dict:
        """Put an asset on sale."""
        csrf = await self._get_csrf_token()
        data = {
            "saleLocationConfiguration": {"saleLocationType": 1, "places": []},
            "targetId": asset_id,
            "priceInRobux": price,
            "publishingType": 2,
            "idempotencyToken": str(uuid.uuid4()),
            "publisherUserId": self._publisher_user_id,
            "creatorGroupId": group_id,
            "name": name,
            "description": description,
            "isFree": False,
            "agreedPublishingFee": 0,
            "priceOffset": 0,
            "quantity": 0,
            "quantityLimitPerUser": 0,
            "resaleRestriction": 2,
            "targetType": 0,
        }
        response = await self._http.post(
            self._proxy_url("https://itemconfiguration.roblox.com/v1/collectibles"),
            json=data,
            headers={
                "X-CSRF-TOKEN": csrf,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
                "Referer": "https://create.roblox.com/",
                "Origin": "https://create.roblox.com",
            },
            cookies=self._csrf_cookies,
        )

        if response.status_code == 429:
            raise RateLimitError("Rate limit hit during onsale")

        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
