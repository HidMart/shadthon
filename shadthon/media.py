from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from .exceptions import (
    DownloadError,
    UploadError,
)
from .models import FileInfo
from .utils import random_id


class MediaManager:

    def __init__(self, transport):
        self.transport = transport

    async def send_photo(
        self,
        object_guid: str,
        file_path: str,
        caption: str | None = None,
    ):
        return await self._send_media(
            object_guid,
            file_path,
            "Image",
            caption,
        )

    async def send_video(
        self,
        object_guid: str,
        file_path: str,
        caption: str | None = None,
    ):
        return await self._send_media(
            object_guid,
            file_path,
            "Video",
            caption,
        )

    async def send_file(
        self,
        object_guid: str,
        file_path: str,
        caption: str | None = None,
    ):
        return await self._send_media(
            object_guid,
            file_path,
            "File",
            caption,
        )

    async def _send_media(
        self,
        object_guid: str,
        file_path: str,
        media_type: str,
        caption: str | None,
    ):

        path = Path(file_path)

        if not path.exists():
            raise UploadError(
                f"File does not exist: {path}"
            )

        if not path.is_file():
            raise UploadError(
                f"Not a file: {path}"
            )

        size = path.stat().st_size

        mime = (
            mimetypes.guess_type(
                path.name
            )[0]
            or "application/octet-stream"
        )

        upload_result = (
            await self.upload_file(path)
        )

        file_info = FileInfo.from_dict(
            upload_result
        )

        inline = {
            "dc_id": file_info.dc_id,
            "file_id": file_info.file_id,
            "type": media_type,
            "file_name": path.name,
            "size": size,
            "mime": mime,
            "access_hash_rec":
                file_info.access_hash,
        }

        data: dict[str, Any] = {
            "object_guid": object_guid,
            "rnd": random_id(),
            "file_inline": inline,
        }

        if caption:
            data["text"] = caption

        return await self.transport.authenticated(
            "sendMessage",
            data,
        )

    async def upload_file(
        self,
        file_path: str | Path,
    ) -> dict[str, Any]:

        path = Path(file_path)

        if not path.exists():
            raise UploadError(
                f"File does not exist: {path}"
            )

        size = path.stat().st_size

        mime = (
            mimetypes.guess_type(
                path.name
            )[0]
            or "application/octet-stream"
        )

        result = await self.transport.authenticated(
            "requestSendFile",
            {
                "file_name": path.name,
                "size": size,
                "mime": mime,
            },
        )

        return result.get(
            "data",
            result,
        )

    async def download_file(
        self,
        file_info: FileInfo | dict[str, Any],
        output_path: str,
    ) -> str:

        if isinstance(
            file_info,
            FileInfo,
        ):
            data = file_info.raw or {}

        else:
            data = file_info

        url = data.get(
            "download_url"
        )

        if not url:
            raise DownloadError(
                "Server did not return a download URL"
            )

        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:

                    if response.status >= 400:
                        raise DownloadError(
                            f"HTTP {response.status}"
                        )

                    with open(
                        output_path,
                        "wb",
                    ) as file:

                        while True:
                            chunk = await response.content.read(
                                1024 * 1024
                            )

                            if not chunk:
                                break

                            file.write(chunk)

        except aiohttp.ClientError as exc:
            raise DownloadError(
                str(exc)
            ) from exc

        return output_path