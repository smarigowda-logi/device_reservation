import os
import json
import threading

from app import db
from datetime import datetime
from app.models import User,Reservation, AgentProfile

json_file = os.path.join(os.path.dirname(__file__), 'resources', 'host_info.json')
json_obj = json.load(open(json_file))


class SchedulerHelper:
    def get_agent_list(self, platform, labels):
        print(platform)
        print(labels)


class ReservationHelper:
    def get_agent_list(self, platform, rig_list):
        agent_list = []
        platform_hash = json_obj['host_info'][platform]
        for key, value in platform_hash.items():
            if all(elem in value for elem in rig_list):
                agent_list.append(key)
        return agent_list


class PollHandler(threading.Thread):
    """
    Class to handle google sheet update
    """

    def __init__(self, reserve_agent, current_user):
        super().__init__()
        self.reserve_agent = reserve_agent
        self.current_user = current_user

    def run(self):
        agent_dict = {}
        agent_list = []
        agent_found = False
        while not agent_found:
            agent = AgentProfile.query.all()
            for a in agent:
                agent_env_list = a.a_env.split(',')
                r_env_list = self.reserve_agent.env.split(',')
                check_agent = all(item in agent_env_list for item in r_env_list)
                if check_agent:
                    agent_dict[a.a_name] = agent_env_list
            for k in sorted(agent_dict, key=lambda k: len(agent_dict[k]), reverse=False):
                agent_list.append(k)
            for agent in agent_list:
                agent_stat = AgentProfile.query.filter_by(a_name=agent).first()
                if not (agent_stat.a_owner and agent_found):
                    agent_stat.a_owner = self.current_user.username
                    agent_stat.a_duration = self.reserve_agent.duration
                    agent_stat.a_last_reserved = datetime.utcnow
                    db.session.commit()
                    db.session.delete(self.reserve_agent)
                    db.session.commit()
                    # send_slack_with_agent_details
                    # add agent details to history table
                    agent_found = True
