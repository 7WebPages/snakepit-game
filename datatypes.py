from collections import namedtuple

Position = namedtuple("Position", "x y")

Vector = namedtuple("Vector", "xdir ydir")

Char = namedtuple("Char", "char color")

Draw = namedtuple("Draw",  "x y char color")
