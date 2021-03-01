import requests
import json


class SlackBot:
    def __init__(self):
        self.slack_token = 'xoxb-95721441479-1673049977510-RL6hRMla2KsD7DHmW7S7YNlK'
        self.slack_icon_url = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTuGqps7ZafuzUsViFGIremEL2a3NR0KO0s0RTCMXmzmREJd5m4MA&s'
        self.slack_user_name = 'DeviceReservation'

    def post_message_to_slack(self, text, channel, blocks = None):
        return requests.post('https://slack.com/api/chat.postMessage', {
            'token': self.slack_token,
            'channel': '@'+channel,
            'text': text,
            'icon_url': self.slack_icon_url,
            'username': self.slack_user_name,
            'blocks': json.dumps(blocks) if blocks else None
        }).json()
