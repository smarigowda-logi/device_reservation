from threading import Thread
from app import db
import time
from app.scheduler_helper import ReservationHelper
from flask import render_template, flash, redirect, url_for, request, session, current_app
from app.main.forms import EditProfileForm, AgentEntry, RigEntry, EditAgent, EditRig
from app.models import User, Reservation, Agentprofile, History, Rigdescriptor
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
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
@bp.route('/index', methods=['POST', 'GET'])
@login_required
def index():
    reserved_time = {}
    app = current_app._get_current_object()
    Thread(target=reserve_obj.free_agent, args=(app, current_user.username)).start()
    user = User.query.filter_by(username=current_user.username).first_or_404()
    reservation = Reservation.query.filter_by(r_user=user.username)
    agents = Agentprofile.query.filter_by(a_owner=user.username)
    for agent in agents:
        reserved_time[agent.a_name] = datetime.strptime(agent.a_last_reserved, '%m-%d-%Y %H:%M:%S')
    if request.method == 'POST':
        agent = request.form['options']
        agent_obj = Agentprofile.query.filter_by(a_name=agent).first()
        if request.form['action'] == 'Release Reservation':
            agent_obj.a_owner = None
            agent_obj.a_duration = 0
            agent_obj.a_last_reserved = None
            db.session.commit()
            slack_bot.post_message_to_slack('Reservation for Agent {} has been released'.format(agent_obj.a_name), current_user.username)
            return redirect(url_for('main.index'))
        elif request.form['action'] == 'Extend Reservation':
            return redirect(url_for('main.extend', agent=agent))
    return render_template('index.html', title='Home', user=user, reservation=reservation, agents=agents, time_dict=reserved_time)


@bp.route('/queue', methods=['POST', 'GET'])
@login_required
def queue():
    if request.method == 'POST':
        queue_detail = request.form['q_options']
        char = '}{\''
        for c in char:
            queue_detail = queue_detail.replace(c, '')
        print(queue_detail)
        platform, env = str(queue_detail).split(':')[0], str(queue_detail).split(':')[1]
        print('***********')
        print(platform.strip())
        print(env.strip())
        r = Reservation.query.filter_by(platform=platform.strip(), env=env.strip()).first()
        print(r)
        db.session.delete(r)
        db.session.commit()
        return redirect(url_for('main.index'))


@bp.route('/extend/<agent>', methods=['POST', 'GET'])
@login_required
def extend(agent):
    days = []
    hours = []
    for i in range(1, 6):
        days.append(str(i))
    for i in range(1, 24):
        hours.append(str(i))
    if request.method == 'POST':
        day = 0 if (request.form.get('day') == '') else int(request.form.get('day'))
        hour = 0 if (request.form.get('hour') == '') else int(request.form.get('hour'))
        duration = (day * 24) + hour
        agent_obj = Agentprofile.query.filter_by(a_name=agent).first()
        agent_obj.a_duration = int(agent_obj.a_duration) + duration
        db.session.commit()
        slack_bot.post_message_to_slack('Reservation for Agent {} has been extended by {} '
                                        'hours'.format(agent_obj.a_name, duration), current_user.username)
        return redirect(url_for('main.index', username=current_user.username))
    return render_template('extend.html', agent=agent, days=days, hours=hours)


@bp.route('/history', methods=['POST', 'GET'])
@login_required
def history():
    history_entry = History.query.all()
    return render_template('history.html', history=history_entry)


@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_history = History.query.filter_by(user=username)
    return render_template('user.html', user=user, user_history=user_history)


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
def contact():
    return render_template('contact.html')


@bp.route('/job_schedule')
def job_schedule():
    return render_template('job_schedule.html')


@bp.route('/reserve_device', methods=['POST', 'GET'])
def reserve_device():

    platform_list = []
    days = []
    hours = []
    agent = Agentprofile.query.filter_by(a_status='Active').all()
    for a in agent:
        if not a.a_platform in platform_list:
            platform_list.append(a.a_platform)
    for i in range(1, 6):
        days.append(str(i))
    for i in range(1, 24):
        hours.append(str(i))
    if request.method == 'POST':
        print(request.form.get('platform'))
        day = 0 if (request.form.get('day') == '') else int(request.form.get('day'))
        hour = 0 if (request.form.get('hour') == '') else int(request.form.get('hour'))
        duration = (day * 24) + hour
        session['rtc'] = {'platform': request.form.get('platform'), 'duration': duration}
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('/'):
            next_page = url_for('main.get_env')
        return redirect(next_page)
    return render_template('reservation_page.html', platform_list=platform_list, hours=hours,days=days)


