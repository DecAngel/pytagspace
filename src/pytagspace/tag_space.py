"""pytagspace package

This module implements the TagSpace, Tag
"""

import functools
import collections
from typing import Dict, Optional, Union, Callable, Set, Hashable, Mapping, Iterator, Type, Any


TagNameType = str
TagValueType = Hashable
TagObjectType = Any


class Filter:
    """A wrapper of function that select tag values.

    """
    def __init__(self, function: Callable[[TagValueType], bool]):
        self._func = function

    def __call__(self, value: TagValueType) -> bool:
        return self._func(value)


TagValueFilter = Filter


def is_tag_name(name: TagNameType) -> bool:
    """Identify if ``name`` is a valid tag name.

    """
    return isinstance(name, str) and not name.startswith('_')


def is_tag_value(value: TagValueType) -> bool:
    """Identify if ``value`` is a valid tag value.

    """
    return isinstance(value, Hashable)


def is_tag_value_function(func: Filter) -> bool:
    """Identify if ``func`` is a valid tag value selection function.

    """
    return isinstance(func, Filter)


def is_tag_obj_hashable(obj: TagObjectType) -> bool:
    """Identify if ``obj`` is a hashable tag object

    """
    return isinstance(obj, Hashable)


class Tag(Mapping[TagValueType, Set[TagObjectType]]):
    """A *Reversible* mapping from ``tag_value`` to ``tag_object``s.

    The ``tag_value`` and ``tag_object``s must be *Hashable*, each ``tag_objects`` can only have one ``tag_value``.

    """

    def __init__(self):
        self._mapping: Dict[TagValueType, Set[TagObjectType]] = collections.defaultdict(set)
        self._reverse_mapping: Dict[TagObjectType, TagValueType] = {}

    def __len__(self) -> int:
        return len(self._mapping)

    def __iter__(self) -> Iterator[TagValueType]:
        return self._mapping

    def __getitem__(self, item: Union[TagValueType, Filter]) -> Set[TagObjectType]:
        return self.find_objs(item)

    def __delitem__(self, key: Union[TagValueType, Filter]) -> None:
        self.remove_tags(key)

    def _tag(self, obj: TagObjectType, tag_value: TagValueType):
        if not is_tag_obj_hashable(obj):
            if hasattr(obj, '__repr__') or hasattr(obj, '__str__'):
                raise ValueError('obj {} must be *Hashable*.'.format(obj))
            else:
                raise ValueError('obj must be *Hashable*.')
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

    def tag(self, *objs: TagObjectType, tag_value: TagValueType) -> None:
        """Mark ``objs`` with ``tag_value``.

        If ``obj`` is already tagged, overwrite the tag. (Each ``obj`` can only have one ``tag_value``)

        :param objs: objects to mark
        :param tag_value: a *Hashable* tag value
        :return: None
        """
        if is_tag_value(tag_value):
            for obj in objs:
                self._tag(obj, tag_value)
        else:
            raise ValueError('tag_value must be a Hashable')

    def find_objs(
            self,
            tag_value: Union[TagValueType, Filter]
    ) -> Set[TagObjectType]:
        """Find objects with tag value qualified by ``tag_value``.

        :param tag_value: a *Hashable* tag value, or a *Callable* that checks each tag value if it is qualified
        :return: the set of qualified objects
        """
        if is_tag_value_function(tag_value):
            objs = [self._mapping[value] for value in self._mapping.keys() if tag_value(value)]
            return set() if len(objs) == 0 else functools.reduce(
                lambda x, y: x.union(y),
                objs
            ).copy()
        elif is_tag_value(tag_value):
            return self._mapping[tag_value].copy()
        else:
            raise ValueError('tag_value must be a Hashable or a Callable')

    def find_tag(self, *objs: TagObjectType) -> Optional[TagValueType]:
        """Find tag value that shared by all ``objs``.

        :param objs: objects to find tag value with
        :return: the tag value, or None if ``objs`` don't share the same tag
        """
        return functools.reduce(
            lambda x, y: x if x == y else None,
            [
                (self._reverse_mapping[obj] if obj in self._reverse_mapping else None)
                for obj in objs
            ]
        )

    def remove_tags(self, tag_value: Union[TagValueType, Filter]) -> None:
        """Remove tags qualified by ``tag_value``.

        :param tag_value: a *Hashable* tag value, or a *Callable* that checks each tag value if it is qualified
        :return: None
        """
        if is_tag_value_function(tag_value):
            values = []
            for value in self._mapping.keys():
                if tag_value(value):
                    values.append(value)
            for value in values:
                self._remove_tag(value)
        elif is_tag_value(tag_value):
            self._remove_tag(tag_value)
        else:
            raise ValueError('tag_value must be a Hashable or a Callable')

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

    def __init__(self, is_strict: bool = False, default_tag: Type[Tag] = Tag):
        if is_strict:
            self._mapping: Dict[TagNameType, default_tag] = {}
        else:
            self._mapping: Dict[TagNameType, default_tag] = collections.defaultdict(default_tag)
        self._default_tag = default_tag

    def __getitem__(self, item: TagNameType):
        return self._mapping[item]

    def __delitem__(self, key: TagNameType):
        self.remove_tags(key)

    def tag(self, *objs: TagObjectType, **kw_tags: TagValueType) -> None:
        """Mark ``objs`` with tag name = tag value in ``kw_tags``.

        :param objs: objects to mark
        :param kw_tags: keyword pairs containing tag name = tag value
        :return: None
        """
        for tag_name, tag_value in kw_tags.items():
            if is_tag_name(tag_name):
                self._mapping[tag_name].tag(*objs, tag_value=tag_value)

    def find_objs(
            self,
            **kw_tags: Union[TagValueType, Filter]
    ) -> Set[TagObjectType]:
        """Find objects with tag qualified by ``tag_value``.

        :param kw_tags: keyword pairs containing tag name = tag value
            or tag name = condition function that checks each tag value if it is qualified
        :return: the set of qualified objects
        """
        objs = [self._mapping[tag_name].find_objs(tag_value=tag_value) for tag_name, tag_value in kw_tags.items()]
        return set() if len(objs) == 0 else functools.reduce(
            lambda x, y: x.intersection(y),
            objs,
        )

    def find_tags(self, *objs: TagObjectType) -> Dict[TagNameType, TagValueType]:
        """Find every tag name = tag value pair that share by all ``objs``.

        This function will raise

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
            **kw_tags: Union[TagValueType, Filter]
    ) -> None:
        """Remove tags with name in ``tag_names``, or with value qualified by ``kw_tags``.

        :param tag_names: tags to remove
        :param kw_tags: keyword pairs containing tag name = tag value,
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
