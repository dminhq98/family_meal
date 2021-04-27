from django.urls import path
from recipe import views
from django.contrib.auth import views as auth_views

# app_name = 'recipe'
urlpatterns = [
   path('', views.HomePageView.as_view(), name='home'),
   path('signin', views.SignInView.as_view(), name='sign_in'),
   path('detail/<int:pk>', views.RecipeDetailView.as_view(), name='recipe'),
   # path('review/<int:pk>/', views.review , name='review'),
   path('search_image', views.SearchImageRecipeView.as_view(), name='search_image'),
   path('search_ingredient', views.SearchIngredientRecipeView.as_view(), name='search_ingredient'),
   path('search_keyword', views.SearchKeywordRecipeView.as_view(), name='search_keyword'),
   path('favore_recipe', views.ListFavoreRecipeView.as_view(), name='favore_recipe'),
   path('share_recipe', views.ListShareRecipeView.as_view(), name='share_recipe'),
   path('shop_list', views.ShopListView.as_view(), name='shop_list'),
   path('add_shoplist/<int:pk>', views.add_shoplist, name='add_shoplist'),
   path('clear_shoplist/<int:pk>', views.clear_shoplist, name='clear_shoplist'),
   path('add', views.AddRecipeView.as_view(), name='add'),
   path('edit/<int:pk>', views.EditRecipeView.as_view(), name='edit'),
   path('login', auth_views.LoginView.as_view(template_name="pages/log_in.html"), name='login'),
   path('logout/',auth_views.LogoutView.as_view(next_page='/'),name='logout'),
]

