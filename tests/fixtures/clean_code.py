"""A module with no sensitive data — used to test false positive rates."""

from dataclasses import dataclass


@dataclass
class Point:
    """A 2D point."""

    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        """Calculate Euclidean distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def midpoint(self, other: "Point") -> "Point":
        """Return the midpoint between this point and another."""
        return Point(
            x=(self.x + other.x) / 2,
            y=(self.y + other.y) / 2,
        )


def fibonacci(n: int) -> list[int]:
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    if n == 1:
        return [0]

    result = [0, 1]
    for i in range(2, n):
        result.append(result[i - 1] + result[i - 2])
    return result


def binary_search(arr: list[int], target: int) -> int | None:
    """Return index of target in sorted array, or None if not found."""
    low, high = 0, len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return None
