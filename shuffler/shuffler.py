from collections import namedtuple
from pathlib import Path
from shuffler.exceptions import NoImagesError
import numpy as np
from PIL import Image


IMAGE_EXTS = ['.png', '.jpg', '.jpeg']


class Shuffler:
    """
    Class that represents Shuffler
    """

    def __init__(self, files=None, folder=None, settings=None, is_join_enabled=False, save_location=None):
        try:
            self.image_list = self._load_files(files=files, folder=folder)
            self.settings = self._create_settings(settings)
            self.is_join_enabled = is_join_enabled and len(self.image_list) == 2
            self.save_location = save_location
        except (NoImagesError, FileNotFoundError, ValueError) as e:
            print(e)

    def _create_settings(self, settings):
        Settings = namedtuple('Setting', ['b_height', 'b_width', 'h_blocks', 'v_blocks', 'bp'])
        return Settings(*settings) 

    def _is_folder_exist(self, path):
        """
        Checks if folder exists.

        params:
            path (str): path to a folder.
        returns: bool.
        """

        if not Path(path).is_dir():
            raise FileNotFoundError('Not directory or directory doesn\'t exist.')
        return True

    def _is_file_exist(self, path):
        """
        Checks if file exists.

        params:
            path (str): path to a folder.
        returns: bool.
        """

        return Path(path).is_file()

    def _load_files(self, files=None, folder=None):
        """
        Loads files from list of files if provided else loads from folder.

        params:
            files (list[str]): list of file names.
            folder (str): path to a folder.
        returns: list[Path]
        """

        if files:
            return self._load_files_from_file_list(files)
        elif folder:
            return self._load_files_from_folder(folder)
        else:
            raise ValueError('No files provided')

    def _load_files_from_file_list(self, files):
        """
        Loads files from list of file names.

        params:
            files (list[str]): list of file names.
        returns: list[Path]
        """

        file_names = []
        for file_path in files:
            ext = Path(file_path).suffix
            if not self._is_file_exist(file_path) or ext not in IMAGE_EXTS:
                continue
            file_names.append(Path(file_path))

        if not file_names:
            raise NoImagesError('No images found.')

        return file_names

    def _load_files_from_folder(self, folder):
        """
        Loads files from folder.

        params:
            folder (str): path to a folder.
        returns: list[Path]
        """

        self._is_folder_exist(folder)
        file_list = Path(folder).iterdir()
        file_names = self._load_files_from_file_list(file_list)

        return file_names


    def _reshuffle_image(self, image):
        """
        Reshuffles image.

        params:
            image (np.array): image to process.
        returns: image
        """

        blank = np.zeros(image.shape, np.uint8)

        b_height, b_width, h_blocks, v_blocks, bp = self.settings

        # fill bottom pixels
        blank[-bp:, :] = image[-bp:, :]

        for i in range(h_blocks):
            for j in range(v_blocks):
                blank[j*b_height:j*b_height+b_height, i*b_width:i*b_width+b_width] = image[i*b_height:i*b_height+b_height, j*b_width:j*b_width+b_width]
        return blank


    def _join_images(self, image_list):
        """
        Joins 2 images

        params:
            image_list (list(np.array)): list of images to join.
        returns: np.array
        """

        return np.hstack(tuple(image_list))


    def _save_image(self, name, image, save_location):
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


    def save(self, images, save_location=None):
        """
        Saves images

        params:
            images (list[(name, img)]): list of tuples - name, image.
            save_location (str): save location path.
        """

        if save_location is None:
            save_location = self.save_location

        for name, image in images:
            print(name, image.shape)
            self._save_image(name, image, save_location)


    def _open_image(self, image_path):
        """
        Opens image. Converts to np.array.

        params:
            image_path (Path): path to image.
        returns: np.array
        """
        image = Image.open(image_path)
        return np.asarray(image)

    def process_images(self, save=False):
        """
        Process images.

        params:
            image_list (list[np.array]): images to process.
            settings (namedtuple): settings that include number of blocks and block sizes.
        returns: list[(name, image)]
        """

        names = [image_path.name for image_path in self.image_list]
        result = []
        for image_path in self.image_list:
            image = self._open_image(image_path)
            reshuffled_image = self._reshuffle_image(image)
            result.append(reshuffled_image)

        if self.is_join_enabled:
            names = [f'{self.image_list[0].stem}_{self.image_list[1].name}']
            result = [self._join_images(result)]

        result = zip(names, result)
        if save:
            self.save(result)
        return list(result)
