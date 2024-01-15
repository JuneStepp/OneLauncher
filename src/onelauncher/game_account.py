import contextlib
from uuid import UUID
import attrs

import keyring

from .__about__ import __title__


@attrs.define
class GameAccount():
    game_uuid: UUID
    username: str = attrs.field(on_setattr=attrs.setters.frozen)
    display_name: str | None
    last_used_world_name: str

    @property
    def _account_keyring_username(self) -> str:
        return f"{self.game_uuid}{self.username}"

    @property
    def password(self) -> str | None:
        """
        Account password that is saved in keyring.
        Will return `None` if no saved passwords are found
        """
        return keyring.get_password(
            __title__,
            self._account_keyring_username,
        )

    @password.setter
    def password(self, password: str) -> None:
        keyring.set_password(
            __title__,
            self._account_keyring_username,
            password)

    def delete_password(self) -> None:
        """Delete account password from keyring."""
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(
                __title__,
                self._account_keyring_username,
            )

    @property
    def _last_used_subscription_keyring_username(self) -> str:
        return f"{self._account_keyring_username}LastUsedSubscription"

    @property
    def last_used_subscription_name(self) -> str | None:
        """
        Name of the subscription that was last played.
        See `login_account.py`
        """
        return keyring.get_password(
            __title__,
            self._last_used_subscription_keyring_username,
        )

    @last_used_subscription_name.setter
    def last_used_subscription_name(self, subscription_name: str):
        keyring.set_password(
            __title__,
            self._last_used_subscription_keyring_username,
            subscription_name,
        )

    def delete_last_used_subscription_name(self) -> None:
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(
                __title__,
                self._last_used_subscription_keyring_username,
            )

    def delete_account_keyring_info(self) -> None:
        """
        Delete all information for account saved with keyring. ex. password
        """
        self.delete_password()
        self.delete_last_used_subscription_name()
