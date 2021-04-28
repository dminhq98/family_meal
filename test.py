import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_meal.settings')
application = get_wsgi_application()
from recipe.utils import IngredientSearch
from search import SimilaritySearch
seach_ing = IngredientSearch()

res = seach_ing.search_topk(['eggs'])
# print(res)

# search_img = SimilaritySearch()

from recipe.models import Review, Favore
from PIL import Image
# review_recipes = Review.objects.values_list('recipe', flat=True).distinct()
# print(review_recipes)
from recipe.utils import load_search_initialize
from recipe.models import Recipe, ImageRecipe, User
DMM_CONF_PATH = "recipe/config/dmm_config.json"
# search_ingredient, searche_image = load_search_initialize(config_img_path=DMM_CONF_PATH)
# path = "test/image.jpeg"
# img = Image.open(path).convert("RGB")
# top = searche_image.search_topk(img, k=20)
# res = [top[str(i)][0] for i in range(len(top))]
# print(res)
# recipes = []
# for i in res:
#    try:
#       img_rec = ImageRecipe.objects.get(images=i)
#       if img_rec.recipe not in recipes:
#          recipes.append(img_rec.recipe)
#    except:
#       pass
# print(recipes)

fav = Favore.objects.filter(user=User.objects.get(id=3), recipe=Recipe.objects.get(id=16))
print(fav)
print(len(fav))
if len(fav):
   fav.delete()
else:
   print(1)
