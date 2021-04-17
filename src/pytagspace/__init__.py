from .tag_space import TagSpace, Tag, TagValueFilter


__default = TagSpace()
tag = __default.tag
tag_decorator = __default.tag_decorator
find_objs = __default.find_objs
find_tags = __default.find_tags
remove_objs = __default.remove_objs
remove_tags = __default.remove_tags
clear = __default.clear
get_content_string = __default.get_content_string
