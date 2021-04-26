'''
    Annoy Indexing module
'''
from annoy import AnnoyIndex
from search import load_features, vntime_now, datetime_format


class AnnoyIndexing:
    """
        Index features by AnnoyIndex.
        Parameters
        ----------
        path_index : list
            path to index files. (.ann)
        distance_type : str
            distance type for index, ex: euclidean ...
        length :int
            length feature vector

        """

    def __init__(self, **kwargs):
        self.length = kwargs.pop('length', False)
        if not self.length:
            raise Exception("AnnoyIndexing() missing 1 required positional argument: length")
        self.distance_type = kwargs.pop('distance_type', False)
        if not self.distance_type:
            raise Exception("AnnoyIndexing() missing 1 required positional argument: distance_type")
        self.path_index = kwargs.pop('path_index', False)
        if not self.path_index:
            raise Exception("AnnoyIndexing() missing 1 required positional argument: path_index")
        self.index = AnnoyIndex(self.length, self.distance_type)
        self.index.load(self.path_index)

    def get_knn(self, feature, k):
        '''
            Get k results from index
        '''
        vector_k = self.index.get_nns_by_vector(feature, k, include_distances=True)
        return vector_k

def make_index(path_feature, path_index, distance_type, n_trees=10):
    """
        Build index from feature file.

        Parameters
        ----------
        path_feature : str
            path to feature files. (.h5)
        path_index : str
            path to index files. (.ann)
        distance_type :str
            distance type for index, ex: euclidean ...

        """

    features, _ = load_features(path_feature)
    length = len(features[0])
    # Length of item vector that will be indexed
    index = AnnoyIndex(length, distance_type)
    for idx, vector in enumerate(features):
        index.add_item(idx, vector)

    index.build(n_trees)  # 10 trees
    index.save(path_index)
    print("Maked index in {}".format(path_index))

    info = dict()
    info["path_index"] = path_index
    info["path_features"] = path_feature
    update_time = vntime_now(dt_format=datetime_format)
    info["index_update"] = update_time

    return info
