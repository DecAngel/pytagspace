# pytagspace

A utility package that marks objects and finds them with tags.

## Examples:
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

# create a space instead of the default one
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