import sys
from argparse import ArgumentParser
from collections import namedtuple
from pathlib import Path
from exceptions import NoImagesError, MinMaxError
import numpy as np
from PIL import Image


IMAGE_EXTS = ['.png', '.jpg', '.jpeg']


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


def is_folder_exist(path):
    """
    Checks if folder exists.

    params:
        path (str): path to a folder.
    returns: bool.
    """

    if not Path(path).is_dir():
        raise FileNotFoundError('Not directory or directory doesn\'t exist.')
    return True


def is_file_exist(path):
    """
    Checks if file exists.

    params:
        path (str): path to a folder.
    returns: bool.
    """

    return Path(path).is_file()


def load_files(file_list):
    """
    Loads files from list of file names.

    params:
        file_list (list[str]): list of file names.
    returns: list[Path]
    """

    file_names = []
    for file_path in file_list:
        ext = Path(file_path).suffix
        if not is_file_exist(file_path) or ext not in IMAGE_EXTS:
            continue
        file_names.append(Path(file_path))

    if not file_names:
        raise NoImagesError('No images found.')

    return file_names


def load_files_from_folder(path):
    """
    Loads files from folder.

    params:
        path (str): path to a folder.
    returns: list[Path]
    """
    

    file_list = Path(path).iterdir()
    file_names = load_files(file_list)

    return file_names


def reshuffle_image(image, settings):
    """
    Reshuffles image.

    params:
        image (np.array): image to process.
        settings (namedtuple): settings that include number of blocks and block sizes.
    returns: image
    """

    processed_image = np.zeros(image.shape, np.uint8)

    h_blocks = settings.h_blocks
    v_blocks = settings.v_blocks
    b_height = settings.b_height
    b_width = settings.b_width
    bp = settings.bp

    # fill bottom pixels
    processed_image[-bp:, :] = image[-bp:, :]

    for i in range(h_blocks):
        for j in range(v_blocks):
            processed_image[j*b_height:j*b_height+b_height, i*b_width:i*b_width+b_width] = image[i*b_height:i*b_height+b_height, j*b_width:j*b_width+b_width]
    return processed_image


def join_images(image_list):
    """
    Joins 2 images

    params:
        image_list (list(np.array)): list of images to join.
    returns: np.array
    """

    return np.hstack(tuple(image_list))


def save_image(name, image, save_location):
    """
    Saves image

    params:
        name (str) - name of the image.
        image (np.array) - image to save.
        save_location (str): save location path.
    """

    Path(save_location).mkdir(parents=True, exist_ok=True)

    image = Image.fromarray(image)
    save_path = Path(save_location).joinpath(f'reshuffled_{name}')
    image.save(save_path)


def save_images(names, image_list, save_location):
    """
    Saves images

    params:
        names (list[str]) - names of the images.
        image_list (list[np.array]) - images to save.
        save_location (str): save location path.
    """

    for name, image in zip(names, image_list):
        save_image(name, image, save_location)


def process_images(image_list, settings):
    """
    Process images.

    params:
        image_list (list[np.array]): images to process.
        settings (namedtuple): settings that include number of blocks and block sizes.
    returns: list[np.array]
    """

    reshuffled_images = []
    stems = []
    for image_path in image_list:
        image = Image.open(image_path)
        image = np.asarray(image)
        reshuffled_image = reshuffle_image(image, settings)
        reshuffled_images.append(reshuffled_image)

    return reshuffled_images


def main():
    """
    Main script.
    """

    parser = create_parser()

    (file_list, folder_path, join_enabled, save_location), arg_settings = parse_arguments(parser)

    if file_list:
        image_list = load_files(file_list)
    elif folder_path:
        is_folder_exist(folder_path)
        image_list = load_files_from_folder(folder_path)

    Settings = namedtuple('Setting', ['b_height', 'b_width', 'h_blocks', 'v_blocks', 'bp'])
    shuffle_settings = Settings(*arg_settings)

    reshuffled_images = process_images(image_list, shuffle_settings)

    if len(reshuffled_images) == 2 and join_enabled:
        name = f'{image_list[0].stem}_{image_list[1].name}'
        reshuffled_image = join_images(reshuffled_images)
        save_image(name, reshuffled_image, save_location)
    else:
        names = [image_path.name for image_path in image_list]
        save_images(names, reshuffled_images, save_location)


if __name__ == '__main__':
    try:
        main()
    except (NoImagesError, FileNotFoundError) as er:
        print(er)
