from django.contrib import admin
from .models import WAUser, ExerciseType, ExpectedSet, Program, ProgramDay, UserModel
from .models import UserWeight, UserProgram, Set, UnitType, Workout

admin.site.register(WAUser)
admin.site.register(ExerciseType)
admin.site.register(ExpectedSet)
admin.site.register(Program)
admin.site.register(ProgramDay)
admin.site.register(UserModel)
admin.site.register(UserWeight)
admin.site.register(UserProgram)
admin.site.register(Set)
admin.site.register(UnitType)
admin.site.register(Workout)


