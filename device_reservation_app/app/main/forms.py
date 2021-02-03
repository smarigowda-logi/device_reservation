from flask_wtf import FlaskForm
from wtforms import widgets, SelectMultipleField, StringField, TextField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != self.original_email:
            email = User.query.filter_by(email=self.email.data).first()
            if email is not None:
                raise ValidationError('Please use a different email.')


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class EnvironmentForm(FlaskForm):

    env_comp = ['HDMI', 'TAP', 'USB', 'Remote', 'Windows', 'Linux', 'MAC']
    env_string = '\r\n'.join(env_comp)
    list_of_files = env_string.split()
    files = [(x, x) for x in list_of_files]
    env_data = MultiCheckboxField('Label', choices=files)


class ReserveDevice(FlaskForm):
    platform = StringField('Platform', [DataRequired()])
    duration = StringField('Duration', [DataRequired()])
    username = StringField('Username', [DataRequired()])
    submit = SubmitField('Select Environment')


class AgentEntry(FlaskForm):
    agent_name = StringField('Agent name', [DataRequired()])
    agent_user = StringField('Agent Username', [DataRequired()])
    agent_password = StringField('Password', [DataRequired()])
    agent_serial = StringField('DNS Name', [DataRequired()])
    agent_access = StringField('UI Access', [DataRequired()])
    agent_env = StringField('Environment/Rigs', [DataRequired()])
    agent_ipaddr = StringField('IP Address', [DataRequired()])
    agent_location = StringField('Location', [DataRequired()])
    agent_command_line_access = StringField('Command Line Access', [DataRequired()])
    submit = SubmitField('Add Agent')
