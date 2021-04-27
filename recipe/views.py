import json
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import View
from django.http import HttpResponseRedirect
from django.db.models import Avg
from recipe.models import Recipe, Ingredient, Direction, Category, User, Review, ImageRecipe
from recipe.forms import RegistrationForm
from core.ingredient import IngredientList
from recipe.utils import load_search_initialize
from PIL import Image
import io
import requests
from django.core.files.storage import FileSystemStorage
# Create your views here.
DMM_CONF_PATH = "recipe/config/dmm_config.json"
# search_ingredient, searche_image = load_search_initialize(config_img_path=DMM_CONF_PATH)
from recipe.utils import IngredientSearch
search_ingredient = IngredientSearch()
class HomePageView(View):

   def get(self, request):

      new_recipe1 = Recipe.objects.all().order_by('-create_at')[:3]
      new_recipe2 = Recipe.objects.all().order_by('-create_at')[3:6]
      fastest_recipes = Recipe.objects.filter(total__contains='min').order_by('total')[:6]
      fastest_recipe1 = fastest_recipes[:3]
      fastest_recipe2 = fastest_recipes[3:6]
      top_rate = Recipe.objects.order_by('-rate')[:6]
      top_rate1 = top_rate[:3]
      top_rate2 = top_rate[3:6]
      review_recipes = Review.objects.order_by().values_list('recipe', flat=True).distinct()[:6]
      review_recipe1 = [Recipe.objects.get(id=i) for i in review_recipes[:3]]
      review_recipe2 = [Recipe.objects.get(id=i) for i in review_recipes[3:6]]
      category = Category.objects.filter(name__in=['Vegetable', 'Snacks', 'Healthy','Seafood'])[:12]
      data = {'new_recipe1':new_recipe1, 'new_recipe2':new_recipe2, 'fastest_recipe1':fastest_recipe1\
              , 'fastest_recipe2':fastest_recipe2, 'top_rate1':top_rate1, 'top_rate2':top_rate2,'review_recipe1':review_recipe1\
              ,'review_recipe2':review_recipe2, 'category':category}
      return render(request, 'pages/home.html', data)

class SignInView(View):

   def get(self, request):
      form = RegistrationForm()
      return render(request, 'pages/sign_in.html', {'form': form})

   def post(self, request):
      form = RegistrationForm(request.POST)
      if form.is_valid():
         form.save()
         return HttpResponseRedirect('/login')
      return render(request, 'pages/sign_in.html', {'form': form,'err':""})


class RecipeDetailView(View):

   def get(self, request, pk):
      rec = Recipe.objects.get(id=pk)
      servings = rec.servings
      user_ingr = [i.content for i in rec.ingredient.all()]
      ingredients = IngredientList(user_ingr)
      related_recipe = Recipe.objects.filter(category__name__in= [i.name for i in rec.category.all()] ).distinct()[:3]
      response_data = {
         "recipe": rec,
         "related_recipe":related_recipe,
         "ingredients": user_ingr,
         "bad": ingredients.bad,
         "servings": servings,
         "nutrition": ingredients.total_nutrition(servings),
      }
      return render(request, 'pages/recipe_detail.html', response_data)

   def post(self, request, pk):
      # data = request.POST.keys()
      # a = "123"
      # if request.POST['images']:
      #    a = "456"
      # return render(request, 'test.html', {'data':request.POST, 'a':a})
      rec = Recipe.objects.get(id=pk)
      if request.FILES['images']:
         image = request.FILES["images"]
         fs = FileSystemStorage()
         filename = fs.save(image.name, image)
         # uploaded_file_url = fs.url(filename)
         img = ImageRecipe()
         img.recipe = rec
         img.images = filename
         img.save()
      rev = Review()
      rev.recipe = rec
      rev.user = request.user
      rev.content = request.POST['content']
      rev.rate = request.POST['stars']
      rev.images = filename
      rev.save()
      rec.rate = round(rec.recipe_review.all().aggregate(Avg('rate'))['rate__avg'], 1)
      rec.save()

      return HttpResponseRedirect(request.path)

class SearchImageRecipeView(View):

   def post(self, request):
      if "search-file" in request.FILES:
         image = request.FILES["search-file"]
         fs = FileSystemStorage()
         filename = fs.save(image.name, image)
         uploaded_file_url = fs.url(filename)
         img = Image.open(image).convert("RGB")
         top = searche_image.search_topk(img, k=20)
         res = [top[str(i)][0] for i in range(len(top))]
         recipes = [Recipe.objects.get(id=idx) for idx in res]
         return render(request, "pages/search_image.html", {"recipes": recipes, "uploaded_file_url": uploaded_file_url}, )
      elif "search-url" in request.POST and request.POST["search-url"]:
         url = request.POST["search-url"]
         response = requests.get(url)
         if hasattr(response, "content"):
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            top = searche_image.search_topk(img, k=20)
            res = [top[str(i)][0] for i in range(len(top))]
            recipes = [Recipe.objects.get(id=idx) for idx in res]
            return render(request, "pages/search_image.html", {"recipes": recipes, "uploaded_file_url": url}, )
         else:
            return render(request, "pages/search_image.html", {"error": "Invalid url."}, )

      return self.get(request)


class SearchIngredientRecipeView(TemplateView):
   template_name = "pages/search_ingredient.html"

   def post(self, request):

      include_ingredients = request.POST['include_ingredients']
      exclude_ingredients = request.POST['exclude_ingredients']

      rec = search_ingredient.search_topk(include_ingredients, exclude_ingredients, k=20)
      return render(request, 'pages/search_ingredient.html', {'recipes': rec, 'include_ingredients':include_ingredients,'exclude_ingredients':exclude_ingredients})

class ListShareRecipeView(View):

   def get(self, request):
      rec = request.user.user_recipe.all()
      return render(request, 'pages/share_recipe.html', {'recipes': rec})

class ListFavoreRecipeView(View):

   def get(self, request):
      rec = request.user.user_favore.recipe.all()
      return render(request, 'pages/favore_recipe.html', {'recipes': rec})

class ShopListView(View):

   def get(self, request):
      rec = request.user.user_shoplist.recipe.all()
      return render(request, 'pages/shop_list.html', {'recipes': rec})

   def post(self, request):
      request.user.user_shoplist.recipe.all().delete()
      return HttpResponseRedirect(request.path)

class AddRecipeView(TemplateView):
   template_name = "pages/add_recipe.html"

   def post(self, request):
      rec = Recipe()
      rec.name = request.POST['name']
      rec.servings = int(request.POST['servings'])
      rec.prep = request.POST['prep']
      rec.cook = request.POST['cook']
      rec.total = request.POST['total']
      rec.note = request.POST['note']
      rec.description = request.POST['description']
      rec.images = request.POST['image']
      rec.save()

      categorys = request.POST['category']
      for i in categorys:
         cate = Category()
         cate.recipe = rec
         cate.name = i
         cate.save()

      ingredients = request.POST['ingredient']
      for i in ingredients:
         ing = Ingredient()
         ing.recipe = rec
         ing.content = i
         ing.save()

      direction = request.POST['direction']
      for i in direction:
         dire = Direction()
         dire.recipe = rec
         dire.content = i
         dire.save()
      return HttpResponseRedirect('/share_recipe')


class EditRecipeView(TemplateView):
   template_name = "pages/edit_recipe.html"



# from recipe.models import Recipe, Ingredient, Direction, Category
# from django.http import HttpResponseRedirect

