"""pytagspace package

This module implements the TagSpace, Tag and its subclasses

"""

import weakref
import math
from collections import defaultdict
from typing import Any, Set, Callable, TypeVar, Dict, Union, Optional


TagKeyTypes = TypeVar('TagKeyTypes', int, float, str, bool)


class Tag:
    """A dictionary-like class that store references (possibly weak) to objects under different tags.

    """
    def __init__(self, *, is_weak: bool = False, description: str = None):
        self._is_weak: bool = is_weak
        self._description: str = description
        self._mapping: Dict[TagKeyTypes, Set[Any]] = defaultdict(set)

    def __getitem__(self, tag_key: Union[TagKeyTypes, Callable[[TagKeyTypes], bool]]):
        return self.find(tag_key=tag_key)

    def __delitem__(self, tag_key: Union[TagKeyTypes, Callable[[TagKeyTypes], bool]]):
        return self.remove(tag_key=tag_key)

    def __setitem__(self, tag_key, obj):
        raise PermissionError('Cannot set tag objects')

    def __str__(self):
        return str(self._mapping)

    def tag(self, *objs: Any, tag_key: TagKeyTypes):
        """Mark objects with ``tag_key`` as tag.

        :param objs: the objects to mark
        :param tag_key: the tag
        :return:
        """
        if self._is_weak is True:
            refs = {weakref.ref(obj) for obj in objs}
        else:
            refs = set(objs)
        self._mapping[tag_key].update(refs)

    def find(self, *, tag_key: Union[TagKeyTypes, Callable[[TagKeyTypes], bool]]) -> Set[Any]:
        """Find objects with tag equals ``tag_key`` or with tag qualified by ``tag_key``.

        :param tag_key: the tag or the tag condition function
        :return: a set of qualified objects
        """
        objs = set()
        if isinstance(tag_key, (int, float, str, bool)):
            if self._is_weak is True:
                self._weak_clear()
                objs.update({ref() for ref in self._mapping[tag_key]})
            else:
                objs.update(self._mapping[tag_key])
        else:
            if self._is_weak is True:
                self._weak_clear()
                for key in self._mapping.keys():
                    if tag_key(key) is True:
                        objs.update({ref() for ref in self._mapping[key]})
            else:
                for key in self._mapping.keys():
                    if tag_key(key) is True:
                        objs.update(self._mapping[key])
        return objs

    def remove(self, *, tag_key: Union[TagKeyTypes, Callable[[TagKeyTypes], bool]]):
        """Remove references stored under ``tag_key`` as tag.

        :param tag_key: the tag to remove
        :return:
        """
        if isinstance(tag_key, (int, float, str, bool)):
            self._mapping[tag_key].clear()
        else:
            for key in self._mapping.keys():
                if tag_key(key) is True:
                    self._mapping[key].clear()

    def _weak_clear(self):
        """ Clear unavailable weak references.

        :return:
        """
        invalid_refs = set()
        for refs in self._mapping.values():
            for ref in refs:
                if ref() is None:
                    invalid_refs.add(ref)
        for key in self._mapping.keys():
            self._mapping[key].difference_update(invalid_refs)


class BoolTag(Tag):
    """A ``Tag`` class with bool tags.

    """
    def tag(self, *objs: Any, tag_key: bool = True):
        super(BoolTag, self).tag(*objs, tag_key=tag_key)

    def find(self, *, tag_key: bool = True) -> Set[Any]:
        return super(BoolTag, self).find(tag_key=tag_key)

    def remove(self, *, tag_key: bool = True):
        super(BoolTag, self).remove(tag_key=tag_key)


class NumTag(Tag):
    """A ``Tag`` class with numerical tags.

    Includes a boundary check if bounds are provided.

    """
    def __init__(self, *, lower_bound: Union[int, float] = -math.inf,
                 upper_bound: Union[int, float] = math.inf, **kwargs):
        super().__init__(**kwargs)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def tag(self, *objs: Any, tag_key: Union[int, float]):
        self._check_range(tag_key)
        super(NumTag, self).tag(*objs, tag_key=tag_key)

    def find(self, *, tag_key: Union[int, float, Callable[[Union[int, float]], bool]]) -> Set[Any]:
        if isinstance(tag_key, (int, float)):
            self._check_range(tag_key)
        return super(NumTag, self).find(tag_key=tag_key)

    def remove(self, *, tag_key: Union[int, float, Callable[[Union[int, float]], bool]]):
        if isinstance(tag_key, (int, float)):
            self._check_range(tag_key)
        return super(NumTag, self).remove(tag_key=tag_key)

    def _check_range(self, tag_key: Union[int, float]):
        if tag_key < self.lower_bound:
            raise ValueError('tag_key = {} is less than lower_bound = {}'.format(tag_key, self.lower_bound))
        elif tag_key > self.upper_bound:
            raise ValueError('tag_key = {} is greater than upper_bound = {}'.format(tag_key, self.upper_bound))


