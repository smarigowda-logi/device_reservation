from flask_wtf import FlaskForm
from wtforms import widgets, SelectMultipleField, StringField, TextField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User, Agentprofile, Rigdescriptor, Reservation


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


class ReserveDevice(FlaskForm):
    platform = StringField('Platform', [DataRequired()])
    duration = StringField('Duration', [DataRequired()])
    username = StringField('Username', [DataRequired()])
    submit = SubmitField('Select Environment')


class AgentEntry(FlaskForm):
    agent_name = StringField('Agent name', [DataRequired()])
    agent_platform = StringField('Agent Platform', [DataRequired()])
    agent_user = StringField('Agent Username', [DataRequired()])
    agent_password = StringField('Agent Password', [DataRequired()])
    agent_serial = StringField('DNS Name', [DataRequired()])
    agent_access = StringField('UI Access', [DataRequired()])
    agent_ipaddr = StringField('IP Address', [DataRequired()])
    agent_location = StringField('Location', [DataRequired()])
    agent_command_line_access = StringField('Command Line Access', [DataRequired()])
    submit = SubmitField('Add Agent')

    def validate_agent_name(self, agent_name):
        agent = Agentprofile.query.filter_by(a_name=agent_name.data).first()
        if agent is not None:
            raise ValidationError('Agent with similar name already exists in Inventory. Please use different agent name')


class EditAgent(FlaskForm):
    agent_name = StringField('Agent name', [DataRequired()])
    agent_platform = StringField('Agent Platform', [DataRequired()])
    agent_user = StringField('Agent Username', [DataRequired()])
    agent_password = StringField('Agent Password', [DataRequired()])
    agent_serial = StringField('DNS Name', [DataRequired()])
    agent_access = StringField('UI Access', [DataRequired()])
    agent_ipaddr = StringField('IP Address', [DataRequired()])
    agent_location = StringField('Location', [DataRequired()])
    agent_command_line_access = StringField('Command Line Access', [DataRequired()])
    submit1 = SubmitField('Cancel')
    submit = SubmitField('Edit Agent')


    def __init__(self, *args, **kwargs):
        super(EditAgent, self).__init__(*args, **kwargs)


class RigEntry(FlaskForm):
    rig_name = StringField('Rig name', [DataRequired()])
    rig_description = StringField('Rig Description ', [DataRequired()])
    submit = SubmitField('Add Rig')

    def validate_rig_name(self, rig_name):
        rig = Rigdescriptor.query.filter_by(rig=rig_name.data).first()
        if rig is not None:
            raise ValidationError('Rig with similar name already exists in Inventory. Please use different Rig name')


class EditRig(FlaskForm):
    rig = StringField('Rig name', [DataRequired()])
    rig_desc = StringField('Rig Description ', [DataRequired()])
    submit = SubmitField('Edit Rig')
