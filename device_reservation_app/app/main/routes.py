from app import db
from app.scheduler_helper import ReservationHelper, PollHandler
from flask import render_template, flash, redirect, url_for, request, session, current_app
from app.main.forms import EnvironmentForm, ReserveDevice, EditProfileForm
from app.models import User, Reservation, AgentProfile
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from app.main import bp

reserve_obj = ReservationHelper()


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    reservation = [
        {
            'user': {'username': 'pqa_user'},
            'agent': 'vcal5'
        }
    ]
    return render_template('index.html', title='Home', reservation=reservation)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    reservation = [
        {'user': user, 'agent': 'vcal4'},
        {'user': user, 'agent': 'vcal5'},
    ]
    return render_template('user.html', user=user, reservation=reservation)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/job_schedule')
def job_schedule():
    return render_template('job_schedule.html')


@bp.route('/reserve_device', methods=['POST', 'GET'])
def reserve_device():
    form = ReserveDevice()
    if request.method == 'POST':
        print(form.platform.data)
        session['rtc'] = {'platform': form.platform.data, 'duration': form.duration.data}
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('/'):
            next_page = url_for('get_env')
        return redirect(next_page)
    return render_template('reservation_page.html', form=form)


@bp.route('/device_inventory')
def device_inventory():
    return render_template('device_inventory.html')


@bp.route('/get_env', methods=['POST', 'GET'])
def get_env():
    env_var = ['HDMI1', 'HDMI2', 'TAP', 'USB', 'Remote', 'Windows', 'Linux', 'MAC']
    if request.method == 'POST':
        data = dict((key, request.form.getlist(key) if len(
            request.form.getlist(key)) > 1 else request.form.getlist(key)[0])
                    for key in request.form.keys())
        session['env'] = [key for key in data.keys()]
        print('DATA:{}'.format(session['env']))
        return redirect(url_for('reserve'))
    return render_template('get_env.html', env_var=env_var)


@bp.route('/reserve', methods=['POST', 'GET'])
@login_required
def reserve():
    reserve_agent = Reservation(env=session['env'], duration=session['rtc']['duration'],
                                     r_user=current_user.username)
    db.session.add(reserve_agent)
    db.session.commit()
    PollHandler(reserve_agent, current_user).start()
    flash('Congratulations, your reservation request is received!. We will mail you your agent details shortly.')
    return redirect(url_for('index'))
