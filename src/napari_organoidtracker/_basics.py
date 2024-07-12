from typing import List, Tuple, Union

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
