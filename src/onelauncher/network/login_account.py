from typing import List, NamedTuple, Optional
import zeep.exceptions
from onelauncher.network.soap import GLSServiceError, get_soap_client


class GameSubscription(NamedTuple):
    datacenter_game_name: str
    name: str
    description: str
    product_tokens: List[str]
    customer_service_tokens: List[str]
    expiration_date: Optional[str]
    status: Optional[str]
    next_billing_date: Optional[str]
    pending_cancel_date: Optional[str]
    auto_renew: Optional[str]
    billing_system_time: Optional[str]
    aditional_info: Optional[str]

    @classmethod
    def from_dict(cls, subscription_dict: dict):
        """Construct from a `subscription_dict` of the "GameSubscription" list
           in the dictionary SOAP response of LoginAccount operation.
           See `login_account`."""
        try:
            product_tokens: List[str] = []
            if "ProductTokens" in subscription_dict and subscription_dict[
                    "ProductTokens"] is not None:
                product_tokens = subscription_dict["ProductTokens"]["string"]

            customer_service_tokens: List[str] = []
            if "CustomerServiceTokens" in subscription_dict and subscription_dict[
                    "CustomerServiceTokens"] is not None:
                customer_service_tokens = subscription_dict[
                    "CustomerServiceTokens"]["string"]

            return cls(
                subscription_dict["Game"],
                subscription_dict["Name"],
                subscription_dict["Description"],
                product_tokens,
                customer_service_tokens,
                subscription_dict["ExpirationDate"],
                subscription_dict["Status"],
                subscription_dict["NextBillingDate"],
                subscription_dict["PendingCancelDate"],
                subscription_dict["AutoRenew"],
                subscription_dict["BillingSystemTime"],
                subscription_dict["AdditionalInfo"])
        except KeyError as e:
            raise GLSServiceError(
                "LoginAccount response missing required value") from e


class AccountLoginResponse():
    def __init__(
            self,
            subscriptions: List[GameSubscription],
            session_ticket: str) -> None:
        self._subscriptions = subscriptions
        self._session_ticket = session_ticket

    @property
    def subscriptions(self) -> List[GameSubscription]:
        """All subscriptions in the account. Not all of these are used
           for logging into the game. There can also be subscriptions for
           multiple game types on a single account.

           Using `get_game_subscriptions` is recommended for mmost use cases."""
        return self._subscriptions

    def get_game_subscriptions(
            self, datacenter_game_name: str) -> List[GameSubscription]:
        return [subscription for subscription in self.subscriptions
                if subscription.datacenter_game_name == datacenter_game_name]

    @property
    def session_ticket(self) -> str:
        return self._session_ticket

    @classmethod
    def from_soap_response_dict(cls, login_response_dict: dict):
        """Construct from dictionary SOAP response
           of LoginAccount operation. See `login_account`."""

        try:
            subscriptions = [GameSubscription.from_dict(
                sub_dict) for sub_dict in
                login_response_dict["Subscriptions"]["GameSubscription"]]

            return cls(subscriptions, login_response_dict["Ticket"])
        except KeyError as e:
            raise GLSServiceError(
                "LoginAccount response missing required value") from e


class WrongUsernameOrPasswordError(Exception):
    """Either the username does not exist, or the password was incorrect."""


def login_account(
        auth_server: str,
        username: str,
        password: str) -> AccountLoginResponse:
    """Login to game account using SOAP API

    Args:
        auth_server (str): Authentification server. Normally found in `GameServicesInfo`
        username (str): Account username
        password (str): Account password

    Raises:
        WrongUsernameOrPasswordError: Username doesn't exist or password is wrong.
        RequestException: Network error
        GLSServiceError: Non-network issue with the GLS service

    Returns:
        AccountLoginResponse
    """
    client = get_soap_client(auth_server)

    try:
        return AccountLoginResponse.from_soap_response_dict(
            client.service.LoginAccount(
                username, password, ""))
    except zeep.exceptions.Fault as e:
        raise WrongUsernameOrPasswordError("") from e
    except zeep.exceptions.Error as e:
        raise GLSServiceError(
            "Error while parsing LoginAccount response") from e
    except AttributeError as e:
        raise GLSServiceError(
            "Service has no LoginAccount operation") from e
