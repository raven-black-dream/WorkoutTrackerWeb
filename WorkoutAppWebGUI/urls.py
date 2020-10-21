from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='WorkoutAppWebGUI/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='WorkoutAppWebGUI/logout.html'), name='logout'),
    path('landing', views.landing, name="landing"),
    path('user/<int:pk>', views.UserView.as_view(), name="profile"),
    path('user/edit', views.edit_user, name="user_edit"),
    path('user/<int:pk>/program', views.ProgramView.as_view(), name="view_program"),
    path('workout/<int:pk>', views.WorkoutView.as_view(), name="view_workout"),
    path('contact', views.contact, name="contact")

]