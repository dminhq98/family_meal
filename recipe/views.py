import json
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views import View
from django.http import HttpResponseRedirect
from django.db.models import Avg
from recipe.models import Recipe, Ingredient, Direction, Category, User, Review, ImageRecipe, ShopList, Favore
from recipe.forms import RegistrationForm
from core.ingredient import IngredientList
from recipe.utils import load_search_initialize, parseTimes, id_generator, parseStringTimes
from PIL import Image
import io
import requests
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
# Create your views here.
DMM_CONF_PATH = "recipe/config/dmm_config.json"
# search_ingredient, searche_image = load_search_initialize(config_img_path=DMM_CONF_PATH)
# from recipe.utils import IngredientSearch
# search_ingredient = IngredientSearch()

class HomePageView(View):

   def get(self, request):

      if request.user.is_authenticated:
         if request.user.level == 0 or request.user.level == 1:
            data = {
               "num_recipe":Recipe.objects.count(),
               "num_user": User.objects.count(),
               "num_review": Review.objects.count(),
               "num_favore": Favore.objects.count(),
            }
            return render(request, 'admin/home.html', data)

      new_recipe1 = Recipe.objects.filter(status=1).order_by('-create_at')[:3]
      new_recipe2 = Recipe.objects.filter(status=1).order_by('-create_at')[3:6]
      fastest_recipes = Recipe.objects.filter(total__contains='min', status=1).order_by('total')[:6]
      fastest_recipe1 = fastest_recipes[:3]
      fastest_recipe2 = fastest_recipes[3:6]
      top_rate = Recipe.objects.order_by('-rate')[:6]
      top_rate1 = top_rate[:3]
      top_rate2 = top_rate[3:6]
      review_recipes = Review.objects.order_by().values_list('recipe', flat=True).distinct()[:6]
      review_recipe1 = [Recipe.objects.get(id=i) for i in review_recipes[:3]]
      review_recipe2 = [Recipe.objects.get(id=i) for i in review_recipes[3:6]]
      category = []
      cate = Category.objects.filter(name='Vegetable')[:4]
      category.extend(list(cate))
      cate = Category.objects.filter(name='Snacks')[:4]
      category.extend(list(cate))
      cate = Category.objects.filter(name='Healthy')[:4]
      category.extend(list(cate))
      cate = Category.objects.filter(name='Seafood')[:4]
      category.extend(list(cate))
      category = set(category)
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
      related_recipe = Recipe.objects.filter(category__name__in= [i.name for i in rec.category.all()], status=1).distinct()[:3]
      categorys = [i.name for i in rec.category.all()]
      categorys = ','.join(categorys)
      response_data = {
         "recipe": rec,
         "related_recipe": related_recipe,
         "ingredients": user_ingr,
         "bad": ingredients.bad,
         "servings": servings,
         "nutrition": ingredients.total_nutrition(servings),
         "categorys":categorys
      }
      if request.user.is_authenticated:
         fav = Favore.objects.filter(user=request.user, recipe=Recipe.objects.get(id=pk), status=1)
         if len(fav):
            response_data['favore'] = True
      return render(request, 'pages/recipe_detail.html', response_data)

   def post(self, request, pk):
      # data = request.POST.keys()
      # a = "123"
      # if request.POST['images']:
      #    a = "456"
      # return render(request, 'test.html', {'data':request.POST, 'a':a})
      rec = Recipe.objects.get(id=pk)
      rev = Review()
      rev.recipe = rec
      rev.user = request.user
      rev.content = request.POST['content']
      rev.rate = request.POST['stars']
      is_imasge = request.FILES.get('images', False)
      if is_imasge:
         image = request.FILES["images"]
         fs = FileSystemStorage()
         filename = fs.save(image.name, image)
         # uploaded_file_url = fs.url(filename)
         img = ImageRecipe()
         img.recipe = rec
         img.images = filename
         img.save()
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
         top = searche_image.search_topk(img, k=30)
         res = [top[str(i)][0] for i in range(len(top))]
         recipes = []
         for i in res:
            try:
               img_rec = ImageRecipe.objects.get(images=i)
               if img_rec.recipe not in recipes and img_rec.recipe.status == 1:
                  recipes.append(img_rec.recipe)
            except:
               pass
         # recipes = [Recipe.objects.get(id=idx) for idx in recipes]
         return render(request, "pages/search_image.html", {"recipes": recipes, "uploaded_file_url": uploaded_file_url}, )
      elif "search-url" in request.POST and request.POST["search-url"]:
         url = request.POST["search-url"]
         response = requests.get(url)
         if hasattr(response, "content"):
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            top = searche_image.search_topk(img, k=20)
            res = [top[str(i)][0] for i in range(len(top))]
            recipes = []
            for i in res:
               try:
                  img_rec = ImageRecipe.objects.get(images=i)
                  if img_rec.recipe not in recipes and img_rec.recipe.status == 1:
                     recipes.append(img_rec.recipe)
               except:
                  pass
            # recipes = [Recipe.objects.get(id=idx) for idx in recipes]
            return render(request, "pages/search_image.html", {"recipes": recipes, "uploaded_file_url": url}, )
         else:
            return render(request, "pages/search_image.html", {"error": "Invalid url."}, )

      return self.get(request)

