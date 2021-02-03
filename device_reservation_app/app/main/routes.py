from threading import Thread
from app import db
from app.scheduler_helper import ReservationHelper, PollHandler
from flask import render_template, flash, redirect, url_for, request, session, current_app
from app.main.forms import EnvironmentForm, ReserveDevice, EditProfileForm, AgentEntry
from app.models import User, Reservation, Agentprofile
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from app.main import bp
from app.slack_message import SlackBot
from multiprocessing.dummy import Pool as ThreadPool


slack_bot = SlackBot()
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
        return redirect(url_for('main.edit_profile'))
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
            next_page = url_for('main.get_env')
        return redirect(next_page)
    return render_template('reservation_page.html', form=form)


@bp.route('/device_inventory', methods=['POST', 'GET'])
def device_inventory():
    form = AgentEntry()
    if request.method == 'POST':
        agent = Agentprofile(a_name=form.agent_name.data,a_user=form.agent_user.data,a_pass=form.agent_password.data,
                             a_serial=form.agent_serial.data, a_access=form.agent_access.data, a_env=form.agent_env.data,
                             a_ipaddr=form.agent_ipaddr.data, a_location=form.agent_location.data,
                             a_command_line=form.agent_command_line_access.data)
        db.session.add(agent)
        db.session.commit()
        flash('Agent details successfully Updated.')
        return redirect(url_for('main.index'))
    return render_template('device_inventory.html', form=form)


@bp.route('/get_env', methods=['POST', 'GET'])
def get_env():
    env_var = ['HDMI1', 'HDMI2', 'TAP', 'USB', 'Remote', 'Windows', 'Linux', 'MAC']
    if request.method == 'POST':
        data = dict((key, request.form.getlist(key) if len(
            request.form.getlist(key)) > 1 else request.form.getlist(key)[0])
                    for key in request.form.keys())
        env_list = [key for key in data.keys()]
        session['env'] = ','.join(env_list)
        print('DATA:{}'.format(session['env']))
        return redirect(url_for('main.reserve'))
    return render_template('get_env.html', env_var=env_var)


@bp.route('/reserve', methods=['POST', 'GET'])
@login_required
def reserve():
    reserve_agent = Reservation(env=session['env'], duration=session['rtc']['duration'],
                                     r_user=current_user.username)
    db.session.add(reserve_agent)
    db.session.commit()
    agent_filter = Agentprofile.query.all()
    print(session['rtc']['duration'])
    TIMEOUT = 60*60*int(session['rtc']['duration'])
    print(TIMEOUT)
    job = current_app.task_queue.enqueue_call(
        func=reserve_obj.insert_agent, args=(agent_filter, reserve_agent, current_user.username), timeout=TIMEOUT, result_ttl=5000
    )
    print(job.get_id())
    #Thread(target=reserve_obj.insert_agent, args=(current_app, agent_filter, reserve_agent, current_user.username)).start()
    #PollHandler(reserve_agent, current_user, db, Agentprofile, agent_filter).start()
    flash('Congratulations, your reservation request is received!. We will mail you your agent details shortly.')
    return redirect(url_for('main.index'))
