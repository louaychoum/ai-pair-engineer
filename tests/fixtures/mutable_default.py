"""Python mutable-default-argument gotcha.

The default list is created once at function-definition time and shared
across every call. Each call that doesn't pass `tags` accumulates state
from previous calls.
"""


def add_tag(tag: str, tags: list = []) -> list:
    tags.append(tag)
    return tags


def demo() -> None:
    print(add_tag("first"))   # ['first']
    print(add_tag("second"))  # ['first', 'second']  <-- not ['second']
    print(add_tag("third"))   # ['first', 'second', 'third']


if __name__ == "__main__":
    demo()
