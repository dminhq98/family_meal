import os
import base64
import io
import requests
import cv2
import json
import logging
import argparse
import numpy as np
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from datetime import datetime
import pytz
import torch
import torchvision.transforms as transforms
from torchvision.datasets.folder import default_loader
import search.models as models
import h5py

date_format = "%Y-%m-%d"
datetime_format = "%Y-%m-%d_%H-%M-%S"
datetime_format_miliseconds = "%Y-%m-%d_%H:%M:%S.%f"
vn_timezone = 'Asia/Ho_Chi_Minh'

def load_config_file(config_path):
    json_load = None
    if os.path.isfile(config_path):
        with open(config_path, encoding="utf-8") as f:
            json_load = json.load(f)
    else:
        raise FileExistsError(f"{config_path} is not valid")
    return json_load

def make_dir(path):
    if path != "":
        os.makedirs(path, exist_ok=True)

def make_dir_path(path):
    if os.path.dirname(path) != "":
        os.makedirs(os.path.dirname(path), exist_ok=True)

def validate_file_exists(path):
    if not os.path.exists(path):
        print(path, "not exist")
        msg_text = "{} does not exist".format(path)
        raise FileNotFoundError(msg_text)

def vntime_now(dt_format=None):
    utc_now = pytz.utc.localize(datetime.utcnow())
    if dt_format is not None:
        # return formatted time
        vntime = utc_now.astimezone(
            pytz.timezone(vn_timezone)).strftime(dt_format)
    else:
        vntime = utc_now.astimezone(pytz.timezone(vn_timezone))

    return vntime

class ListDataset(torch.utils.data.Dataset):
    '''
        Datasets for extract features

        Parameters
        ----------

        images_list : list
            images list of datasets
        transform:
            transforms for images return
        loader:
            function read images
    '''

    def __init__(self, images_list, transform=None, loader=default_loader):
        self.images_list = images_list
        self.loader = loader
        self.transform = transform

    def __getitem__(self, index):

        image_path = self.images_list[index]
        image = self.loader(image_path)
        if self.transform is not None:
            image = self.transform(image)
        return image, image_path

    def __len__(self):
        return len(self.images_list)

def load_model(
        name,
        pretrained=True,
        weight=None,
        disable_gpu=True,
        cuda_id=-1):
    """
        returns 1 pair of model and device respectively.

        Parameters
        ----------
        name : str
            name model. eg: resnet50 ....
        pretrained : boolean
            using pretrained or Not
        weight :str
            path weight file for model. (.pt, .pth)
        disable_gpu : boolean
            not use GPU or use GPU
        cuda_id:
            GPU id is used

    """
    print("\nload model extract features")
    if disable_gpu:
        print("\n Load feature model in CPU")
        torch_device = torch.device("cpu")
    else:
        print("\n Try load model in GPU if available")
        torch_device = torch.device("cuda:{}".format(cuda_id)) \
            if torch.cuda.is_available() else torch.device("cpu")
        print("Device :{}".format(torch_device))
    if 'rmac' in name.split('_'):
        if weight:
            # load checkpoint weights and update model and optimizer
            print(">> Loading checkpoint:\n>> '{}'".format(weight))
            checkpoint = torch.load(weight, map_location=torch_device)
            arg_model = checkpoint['arg_model']
            model = models.__dict__[name](**arg_model)
            model.load_state_dict(checkpoint['state_dict'])
            model.to(torch_device)
            model.eval()
            return model, torch_device
        else:
            raise (RuntimeError("Can not find the weight for {} !".format(name)))

    model = models.__dict__[name](pretrained=pretrained)
    if weight:
        checkpoint = torch.load(weight, map_location=torch_device)

        if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
            checkpoint = checkpoint['state_dict']
        print('Loading weight from : {}'.format(weight))
        model.load_state_dict(checkpoint, strict=False)

        missing_keys = set(model.state_dict().keys()) - set(checkpoint.keys())
        extra_keys = set(checkpoint.keys()) - set(model.state_dict().keys())
        if missing_keys:
            print('Missing keys in --weight-file: {}.'.format(missing_keys))
        if extra_keys:
            print('Extra keys ignored in --weight-file: {}.'.format(extra_keys))

    model.to(torch_device)
    model.eval()
    return model, torch_device

def load_features(path_feature):
    """
    Read features, path_images from HDF5 file.
    Parameters
        ----------
        path_feature : str
            path to features file. (.h5)

    """
    try:
        file = h5py.File(path_feature, 'r')
        features = file['features'][:]
        path_images = file['path_images']
        path_images = list(path_images)
        for idx, i in enumerate(path_images):
            if not isinstance(i, str):
                path_images[idx] = i.decode("utf-8")

        print("\n Loaded feature: {} ".format(path_feature))
        return features, path_images
    except OSError as eror:

        print("\n Failed {} "
              "OSError: {} ".
              format(path_feature, eror))
        raise


