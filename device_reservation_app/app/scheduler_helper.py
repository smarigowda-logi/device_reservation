import os
import json
import threading
import time

#from app import db
from datetime import datetime
#from app.models import User, Reservation, Agentprofile
from app.slack_message import SlackBot
from flask import current_app
from app import db, executor
from app.models import Agentprofile
from datetime import datetime, timedelta

json_file = os.path.join(os.path.dirname(__file__), 'resources', 'host_info.json')
json_obj = json.load(open(json_file))
slack_bot = SlackBot()


class SchedulerHelper:
    def get_agent_list(self, platform, labels):
        print(platform)
        print(labels)


class ReservationHelper:

    def insert_agent(self, agent_filter, reserve_agent, username):
        from app import create_app
        app = create_app()
        app.app_context().push()

        with app.app_context():
            agent_dict = {}
            agent_list = []
            agent_found = False
            while not agent_found:
                for a in agent_filter:
                    agent_env_list = a.a_env.split(',')
                    r_env_list = reserve_agent.env.split(',')
                    check_agent = all(item in agent_env_list for item in r_env_list)
                    if check_agent:
                        agent_dict[a.a_name] = agent_env_list
                for k in sorted(agent_dict, key=lambda k: len(agent_dict[k]), reverse=False):
                    print(k)
                    agent_list.append(k)
                print(agent_list)
                for agent in agent_list:
                    agent_stat = Agentprofile.query.filter_by(a_name=agent).first()
                    if not agent_stat.a_owner and not agent_found:
                        agent_stat.a_owner = username
                        agent_stat.a_duration = reserve_agent.duration
                        # agent_stat.a_last_reserved = "time"
                        db.session.commit()
                        db.session.delete(reserve_agent)
                        db.session.commit()

                        slack_bot.post_message_to_slack('Agent {} reserved under your name for {} hours.'
                                                        ' Please release the agent if you are done '
                                                        'early'.format(agent_stat.a_name, reserve_agent.duration),
                                                        username)
                        # add agent details to history table
                        agent_found = True
                        total_time = datetime.now() + timedelta(hours=agent_stat.a_duration)

                        while datetime.now() < total_time:
                            print(total_time, datetime.now())
                            time.sleep(5)
                        agent_stat.a_owner = ''
                        agent_stat.a_duration = 0
                        db.session.commit()

    def free_agent(self, agent):
        from app import create_app
        app = create_app()
        app.app_context().push()
        with app.app_context():
            total_time = datetime.now() + timedelta(hours=agent.a_duration)
            print(total_time, datetime.now())
            while datetime.now() < total_time:
                time.sleep(5)
            agent.a_owner = ''
            agent.a_duration = ''
            db.session.commit()


class PollHandler(threading.Thread):
    """
    Class to handle google sheet update
    """

    def __init__(self, reserve_agent, current_user, db, agentprofile, agent):
        super().__init__()
        from app import create_app
        self.app = create_app()
        self.app.app_context().push()
        self.reserve_agent = reserve_agent
        self.current_user = current_user
        self.db = db
        self.agentprofile = agentprofile
        self.agent = agent

    def run(self):
        agent_dict = {}
        agent_list = []
        agent_found = False
        with self.app.app_context:
            while not agent_found:
                for a in self.agent:
                    agent_env_list = a.a_env.split(',')
                    r_env_list = self.reserve_agent.env.split(',')
                    check_agent = all(item in agent_env_list for item in r_env_list)
                    if check_agent:
                        agent_dict[a.a_name] = agent_env_list
                for k in sorted(agent_dict, key=lambda k: len(agent_dict[k]), reverse=False):
                    agent_list.append(k)
                for agent in agent_list:
                    agent_stat = executor.submit(self.agentprofile.query.filter_by(a_name=agent).first())
                    if not (agent_stat.a_owner and agent_found):
                        agent_stat.a_owner = self.current_user.username
                        agent_stat.a_duration = self.reserve_agent.duration
                        agent_stat.a_last_reserved = datetime.utcnow
                        executor.submit(self.db.session.commit())
                        executor.submit(self.db.session.delete(self.reserve_agent))
                        executor.submit(self.db.session.commit())
                        slack_bot.post_message_to_slack('Agent {} reserved under your name for {} hours. Please release '
                                                        'the agent if you are done early'.format(agent.a_name,
                                                                                                 self.reserve_agent.duration,
                                                                                                 self.current_user.username))
                        # add agent details to history table
                        agent_found = True
