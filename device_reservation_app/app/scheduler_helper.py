import os
import json
import threading
import time as time
import pymysql

from app.slack_message import SlackBot
from flask import current_app
from app import db
from app.models import Agentprofile, History, Session, Reservation
from datetime import datetime, timedelta

json_file = os.path.join(os.path.dirname(__file__), 'resources', 'host_info.json')
json_obj = json.load(open(json_file))
slack_bot = SlackBot()


class SchedulerHelper:
    def get_agent_list(self, platform, labels):
        print(platform)
        print(labels)


class ReservationHelper:
    def insert_agent(self, app, reserve_id, agent_list, username):
        with app.app_context():
            reserve_agent = Reservation.query.filter_by(id=reserve_id).first()
            agent_found = False
            while not agent_found:
                for agent in agent_list:
                    agent_stat = Agentprofile.query.filter_by(a_name=agent).first()
                    db.session.refresh(agent_stat)
                    # print(agent_stat.a_owner, agent, reserve_agent.id)
                    if not agent_stat.a_owner and not agent_found:
                        agent_stat.a_owner = username
                        agent_stat.a_duration = reserve_agent.duration
                        time1 = datetime.utcnow()
                        str_time = time1.strftime("%m-%d-%Y %H:%M:%S")
                        agent_stat.a_last_reserved = str_time
                        db.session.delete(reserve_agent)
                        db.session.commit()

                        slack_bot.post_message_to_slack('Agent {} reserved under your name for {} hours.'
                                                        ' Below are the agent details: \n IP Address: {} \n Serial'
                                                        ' number: {} \n UI_Access: {} \nUsername: {} \n '
                                                        'Password:{} \n'.format(agent_stat.a_name, agent_stat.a_duration,
                                                                                agent_stat.a_ipaddr, agent_stat.a_serial,
                                                                                agent_stat.a_access, agent_stat.a_user,
                                                                                agent_stat.a_pass), username)
                        history = History(user=username, agent=agent_stat.a_name, platform=agent_stat.a_platform, env=agent_stat.a_env, duration=agent_stat.a_duration)
                        db.session.add(history)
                        db.session.commit()
                        agent_found = True
                        total_time = datetime.utcnow() + timedelta(hours=agent_stat.a_duration)

                        while datetime.utcnow() < total_time:
                            print(total_time, datetime.utcnow())
                            agent_stat = Agentprofile.query.filter_by(a_name=agent).first()
                            db.session.refresh(agent_stat)
                            if agent_stat.a_owner != username:
                                break
                            print(agent_stat.a_duration)
                            time.sleep(10)
                        agent_stat.a_owner = None
                        agent_stat.a_duration = 0
                        agent_stat.a_last_reserved = None
                        db.session.commit()

    def free_agent(self, app, username):
        with app.app_context():
            agents = Agentprofile.query.filter_by(a_status='Active').all()
            for agent in agents:
                if agent.a_owner:
                    reserved_time = agent.a_last_reserved
                    reserved_datetime = datetime.strptime(reserved_time, '%m-%d-%Y %H:%M:%S')
                    expire_time = reserved_datetime + timedelta(hours=agent.a_duration)
                    if expire_time < datetime.utcnow():
                        agent.a_owner = None
                        agent.a_duration = 0
                        agent.a_last_reserved = None
                        db.session.commit()
            reservations = Reservation.query.all()
            free_agents = Agentprofile.query.filter_by(a_owner=None).all()
            if free_agents:
                for reservation in reservations:
                    reserve_list = reservation.env.split(',')
                    for free_agent in free_agents:
                        env_list = free_agent.a_env.split(',')
                        check_agent = all(item in env_list for item in reserve_list)
                        if check_agent and (free_agent.a_platform == reservation.platform):
                            free_agent.a_owner = reservation.r_user
                            free_agent.a_duration = reservation.duration
                            time1 = datetime.utcnow()
                            print(time1)
                            str_time = time1.strftime("%m-%d-%Y %H:%M:%S")
                            free_agent.a_s = str_time
                            slack_bot.post_message_to_slack('Agent {} reserved under your name for {} hours.'
                                                            ' Below are the agent details: \n IP Address: {} \n Serial'
                                                            ' number: {} \n UI_Access: {} \nUsername: {} \n '
                                                            'Password:{} \n'.format(free_agent.a_name,
                                                                                    free_agent.a_duration,
                                                                                    free_agent.a_ipaddr,
                                                                                    free_agent.a_serial,
                                                                                    free_agent.a_access,
                                                                                    free_agent.a_user,
                                                                                    free_agent.a_pass), username)
                            history = History(user=username, agent=free_agent.a_name, platform=free_agent.a_platform,
                                              env=free_agent.a_env, duration=free_agent.a_duration)
                            db.session.add(history)
                            db.session.delete(reservation)
                            db.session.commit()
