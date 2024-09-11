import json
import time
from abc import abstractmethod
from collections.abc import Iterator
from enum import Enum
from typing import Any, Literal, TypeVar

import numpy as np
import numpy.typing as npt
import requests


class CSBackend[T]:
    """An abstract backend allowing a CS value to be sent or received"""

    @abstractmethod
    def send(self, value: T): ...

    @abstractmethod
    def recv(self) -> T: ...


class CSValue[T]:
    """A wrapper class that presents the interface the user would like to a CS value"""

    def __init__(self, backend: CSBackend[T]):
        self.backend = backend

    def set(self, value: T):
        # Do logging, caching, other common things
        self.backend.send(value)

    def get(self) -> T:
        # Do logging, caching, other common things
        return self.backend.recv()

    def poll(self, interval: int) -> Iterator[T]:
        while True:
            time.sleep(interval)
            yield self.get()

    # And many other methods...


# The sort of things we can send over HTTP
HTTPType = TypeVar("HTTPType", bound=str | int | Enum | npt.NDArray[np.float64])


def convert_to(datatype: type[HTTPType], value: Any) -> HTTPType: ...


class HTTPBackend(CSBackend[HTTPType]):
    """An backend backed by HTTP"""

    def __init__(self, datatype: type[HTTPType], uri: str) -> None:
        self.datatype = datatype
        self.uri = uri

    def send(self, value: HTTPType):
        requests.put(self.uri, json.dumps(value))

    def recv(self) -> HTTPType:
        return convert_to(self.datatype, requests.get(self.uri).json())


# A helper function to create these wrapper instances
def http_value(datatype: type[HTTPType], uri: str) -> CSValue[HTTPType]:
    # We would return a different backend if the service is in simulation mode...
    backend = HTTPBackend(datatype, uri)
    return CSValue(backend)


# Another different backend would support different types
MQTTType = TypeVar("MQTTType", bound=str | int | Enum)


def mqtt_value(datatype: type[MQTTType], host: str, port: int) -> CSValue[MQTTType]: ...


class MyEnum(str, Enum):
    a = "A"
    b = "B"
    # Check that CS enum is precisely {"A", "B"}


# The use wants to form these values into devices, of which there will be many


class MyGoodDevice:
    def __init__(self, http_uri: str = "http://example.com"):
        # These all work
        self.v1 = http_value(str, http_uri)
        self.v2 = mqtt_value(str, "localhost", 1883)
        self.v3 = http_value(MyEnum, http_uri)
        self.v4 = http_value(npt.NDArray[np.float64], http_uri)
        self.v4.set(np.array([1]))


# These legitimately fail
http_value(dict, "http://example.com")
http_value(npt.NDArray[np.float64], "http://example.com").set(
    np.array([1], dtype=np.int32)
)
mqtt_value(npt.NDArray[np.float64], "localhost", 1883)

# This doesn't work
http_value(Literal["a", "b"], "http://example.com")


# But this works, so I'll do this instead...
class SubsetEnum(Enum): ...


class MySubsetEnum(str, SubsetEnum):
    a = "A"
    b = "B"
    # Check that {"A", "B"} is a subset of CS enum


http_value(MySubsetEnum, "http://example.com")
