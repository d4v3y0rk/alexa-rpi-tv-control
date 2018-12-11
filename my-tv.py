from flask import Flask, render_template
from flask_ask import Ask, statement, question, request, session, convert_errors
import os, time

#sends a repeating command
#see the irsend command in lirc documentation http://www.lirc.org/html/irsend.html
#command : The IR command to execute
#duration : The duration in seconds to sleep/pause while the command is being repeated
def sendRepeatCommand(command, duration):
    os.system("irsend SEND_START {} {} ; sleep {}".format(device, command, duration))
    os.system("irsend SEND_STOP {} {}".format(device, command))

#initialize the app
app = Flask(__name__)
ask = Ask(app, '/')

#name of your TV
device = "panasonic"

@ask.launch
def start_skill():
    welcome_message = render_template('welcome')
    return question(welcome_message)

@ask.intent('AMAZON.HelpIntent')
def help():
    return start_skill()

@ask.intent('AMAZON.FallbackIntent')
def fallback():
    fallback_message = render_template('fallback_message')
    return statement(fallback_message)

@ask.session_ended
def session_ended():
    return "{}", 200

#onOffCommand : on | off
@ask.intent('PowerIntent')
def power(onOffCommand):
    os.system("irsend --count=1 SEND_ONCE %s KEY_POWER" % device)
    text = render_template('power_on') if onOffCommand == "on" else render_template('power_off')
    return statement(text).simple_card('Status', text)

@ask.intent('netflix')
def netflix():
    os.system("irsend --count=1 SEND_ONCE %s KEY_PROGRAM" % device)
    text = render_template('netflix')
    return statement(text).simple_card('Status', text)

#volumeCommand : increase | decrease | mute |unmute
@ask.intent('VolumeIntent')
def volume(volumeCommand):
    clarifyText = render_template('clarify_volume_command')
    #volume adjustment not specified
    if volumeCommand is None:
        return question(clarifyText)
    else:
        #determine what was asked
        if volumeCommand == "increase":
            sendRepeatCommand("KEY_VOLUMEUP", 3)
            text = render_template('volume_increase')
        elif volumeCommand == "decrease":
            sendRepeatCommand("KEY_VOLUMEDOWN", 3)
            text = render_template('volume_decrease')
        elif volumeCommand == "mute" or volumeCommand == "unmute":
            os.system("irsend --count=1 SEND_ONCE %s KEY_MUTE" % device)
            text = render_template('volume_mute') if volumeCommand == "mute" else render_template('volume_unmute')
        else:
            #recevied a command that we did not expect
            return question(clarifyText)
        return statement(text).simple_card('Status', text)

#channelNumber : integer
@ask.intent('GotoChannelIntent', convert={'channelNumber': int})
def gotoChannel(channelNumber):
    if channelNumber is None:
        channel_question = render_template('channel_question')
        return question (channel_question)
    else:
        channelNums = list(str(channelNumber))
        #loop over each number and send the ir signal for each number key
        for i in channelNums:
            sendRepeatCommand("KEY_" + i, 0.1)
            time.sleep(0.5)
        text = render_template('change_channel', channel=channelNumber)
        return statement(text).simple_card('Status', text)

#direction: up | down | stop
@ask.intent('ChannelSurfIntent')
def channelSurf(direction):
    if direction == "up":
        sendRepeatCommand("KEY_CHANNELUP", 0.1);
        text = render_template('change_channel_up')
        return question(text).reprompt(render_template('channel_done')).simple_card('Status', text)
    elif direction == "down":
        sendRepeatCommand("KEY_CHANNELDOWN", 0.1);
        text = render_template('change_channel_down')
        return question(text).reprompt(render_template('channel_done')).simple_card('Status', text)
    elif direction == "stop":
        return statement(render_template('finished'))
    else:
        return question("Did you want to move up, down or stop")

if __name__ == '__main__':
    app.run(debug=True)
