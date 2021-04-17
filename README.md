# pytagspace

A utility package that marks objects and finds them with tags.

## Description
This package is a simple tool to organize different objects by tags.
Use ``TagSpace`` to tag the objects with ``tag_name = tag_value`` pairs.
### Note
+ ``TagSpace`` ``Tag`` keep strong references to the tagged objects and
  therefore could use large memory if they are not removed explicitly. 
  Use ``remove_objs`` to delete them.
+ The tagged objects and tag value must be *Hashable*.
+ The name of each tag must not start with '_'.
+ Each object can only have one tag value under each tag.

## Installation
+ Install via pip
```commandline
pip install pytagspace
```

## Examples
+ Tag objects and find them
```python
import pytagspace as pts

# tag objects by kwargs
pts.tag(1, 3, 5, 7, 9, odd=True, even=False)
pts.tag(2, 3, 5, 7, prime=True)
pts.tag(5, 9, info='like')
pts.tag(2, 4, info='dislike')

# find objects (return value is a set)
print(pts.find_objs(prime=True, info='like'))
# {5}
print(pts.find_objs(info='love'))
# set()  # Empty

# find objects with list as kwargs value
print(pts.find_objs(prime=True, info=['like', 'dislike']))
# {2, 5}
print(pts.find_objs(prime=[1, 2, True]))
# {2, 3, 5, 7}

# find objects with function as kwargs value
print(pts.find_objs(prime=True, info=lambda x: x.endswith('like')))
# {2, 5}

# find common tags by objects
print(pts.find_tags(5, 9))
# {'odd': True, 'even': False, 'info': 'like'}
print(pts.find_tags(2))
# {'prime': True, 'info': 'dislike'}
```

+ Tag functions and classes
```python
from pytagspace import TagSpace

# create a TagSpace instance instead of the default one
space = TagSpace()

# use decorator tag
@space.tag_decorator(return_value=1, is_function=True)
def func1():
    return 1

@space.tag_decorator(return_value=1, is_function=False)
class C1:
    def __call__(self):
        return 1

# use normal tag
def func2():
    return 2
class C2:
    def __call__(self):
        return 2
space.tag(func2, return_value=2, is_function=True)
space.tag(C2, return_value=2, is_function=False)

# find
for f in space.find_objs(return_value=1):
    print(f())
# 1, <class C1>
for f in space.find_objs(is_function=False):
    print(f()())
# 1, 2
```

+ Tag removal
```python
import pytagspace as pts
from datetime import timedelta
from dataclasses import dataclass

@dataclass
class Movie:
    name: str
    duration: timedelta
    year: int

movies = [
    Movie(
        name='Thunder Force',
        duration=timedelta(hours=1, minutes=45), 
        year=2021
    ),
    Movie(
        name='Once Upon A Time...In Hollywood',
        duration=timedelta(hours=2, minutes=40),
        year=2019
    ),
    Movie(
        name='Run',
        duration=timedelta(hours=1, minutes=39),
        year=2020
    )
]

for movie in movies:
  pts.tag(movie, duration=movie.duration, year=movie.year)

print(pts.find_objs(duration=lambda x: x<timedelta(hours=2)))
# Movies under 2 hours: Thunder Force and Run

pts.remove_objs(movies[0])

print(pts.find_objs(duration=lambda x: x<timedelta(hours=2)))
# Movies under 2 hours: Run

pts.remove_tags('duration', year=2019)
print(pts.find_objs(duration=lambda x: x < timedelta(hours=2)))
# set()  # Empty set

print(pts.find_objs(year=2019))
# set() # Empty set
```

## Future improvements
+ Store objects using ``weakref``
+ Store objects that is not hashable(``find_tags`` and ``remove_objs`` will be unavailable) 
