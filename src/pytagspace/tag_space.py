"""pytagspace package

This module implements the TagSpace, Tag
"""

import functools
from collections import defaultdict
from typing import Dict, Optional, Union, Callable, Set, List, Tuple, Hashable

TagNameType = str
TagValueType = Union[int, float, str, bool]
TagValueIterableType = Union[List[TagValueType], Tuple[TagValueType, ...]]
TagValueFunctionType = Callable[[TagValueType], bool]
TagObjectType = Hashable


def is_tag_name(name) -> bool:
    return isinstance(name, str) and not name.startswith('_')


def is_tag_value(value) -> bool:
    return isinstance(value, (int, float, str, bool))


def is_tag_value_iterable(it) -> bool:
    return isinstance(it, (list, tuple)) and functools.reduce(
        lambda x, y: x and y, [isinstance(tag_value, (int, float, str, bool)) for tag_value in it]
    )


def is_tag_value_function(func) -> bool:
    return callable(func)


class Tag:
    """A mapping from ``tag_value`` to ``tag_set``, where ``tag_set``s are mutually exclusive

    """

    def __init__(self):
        self._mapping: Dict[TagValueType, Set[TagObjectType]] = defaultdict(set)
        self._reverse_mapping: Dict[TagObjectType, TagValueType] = {}

    def __getitem__(self, item: Union[TagValueType, TagValueIterableType, TagValueFunctionType]) -> Set[TagObjectType]:
        return self.find_objs(item)

    def __delitem__(self, key: Union[TagValueType, TagValueIterableType, TagValueFunctionType]) -> None:
        self.remove_tags(key)

    def _tag(self, obj: TagObjectType, tag_value: TagValueType):
        if obj in self._reverse_mapping:
            obj_tag_value = self._reverse_mapping[obj]
            self._mapping[obj_tag_value].remove(obj)
        self._mapping[tag_value].add(obj)
        self._reverse_mapping[obj] = tag_value

    def _remove_tag(self, tag_value: TagValueType):
        if tag_value in self._mapping:
            for obj in self._mapping[tag_value]:
                del self._reverse_mapping[obj]
            del self._mapping[tag_value]

    def tag(self, *objs: TagObjectType, tag_value: Union[TagValueType, TagValueIterableType]) -> None:
        """Mark ``objs`` with ``tag_value``.

        :param objs: objects to mark
        :param tag_value: a tag value or a list/tuple containing tag values that corresponds with ``objs``
        :return: None
        """
        if is_tag_value(tag_value):
            for obj in objs:
                self._tag(obj, tag_value)
        elif is_tag_value_iterable(tag_value):
            for obj, value in zip(objs, tag_value):
                self._tag(obj, value)
        else:
            raise ValueError('tag_value ')

    def find_objs(
            self,
            tag_value: Union[TagValueType, TagValueIterableType, TagValueFunctionType]
    ) -> Set[TagObjectType]:
        """Find objects with tag value qualified by ``tag_value``.

        :param tag_value: a tag value, or a list/tuple of qualified tag values,
            or a condition function that checks each tag value if it is qualified
        :return: the set of qualified objects
        """
        if is_tag_value(tag_value):
            return self._mapping[tag_value].copy()
        elif is_tag_value_iterable(tag_value):
            return functools.reduce(
                lambda x, y: x.union(y),
                [self._mapping[value] for value in tag_value]
            ).copy()
        elif is_tag_value_function(tag_value):
            return functools.reduce(
                lambda x, y: x.union(y),
                [self._mapping[value] for value in self._mapping.keys() if tag_value(value)]
            ).copy()
        else:
            raise ValueError()

    def find_tag(self, *objs: TagObjectType) -> Optional[TagValueType]:
        """Find tag that share by all ``objs``.

        :param objs: objects to find tag with
        :return: the tag value or None if ``objs`` don't share the same tag
        """
        return functools.reduce(
            lambda x, y: x if x == y else None,
            [
                (self._reverse_mapping[obj] if obj in self._reverse_mapping else None)
                for obj in objs
            ]
        )

    def remove_tags(self, tag_value: Union[TagValueType, TagValueIterableType, TagValueFunctionType]) -> None:
        """Remove tags qualified by ``tag_value``.

        :param tag_value: a tag value, or a list/tuple of qualified tag values,
            or a condition function that checks each tag value if it is qualified
        :return: None
        """
        if is_tag_value(tag_value):
            self._remove_tag(tag_value)
        elif is_tag_value_iterable(tag_value):
            for value in tag_value:
                self._remove_tag(value)
        elif is_tag_value_function(tag_value):
            values = []
            for value in self._mapping.keys():
                if tag_value(value):
                    values.append(value)
            for value in values:
                self._remove_tag(value)
        else:
            raise ValueError()

    def remove_objs(self, *objs: TagObjectType) -> None:
        """Remove ``objs``.

        :param objs: objects to remove
        :return: None
        """
        for obj in objs:
            if obj in self._reverse_mapping:
                value = self._reverse_mapping[obj]
                self._mapping[value].remove(obj)
                del self._reverse_mapping[obj]

    def clear(self) -> None:
        """Clear everything.

        :return: None
        """
        self._mapping.clear()
        self._reverse_mapping.clear()

    def tag_decorator(self, tag_value: TagValueType):
        """Mark the decorated object with ``tag_value``

        :param tag_value: a tag value
        :return: None
        """
        def inner(dec):
            self.tag(dec, tag_value=tag_value)
            return dec

        return inner

    def get_content_string(self) -> str:
        """Get a formatted string that show tag value -> tag objects mapping.

        :return: the result string
        """
        return '\t' + '\n\t'.join([
            '{}: {}'.format(tag_value, tag_set) for tag_value, tag_set in self._mapping.items()
        ])

    def get_reverse_string(self):
        """Get a formatted string that show tag objects -> tag value mapping.

        :return: the result string
        """
        return '\t' + '\n\t'.join([
            '{}: {}'.format(obj, tag_value) for obj, tag_value in self._reverse_mapping.items()
        ])


