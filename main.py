from argparse import ArgumentParser, ArgumentTypeError
from shuffler.shuffler import Shuffler


class MinMaxError(ArgumentTypeError):
    pass


def min_max_int(min_val=0, max_val=float('inf')):
    """
    Argument validator.
    By default validates if argument is positive.
    Validates if argument is in range min_val < value < max_val.

    params:
        min_val (number): Minimum value of int argument.
        max_val (number): Maximum value of int argument.
    returns: int.
    """

    def min_max(value):
        value = int(value)
        if value < min_val or value > max_val:
            raise MinMaxError(f'Number should be in range: {min_val} < value < {max_val}.')
        return value
    return min_max


def create_parser():
    """
    Create parser with arguments and mutually exclusive group.

    returns: ArgumentParser instance.
    """

    parser = ArgumentParser(description='Reshuffle blocks in images')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--files', '-f', nargs='+', type=str, help='Files (paths) to shuffle.')
    group.add_argument('--folder', '-fd', type=str, help='Folder (path) to shuffle.')
    parser.add_argument('--join', '-j', action='store_true', help='Horizontally joins 2 images. Images must be same heigt.')
    parser.add_argument('--horizontal', '-hor', type=min_max_int(1, 5), default=4, help='Number of horizontal blocks.')
    parser.add_argument('--vertical', '-v', type=min_max_int(1, 5), default=4, help='Number of vertical blocks.')
    parser.add_argument('--height', '-he', type=min_max_int(100, 400), default=280, help='Block height.')
    parser.add_argument('--width', '-w', type=min_max_int(100, 400), default=200, help='Block width.')
    parser.add_argument('--bottom', '-b', type=min_max_int(0, 50), default=17, help='Number of pixels from the bottom to ignore.')
    parser.add_argument('--save-location', '-sl', nargs='?', type=str, default='res', help='Save location path')
    return parser


def parse_arguments(parser):
    """
    Parses arguments.

    params:
        parser (ArgumentParser): parser that parses arguments.
    returns: tuple, tuple.
    """

    args = parser.parse_args()
    file_list = args.files
    folder_path = args.folder
    join_enabled = args.join
    h_blocks = args.horizontal
    v_blocks = args.vertical
    b_height = args.height
    b_width = args.width
    bottom_pixels = args.bottom
    save_location = args.save_location
    return (file_list, folder_path, join_enabled, save_location), (b_height, b_width, h_blocks, v_blocks, bottom_pixels)


def main():
    """
    Main script.
    """

    parser = create_parser()

    (file_list, folder_path, join_enabled, save_location), arg_settings = parse_arguments(parser)

    shuffler = Shuffler(
        files=file_list,
        folder=folder_path,
        settings=arg_settings,
        is_join_enabled=join_enabled,
        save_location=save_location
    )

    shuffler.process_images(save=True)


if __name__ == '__main__':
    main()
