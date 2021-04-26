from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import Food
# Create your models here.

class User(AbstractUser):

    # username = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    # password = models.CharField(max_length=500)
    birthday = models.DateTimeField(null=True, blank=True)
    address = models.TextField()
    level = models.IntegerField()
    status = models.IntegerField(default=1)
    # create_at = models.DateTimeField(auto_now_add=True)
    REQUIRED_FIELDS = []
    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.username}"

class Recipe(models.Model):

    name = models.CharField(max_length=100)
    servings = models.IntegerField()
    prep = models.CharField(max_length=50, null=True)
    cook = models.CharField(max_length=50, null=True)
    total = models.CharField(max_length=50, null=True)
    total_min = models.IntegerField()
    note = models.CharField(max_length=200, null=True, blank=True)
    rate = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    description = models.TextField(null=True)
    images = models.ImageField(null=True, upload_to='images')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_recipe')
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.name}"


class Review(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_review')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_review')
    content = models.TextField()
    images = models.ImageField(null=True, upload_to='reviews')
    rate = models.IntegerField()
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-create_at',)
    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.content}"

class Category(models.Model):

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='category')
    name = models.CharField(max_length=100)

    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.name}"


class Ingredient(models.Model):

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredient')
    content = models.TextField()

    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.content}"

class Direction(models.Model):

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='direction')
    content = models.TextField()

    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.content}"

class Favore(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_favore')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_favore')
    status = models.IntegerField(default=1)
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.user} {self.recipe}"

class ShopList(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_shoplist')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_shoplist')
    status = models.IntegerField(default=1)
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: no cover
        return f"#{self.id} {self.user}"

class MatchFood(models.Model):

    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="food_match")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_match')
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: no cover
        return f"{self.food} and {self.recipe}"


class Nutrition(models.Model):

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='nutrition')
    energy = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    carbs = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    sat_fat = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    polyunsat_fat = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    monounsat_fat = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    sugar = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    chole = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    sodium = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    potas = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    fiber = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: no cover
        return f"{self.recipe}"