class SearchIngredientRecipeView(View):
   template_name = "pages/search_ingredient.html"

   def post(self, request):

      include_ingredients = request.POST['include_ingredients']
      exclude_ingredients = request.POST['exclude_ingredients']
      include_ingredients = include_ingredients.split(',')
      exclude_ingredients = exclude_ingredients.split(',')
      rec = search_ingredient.search_topk(include_ingredients, exclude_ingredients, k=12)

      return render(request, 'pages/search_ingredient.html', {'recipes': rec, 'include_ingredients':include_ingredients,\
                  'exclude_ingredients':exclude_ingredients})

class SearchKeywordRecipeView(TemplateView):
   template_name = "pages/search_keyword.html"

   def post(self, request):

      key_word = request.POST['key_word']

      rec = Recipe.objects.filter(status=1).filter(Q(name__contains=key_word) | Q(description__contains=key_word))[:12]

      return render(request, 'pages/search_keyword.html',{'recipes': rec, 'key_word': key_word})

class ListShareRecipeView(View):

   def get(self, request):

      if request.user.is_authenticated:
         rec = request.user.user_recipe.all()
         paginator = Paginator(rec, 10)

         pageNumber = request.GET.get('page')
         try:
            rec = paginator.page(pageNumber)
         except PageNotAnInteger:
            rec = paginator.page(1)
         except EmptyPage:
            rec = paginator.page(paginator.num_pages)
         return render(request, 'pages/share_recipe.html', {'recipes': rec})
      else:
         return HttpResponseRedirect('/login')

   def post(self, request):
      pk = request.POST['pk']
      Recipe.objects.filter(id=pk).delete()
      return HttpResponseRedirect(request.path)

class ListFavoreRecipeView(View):

   def get(self, request):
      if request.user.is_authenticated:
         rec = request.user.user_favore.all()
         rec = [i.recipe for i in rec]
         return render(request, 'pages/favore_recipe.html', {'recipes': rec})
      else:
         return HttpResponseRedirect('/login')

class ShopListView(View):

   def get(self, request):
      if request.user.is_authenticated:
         ingredients = request.user.user_shoplist.all()
         # ingredients = [i.ingredient for i in ingredients]
         return render(request, 'pages/shop_list.html', {'ingredients': ingredients})
      else:
         return HttpResponseRedirect('/login')


   def post(self, request):
      request.user.user_shoplist.all().delete()
      return HttpResponseRedirect(request.path)

def clear_shoplist(request, pk):
   ShopList.objects.filter(id=pk).delete()
   return HttpResponseRedirect('/shop_list')

def add_shoplist(request, pk):
   data = dict(request.POST)
   data.pop('csrfmiddlewaretoken', None)
   data = list(data.keys())
   data = [int(i) for i in data]
   # return render(request, 'test.html', {'data': data, 'a': request.user.is_authenticated})
   if request.user.is_authenticated:
      for i in data:
         shp = ShopList()
         shp.recipe = Recipe.objects.get(id=pk)
         shp.user = request.user
         shp.content = Ingredient.objects.get(id=i).content
         shp.save()
      return HttpResponseRedirect('/shop_list')
   else:
      return HttpResponseRedirect('/login')

def add_favore(request, pk):
   if request.user.is_authenticated:
      fav = Favore.objects.filter(user=request.user, recipe=Recipe.objects.get(id=pk))
      if len(fav):
         fav.delete()
      else:
         favore = Favore()
         favore.recipe = Recipe.objects.get(id=pk)
         favore.user = request.user
         favore.save()
      return HttpResponseRedirect(f'/detail/{pk}')
   else:
      return HttpResponseRedirect('/login')