@bp.route('/device_inventory', methods=['POST', 'GET'])
@login_required
def device_inventory():
    agents = Agentprofile.query.filter_by(a_status='Active').all()
    print(agents)
    return render_template('device_inventory.html', agents=agents)


@bp.route('/manage_agents', methods=['POST', 'GET'])
@login_required
def manage_agents():
    return render_template('manage_agent.html')


@bp.route('/add_agents', methods=['POST', 'GET'])
@login_required
def add_agents():
    form = AgentEntry()
    if form.validate_on_submit():
        session['agent'] = {'a_name': form.agent_name.data,'a_platform': form.agent_platform.data,
                            'a_user': form.agent_user.data,'a_pass': form.agent_password.data,
                             'a_serial': form.agent_serial.data, 'a_access': form.agent_access.data,
                             'a_ipaddr': form.agent_ipaddr.data, 'a_location': form.agent_location.data,
                             'a_command_line': form.agent_command_line_access.data}
        return redirect(url_for('main.add_agent_env'))
    return render_template('add_agent.html', form=form)


@bp.route('/add_agent_env', methods=['POST', 'GET'])
@login_required
def add_agent_env():
    env_hash = {}
    env_all = Rigdescriptor.query.all()
    for env in env_all:
        env_hash[env.rig] = env.rig_desc
    if request.method == 'POST':
        data = dict((key, request.form.getlist(key) if len(
            request.form.getlist(key)) > 1 else request.form.getlist(key)[0])
                    for key in request.form.keys())
        env_list = [key for key in data.keys()]
        env = ' ,'.join(env_list) + ' '
        agent = Agentprofile(a_name=session['agent']['a_name'], a_platform=session['agent']['a_platform'],
                             a_user=session['agent']['a_user'],
                             a_pass=session['agent']['a_pass'],
                             a_serial=session['agent']['a_serial'], a_access=session['agent']['a_access'],
                             a_ipaddr=session['agent']['a_ipaddr'], a_location=session['agent']['a_location'],
                             a_command_line=session['agent']['a_command_line'], a_status='Active', a_env=env)
        db.session.add(agent)
        db.session.commit()
        flash('Agent ' + session['agent']['a_name'] + ' successfully added to inventory')
        return redirect(url_for('main.manage_agents'))
    return render_template('select_rig.html', env_hash=env_hash)


@bp.route('/delete_agent', methods=['POST', 'GET'])
@login_required
def delete_agent():
    agents = Agentprofile.query.all()
    if request.method == 'POST':
        agent_list = request.form.getlist('agent_list')
        for agent in agent_list:
            agent_obj = Agentprofile.query.filter_by(a_name=agent).first()
            print(agent_obj.a_owner)
            if not agent_obj.a_owner:
                db.session.delete(agent_obj)
                db.session.commit()
                flash('Selected agents successfully deleted from inventory')
            else:
                flash('Agent ' + agent + ' is being used by ' + agent_obj.a_owner + '. Try deleting agent once released')
        return redirect(url_for('main.manage_agents'))
    return render_template('delete_agent.html', agents=agents)


@bp.route('/edit_agent', methods=['POST', 'GET'])
@login_required
def edit_agent():
    agents = Agentprofile.query.filter_by(a_status='Active').all()
    if request.method == 'POST':
        agent = request.form['options']
        return redirect(url_for('main.edit_agent_detail', agent_name=agent))
    return render_template('edit_agent.html', agents=agents)