class TagSpace:
    """A mapping from ``tag_name`` to ``Tag``

    """

    def __init__(self, is_strict: bool = False):
        if is_strict:
            self._mapping: Dict[TagNameType, Tag] = {}
        else:
            self._mapping: Dict[TagNameType, Tag] = defaultdict(Tag)

    def __getitem__(self, item: TagNameType):
        return self._mapping[item]

    def __delitem__(self, key: TagNameType):
        self.remove_tags(key)

    def tag(self, *objs: TagObjectType, **kw_tags: Union[TagValueType, TagValueIterableType]) -> None:
        """Mark ``objs`` with tag name = tag value in ``kw_tags``.

        :param objs: objects to mark
        :param kw_tags: keyword pairs containing tag name = tag value,
            or tag name = list/tuple containing tag values that corresponds with ``objs``
        :return: None
        """
        for tag_name, tag_value in kw_tags.items():
            if is_tag_name(tag_name):
                self._mapping[tag_name].tag(*objs, tag_value=tag_value)

    def find_objs(
            self,
            **kw_tags: Union[TagValueType, TagValueIterableType, TagValueFunctionType]
    ) -> Set[TagObjectType]:
        """Find objects with tag qualified by ``tag_value``.

        :param kw_tags: keyword pairs containing tag name = tag value,
            or tag name = list/tuple of qualified tag values,
            or tag name = condition function that checks each tag value if it is qualified
        :return: the set of qualified objects
        """
        return functools.reduce(
            lambda x, y: x.intersection(y),
            [self._mapping[tag_name].find_objs(tag_value=tag_value) for tag_name, tag_value in kw_tags.items()]
        )

    def find_tags(self, *objs: TagObjectType) -> Dict[TagNameType, TagValueType]:
        """Find every tag name = tag value pair that share by all ``objs``.

        :param objs: objects to find tag with
        :return: the dict containing tag name = tag value pair
        """
        return {
            tag_name: tag_value for tag_name, tag_value in [
                (tag_name, tag.find_tag(*objs)) for tag_name, tag in self._mapping.items()
            ] if tag_value is not None
        }

    def remove_tags(
            self,
            *tag_names: TagNameType,
            **kw_tags: Union[TagValueType, TagValueIterableType, TagValueFunctionType]
    ) -> None:
        """Remove tags with name in ``tag_names``, or with value qualified by ``kw_tags``.

        :param tag_names: tags to remove
        :param kw_tags: keyword pairs containing tag name = tag value,
            or tag name = list/tuple of qualified tag values,
            or tag name = condition function that checks each tag value if it is qualified
        :return: None
        """
        for tag_name in tag_names:
            del self._mapping[tag_name]
        for tag_name, tag_value in kw_tags.items():
            self._mapping[tag_name].remove_tags(tag_value)

    def remove_objs(self, *objs: TagObjectType) -> None:
        """Remove ``objs``.

        :param objs: objects to remove
        :return: None
        """
        for tag in self._mapping.values():
            tag.remove_objs(*objs)

    def clear(self) -> None:
        """Clear everything.

        :return: None
        """
        self._mapping.clear()

    def tag_decorator(self, **kw_tags: TagValueType):
        """Mark the decorated object with ``kw_tags``

        :param kw_tags: keyword pairs containing tag name = tag value
        :return: None
        """
        def inner(dec):
            self.tag(dec, **kw_tags)
            return dec

        return inner

    def get_content_string(self) -> str:
        """Get a formatted string that show tag name -> tag mapping.

        :return: the result string
        """
        return '\n'.join(
            '{}:\n{}'.format(tag_name, tag.get_content_string()) for tag_name, tag in self._mapping.items())


if __name__ == '__main__':
    sp = TagSpace()
    sp.tag(1, 1, 2, 3, 5, 8, 13, fib=True)
    sp.tag(2, 3, 5, 7, 11, 13, 17, 19, prime=True)
    sp.tag(1, 3, 5, 7, 9, 11, 13, 15, 17, 19, odd=True)
    sp.tag(3, 6, 9, 12, 15, 18, triple=True)
    sp.tag(1, 2, 5, 8, 9, pref='like')
    sp.tag(4, 10, pref='dislike')
    for i in range(1, 20):
        sp.tag(i, value=i)
    print(sp.find_objs(fib=True, prime=True, value=lambda x: x < 10))
    sp.remove_objs(2, 13)
    print(sp.find_objs(fib=True, prime=True))
    print(sp.find_tags(1, 5))
    print(sp['pref']['like'])