class AddRecipeView(View):

   def get(self, request):
      if request.user.is_authenticated:
         return render(request, 'pages/add_recipe.html')
      else:
         return HttpResponseRedirect('/login')

   def post(self, request):
      rec = Recipe()
      rec.name = request.POST['name']
      if request.POST['note']:
         rec.note = request.POST['note']
      rec.description = request.POST['description']
      rec.servings = int(request.POST['servings'])
      prep, prep_min = parseTimes(request.POST['prep'], request.POST['prepTimeUnit'])
      cook, cook_min = parseTimes(request.POST['cook'], request.POST['cookTimeUnit'])
      rec.prep = prep
      rec.cook = cook
      rec.total_min = prep_min + cook_min
      image = request.FILES["image-file"]
      fs = FileSystemStorage()
      name = id_generator() + image.name
      filename = fs.save(name, image)
      rec.images = filename
      rec.rate = 0
      rec.user = request.user
      rec.save()

      img = ImageRecipe()
      img.recipe = rec
      img.images = filename
      img.save()

      categorys = request.POST['category']
      categorys = categorys.split(',')
      for i in categorys:
         if i.strip() == '':
            continue
         cate = Category()
         cate.recipe = rec
         cate.name = i.strip()
         cate.save()

      ingredients = request.POST['ingredient']
      ingredients = ingredients.split('\n')
      for i in ingredients:
         if i.strip() == '':
            continue
         ing = Ingredient()
         ing.recipe = rec
         ing.content = i.strip()
         ing.save()

      direction = request.POST['direction']
      direction = direction.split('\n')
      for i in direction:
         if i.strip() == '':
            continue
         dire = Direction()
         dire.recipe = rec
         dire.content = i.strip()
         dire.save()
      return HttpResponseRedirect('/share_recipe')

class EditRecipeView(View):

   def get(self, request, pk):
      if request.user.is_authenticated:
         rec = Recipe.objects.get(id=pk)
         ingredients = [i.content for i in rec.ingredient.all()]
         ingredients = '\n'.join(ingredients)
         directions = [i.content for i in rec.direction.all()]
         directions = '\n'.join(directions)
         categorys = [i.name for i in rec.category.all()]
         categorys = ','.join(categorys)
         prep, prep_unit = parseStringTimes(rec.prep)
         cook, cook_unit = parseStringTimes(rec.cook)
         return render(request, 'pages/edit_recipe.html', {'recipe': rec, 'ingredients':ingredients, 'directions':directions,\
                           'categorys':categorys,'prep':prep, 'prep_unit':prep_unit,'cook':cook,'cook_unit':cook_unit})
      else:
         return HttpResponseRedirect('/login')

   def post(self, request, pk):
      rec = Recipe.objects.get(id=pk)
      rec.name = request.POST['name']
      if request.POST['note']:
         rec.note = request.POST['note']
      rec.description = request.POST['description']
      rec.servings = int(request.POST['servings'])
      prep, prep_min = parseTimes(request.POST['prep'], request.POST['prepTimeUnit'])
      cook, cook_min = parseTimes(request.POST['cook'], request.POST['cookTimeUnit'])
      rec.prep = prep
      rec.cook = cook
      rec.total_min = prep_min + cook_min
      if "search-file" in request.FILES and request.FILES["image-file"]:
         image = request.FILES["image-file"]
         fs = FileSystemStorage()
         name = id_generator() + image.name
         filename = fs.save(name, image)
         rec.images = filename
         img = ImageRecipe()
         img.recipe = rec
         img.images = filename
         img.save()
      rec.rate = 0
      rec.user = request.user
      rec.save()

      rec.category.all().delete()
      categorys = request.POST['category']
      categorys = categorys.split(',')
      for i in categorys:
         if i.strip() == '':
            continue
         cate = Category()
         cate.recipe = rec
         cate.name = i.strip()
         cate.save()

      rec.ingredient.all().delete()
      ingredients = request.POST['ingredient']
      ingredients = ingredients.split('\n')
      for i in ingredients:
         if i.strip() == '':
            continue
         ing = Ingredient()
         ing.recipe = rec
         ing.content = i.strip()
         ing.save()

      rec.direction.all().delete()
      direction = request.POST['direction']
      direction = direction.split('\n')
      for i in direction:
         if i.strip() == '':
            continue
         dire = Direction()
         dire.recipe = rec
         dire.content = i.strip()
         dire.save()
      return HttpResponseRedirect('/share_recipe')

class ManageRecipeView(View):

   def get(self, request):
      recipes = Recipe.objects.all().order_by('-create_at')
      paginator = Paginator(recipes, 10)

      pageNumber = request.GET.get('page')
      try:
         recipes = paginator.page(pageNumber)
      except PageNotAnInteger:
         recipes = paginator.page(1)
      except EmptyPage:
         recipes = paginator.page(paginator.num_pages)

      return render(request, 'admin/manage_recipe.html', {'recipes': recipes})

   def post(self, request):
      pk = request.POST['pk']
      rec = Recipe.objects.get(id=pk)
      if rec.status == 0:
         rec.status = 1
         rec.save()
         if Recipe.objects.filter(status=0, user=rec.user).count() < 2:
            user = User.objects.get(id=rec.user.id)
            user.status = 1
            user.is_active = 1
            user.save()
         return HttpResponseRedirect('/recipe_active')
      else:
         rec.status = 0
         rec.save()
         if Recipe.objects.filter(status=0, user=rec.user).count() > 1:
            user = User.objects.get(id=rec.user.id)
            user.status = 0
            user.is_active = 0
            user.save()
         return HttpResponseRedirect('/recipe_disable')
      # return HttpResponseRedirect(request.path)