@bp.route('/edit_agent_detail/<agent_name>', methods=['POST', 'GET'])
@login_required
def edit_agent_detail(agent_name):
    form = EditAgent()
    edit_agent = {}
    agent = Agentprofile.query.filter_by(a_name=agent_name).first()
    if request.method == 'POST':
        if request.form['action'] == 'Next':
            edit_agent['a_name'] = form.agent_name.data
            edit_agent['a_platform'] = form.agent_platform.data
            edit_agent['a_user'] = form.agent_user.data
            edit_agent['a_pass'] = form.agent_password.data
            edit_agent['a_ipaddr'] = form.agent_ipaddr.data
            edit_agent['a_access'] = form.agent_access.data
            edit_agent['a_serial'] = form.agent_serial.data
            edit_agent['a_location'] = form.agent_location.data
            edit_agent['a_command_line'] = form.agent_command_line_access.data
            session['edit_agent'] = edit_agent
            return redirect(url_for('main.edit_agent_env', agent_name=agent_name))
        elif request.form['action'] == 'Cancel':
            return redirect(url_for('main.edit_agent_detail', agent_name=agent_name))
    elif request.method == 'GET':
        form.agent_name.data = agent.a_name
        form.agent_platform.data = agent.a_platform
        form.agent_user.data = agent.a_user
        form.agent_password.data = agent.a_pass
        form.agent_ipaddr.data = agent.a_ipaddr
        form.agent_access.data = agent.a_access
        form.agent_serial.data = agent.a_serial
        form.agent_location.data = agent.a_location
        form.agent_command_line_access.data = agent.a_command_line
    return render_template('edit_agent_detail.html', form=form, agent=agent)


@bp.route('/edit_agent_env/<agent_name>', methods=['POST', 'GET'])
@login_required
def edit_agent_env(agent_name):
    env_hash = {}
    env_all = Rigdescriptor.query.all()
    for env in env_all:
        env_hash[env.rig] = env.rig_desc
    agent = Agentprofile.query.filter_by(a_name=agent_name).first()
    current_env = agent.a_env.split(',')
    if request.method == 'POST':
        agent.a_name = session['edit_agent']['a_name']
        agent.a_platform = session['edit_agent']['a_platform']
        agent.a_user = session['edit_agent']['a_user']
        agent.a_pass = session['edit_agent']['a_pass']
        agent.a_access = session['edit_agent']['a_access']
        agent.a_serial = session['edit_agent']['a_serial']
        agent.a_ipaddr = session['edit_agent']['a_ipaddr']
        agent.a_command_line = session['edit_agent']['a_command_line']
        agent.a_location = session['edit_agent']['a_location']
        data = dict((key, request.form.getlist(key) if len(
            request.form.getlist(key)) > 1 else request.form.getlist(key)[0])
                    for key in request.form.keys())
        env_list = [key for key in data.keys()]
        a_env = ', '.join(env_list)
        agent.a_env = a_env
        db.session.commit()
        flash('Changes to agent ' + agent.a_name + ' saved to inventory')
        return redirect(url_for('main.manage_agents'))
    return render_template('edit_agent_env.html', current_rig=current_env, env_hash=env_hash, agent_name=agent_name)


@bp.route('/maintain_agent', methods=['POST', 'GET'])
@login_required
def maintain_agent():
    agents = Agentprofile.query.all()
    if request.method == 'POST':
        for agent in agents:
            status = request.form[agent.a_name]
            if not agent.a_owner:
                agent.a_status = status
                db.session.commit()
            else:
                flash('Agent '+ agent.a_name + ' is being used by ' + agent.a_owner + '. Please make sure the agent is'
                                                                                      ' not reserved.')
        return redirect(url_for('main.maintain_agent'))
    return render_template('maintain_agent.html', agents=agents)


@bp.route('/manage_rig', methods=['POST', 'GET'])
@login_required
def manage_rig():
    return render_template('manage_rig.html')


@bp.route('/add_rig', methods=['POST', 'GET'])
@login_required
def add_rig():
    form = RigEntry()
    if form.validate_on_submit():
        rig = Rigdescriptor(rig=form.rig_name.data, rig_desc=form.rig_description.data)
        db.session.add(rig)
        db.session.commit()
        flash('Rig ' + form.rig_name.data + ' successfully added to inventory')
        return redirect(url_for('main.manage_rig'))
    return render_template('add_rig.html', form=form)


