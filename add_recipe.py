import os
import requests
import json

def add():
    API_URL = "http://127.0.0.1:8000/add"

    with open("recipe_final.json", 'r') as f:
        recipes = json.load(f)


    for rec in recipes:
        filename = os.path.join('images', rec['images'].split('%')[-1])
        print(filename)
        data = {}
        data['name'] = rec['name']
        data['prep'] = rec['prep']
        data['total'] = rec['total']
        data['servings'] = int(rec['servings'])
        data['note'] = rec['notes']
        data['category'] = rec['category']
        data['ingredients'] = rec['ingredients']
        data['directions'] = rec['directions']
        data = json.dumps(data)
        print(data)
        files = {"media": open(filename, "rb")}
        files = {'image': (filename, open(filename, "rb"), 'multipart/form-data', {'Expires': '0'})}
        print(files)
        response = requests.post(API_URL, files=files, data=data)
        print(response.status_code)
        # print(response.content)
        break

import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_meal.settings')

application = get_wsgi_application()
from recipe.models import Recipe, Category, Ingredient, Direction, User
def add_recipe():
    with open("recipe_final.json", 'r') as f:
        data = json.load(f)

    user = User.objects.get(id=1)
    for dt in data:
        rec = Recipe()
        rec.name = dt['name']
        rec.user = user
        rec.servings = int(dt['servings'])
        rec.prep = dt['prep']
        # rec.cook = request.POST['cook']
        rec.total = dt['total']
        rec.note = dt['notes']
        rec.rate = 0
        rec.description = dt['description']
        filename = os.path.join('images', dt['images'].split('%')[-1])
        rec.images = filename
        rec.save()

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

        direction = dt['directions']
        for i in direction:
            dire = Direction()
            dire.recipe = rec
            dire.content = i
            dire.save()
        print(dt['name'])
# add_recipe()

# rec = Recipe.objects.get(id=1)
# print(rec)
# print(rec.images.url)

# user = User.objects.get(id=1)
# print(user)
recipes = Recipe.objects.all().order_by('-create_at')[:6]
print(recipes[0].recipe_review.count())