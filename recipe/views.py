from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from recipe.models import Recipe, Ingredient, Direction, Category, User, Review
from recipe.forms import RegistrationForm

# Create your views here.


class HomePageView(TemplateView):
   template_name = "pages/home.html"

   def get(self, request):
      recipes = Recipe.objects.all()

      new_recipe1 = Recipe.objects.all().order_by('-create_at')[:3]
      new_recipe2 = Recipe.objects.all().order_by('-create_at')[3:6]
      fastest_recipes = Recipe.objects.filter(total__contains='min').order_by('total')[:6]
      top_recipes = Recipe.objects.order_by('-rate')[:6]
      review_recipes = Recipe.objects.order_by('create_at')[:6]
      data = {'new_recipe1':new_recipe1, 'new_recipe2':new_recipe2, 'fastest_recipes':fastest_recipes\
              , 'top_recipes':top_recipes}
      return render(request,'pages/home.html', data)

class SignInView(TemplateView):
   template_name = "pages/sign_in.html"

   def get(self, request):
      form = RegistrationForm()
      return render(request, 'pages/sign_in.html', {'form': form})

   def post(self, request):
      form = RegistrationForm(request.POST)
      if form.is_valid():
         form.save()
         return HttpResponseRedirect('/')
      return render(request, 'pages/sign_in.html', {'form': form,'err':""})


class RecipeDetailView(TemplateView):
   template_name = "pages/recipe_detail.html"

class SearchImageRecipeView(TemplateView):
   template_name = "pages/search_image.html"

class SearchIngredientRecipeView(TemplateView):
   template_name = "pages/search_ingredient.html"

class ListShareRecipeView(TemplateView):
   template_name = "pages/share_recipe.html"

class ListFavoreRecipeView(TemplateView):
   template_name = "pages/favore_recipe.html"

class ShopListView(TemplateView):
   template_name = "pages/shop_list.html"

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
# def add_recipe(request):
#    if request.method == 'POST':
#
#       return HttpResponseRedirect('/')
#    return render(request, 'pages/add.html')