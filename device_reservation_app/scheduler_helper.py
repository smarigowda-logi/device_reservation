import os
import json
import threading


from app import db
from app.models import Reservation
json_file = os.path.join(os.path.dirname(__file__), 'resources', 'host_info.json')
json_obj = json.load(open(json_file))


class SchedulerHelper:
    def get_agent_list(self, platform, labels):
        print(platform)
        print(labels)


class ReservationHelper:
    @staticmethod
    def get_agent_list(platform, rig_list):
        agent_list = []
        platform_hash = json_obj['host_info'][platform]
        for key, value in platform_hash.items():
            if all(elem in value for elem in rig_list):
                agent_list.append(key)
        return agent_list

    @staticmethod
    def delete_reservation_row(env, user, duration):
        """
        Function to delete row from Reservation table if agent is assigned to the request
        :param env:
        :param user:
        :param duration:
        :return:
        """
        r = Reservation.query.filter_by(env=env, r_user=user, duration=duration)
        Reservation.query.filter_by(id=r.id).delete()


