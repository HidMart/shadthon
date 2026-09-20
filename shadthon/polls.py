from __future__ import annotations

from typing import Any

from .models import Poll


class PollManager:

    def __init__(self, transport):
        self.transport = transport

    async def get_poll(
        self,
        poll_id: str,
    ) -> Poll:

        result = await self.transport.authenticated(
            "getPollStatus",
            {
                "poll_id": poll_id,
            },
        )

        data = result.get(
            "data",
            result,
        )

        return Poll.from_dict(
            data
        )

    async def vote_poll(
        self,
        poll_id: str,
        option: int,
    ) -> dict[str, Any]:

        return await self.transport.authenticated(
            "votePoll",
            {
                "poll_id": poll_id,
                "selection_index": option,
            },
        )