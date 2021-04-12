import unittest

from datetime import timedelta
from dataclasses import dataclass

from src.pytagspace import TagSpace
import src.pytagspace as pts


class TSTestCase(unittest.TestCase):
    def test_number(self):
        space = TagSpace()
        space.tag(2, 3, 5, 7, 11, 13, 17, 19, prime=True)
        space.tag(1, 3, 5, 7, 9, 11, 13, 15, 17, 19, odd=True)
        space.tag(*list(range(11, 20)), note='ROI A')
        space.tag(*list(range(1, 17)), note='ROI B')
        self.assertSetEqual(
            space.find_objs(note='ROI A', prime=True, odd=True),
            {17, 19}
        )
        self.assertSetEqual(
            space.find_objs(note='ROI B', prime=True, odd=True),
            {3, 5, 7, 11, 13}
        )
        space.remove_tags(note='ROI A')
        self.assertSetEqual(
            space.find_objs(note='ROI A', prime=True, odd=True),
            set()
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

        @pts.tag_decorator(is_function=True)
        def fun1():
            return 1

        @pts.tag_decorator(is_function=True)
        def fun2():
            return 2

        pts.tag(C1, C2, is_class=True)
        pts.tag(c1, c2, is_inst=True)
        pts.tag(fun1, c1, return_value=1)
        pts.tag(fun2, c2, return_value=2)
        self.assertSetEqual(
            pts.find_objs(is_function=True, return_value=1),
            {fun1}
        )
        self.assertSetEqual(
            pts.find_objs(is_class=True),
            {C1, C2}
        )
        s = pts.find_objs(return_value=2)
        self.assertEqual(len(s), 2)
        for e in s:
            self.assertEqual(e(), 2)

    def test_movie(self):
        pts.clear()

        @dataclass(frozen=True)
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
        self.assertSetEqual(
            pts.find_objs(duration=lambda x: x < timedelta(hours=2)),
            {movies[0], movies[2]}
        )
        # Movies under 2 hours: Thunder Force and Run

        pts.remove_objs(movies[0])

        self.assertSetEqual(
            pts.find_objs(duration=lambda x: x < timedelta(hours=2)),
            {movies[2]}
        )
        # Movies under 2 hours: Run

        pts.remove_tags('duration', year=2019)

        self.assertSetEqual(
            pts.find_objs(duration=lambda x: x < timedelta(hours=2)),
            set()
        )
        self.assertSetEqual(
            pts.find_objs(year=2019),
            set()
        )


if __name__ == '__main__':
    unittest.main()
