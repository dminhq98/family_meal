import decimal
import json
import os
import string
import random
from core.search import match_one_food
from core.utils import singularize
from recipe.models import Recipe
from search import SimilaritySearch

def id_generator(size=64, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def getIngredientList(ingredient_name_list):
    ingredient_list_id = [match_one_food(singularize(i)) for i in ingredient_name_list]
    ingredient_list_id = [i.id for i in ingredient_list_id if i]
    return ingredient_list_id

def score(recipe_data):
    try:
        if recipe_data['time_req']==0:
            return -decimal.Decimal(2)**decimal.Decimal(1000)
        else:
            score = (decimal.Decimal((len(recipe_data['i_avail']))**decimal.Decimal(30.0/float(recipe_data['time_req']))) - (decimal.Decimal(len(recipe_data['i_needed']))**decimal.Decimal(float(recipe_data['time_req'])/30)))
        return score
    except:
        return -decimal.Decimal(2)**decimal.Decimal(1000)

def sortByScore(output_data):
    return sorted(list(output_data.keys()), key=lambda recipe: score(output_data[recipe]), reverse=True)

def maxScoreRecipeId(output_data):
    return sortByScore(output_data)[0]

class IngredientSearch:

    def __init__(self):
        self.ingredients = []
        self.match_rec = []
        self.time_reqs = []

        recipes = Recipe.objects.filter(status=1)
        for rec in recipes:
            ing = [i.food.id for i in rec.recipe_match.all()]
            self.ingredients.append(ing)
            self.match_rec.append(rec.id)
            self.time_reqs.append(rec.total_min)

    def getRecipes(self, include_ingredient_id, exclude_ingredient_id):
        output_data = {}

        for idx, ing in enumerate(self.ingredients):
            ex_inter = set(exclude_ingredient_id) & set(ing)
            if len(ex_inter) > 0:
                continue
            intersection = set(include_ingredient_id) & set(ing)
            if len(intersection) > 0:
                output_data[self.match_rec[idx]] = {}
                output_data[self.match_rec[idx]]['i_avail'] = intersection
                output_data[self.match_rec[idx]]['i_needed'] = set(include_ingredient_id) - intersection
                output_data[self.match_rec[idx]]['time_req'] = self.time_reqs[idx]
        return output_data

    def search_topk(self, include_ingredients, exclude_ingredients=[], k=10):

        include_ingredient_id = getIngredientList(include_ingredients)
        exclude_ingredient_id = getIngredientList(exclude_ingredients)
        output_data = self.getRecipes(include_ingredient_id, exclude_ingredient_id)
        res = sortByScore(output_data)
        res_detail = [Recipe.objects.get(id=i) for i in res[:k]]

        return res_detail

def load_config_file(config_path):
    json_load = None
    if os.path.isfile(config_path):
        with open(config_path, encoding="utf-8") as f:
            json_load = json.load(f)
    else:
        raise FileExistsError(f"{config_path} is not valid")
    return json_load

def load_search_initialize(config_img_path):
    search_ingredient = IngredientSearch()
    config = load_config_file(config_img_path)
    searche_image = SimilaritySearch(
        path_feature=config['feature'],
        model_name='resnet50_rmac',
        pretrained=False,
        weight=config['weight'],
        size=224,
        cuda_id=-1,
        index_type="annoy",
        length=256,
        distance_type="euclidean",
        path_index=config['index'],
    )

    return search_ingredient, searche_image

def parseTimes(time, unit):
    maxint = 1e7
    if time == 0:
        return None, 0
    if unit == 1:
        if time == 1:
            time_str = "1 min"
        else:
            time_str = str(time) + " mins"
        time_min = float(time)*int(unit)
    elif unit == 60:
        if time == 1:
            time_str = "1 hr"
        else:
            time_str = str(time) + " hrs"
        time_min = float(time) * int(unit)
    else:
        if time == 1:
            time_str = "1 day"
        else:
            time_str = str(time) + " days"
        time_min = float(time) * int(unit)
    time_min = int(time_min)
    if time_min > maxint: time_min = maxint
    return time_str, time_min

def parseStringTimes(time_str):
    if time_str == 0 or not time_str:
        return 0, 1
    if 'day' in time_str:
        time = time_str.split(' ')[0].strip()
        unit = 1440
    elif 'hr' in time_str:
        time = time_str.split(' ')[0].strip()
        unit = 60
    else:
        time = time_str.split(' ')[0].strip()
        unit = 1
    return float(time), unit