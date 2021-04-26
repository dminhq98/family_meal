'''
    Similar Search module for Virl-ib
'''
import math
import search.indexs as indexs
from search.indexs import index_type_to_obj
from search import load_features, FeatureExtraction

ALPHA = -20
BETA = 0.8
GAMMA = 0.35
KA = 1


class SimilaritySearch:
    """
    Search and rank image.

    Parameters
    ----------
        model_name: str
            model name
        pretrained: boolean
            using pretrained or Not
        weight: str
            path weight file for model. (.pt, .pth)
        size: int
            image size before pass model extract feature
        pre_crop: int
            image size resized before CropCenter ,if are none(False, 0), not use cropcenter
        disable_gpu: boolean
            not use GPU or use GPU
        cuda_id: int
            GPU id is used
        region : str
            The region is parameter has the form xxx-yyy. xxx is type_region, yyy is type merge
            Eg: sos-avgpool. Note: If using type region = sos, you need a config file in the root
            directory to run command.
        pca_path : str
            path to pca file for reduce size feature vector.
        index_type: str
            the type of index. ex: annoy
        **index_args:
            arguments passed index, depends on the type of index
    """

    def __init__(
            self,
            path_feature,
            model_name,
            pretrained=False,
            weight=None,
            size=224,
            pre_crop=None,
            padding=True,
            cuda_id=-1,
            index_type='annoy',
            **index_args):
        disable_gpu = True if cuda_id == -1 else False
        self.extractor = FeatureExtraction(
            model_name,
            pretrained,
            weight,
            size,
            pre_crop,
            padding,
            disable_gpu,
            cuda_id)
        self.index_type = index_type
        self.index = indexs.__dict__[
            index_type_to_obj[self.index_type]](**index_args)
        _, self.path_images_knn = load_features(path_feature)
        self.distance = index_args['distance_type']

    @staticmethod
    def normalized_score(input_score, distance_type="euclidean"):
        '''
            transform from euclidean to score similar for pretraine model
        '''
        # return input_score
        if distance_type == "euclidean":
            # return 1 - input_score / normalized_factor
            return \
                KA / (1 + math.exp(GAMMA * BETA * (ALPHA + BETA * input_score))) \
                if input_score < 3000 else 0
        return input_score

    @staticmethod
    def dmm_normalized_score(input_score):
        '''
            transform from euclidean to score similar for deep metric model
        '''
        # norm_scorer = 1 / (1 + math.exp(12.5*input_score - 5.6))
        # return norm_scorer
        return 1 - input_score ** 2 / 4

    def search_topk(self, img, k=10, object_type='', use_dmm=True):
        """
        Retrieve the nearest k images.

        Parameters
        ----------
        img : vector
            Vector image search.
        k : int
            The nearest number of images will be returned (default: 10).
        object_type : str
            The object type of img
        use_dmm: bool
            if True then use the function dmm_normalized_score, else use normalized_score
        """
        feature = self.extractor.extract_image(img)
        
        return self.search_topk_feature(feature, k=k, object_type=object_type, use_dmm=use_dmm )
    
    def search_topk_distance(self, img, k=10, object_type=''):
        """
        Retrieve the nearest k images with distnace.

        Parameters
        ----------
        img : vector
            Vector image search.
        k : int
            The nearest number of images will be returned (default: 10).
        object_type : str
            The object type of img
        """
        feature = self.extractor.extract_image(img)
        top = dict()
        vector_k = self.index.get_knn(feature, k)
        if vector_k:
            if object_type:
                for i, idx in enumerate(vector_k[0]):
                    if self.path_images_knn[idx].split(
                            '/')[0].lower() == object_type.lower():
                        top[str(i)] = [
                            self.path_images_knn[idx], vector_k[1][i]]
            else:
                for i, idx in enumerate(vector_k[0]):
                    top[str(i)] = [self.path_images_knn[idx], vector_k[1][i]]

        return top

    def search_topk_feature(self, feature, k=10, object_type='', use_dmm=True):

        top = {}
        vector_k = self.index.get_knn(feature, k)
        if vector_k:
            if object_type:
                for i, idx in enumerate(vector_k[0]):
                    if self.path_images_knn[idx].split(
                            '/')[0].lower() == object_type.lower():
                        if use_dmm:
                            top[str(i)] = [self.path_images_knn[idx],
                                           self.dmm_normalized_score(vector_k[1][i])]
                        else:
                            top[str(i)] = [self.path_images_knn[idx],
                                           self.normalized_score(vector_k[1][i])]
            else:
                for i, idx in enumerate(vector_k[0]):
                    if use_dmm:
                        top[str(i)] = [self.path_images_knn[idx],
                                       self.dmm_normalized_score(vector_k[1][i])]
                    else:
                        top[str(i)] = [self.path_images_knn[idx],
                                       self.normalized_score(vector_k[1][i])]

        return top