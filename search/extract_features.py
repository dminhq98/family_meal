'''
    Extract features module for VIR-lib
'''
import sys
import os
import logging
import pickle
import time
from shutil import copyfile
import numpy as np
import h5py
import torch
from torch import nn
from PIL import Image
from tqdm import tqdm
from search.utils import vntime_now, datetime_format, load_model, \
                            load_transform, ListDataset, make_dir_path
logger = logging.getLogger(__name__)


class FeatureExtraction:
    """
    Extract features from images.

    Parameters
        ----------
        name : str
            name model. ex: resnet50 ....
        pretrained : boolean
            using pretrained or Not
        weight :str
            path weight file for model. (.pt, .pth)
        size: int
            image size before pass model extract feature
        pre_crop: int
            image size resized before CropCenter ,if are none(False, 0), not use cropcenter
        disable_gpu : boolean
            do not use GPU or use GPU
        cuda_id : int
            GPU id is used
        region : str
            The region is parameter has the form xxx-yyy. xxx is type_region, yyy is type merge
            Eg: sos-avgpool. Note: If using type region = sos, you need a config file in the root
            directory to run command.
        pca_path : str
            path to pca file for reduce size feature vector.
    """

    def __init__(
            self,
            model_name,
            pretrained=True,
            weight=None,
            size=224,
            pre_crop=None,
            padding=True,
            disable_gpu=True,
            cuda_id=-1,
    ):

        self.model, self.torch_device = load_model(
            model_name, pretrained, weight, disable_gpu, cuda_id)
        self.image_mode = "pil"

        self.transform = load_transform(
            size=size, pre_crop=pre_crop, padding=padding)

    def extract_features_to_disk(self,
                                 image_paths,
                                 output_hdf5,
                                 batch_size=4,
                                 workers=2,
                                 extract_logger=logger,
                                 global_search=True,
                                 base_path="./data/"
                                 ):
        """
        Extract a specific list of images and save as HDF5 file

        Parameters
        ----------
        image_paths : list
            List image path create or update feature.
        output_hdf5 : str
            Output features as HDF5 to this location.
        batch_size : int
            the number of samples that will be propagated through the network (default: 10).
        workers : int
            number of data loading workers (default: 4).
        extract_logger :logging object
            logging var (ex: logger = set_logging(logging_filepath))
        global_search : boolean
            feature_type is global or not
        base_path: str
            Base path to the dataset
        """
        start = time.time()
        extract_logger.info("Start extract features into file")
        # Data loading code
        based_hdf5 = output_hdf5
        feature_type = "global" if global_search else "instances"
        duplicated_list = []
        inserted_list = []
        update = os.path.isfile(output_hdf5) and output_hdf5.endswith('.h5')
        make_dir_path(output_hdf5)
        if update:
            extract_logger.info("Update process")
            update_time = vntime_now(dt_format=datetime_format)
            # new_features_path = output_hdf5[:-3] + "_" + update_time + ".h5"
            new_features_path = os.path.join(
                os.path.dirname(output_hdf5),
                update_time + "_" + feature_type + ".h5")
            extract_logger.info("{} exists".format(output_hdf5))
            # replace this with proper backup function
            with h5py.File(output_hdf5, "r") as f:
                current_list = list(f["path_images"])
                for idx,i in enumerate(current_list):
                    if not isinstance(i, str):
                        current_list[idx] = i.decode("utf-8")
                set_paths = [p.replace(base_path, '') for p in image_paths]
                # set_shorted_path = set(set_paths)
                set_current_list = set(current_list)
                inserted_list = [
                    p for p in set_paths if p not in set_current_list]
                duplicated_list = [
                    q for q in set_paths if q in set_current_list]                        
                image_paths = [os.path.join(base_path, p) for p in inserted_list]
            if len(inserted_list) == 0:
                info = {}
                info["incremental_update"] = False
                info["status"] = "NO"
                extract_logger.info("Finished. {}".format(info))
                extract_logger.info("No new images to update !")
                return info
            extract_logger.info(
                "Clone into new one {} ".format(new_features_path))
            copyfile(output_hdf5, new_features_path)   
            output_hdf5 = new_features_path
        
        dataset = ListDataset(image_paths,
                              self.transform,
                              )
        extract_logger.info(f"Load data into buffer, processing path format. ")

        features_stacked, paths = get_all_features(dataset, self.model, self.torch_device, batch_size=batch_size, num_workers=workers)
        paths = [_.replace(base_path, '') for _ in paths]
        if sys.version_info >= (3, 0):
            # 2020-06-17 11:40:30
            # h5py should use string_dtype instead of special_dtype
            string_type = h5py.string_dtype(encoding="utf-8")
        else:
            print("\n Python 3.6 is required.")
            raise ValueError("Python 3.6 must be installed")


        info = dict()
        os.makedirs(os.path.dirname(output_hdf5), exist_ok=True)
        print(f"Output feature path: {output_hdf5}")
        # shorted_paths = [img_path.replace(base_path, '') for img_path in paths]
        with h5py.File(output_hdf5, "a") as f:
            if update:
                extract_logger.info("Writing update information into stack")
                num_features = len(current_list)
                print(
                    f"\n Current list len : {len(current_list)}"
                    f"\n Duplicated list len : {len(duplicated_list)}"
                    f"\n Inserted list: len: {len(inserted_list)}\n")
                f["features"].resize(num_features + len(paths), axis=0)
                f["path_images"].resize(
                    num_features + len(paths), axis=0)
                for i, img_path in enumerate(paths):
                    f["features"][i + num_features] = features_stacked[i]
                    f["path_images"][i + num_features] = img_path

            else:
                extract_logger.info("Creating new stack")
                f.create_dataset(name="features",
                                 shape=features_stacked.shape,
                                 maxshape=(None, None),
                                 chunks=True)
                f.create_dataset(name="path_images",
                                 shape=(len(paths),),
                                 maxshape=(None,),
                                 dtype=string_type,
                                 chunks=True)
                for i, image_path in enumerate(paths):
                    f["features"][i] = features_stacked[i]
                    f["path_images"][i] = image_path
            # Summarize features extraction process
            info["based_features"] = based_hdf5
            info["path_features"] = output_hdf5
            info["incremental_update"] = update
            update_time = vntime_now(dt_format=datetime_format)
            info["late_update"] = update_time if update else ""
            info["feature_dim"] = len(features_stacked[0])
            # info["images_list"] = list(f["path_images"])
            # info["duplicated_list"] = duplicated_list
            # info["inserted_list"] = inserted_list
            info["total_items"] = str(len(list(f["path_images"])))
            info["status"] = "OK"
            extract_logger.info("Finished. {}".format(info))
            tm = (time.time() - start) / 60
            extract_logger.info("Total times extract: {} minutes".format(tm))

        return info

    def remove_features_to_disk(self,
                                remove_image_paths,
                                output_hdf5,
                                extract_logger=logger,
                                global_search=True,
                                base_path="./data/"
                                ):
        """
        Remove fearure from HDF5 file

        Parameters
        ----------
        remove_image_paths : list
            List image path to remove feature.
        output_hdf5 : str
            Output features as HDF5 to this location.
        extract_logger :logging object
            logging var (ex: logger = set_logging(logging_filepath))
        global_search : boolean
             feature_type is global or not
        base_path: str
             Base path to the dataset
        """

        extract_logger.info("Start remove features into file")
        start = time.time()
        # Data loading code
        based_hdf5 = output_hdf5
        feature_type = "global" if global_search else "instances"
        extract_logger.info("Remove process")
        update_time = vntime_now(dt_format=datetime_format)

        new_features_path = os.path.join(
            os.path.dirname(output_hdf5),
            update_time + "_" + feature_type + ".h5")
        if os.path.isfile(output_hdf5):
            extract_logger.info("{} exists".format(output_hdf5))

            # replace this with proper backup function
            extract_logger.info(
                "Clone into new one {} ".format(new_features_path))
            copyfile(output_hdf5, new_features_path)
        else:
            # There is not existed h5.
            extract_logger.info("Nothing exists features files")
            print("\nFeatures not exist.")
            raise Exception("Nothing exists features files")

        output_hdf5 = new_features_path

        info = dict()
        os.makedirs(os.path.dirname(output_hdf5), exist_ok=True)
        print(f"Output feature path: {output_hdf5}")
        unduplicated_list = []
        removed_list = []
        shorted_paths = [
            img_path.replace(
                base_path,
                '') for img_path in remove_image_paths]
        with h5py.File(output_hdf5, "a") as f:

            extract_logger.info("Writing remove information into stack")
            current_list = list(f["path_images"])
            features_stacked = f['features'][:]
            num_features = len(current_list)
            set_shorted_path = set(shorted_paths)
            unduplicated_list = [
                p for p in set_shorted_path if p not in current_list]
            removed_list = [q for q in set_shorted_path if q in current_list]
            new_data_list = [[p, q] for p, q in zip(
                current_list, features_stacked) if p not in removed_list]

            print(
                f"\n Current list len : {len(current_list)}"
                f"\n Unduplicated list len : {len(unduplicated_list)}"
                f"\n Removed list: len: {len(removed_list)}\n {removed_list}")
            f["features"].resize(num_features - len(removed_list), axis=0)
            f["path_images"].resize(num_features - len(removed_list), axis=0)
            for i, (image_path, feature) in enumerate(new_data_list):
                f["features"][i] = feature
                f["path_images"][i] = image_path

            # Summarize features extraction process
            info["based_features"] = based_hdf5
            info["path_features"] = output_hdf5
            update_time = vntime_now(dt_format=datetime_format)
            info["late_remove_time"] = update_time
            # info["images_list"] = list(f["path_images"])
            # info["unduplicated_list"] = unduplicated_list
            # info["removed_list"] = removed_list
            info["total_items"] = str(len(list(f["path_images"])))
            info["status"] = "OK"
            extract_logger.info("Finished. {}".format(info))
            tme = (time.time() - start) / 60
            extract_logger.info("Total times remove: {} minutes".format(tme))
        return info

    def extract_image(self, img):
        """
        Extract vector features of an image.

        ::param img : a pil image
        """

        model = self.model.to(self.torch_device)
        image = self.transform(img).unsqueeze(0).to(self.torch_device)
        feature = model(image).data.cpu().numpy().reshape(1, -1)
        return feature.reshape(-1,)


def get_all_features(
        dataset,
        model,
        devide,
        batch_size=32,
        num_workers=8):

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True)
    features = []
    labels = []
    paths = []
    with torch.no_grad():
        for i, (input_data, path) in enumerate(tqdm(loader)):
            input_var = input_data.to(devide, non_blocking=True)
            current_features = model(input_var).data.cpu().numpy()
            for j, image_path in enumerate(path):
                paths.append(image_path)
                features.append(current_features[j].reshape(-1, ))

    features_stacked = np.vstack(features)
    return features_stacked, paths