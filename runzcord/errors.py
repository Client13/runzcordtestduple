"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present runzcord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientWebSocketResponse

    try:
        from requests import Response

        _ResponseType = Union[ClientResponse, Response]
    except ModuleNotFoundError:
        _ResponseType = ClientResponse

    from .interactions import Interaction, ModalInteraction

__all__ = (
    "DiscordException",
    "ClientException",
    "NoMoreItems",
    "GatewayNotFound",
    "HTTPException",
    "Forbidden",
    "NotFound",
    "DiscordServerError",
    "InvalidData",
    "InvalidArgument",
    "LoginFailure",
    "ConnectionClosed",
    "PrivilegedIntentsRequired",
    "InteractionException",
    "InteractionTimedOut",
    "InteractionResponded",
    "InteractionNotResponded",
    "ModalChainNotSupported",
    "InteractionNotEditable",
    "LocalizationKeyError",
)


class DiscordException(Exception):
    """Base exception class for runzcord.

    Ideally speaking, this could be caught to handle any exceptions raised from this library.
    """

    pass


class ClientException(DiscordException):
    """Exception that's raised when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """

    pass


class NoMoreItems(DiscordException):
    """Exception that is raised when an async iteration operation has no more items."""

    pass


class GatewayNotFound(DiscordException):
    """An exception that is raised when the gateway for Discord could not be found"""

    def __init__(self) -> None:
        message = "The gateway to connect to Discord was not found."
        super().__init__(message)


