import unittest

from src.pytagspace import TagSpace
import src.pytagspace as pts


class TSTestCase(unittest.TestCase):
    def test_number(self):
        space = TagSpace()
        space.tag(2, 3, 5, 7, 11, 13, 17, 19, prime=True)
        space.tag(1, 3, 5, 7, 9, 11, 13, 15, 17, 19, odd=True)
        space.tag(*range(11, 20), note='ROI A')
        space.tag(*range(1, 17), note='ROI B')
        self.assertSetEqual(
            space.find(note='ROI A', prime=True, odd=True),
            {11, 13, 17, 19}
        )
        self.assertSetEqual(
            space.find(note='ROI B', prime=True, odd=True),
            {3, 5, 7, 11, 13}
        )
        space.remove(note='ROI A')
        self.assertSetEqual(
            space.find(note='ROI A', prime=True, odd=True),
            set()
        )
        space.remove('note')
        self.assertRaises(
            KeyError,
            space.find,
            note='ROI B'
        )

    def test_function(self):
        class C1:
            def __call__(self, *args, **kwargs):
                return 1

        class C2:
            def __call__(self, *args, **kwargs):
                return 2

        c1 = C1()
        c2 = C2()

        def fun1():
            return 1

        def fun2():
            return 2

        pts.tag(fun1, fun2, is_function=True)
        pts.tag(C1, C2, is_class=True)
        pts.tag(c1, c2, is_inst=True)
        pts.tag(fun1, c1, return_value=1)
        pts.tag(fun2, c2, return_value=2)
        self.assertSetEqual(
            pts.find(is_function=True, return_value=1),
            {fun1}
        )
        self.assertSetEqual(
            pts.find(is_class=True),
            {C1, C2}
        )
        s = pts.find(return_value=2)
        self.assertEqual(len(s), 2)
        for e in s:
            self.assertEqual(e(), 2)


if __name__ == '__main__':
    unittest.main()
