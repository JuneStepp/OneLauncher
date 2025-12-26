from typing import Any, Final, NamedTuple

import attrs
import xmlschema

from ..resources import data_dir
from .httpx_client import get_httpx_client


class JoinWorldQueueResult(NamedTuple):
    queue_number: int
    now_serving_number: int


class WorldQueueResultXMLParseError(Exception):
    """Error with content/formatting of world queue response XML"""


@attrs.frozen(kw_only=True)
class JoinWorldQueueFailedError(Exception):
    msg: str


class WorldLoginQueue:
    _WORLD_QUEUE_RESULT_SCHEMA: Final = xmlschema.XMLSchema(
        data_dir / "network" / "schemas" / "world_queue_result.xsd"
    )

    def __init__(
        self,
        login_queue_url: str,
        login_queue_params_template: str,
        subscription_name: str,
        session_ticket: str,
        world_queue_url: str,
    ) -> None:
        self._login_queue_url = login_queue_url
        self._login_queue_arguments_dict = self.get_login_queue_arguments_dict(
            login_queue_params_template,
            subscription_name,
            session_ticket,
            world_queue_url,
        )

    def get_login_queue_arguments_dict(
        self,
        login_queue_params_template: str,
        subscription_name: str,
        session_ticket: str,
        world_queue_url: str,
    ) -> dict[str, str]:
        arguments_dict: dict[str, str] = {}
        for param_template in login_queue_params_template.split("&"):
            param_name, param_value = param_template.split("=")
            # Replace known template values
            param_value = (
                param_value.replace("{0}", subscription_name)
                .replace("{1}", session_ticket)
                .replace("{2}", world_queue_url)
            )
            arguments_dict[param_name] = param_value
        return arguments_dict

    async def join_queue(self) -> JoinWorldQueueResult:
        """
        Raises:
            HTTPError: Network error
            WorldQueueResultXMLParseError: Error with content/formatting of
                                           world queue response XML
            JoinWorldQueueFailedError: Failed to join world login queue
        """
        response = await get_httpx_client(self._login_queue_url).post(
            self._login_queue_url, data=self._login_queue_arguments_dict
        )

        try:
            queue_result_dict: dict[str, Any] = self._WORLD_QUEUE_RESULT_SCHEMA.to_dict(
                response.text
            )  # type: ignore[assignment]
        except xmlschema.XMLSchemaValidationError as e:
            raise WorldQueueResultXMLParseError(
                "Queue XML result doesn't match schema"
            ) from e

        hresult = int(queue_result_dict["HResult"], base=16)
        # Check if joining queue failed. See
        # https://en.wikipedia.org/wiki/HRESULT
        if hresult >> 31 & 1:
            # This HRESULT is commonly known as "Unspecified failure". For LOTRO/DDO,
            # I've so far seen it when:
            #   - The preview servers are closed. Looking at the world status in this
            #     case, the only allowed billing role is "TurbineEmployee".
            #   - Once, when the servers were down.
            #   - After probably logging in too many times and getting the account
            #     timed out/suspended for a little while.
            if hresult == 0x80004005:  # noqa: PLR2004
                raise JoinWorldQueueFailedError(
                    msg="Failed to join world login queue. Please try again later."
                )
            else:
                exception = JoinWorldQueueFailedError(
                    msg="Non-network error joining world login queue"
                )
                exception.add_note(f"HRESULT: {hex(hresult)}")
                raise exception

        try:
            return JoinWorldQueueResult(
                int(queue_result_dict["QueueNumber"], base=16),
                int(queue_result_dict["NowServingNumber"], base=16),
            )
        except KeyError as e:
            raise WorldQueueResultXMLParseError(
                "World queue result missing required value"
            ) from e