@bp.route('/delete_rig', methods=['POST', 'GET'])
@login_required
def delete_rig():
    rigs = Rigdescriptor.query.all()
    if request.method == 'POST':
        rig_list = request.form.getlist('rig_list')
        for rig in rig_list:
            rig_obj = Rigdescriptor.query.filter_by(rig=rig).first()
            agents = Agentprofile.query.filter(Agentprofile.a_env.contains(rig)).all()
            agent_name = []
            for agent in agents:
                if agent.a_env.startswith(rig):
                    agent.a_env = agent.a_env.replace(rig+' ,', '')
                agent.a_env = agent.a_env.replace(rig + ' ', '').replace(',,', ',')
                agent_name.append(agent.a_name)
            db.session.delete(rig_obj)
            db.session.commit()
            flash('Deleted rig ' + rig_obj.rig + ' from inventory and agents ' + ','.join(agent_name))
        return redirect(url_for('main.manage_rig'))
    return render_template('delete_rig.html', rigs=rigs)


@bp.route('/edit_rig', methods=['POST', 'GET'])
@login_required
def edit_rig():
    rigs = Rigdescriptor.query.all()
    if request.method == 'POST':
        rig = request.form['options']
        return redirect(url_for('main.edit_rig_detail', rig=rig))
    return render_template('edit_rig.html', rigs=rigs)


@bp.route('/edit_rig_detail/<rig>', methods=['POST', 'GET'])
@login_required
def edit_rig_detail(rig):
    form = EditRig()
    rig_info = Rigdescriptor.query.filter_by(rig=rig).first()
    if request.method == 'POST':
        if request.form['action'] == 'Edit Rig':
            rig_info.rig = form.rig.data
            rig_info.rig_desc = form.rig_desc.data
            db.session.commit()
            flash('Changes saved for rig ' + rig_info.rig)
            return redirect(url_for('main.manage_rig'))
        elif request.form['action'] == 'Cancel':
            return redirect(url_for('main.edit_rig_detail', rig=rig))
    elif request.method == 'GET':
        form.rig.data = rig_info.rig
        form.rig_desc.data = rig_info.rig_desc
    return render_template('edit_rig_detail.html', form=form)


@bp.route('/manage_user_access', methods=['POST', 'GET'])
@login_required
def manage_user_access():
    users = User.query.all()
    if request.method == 'POST':
        for user in users:
            access = request.form[user.username]
            user.administrator = access
            db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('manage_user.html', users=users)


@bp.route('/get_env', methods=['POST', 'GET'])
def get_env():
    agents = Agentprofile.query.filter_by(a_platform=session['rtc']['platform'])
    env_var = {}
    for agent in agents:
        env_list = agent.a_env.split(',')
        for env in env_list:
            if env not in env_var.keys():
                env = env.strip()
                if env:
                    rig = Rigdescriptor.query.filter_by(rig=env).first()
                    env_var[env] = rig.rig_desc
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
    agent_dict = {}
    agent_list = []

    agent_filter = Agentprofile.query.filter_by(a_status='Active').all()
    for a in agent_filter:
        agent_env_list = a.a_env.replace(' ', '').split(',')
        r_env_list = session['env'].split(',')
        check_agent = all(item in agent_env_list for item in r_env_list)
        if check_agent and (a.a_platform == session['rtc']['platform']):
            agent_dict[a.a_name] = agent_env_list
    for k in sorted(agent_dict, key=lambda k: len(agent_dict[k]), reverse=False):
        agent_list.append(k)
    print(agent_list)
    if not agent_list:
        flash('Sorry reservation could not be completed. There are no devices matching your request in inventory.'
              ' Please refer Device Inventory page for current snapshot of available inventory and reserve your device')
        return redirect(url_for('main.index'))
    reserve_agent = Reservation(env=session['env'], duration=session['rtc']['duration'],
                                platform=session['rtc']['platform'], reserve_user=current_user,
                                r_user=current_user.username)
    db.session.add(reserve_agent)
    db.session.commit()
    app = current_app._get_current_object()
    Thread(target=reserve_obj.insert_agent, args=(app, reserve_agent.id, agent_list,
                                                  current_user.username)).start()
    flash('Your reservation request is received!. We will slack your agent details shortly.')
    return redirect(url_for('main.index'))


@bp.route('/release_device', methods=['POST', 'GET'])
@login_required
def release_device():
    if request.method == 'POST':
        agent_list = request.form.getlist('agent_list')
        print(agent_list)
        return redirect(url_for('main.user, username=current_user.username'))
    return render_template('user.html', user=current_user)
