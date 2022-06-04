import sys
import os
from argparse import ArgumentParser, ArgumentTypeError
from collections import namedtuple
from pathlib import Path

import numpy as np
from PIL import Image


IMAGE_EXTS = ['.png', '.jpg', '.jpeg']


class MinMaxError(ArgumentTypeError):
    pass


class NoImagesError(FileNotFoundError):
    pass


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
    print((file_list, folder_path, join_enabled, save_location), (b_height, b_width, h_blocks, v_blocks, bottom_pixels))
    return (file_list, folder_path, join_enabled, save_location), (b_height, b_width, h_blocks, v_blocks, bottom_pixels)


def is_folder_exist(path):
    if not os.path.isdir(path):
        raise FileNotFoundError('Not directory or directory doesn\'t exist.')
    return True


def is_file_exist(path):
    return not os.path.isfile(path)


def load_files(file_list):
    file_names = []
    for file_path in file_list:
        ext = os.path.splitext(file_path)[1]
        if not is_file_exist(file_path) or ext not in IMAGE_EXTS:
            continue
        file_names.append(file_path)

    if not file_names:
        raise NoImagesError('Folder doesn\'t contain images or no appropriate images provided.')

    return file_names


def load_files_from_folder(path):
    file_list = os.listdir(path)
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


def save_images(image_list, save_location):
    if not os.path.exists(save_location):
        os.makedirs(save_location)

    for name, img in image_list:
        image = Image.fromarray(img)
        save_path = Path(save_location).joinpath(f'reshuffled_{name}')
        image.save(save_path)


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

    processed_images = []
    for image_path in image_list:
        name = Path(image_path).name
        img_path = Path(folder_path).joinpath(image_path)
        img = Image.open(img_path)
        img = np.asarray(img)
        img = reshuffle_image(img, shuffle_settings)
        processed_images.append((name, img))

    save_images(processed_images, save_location)

if __name__ == '__main__':
    try:
        main()
    except (NoImagesError, FileNotFoundError) as er:
        print(er)