class CustomPadding:
    """
    Transform padding image to a square
    """

    def __init__(self, value):
        assert len(value) == 3
        self.value = value

    def __call__(self, pil_img):
        w, h = pil_img.size
        new_size = max(pil_img.size)
        new_img = Image.fromarray(
            np.full((new_size, new_size, 3), self.value, dtype=np.uint8))
        if w >= h:
            top_pad = (w - h) // 2
            new_img.paste(pil_img, (0, top_pad))
        else:
            left_pad = (h - w) // 2
            new_img.paste(pil_img, (left_pad, 0))
        return new_img

def load_transform(size=224, pre_crop=256, padding=False):
    '''
        Loading transforms for extracter and seacher
    '''
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    )
    if size == (288, 144):
        normalize = transforms.Normalize(
            (0.486, 0.459, 0.408), (0.229, 0.224, 0.225))

    transform = [
        transforms.ToTensor(),
        normalize,
    ]
    if pre_crop:
        transform = [
            transforms.Resize(pre_crop),
            transforms.CenterCrop(size)] + transform
    else:
        transform = [transforms.Resize(size)] + transform
    if padding:
        transform = [CustomPadding((255, 255, 255))] + transform
    transform = transforms.Compose(transform)
    return transform

class ImageAdapter:
    """
        Handle image type to convert
    """

    def __init__(self, **kwargs):
        """
            kargs: base64_img, cv_img, pil_img, url , path
        """
        self.cv_img = None
        self.pil_img = None
        # print(kwargs)

        if len(kwargs) > 1:
            raise ValueError("Can't pass multi image into ImageAdapter")
        try:
            if "base64_img" in kwargs:
                base64_img = kwargs["base64_img"]
                self.pil_img = ImageAdapter.base_64_to_pil(base64_img)
                self.cv_img = ImageAdapter.base_64_to_cv(base64_img)
            elif "cv_img" in kwargs:
                self.cv_img = kwargs["cv_img"]
                self.pil_img = ImageAdapter.cv_to_pil(self.cv_img)
            elif "pil_img" in kwargs:
                self.pil_img = kwargs["pil_img"]
                self.cv_img = ImageAdapter.pil_to_cv(self.pil_img)
            elif "url" in kwargs:
                response = requests.get(kwargs["url"])
                self.pil_img = Image.open(io.BytesIO(
                    response.content)).convert("RGB")
                self.cv_img = ImageAdapter.pil_to_cv(self.pil_img)
            elif "path" in kwargs:
                path = kwargs["path"]
                self.pil_img = Image.open(path).convert("RGB")
                self.cv_img = ImageAdapter.pil_to_cv(self.pil_img)

        except Exception:
            print("Your input argument is not valid")
            raise

    def get_cv(self):
        return self.cv_img

    def get_pil(self):
        return self.pil_img

    def get_np_array(self):
        return np.array(self.pil_img)

    @staticmethod
    def base_64_to_pil(msg):
        msg = msg[
            msg.find(b"<plain_txt_msg:img>")
            + len(b"<plain_txt_msg:img>"): msg.find(b"<!plain_txt_msg>")
        ]
        msg = base64.b64decode(msg)
        buf = io.BytesIO(msg)
        img = Image.open(buf)
        return img

    @staticmethod
    def base_64_to_cv(msg):
        return cv2.cvtColor(
            np.array(ImageAdapter.base_64_to_pil(msg)), cv2.COLOR_BGR2RGB
        )

    @staticmethod
    def pil_to_cv(image):
        return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)

    @staticmethod
    def cv_to_pil(image):
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

def str2size(v):
    if isinstance(v, int):
        return v
    try:
        return int(v)
    except:
        if len(v.split(',')) == 2:
            try:
                return (int(v.split(',')[0]), int(v.split(',')[1]))
            except BaseException:
                raise argparse.ArgumentTypeError('Size value expected.')
        else:
            raise argparse.ArgumentTypeError('Size value expected.')

def set_logging(logging_filepath):
    """Setup logger to log to file and stdout."""
    log_format = "%(asctime)s.%(msecs).03d: %(message)s"
    date_format = "%H:%M:%S"
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if os.path.dirname(logging_filepath) != "":
        os.makedirs(os.path.dirname(logging_filepath), exist_ok=True)
    file_handler = logging.FileHandler(logging_filepath)
    file_handler.setFormatter(
        logging.Formatter(
            log_format,
            datefmt=date_format))
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            log_format,
            datefmt=date_format))
    root_logger.addHandler(console_handler)

    logging.info("Writing log file to %s", logging_filepath)

    return root_logger

def check_valid_image(path_img):
    '''
    Check a image files, if the image fails return False ,otherwise True.
    '''
    try:
        img = Image.open(path_img)
        if img:
            return True
        print("file {} error.".format(path_img))
        return False
    except IOError:
        print("file {} error.".format(path_img))
        return False

def get_list_images(path):
    """
    Get a list of image files in a directory.
    return:
        - file_list :list of images
        - dir_list : list of folder
    """

    file_list, dir_list = [], []
    for dir, subdirs, files in os.walk(path):
        file_list.extend([os.path.join(dir, f) for f in files])
        dir_list.extend([os.path.join(dir, d) for d in subdirs])
    file_list = filter(lambda x: not os.path.islink(x), file_list)
    dir_list = filter(lambda x: not os.path.islink(x), dir_list)
    file_list = [i for i in file_list if check_valid_image(i)]
    return list(file_list), list(dir_list)