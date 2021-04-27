'''
    Script for extract feature and indexing
'''
import argparse
import os
import sys
import search.indexs as indexs
from search import FeatureExtraction
from search.utils import vntime_now, datetime_format, str2size, get_list_images, set_logging, load_csv_images

sys.path.append(".")
PATH_LOG = "extracter.log"
def extract_data(
        path_data,
        path_save,
        path_log,
        model_name,
        weight,
        size,
        pre_crop,
        padding,
        batch_size,
        num_workers,
        cuda_id,
        global_search,
        n_trees,):

    base_data = ''
    disable_gpu = True if cuda_id == -1 else False
    pretrained = False if weight else True
    extracter = FeatureExtraction(
        model_name=model_name,
        pretrained=pretrained,
        weight=weight,
        size=size,
        pre_crop=pre_crop,
        padding=padding,
        disable_gpu=disable_gpu,
        cuda_id=cuda_id)
    img_list, _ = load_csv_images(path_data)
    print("num valid path", len(img_list))
    extract_logger = set_logging(path_log)
    # extract_logger.info(args)
    update_time = vntime_now(dt_format=datetime_format)
    print(global_search)
    feature_type = "global" if global_search else "instances"
    if os.path.isfile(path_save) and path_save.endswith('.h5'):
        new_features_path = path_save
    else:
        new_features_path = os.path.join(
            path_save, update_time + "_" + feature_type + ".h5")
    returned_extract_info = extracter.extract_features_to_disk(
        img_list,
        new_features_path,
        extract_logger=extract_logger,
        batch_size=batch_size,
        workers=num_workers,
        base_path=base_data,
        global_search=global_search)
    if returned_extract_info["status"] == "OK":
        new_features_path = returned_extract_info["path_features"]
        new_indexs_path = new_features_path[:-2] + 'ann'
        _ = indexs.annoy.make_index(
            new_features_path, new_indexs_path, 'euclidean', n_trees)


def main():
    '''
        get parameters and run script
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--path_data',
        type=str,
        required=True,
        default='data/images.csv',
        help='path to csv file which to extract \
                the data')
    parser.add_argument(
        '--path_save',
        type=str,
        default='data/search',
        help='path to the directory where the extract \
            data is stored or path to the h5 file to update')
    parser.add_argument(
        '--model_name',
        type=str,
        default='resnet50',
        help='The model name you want to use to extract the data')
    parser.add_argument(
        '--weight',
        type=str,
        default=None,
        help='path to file weight for model, otherwise use pretrained')
    parser.add_argument(
        '--size',
        type=str2size,
        default='224',
        help='image size before pass model extract feature . format : s or s1,s2')
    parser.add_argument(
        '--pre_crop',
        type=str2size,
        default=None,
        help='image size resized before CropCenter ,\
            if are none (False, 0), not use cropcenter. format : s or s1,s2')
    parser.add_argument(
        '--no_padding',
        action='store_true',
        help='No padding image before resize')
    parser.add_argument(
        '--batch_size',
        type=int,
        default=64,
        help='number of image in a batch')
    parser.add_argument(
        '--threads',
        type=int,
        default=8,
        help='number of thread workers')
    parser.add_argument(
        '--cuda_id',
        type=int,
        default=-1,
        help='GPU id you want use, equal -1 if use CPU')
    parser.add_argument(
        '--n_trees',
        type=int,
        default=100,
        help='Nums tree on annoy build')
    parser.add_argument(
        '--global_search',
        action='store_true',
        help='feature_type = "global" if global_search is True else "instances"')
    args = parser.parse_args()
    print(args)
    padding = not args.no_padding

    extract_data(
        args.path_data,
        args.path_save,
        PATH_LOG,
        args.model_name,
        args.weight,
        args.size,
        args.pre_crop,
        padding,
        args.batch_size,
        args.threads,
        args.cuda_id,
        args.global_search,
        args.n_trees)


if __name__ == "__main__":
    main()