class StringTag(Tag):
    """A ``Tag`` class with string tags.

    Includes a category check if categories are provided.

    """
    def __init__(self, *categories: str, **kwargs):
        super().__init__(**kwargs)
        self.categories = categories

    def tag(self, *objs: Any, tag_key: str):
        self._check_categories(tag_key)
        super(StringTag, self).tag(*objs, tag_key=tag_key)

    def find(self, *, tag_key: Union[str, Callable[[str], bool]]) -> Set[Any]:
        if isinstance(tag_key, str):
            self._check_categories(tag_key)
        return super(StringTag, self).find(tag_key=tag_key)

    def remove(self, *, tag_key: Union[str, Callable[[str], bool]]):
        if isinstance(tag_key, str):
            self._check_categories(tag_key)
        super(StringTag, self).remove(tag_key=tag_key)

    def _check_categories(self, tag_key: str):
        if len(self.categories) > 0:
            if tag_key not in self.categories:
                raise ValueError('tag_key = {} not in categories = {}'.format(tag_key, self.categories))


class TagSpace:
    """A collection of ``Tag``s.

    """
    def __init__(self, is_arbitrary: bool = True, is_weak: bool = False, description: str = None):
        self._is_arbitrary = is_arbitrary
        self._is_weak = is_weak
        self._description = description

    def tag(self, *objs, **kw_tags: TagKeyTypes):
        """Mark objects with one or more tags

        :param objs: the objects to tag.
        :param kw_tags: tag name and tag key pairs
        :return:
        """
        for tag_name, tag_key in kw_tags.items():
            if not hasattr(self, tag_name):
                if self._is_arbitrary is True:
                    if isinstance(tag_key, bool):
                        self.__setattr__(tag_name, BoolTag(is_weak=self._is_weak))
                    elif isinstance(tag_key, (int, float)):
                        self.__setattr__(tag_name, NumTag(is_weak=self._is_weak))
                    else:
                        self.__setattr__(tag_name, StringTag(is_weak=self._is_weak))
                else:
                    raise KeyError('{} not in this TagSpace'.format(tag_name))
            self.__getattribute__(tag_name).tag(*objs, tag_key=tag_key)

    def find(self, **kw_tags: Union[TagKeyTypes, Callable[[TagKeyTypes], bool]]) -> Set[Any]:
        """Find objects with one or more conditions

        :param kw_tags: tag name and tag key or condition function pairs
        :return: a set of qualified objects
        """
        res: Optional[Set] = None
        for tag_name, tag_key in kw_tags.items():
            if not hasattr(self, tag_name):
                raise KeyError('{} not in this TagSpace'.format(tag_name))
            else:
                q = self.__getattribute__(tag_name).find(tag_key=tag_key)
                if res is None:
                    res = q
                else:
                    res.intersection_update(q)
        return res if res is not None else set()

    def remove(self, *tag_names, **kw_tags: Union[TagKeyTypes, Callable[[TagKeyTypes], bool]]):
        """Remove tags in ``tag_names`` and remove tag key in ``kw_tags``

        :param tag_names: the tag name to remove
        :param kw_tags: the tag name: tag key to remove
        :return:
        """
        for tag_name in tag_names:
            if not hasattr(self, tag_name):
                raise KeyError('{} not in this TagSpace'.format(tag_name))
            else:
                self.__delattr__(tag_name)
        for tag_name, tag_key in kw_tags.items():
            if not hasattr(self, tag_name):
                raise KeyError('{} not in this TagSpace'.format(tag_name))
            else:
                self.__getattribute__(tag_name).remove(tag_key=tag_key)

    def clear(self):
        """Clear all tags

        :return:
        """
        for tag_name, tag_inst in vars(self).items():
            if isinstance(tag_inst, Tag):
                self.__delattr__(tag_name)

    def __str__(self):
        res = ''
        for tag_name, tag_inst in vars(self).items():
            if isinstance(tag_inst, Tag):
                res += '{}: {}\n'.format(tag_name, tag_inst)
        return res
