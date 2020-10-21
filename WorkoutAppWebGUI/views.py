from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.db.models import Avg
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Workout, WAUser, Program, UserWeight, UserProgram, Set, ProgramDay
from .forms import UserForm, UserWeightForm, UserProgramForm
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import Select, CustomJS, ColumnDataSource
from bokeh.layouts import column
import pandas
import numpy


def index(request):
    return render(request, 'WorkoutAppWebGUI/index.html', {})


def contact(request):
    return render(request, 'WorkoutAppWebGUI/contact.html', {})


@login_required()
def landing(request):
    context = {}
    user = get_object_or_404(WAUser, pk=request.user.wauser.pk)
    context['exercise_history'] = user.workout_set.order_by('-workout_id')[:10][::-1]
    data = Set.objects.filter(workout__in=user.workout_set.all()).values('workout__date', 'exercise__name').\
        order_by("workout__date").annotate(avg_reps=Avg('reps'), avg_weight=Avg('weight'))
    context['script'], context['div'] = plot(data)
    return render(request, "WorkoutAppWebGUI/landing.html", context)


def plot(input_data):
    df = pandas.DataFrame(input_data)
    df['one-rep-max'] = df.apply(calculate_one_rep_max, axis=1)
    df = df.drop(['avg_reps', 'avg_weight'], axis=1)
    df['workout__date'] = pandas.to_datetime(df.workout__date)
    df = df.set_index(keys='workout__date')
    data = ColumnDataSource(data=df)
    menu = list(df.exercise__name.unique())
    cur_data = ColumnDataSource(data=dict(x=[], y=[], z=[]))
    callback = CustomJS(args=dict(source=data, ss=cur_data), code="""
        var f = cb_obj.value
        var d2 = ss.data
        d2['x'] = []
        d2['y'] = []
        d2['z'] = []
        
        for(var i = 0; i <= source.get_length(); i++){
            if (source.data['exercise__name'][i] == f){
                d2['x'].push(source.data['workout__date'][i])
                d2['y'].push(source.data['one-rep-max'][i])
                d2['z'].push(source.data['exercise__name'][i])
            }
        }
        ss.change.emit();
        """)
    exercise_chooser = Select(title="Exercise", options=menu)
    exercise_chooser.sizing_mode = 'scale_width'
    exercise = '' if cur_data.data['z'] == [] else cur_data.data['z'][0]
    fig = figure(title=f"Estimated One Rep Max - {exercise}", x_axis_label="Date", x_axis_type='datetime',
                 y_axis_label="Estimated One Rep Max")
    fig.sizing_mode = "scale_both"
    fig.line(x='x', y='y', source=cur_data)
    exercise_chooser.js_on_change("value", callback)
    layout = column(exercise_chooser, fig)
    layout.sizing_mode = "scale_width"
    script, div = components(layout)
    return script, div


def calculate_one_rep_max(row):
    numerator = 100 * row['avg_weight']
    denominator = 48.8 + (53.8 * numpy.exp(-0.075 * row['avg_reps']))
    return float(numerator) / float(denominator)


@login_required()
def edit_user(request):
    user = get_object_or_404(WAUser, pk=request.user.wauser.pk)
    form2 = UserWeightForm(request.POST or None, instance=user)
    form3 = UserProgramForm(request.POST or None, instance=user)
    forms = [form2, form3]
    for form in forms:
        if form.is_valid():
            form.save()
            return redirect(f'users/{request.user.wauser.pk}')
    return render(request, "WorkoutAppWebGUI/profile_edit.html", {'forms': forms})


class UserView(LoginRequiredMixin, generic.DetailView):
    model = WAUser
    template_name = 'WorkoutAppWebGUI/profile.html'
    login_url = 'login/'
    redirect_field_name = ''
    context_object_name = "UserDetails"

    def get_queryset(self):
        query_set = super(UserView, self).get_queryset().filter(user_id=self.request.user.wauser.pk)
        return query_set

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        context['user_data'] = WAUser.objects.filter(user_id=self.kwargs['pk']).first()
        context['weight_data'] = UserWeight.objects.filter(user_id=self.kwargs['pk']).all()
        context['user_weight'] = UserWeight.objects.filter(user_id=self.kwargs['pk']).order_by('seq_num').last()
        program = UserProgram.objects.filter(user_id=self.kwargs['pk']).filter(current=1).first()
        context['program'] = Program.objects.get(pk=program.program_id)
        return context


class ProgramView(LoginRequiredMixin, generic.DetailView):
    model = UserProgram
    template_name = 'WorkoutAppWebGUI/program.html'
    login_url = 'login/'
    redirect_field_name = ''

    def get_queryset(self):
        query_set = super(ProgramView, self).get_queryset().filter(user_id=self.request.user.wauser.pk)
        return query_set

    def get_context_data(self, **kwargs):
        context = super(ProgramView, self).get_context_data(**kwargs)
        program = UserProgram.objects.filter(user_id=self.request.user.wauser.pk).filter(current=1).first()
        context['program'] = program.program
        program_days = program.program.programday_set.all()
        context['program_days'] = {program_day.day_name:
                                       program_day.expectedset_set.all() for program_day in program_days}
        return context


class WorkoutView(LoginRequiredMixin, generic.DetailView):
    model = Workout
    template_name = "WorkoutAppWebGUI/workout_detail.html"
    login_url = 'login/'
    redirect_field_name = ''

    def get_queryset(self):
        query_set = super(WorkoutView, self).get_queryset().filter(user_id=self.request.user.wauser.pk)
        return query_set

    def get_context_data(self, **kwargs):
        context = super(WorkoutView, self).get_context_data(**kwargs)
        context['data'] = Workout.objects.get(workout_id=self.kwargs['pk']).set_set.all()
        return context
