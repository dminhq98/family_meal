import os
import requests
import json
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_meal.settings')

application = get_wsgi_application()
from recipe.models import Recipe, Category, Ingredient, Direction, User, Review, Nutrition, MatchFood, ImageRecipe, Favore
from core.models import Food

from core.ingredient import IngredientList
from search.utils import get_list_images

def add():
    user = User()
    user.username = 'root'
    user.name = 'Root'
    user.address = 'Root system'
    user.birthday = '2021-05-01'
    user.set_password('root@123')
    user.level = 0
    user.save()

    user = User()
    user.username = 'admin'
    user.name = 'Duong Minh Quang'
    user.address = 'HUST'
    user.birthday = '1998-05-13'
    user.set_password('123456')
    user.level = 1
    user.save()

    user = User()
    user.username = 'dminhq98'
    user.name = 'Duong Minh Quang'
    user.address = 'HUST'
    user.birthday = '1998-05-13'
    user.set_password('123456')
    user.level = 2
    user.save()
    global user_id
    user_id = user.id
add()

def parseTimes(time_str):
    maxint = 1e7
    hour = 0
    minues = 0
    if time_str == 0:
        return 0
    if 'hr' in  time_str:
        hour = int(time_str.split(' ')[0].strip())
        if 'min' in time_str:
            minues = int(time_str.split(' ')[2].strip())
    else:
        minues = int(time_str.split(' ')[0].strip())
    total = hour*60 + minues
    if total > maxint: total =maxint
    return total

def add_recipe():
    with open("recipe_final.json", 'r') as f:
        data = json.load(f)

    user = User.objects.get(id=user_id)
    for idx, dt in enumerate(data):
        path_imgs, _ = get_list_images(os.path.join('images',dt['id']))
        # print(len(path_imgs))
        print(dt['name'])
        rec = Recipe()
        rec.name = dt['name']
        rec.user = user
        rec.servings = int(dt['servings'])
        rec.prep = dt['prep']
        # rec.cook = request.POST['cook']
        rec.total = dt['total']
        rec.total_min = parseTimes(dt['total'])
        rec.note = dt['notes']
        rec.rate = 0
        rec.description = dt['description']
        filename = os.path.join('images', dt['images'].split('%')[-1])
        rec.images = filename
        rec.save()

        for i in path_imgs:
            img = ImageRecipe()
            img.recipe = rec
            img.images = i.replace('images/','')
            img.save()

        categorys = dt['category']
        for i in categorys:
            cate = Category()
            cate.recipe = rec
            cate.name = i
            cate.save()

        ingredients = dt['ingredients']
        for i in ingredients:
            ing = Ingredient()
            ing.recipe = rec
            ing.content = i
            ing.save()

        ing_food = IngredientList(dt['ingredients'])
        for i in ing_food.all:
            math_food = MatchFood()
            math_food.recipe = rec
            math_food.food = Food.objects.get(id=i.matched_food.id)
            math_food.save()

        direction = dt['directions']
        for i in direction:
            dire = Direction()
            dire.recipe = rec
            dire.content = i
            dire.save()
        # if idx == 100: break
add_recipe()
import random
from django.db.models import Avg
def add_coment():
    for i in range(50):
        idx = random.randint(1, 50)
        print(idx)
        rev = Review()
        rec = Recipe.objects.get(id=idx)
        rev.recipe = rec
        rev.user = User.objects.get(id=user_id)
        rev.rate = random.randint(3, 5)
        rev.content = "Very good !"
        rev.save()
        rec.rate = round(rec.recipe_review.all().aggregate(Avg('rate'))['rate__avg'], 1)
        rec.save()

add_coment()

def add_favore():
    for i in range(5):
        idx = random.randint(1, 50)
        fav = Favore()
        rec = Recipe.objects.get(id=idx)
        fav.recipe = rec
        fav.user = User.objects.get(id=user_id)
        fav.save()
add_favore()
# make_csv()
# rec = Recipe.objects.get(id=1)
# print(rec.ingredient)
# print(rec.images.url)

# user = User.objects.get(id=1)
# print(user)
# recipes = Recipe.objects.all().order_by('-create_at')[:6]
# print(recipes[0].ingredient.all())

# from recipe.models import Review

# review_recipes = Review.objects.values_list('recipe', flat=True).distinct()
# print(review_recipes)

# vegetable = Recipe.objects.category.filter(name='Vegetable')[:6]
# print(vegetable)