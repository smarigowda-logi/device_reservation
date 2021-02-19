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
                    print(agent_stat.a_owner, agent, reserve_agent.id)
                    if not agent_stat.a_owner and not agent_found:
                        agent_stat.a_owner = username
                        agent_stat.a_duration = reserve_agent.duration
                        time1 = datetime.utcnow()
                        str_time = time1.strftime("%m/%d/%Y, %H:%M:%S")
                        agent_stat.a_last_reserved = str_time
                        db.session.delete(reserve_agent)
                        db.session.commit()

                        slack_bot.post_message_to_slack('Agent {} reserved under your name for {} hours.'
                                                        ' Please release the agent if you are done '
                                                        'early'.format(agent_stat.a_name, agent_stat.a_duration ),
                                                        username)
                        history = History(user=username, agent=agent_stat.a_name, env=agent_stat.a_env, duration=agent_stat.a_duration)
                        db.session.add(history)
                        db.session.commit()
                        agent_found = True
                        total_time = datetime.utcnow() + timedelta(seconds=agent_stat.a_duration)

                        while datetime.utcnow() < total_time:
                            print(total_time, datetime.utcnow())
                            time.sleep(int(agent_stat.a_duration))
                        agent_stat.a_owner = ''
                        agent_stat.a_duration = 0
                        db.session.commit()

    def free_agent(self, app, username):
        with app.app_context():
            agents = Agentprofile.query.all()
            for agent in agents:
                if agent.a_owner:
                    reserved_time = agent.a_last_reserved
                    reserved_datetime = datetime.strptime(reserved_time, '%m/%d/%Y, %H:%M:%S')
                    expire_time = reserved_datetime + timedelta(seconds=agent.a_duration)
                    print(expire_time, datetime.utcnow())
                    if expire_time < datetime.utcnow():
                        agent.a_owner = ''
                        agent.a_duration = 0
                        db.session.commit()
            reservations = Reservation.query.all()
            free_agents = Agentprofile.query.filter_by(a_owner='').all()
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
                            str_time = time1.strftime("%m/%d/%Y, %H:%M:%S")
                            free_agent.a_last_reserved = str_time
                            db.session.delete(reservation)
                            db.session.commit()
