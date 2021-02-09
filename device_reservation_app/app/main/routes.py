from threading import Thread
from app import db
import time
from app.scheduler_helper import ReservationHelper, PollHandler
from flask import render_template, flash, redirect, url_for, request, session, current_app
from app.main.forms import EnvironmentForm, ReserveDevice, EditProfileForm, AgentEntry
from app.models import User, Reservation, Agentprofile
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from app.main import bp
from app.slack_message import SlackBot
from app.models import Session


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
    reservation = Reservation.query.filter_by(r_user=user.username)
    agents = Agentprofile.query.filter_by(a_owner=user.username)
    return render_template('user.html', user=user, reservation=reservation, agents=agents)


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
    #form = ReserveDevice()
    #if request.method == 'GET':
    platform_list = []
    days = ['Days']
    hours = ['Hours']
    agent = Agentprofile.query.all()
    for a in agent:
        if not a.a_platform in platform_list:
            platform_list.append(a.a_platform)
    for i in range(1,6):
        days.append(str(i))
    for i in range(1,24):
        hours.append(str(i))
    if request.method == 'POST':
        print(request.form.get('platform'))
        day = 0 if (request.form.get('day') == 'Days') else int(request.form.get('day'))
        hour = 0 if (request.form.get('hour') == 'Hours') else int(request.form.get('hour'))
        duration = day *24 + hour
        session['rtc'] = {'platform': request.form.get('platform'), 'duration': duration}
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('/'):
            next_page = url_for('main.get_env')
        return redirect(next_page)
    return render_template('reservation_page.html', platform_list=platform_list, hours=hours,days=days)


@bp.route('/device_inventory', methods=['POST', 'GET'])
@login_required
def device_inventory():
    agents = Agentprofile.query.all()
    print(agents)
    return render_template('device_inventory.html', agents=agents)


@bp.route('/add_agents', methods=['POST', 'GET'])
@login_required
def add_agents():
    form = AgentEntry()
    if request.method == 'POST':
        agent = Agentprofile(a_name=form.agent_name.data, a_platform= form.agent_platform.data, a_user=form.agent_user.data,a_pass=form.agent_password.data,
                             a_serial=form.agent_serial.data, a_access=form.agent_access.data, a_env=form.agent_env.data,
                             a_ipaddr=form.agent_ipaddr.data, a_location=form.agent_location.data,
                             a_command_line=form.agent_command_line_access.data)
        db.session.add(agent)
        db.session.commit()
        flash('Agent details successfully Updated.')
        return redirect(url_for('main.index'))
    return render_template('add_agent.html', form=form)

@bp.route('/get_env', methods=['POST', 'GET'])
def get_env():
    agents = Agentprofile.query.all()
    env_var = []
    for agent in agents:
        env_list = agent.a_env.split(',')
        for env in env_list:
            if env not in env_var:
                env_var.append(env)
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
                                platform=session['rtc']['platform'], reserve_user=current_user, r_user=current_user.username)
    db.session.add(reserve_agent)
    db.session.commit()
    print(reserve_agent.id)
    app = current_app._get_current_object()
    Thread(target=reserve_obj.insert_agent, args=(app, reserve_agent.id , current_user.username)).start()
    flash('Congratulations, your reservation request is received!. We will mail you your agent details shortly.')
    return redirect(url_for('main.index'))