def _flatten_error_dict(d: Dict[str, Any], key: str = "") -> Dict[str, str]:
    items: List[Tuple[str, str]] = []
    for k, v in d.items():
        new_key = key + "." + k if key else k

        if isinstance(v, dict):
            try:
                _errors: List[Dict[str, Any]] = v["_errors"]
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, " ".join(x.get("message", "") for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(DiscordException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ----------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.

    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The Discord specific error code for the failure.
    """

    def __init__(self, response: _ResponseType, message: Optional[Union[str, Dict[str, Any]]]):
        self.response: _ResponseType = response
        self.status: int = response.status  # type: ignore
        self.code: int
        self.text: str
        if isinstance(message, dict):
            self.code = message.get("code", 0)
            base = message.get("message", "")
            errors = message.get("errors")
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = "\n".join("In %s: %s" % t for t in errors.items())
                self.text = base + "\n" + helpful
            else:
                self.text = base
        else:
            self.text = message or ""
            self.code = 0

        fmt = "{0.status} {0.reason} (error code: {1})"
        if len(self.text):
            fmt += ": {2}"

        super().__init__(fmt.format(self.response, self.code, self.text))


class Forbidden(HTTPException):
    """Exception that's raised for when status code 403 occurs.

    Subclass of :exc:`HTTPException`.
    """

    pass


class NotFound(HTTPException):
    """Exception that's raised for when status code 404 occurs.

    Subclass of :exc:`HTTPException`.
    """

    pass


class DiscordServerError(HTTPException):
    """Exception that's raised for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.

    .. versionadded:: 1.5
    """

    pass


class InvalidData(ClientException):
    """Exception that's raised when the library encounters unknown
    or invalid data from Discord.
    """

    pass


class InvalidArgument(ClientException):
    """Exception that's raised when an argument to a function
    is invalid some way (e.g. wrong value or wrong type).

    This could be considered the analogous of ``ValueError`` and
    ``TypeError`` except inherited from :exc:`ClientException` and thus
    :exc:`DiscordException`.
    """

    pass


class LoginFailure(ClientException):
    """Exception that's raised when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """

    pass


class ConnectionClosed(ClientException):
    """Exception that's raised when the gateway connection is
    closed for reasons that could not be handled internally.

    Attributes
    ----------
    code: :class:`int`
        The close code of the websocket.
    reason: :class:`str`
        The reason provided for the closure.
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(
        self,
        socket: ClientWebSocketResponse,
        *,
        shard_id: Optional[int],
        code: Optional[int] = None,
    ):
        # This exception is just the same exception except
        # reconfigured to subclass ClientException for users
        self.code: int = code or socket.close_code or -1
        # aiohttp doesn't seem to consistently provide close reason
        self.reason: str = ""
        self.shard_id: Optional[int] = shard_id
        super().__init__(f"Shard ID {self.shard_id} WebSocket closed with {self.code}")


class PrivilegedIntentsRequired(ClientException):
    """Exception that's raised when the gateway is requesting privileged intents
    but they're not ticked in the developer page yet.

    Go to https://discord.com/developers/applications/ and enable the intents
    that are required. Currently these are as follows:

    - :attr:`Intents.members`
    - :attr:`Intents.presences`
    - :attr:`Intents.message_content`

    Attributes
    ----------
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(self, shard_id: Optional[int]):
        self.shard_id: Optional[int] = shard_id
        msg = (
            "Shard ID %s is requesting privileged intents that have not been explicitly enabled in the "
            "developer portal. It is recommended to go to https://discord.com/developers/applications/ "
            "and explicitly enable the privileged intents within your application's page. If this is not "
            "possible, then consider disabling the privileged intents instead."
        )
        super().__init__(msg % shard_id)


class InteractionException(ClientException):
    """Exception that's raised when an interaction operation fails

    .. versionadded:: 2.0

    Attributes
    ----------
    interaction: :class:`Interaction`
        The interaction that was responded to.
    """

    interaction: Interaction


class InteractionTimedOut(InteractionException):
    """Exception that's raised when an interaction takes more than 3 seconds
    to respond but is not deferred.

    .. versionadded:: 2.0

    Attributes
    ----------
    interaction: :class:`Interaction`
        The interaction that was responded to.
    """

    def __init__(self, interaction: Interaction):
        self.interaction: Interaction = interaction

        msg = (
            "Interaction took more than 3 seconds to be responded to. "
            'Please defer it using "interaction.response.defer" on the start of your command. '
            "Later you may send a response by editing the deferred message "
            'using "interaction.edit_original_message"'
            "\n"
            "Note: This might also be caused by a misconfiguration in the components "
            "make sure you do not respond twice in case this is a component."
        )
        super().__init__(msg)


class InteractionResponded(InteractionException):
    """Exception that's raised when sending another interaction response using
    :class:`InteractionResponse` when one has already been done before.

    An interaction can only be responded to once.

    .. versionadded:: 2.0

    Attributes
    ----------
    interaction: :class:`Interaction`
        The interaction that's already been responded to.
    """

    def __init__(self, interaction: Interaction):
        self.interaction: Interaction = interaction
        super().__init__("This interaction has already been responded to before")


class InteractionNotResponded(InteractionException):
    """Exception that's raised when editing an interaction response without
    sending a response message first.

    An interaction must be responded to exactly once.

    .. versionadded:: 2.0

    Attributes
    ----------
    interaction: :class:`Interaction`
        The interaction that hasn't been responded to.
    """

    def __init__(self, interaction: Interaction):
        self.interaction: Interaction = interaction
        super().__init__("This interaction hasn't been responded to yet")


class ModalChainNotSupported(InteractionException):
    """Exception that's raised when responding to a modal with another modal.

    .. versionadded:: 2.4

    Attributes
    ----------
    interaction: :class:`ModalInteraction`
        The interaction that was responded to.
    """

    def __init__(self, interaction: ModalInteraction):
        self.interaction: ModalInteraction = interaction
        super().__init__("You cannot respond to a modal with another modal.")


class InteractionNotEditable(InteractionException):
    """Exception that's raised when trying to use :func:`InteractionResponse.edit_message`
    on an interaction without an associated message (which is thus non-editable).

    .. versionadded:: 2.5

    Attributes
    ----------
    interaction: :class:`Interaction`
        The interaction that was responded to.
    """

    def __init__(self, interaction: Interaction):
        self.interaction: Interaction = interaction
        super().__init__("This interaction does not have a message to edit.")


class LocalizationKeyError(DiscordException):
    """Exception that's raised when a localization key lookup fails.

    .. versionadded:: 2.5

    Attributes
    ----------
    key: :class:`str`
        The localization key that couldn't be found.
    """

    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"No localizations were found for the key '{key}'.")