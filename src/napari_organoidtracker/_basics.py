from typing import List, Tuple, Union, Optional, Iterable

import numpy

MPLColor = Union[
    Tuple[float, float, float], Tuple[float, float, float, float], str, float
]

# Primitive types that can be stored directly in JSON files.
DataType = Union[
    float, int, str, bool, List[float], List[int], List[str], List[bool]
]


class TimePoint:
    """A single point in time."""

    _time_point_number: int

    def __init__(self, time_point_number: int):
        self._time_point_number = time_point_number

    def time_point_number(self) -> int:
        return self._time_point_number

    def __hash__(self):
        return self._time_point_number * 31

    def __eq__(self, other):
        return (
            isinstance(other, TimePoint)
            and other._time_point_number == self._time_point_number
        )

    def __repr__(self):
        return "TimePoint(" + str(self._time_point_number) + ")"

    def __lt__(self, other: "TimePoint") -> bool:
        return self._time_point_number < other._time_point_number

    def __gt__(self, other: "TimePoint") -> bool:
        return self._time_point_number > other._time_point_number

    def __le__(self, other: "TimePoint") -> bool:
        return self._time_point_number <= other._time_point_number

    def __ge__(self, other: "TimePoint") -> bool:
        return self._time_point_number >= other._time_point_number

    def __add__(self, other) -> "TimePoint":
        if isinstance(other, int):
            return TimePoint(self._time_point_number + other)
        if isinstance(other, TimePoint):
            return TimePoint(
                self._time_point_number + other.time_point_number()
            )
        return NotImplemented

    def __sub__(self, other) -> "TimePoint":
        if isinstance(other, int):
            return TimePoint(self._time_point_number - other)
        if isinstance(other, TimePoint):
            return TimePoint(
                self._time_point_number - other.time_point_number()
            )
        return NotImplemented


def min_none(numbers: Union[Optional[float], Iterable[Optional[float]]], *args: Optional[float]):
    """Calculates the minimal number. None values are ignored. Usage:

    >>> min_none(2, 3, 5, None, 5) == 2
    >>> min_none([4, None, 2, None, -1]) == -1
    >>> min_none([]) is None
    >>> min_none(None, None, None) is None
    """
    min_value = None

    if numbers is None or not numpy.iterable(numbers):
        numbers = [numbers] + list(args)

    for number in numbers:
        if number is None:
            continue
        if min_value is None or number < min_value:
            min_value = number
    return min_value


def max_none(numbers: Union[Optional[float], Iterable[Optional[float]]], *args: Optional[float]):
    """Calculates the minimal number. None values are ignored. Usage:

    >>> max_none(2, 3, 5, None, 5)  == 5
    >>> max_none([4, None, 2, None, -1]) == 4
    >>> max_none([]) is None
    >>> max_none(None, None, None) is None
    """
    max_value = None

    if numbers is None or not numpy.iterable(numbers):
        numbers = [numbers] + list(args)

    for number in numbers:
        if number is None:
            continue
        if max_value is None or number > max_value:
            max_value = number
    return max_value