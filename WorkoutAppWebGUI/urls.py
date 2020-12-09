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
    path('record_workout/', views.choose_day, name='choose_day'),
    path('record_workout/<int:day_id>', views.AddWorkoutView.as_view(), name='add_workout'),
    path('programs/', views.ProgramListView.as_view(), name="program_list"),
    path('programs/<int:pk>', views.ProgramDayListView.as_view(), name="program_day_list"),
    path('programs/day/<int:pk>', views.ProgramDayDetailView.as_view(), name='day_detail'),
    path('programs/<int:pk>/edit', views.ProgramDayUpdate.as_view(), name='day_update'),
    path('program/create_day/<int:program_id>', views.ProgramDayCreate.as_view(), name='create_day'),
    path('programs/create', views.CreateProgramView.as_view(), name='create_program'),
    path('programs/<int:program_id>/remove_day/<int:day_id>', views.remove_day, name='day_remove'),
    path('contact', views.contact, name="contact")

]