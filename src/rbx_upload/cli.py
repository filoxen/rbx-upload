import asyncio
import os
import sys

try:
    import click
except ImportError:
    print(
        "CLI dependencies are not installed. Run: pip install rbx-upload[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from .client import RobloxClient
from .models import RbxAssetType


def _get_roblosecurity() -> str:
    token = os.environ.get("ROBLOSECURITY")
    if not token:
        raise click.ClickException(
            "ROBLOSECURITY environment variable is not set."
        )
    return token


@click.group()
def cli():
    """rbx-upload — Roblox asset upload tool."""
    pass


@cli.command()
@click.argument("image", type=click.Path(exists=True, readable=True))
@click.option("--name", "-n", required=True, help="Asset display name.")
@click.option("--description", "-d", default="", show_default=True, help="Asset description.")
@click.option(
    "--type", "-t", "asset_type",
    type=click.Choice(["shirt", "pants"], case_sensitive=False),
    default="shirt",
    show_default=True,
    help="Asset type.",
)
@click.option("--group", "-g", "group_id", required=True, type=int, help="Group ID to upload to.")
@click.option("--publisher", "-p", "publisher_user_id", required=True, type=int, help="Publisher user ID.")
@click.option("--max-attempts", default=10, show_default=True, help="Max polling attempts.")
@click.option("--poll-interval", default=1.0, show_default=True, help="Seconds between polls.")
def upload(image, name, description, asset_type, group_id, publisher_user_id, max_attempts, poll_interval):
    """Upload a clothing image to Roblox."""
    roblosecurity = _get_roblosecurity()
    asset_type_enum = RbxAssetType.SHIRT if asset_type == "shirt" else RbxAssetType.PANTS

    with open(image, "rb") as f:
        image_bytes = f.read()

    async def _run():
        async with RobloxClient(roblosecurity, publisher_user_id) as client:
            result = await client.upload_clothing_image(
                image=image_bytes,
                name=name,
                description=description,
                asset_type=asset_type_enum,
                group_id=group_id,
                max_attempts=max_attempts,
                poll_interval=poll_interval,
            )
        return result

    result = asyncio.run(_run())
    asset_id = result.get("asset_id")
    if asset_id:
        click.echo(f"Uploaded successfully. Asset ID: {asset_id}")
    else:
        click.echo(f"Upload result: {result}")


@cli.command()
@click.argument("asset_id", type=int)
@click.option("--name", "-n", required=True, help="Asset display name.")
@click.option("--description", "-d", default="", show_default=True, help="Asset description.")
@click.option("--group", "-g", "group_id", required=True, type=int, help="Group ID.")
@click.option("--publisher", "-p", "publisher_user_id", required=True, type=int, help="Publisher user ID.")
@click.option("--price", default=5, show_default=True, help="Price in Robux.")
def onsale(asset_id, name, description, group_id, publisher_user_id, price):
    """Put an asset on sale."""
    roblosecurity = _get_roblosecurity()

    async def _run():
        async with RobloxClient(roblosecurity, publisher_user_id) as client:
            return await client.onsale_asset(
                asset_id=asset_id,
                name=name,
                description=description,
                group_id=group_id,
                price=price,
            )

    asyncio.run(_run())
    click.echo(f"Asset {asset_id} put on sale for {price} Robux.")


def main():
    cli()
