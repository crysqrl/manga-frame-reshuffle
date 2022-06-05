import sys
from argparse import ArgumentParser
from collections import namedtuple
from pathlib import Path
from exceptions import NoImagesError, MinMaxError
import numpy as np
from PIL import Image


IMAGE_EXTS = ['.png', '.jpg', '.jpeg']


def min_max_int(min_value=0, max_val=float('inf')):
    def min_max(value):
        value = int(value)
        if value < min_value or value > max_val:
            raise MinMaxError(f'Number should be in range: {min_value} < value < {max_val}.')
        return value
    return min_max


def create_parser():
    parser = ArgumentParser(description='Reshuffle blocks in images')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--files', '-f', nargs='+', type=str)
    group.add_argument('--folder', '-fd', type=str)
    parser.add_argument('--join', '-j', action='store_true')
    parser.add_argument('--horizontal', '-hor', type=min_max_int(1, 5), default=4)
    parser.add_argument('--vertical', '-v', type=min_max_int(1, 5), default=4)
    parser.add_argument('--height', '-he', type=min_max_int(100, 400), default=280)
    parser.add_argument('--width', '-w', type=min_max_int(100, 400), default=200)
    parser.add_argument('--bottom', '-b', type=min_max_int(0, 50), default=17)
    parser.add_argument('--save-location', '-sl', nargs='?', type=str, default='res')
    return parser


def parse_arguments(parser):
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
    if not Path(path).is_dir():
        raise FileNotFoundError('Not directory or directory doesn\'t exist.')
    return True


def is_file_exist(path):
    return Path(path).is_file()


def load_files(file_list):
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
    file_list = Path(path).iterdir()
    file_names = load_files(file_list)

    return file_names


def reshuffle_image(image, settings):
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
    return np.hstack(tuple(image_list))


def save_image(name, image, save_location):
    Path(save_location).mkdir(parents=True, exist_ok=True)

    image = Image.fromarray(image)
    save_path = Path(save_location).joinpath(f'reshuffled_{name}')
    image.save(save_path)


def save_images(names, image_list, save_location):
    for name, image in zip(names, image_list):
        save_image(name, image, save_location)


def process_images(image_list, settings):
    reshuffled_images = []
    stems = []
    for image_path in image_list:

        image = Image.open(image_path)
        image = np.asarray(image)
        reshuffled_image = reshuffle_image(image, settings)

        reshuffled_images.append(reshuffled_image)

    return reshuffled_images


def main():

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
