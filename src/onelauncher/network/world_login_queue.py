from typing import Dict, Final, NamedTuple

from ..resources import data_dir
import xmlschema
from . import session


class JoinWorldQueueResult(NamedTuple):
    queue_number: int
    now_serving_number: int


class WorldQueueResultXMLParseError(Exception):
    """Error with content/formatting of world queue respone XML"""


class JoinWorldQueueFailedError(Exception):
    """Failed to join world login queue"""


class WorldLoginQueue():
    _WORLD_QUEUE_RESULT_SCHEMA: Final = xmlschema.XMLSchema(
        data_dir / "network" / "schemas" / "world_queue_result.xsd")

    def __init__(
            self,
            login_queue_url: str,
            login_queue_params_template: str,
            subscription_name: str,
            session_ticket: str,
            world_queue_url: str) -> None:
        self._login_queue_url = login_queue_url
        self._login_queue_arguments_dict = self.get_login_queue_arguments_dict(
            login_queue_params_template, subscription_name, session_ticket, world_queue_url)

    def get_login_queue_arguments_dict(self,
                                       login_queue_params_template: str,
                                       subscription_name: str,
                                       session_ticket: str,
                                       world_queue_url: str) -> Dict[str,
                                                                     str]:
        arguments_dict: Dict[str, str] = {}
        for param_template in login_queue_params_template.split("&"):
            param_name, param_value = param_template.split("=")
            # Replace known template values
            param_value = param_value.replace(
                "{0}",
                subscription_name).replace(
                "{1}",
                session_ticket).replace(
                "{2}",
                world_queue_url)
            arguments_dict[param_name] = param_value
        return arguments_dict

    def join_queue(self) -> JoinWorldQueueResult:
        """
        Raises:
            RequestException: Network error
            WorldQueueResultXMLParseError: Error with content/formatting of
                                           world queue respone XML
            JoinWorldQueueFailedError: Failed to join world login queue
        """
        response = session.post(
            self._login_queue_url,
            self._login_queue_arguments_dict)

        try:
            queue_result_dict = self._WORLD_QUEUE_RESULT_SCHEMA.to_dict(
                response.text)
        except xmlschema.XMLSchemaValidationError as e:
            raise WorldQueueResultXMLParseError(
                "Queue XML result doesn't match schema") from e

        hresult = int(queue_result_dict["HResult"], base=16)
        # Check if joining queue failed. See
        # https://en.wikipedia.org/wiki/HRESULT
        if hresult >> 31 & 1:
            raise JoinWorldQueueFailedError(
                f"Joining world login queue failed with HRESULT: {hex(hresult)}")

        try:
            return JoinWorldQueueResult(
                int(queue_result_dict["QueueNumber"], base=16),
                int(queue_result_dict["NowServingNumber"], base=16))
        except KeyError as e:
            raise WorldQueueResultXMLParseError(
                "World queue result missing required value") from e