class ManageRecipeActiveView(View):

   def get(self, request):
      recipes = Recipe.objects.order_by('-create_at').filter(status=1)
      paginator = Paginator(recipes, 10)

      pageNumber = request.GET.get('page')
      try:
         recipes = paginator.page(pageNumber)
      except PageNotAnInteger:
         recipes = paginator.page(1)
      except EmptyPage:
         recipes = paginator.page(paginator.num_pages)

      return render(request, 'admin/manage_recipe.html', {'recipes': recipes})

class ManageDisableActiveView(View):

   def get(self, request):
      recipes = Recipe.objects.order_by('-create_at').filter(status=0)
      paginator = Paginator(recipes, 10)

      pageNumber = request.GET.get('page')
      try:
         recipes = paginator.page(pageNumber)
      except PageNotAnInteger:
         recipes = paginator.page(1)
      except EmptyPage:
         recipes = paginator.page(paginator.num_pages)

      return render(request, 'admin/manage_recipe.html', {'recipes': recipes})

class ManageUserView(View):

   def get(self, request):
      users = User.objects.all().order_by('-date_joined')
      paginator = Paginator(users, 10)

      pageNumber = request.GET.get('page')
      try:
         users = paginator.page(pageNumber)
      except PageNotAnInteger:
         users = paginator.page(1)
      except EmptyPage:
         users = paginator.page(paginator.num_pages)
      return render(request, 'admin/manage_user.html', {'users': users})

   def post(self, request):
      pk = request.POST['pk']
      user = User.objects.get(id=pk)
      if user.status == 0:
         user.status = 1
         user.is_active = 1
      else:
         user.status = 0
         user.is_active = 0
      user.save()
      return HttpResponseRedirect(request.path)

class ManageUserActiveView(View):

   def get(self, request):
      users = User.objects.all().order_by('-date_joined').filter(status=1)
      paginator = Paginator(users, 10)

      pageNumber = request.GET.get('page')
      try:
         users = paginator.page(pageNumber)
      except PageNotAnInteger:
         users = paginator.page(1)
      except EmptyPage:
         users = paginator.page(paginator.num_pages)
      return render(request, 'admin/manage_user.html', {'users': users})

class ManageUserDisableView(View):

   def get(self, request):
      users = User.objects.all().order_by('-date_joined').filter(status=0)
      paginator = Paginator(users, 10)

      pageNumber = request.GET.get('page')
      try:
         users = paginator.page(pageNumber)
      except PageNotAnInteger:
         users = paginator.page(1)
      except EmptyPage:
         users = paginator.page(paginator.num_pages)
      return render(request, 'admin/manage_user.html', {'users': users})

class ProfileView(View):

   def get(self, request):
      if request.user.level ==2:
         return render(request, 'pages/profile.html')
      return render(request, 'admin/profile.html')

   def post(self, request):
      user = request.user
      user.name = request.POST['name']
      user.email = request.POST['email']
      user.address = request.POST['address']
      user.birthday = request.POST['birthday']
      user.description = request.POST['description']
      user.save()
      return HttpResponseRedirect(request.path)

from django.contrib.auth.decorators import login_required


class PasswordView(View):

   def get(self, request):
      form = PasswordChangeForm(request.user)
      return render(request, 'admin/change_password.html', {
         'form': form
      })

   def post(self, request):
      form = PasswordChangeForm(request.user, request.POST)
      if form.is_valid():
         user = form.save()
         update_session_auth_hash(request, user)  # Important!
         messages.success(request, 'Your password was successfully updated!')
         return HttpResponseRedirect(request.path)
      else:
         messages.error(request, 'Please correct the error below.')

def change_password(request):
   if request.method == 'POST':
      form = PasswordChangeForm(request.user, request.POST)
      if form.is_valid():
         user = form.save()
         update_session_auth_hash(request, user)  # Important!
         messages.success(request, 'Your password was successfully updated!')
         return redirect('/change_password')
      else:
         messages.error(request, 'Please correct the error below.')
   else:
      form = PasswordChangeForm(request.user)
      return render(request, 'pages/change_password.html', {
         'form': form
      })