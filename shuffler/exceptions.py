from argparse import ArgumentTypeError


class MinMaxError(ArgumentTypeError):
    pass


class NoImagesError(FileNotFoundError):
    pass