# -*- coding: utf-8 -*-
"""
1) Need to clean up code
2) Open DM between assigned used and ticket creator

Handle all JIRA related matters
"""
import json
import bot
from flask import Flask, request, make_response, render_template, Response, jsonify
from urllib.parse import parse_qsl
from threading import Thread
from random import randint


pyBot = bot.Bot()
slack = pyBot.client


app = Flask(__name__)


def _event_handler(event_type, slack_event):
    """
    A helper function that routes events from Slack to our Bot
    by event type and subtype.

    Parameters
    ----------
    event_type : str
        type of event recieved from Slack
    slack_event : dict
        JSON response from a Slack reaction event

    Returns
    ----------
    obj
        Response object with 200 - ok or 500 - No Event Handler error

    """
    print ("in Event Handler")
    team_id = slack_event["team_id"]
    # ================ Team Join Events =============== #
    # When the user first joins a team, the type of event will be team_join
    if event_type == "team_join":
        user_id = slack_event["event"]["user"]["id"]
        # Send the onboarding message
        pyBot.onboarding_message(team_id, user_id)
        return make_response("Welcome Message Sent", 200,)


    elif event_type == "member_joined_channel":
        print ("member joined")
        user_id = slack_event["event"]["user"]
        channel_id = slack_event["event"]["channel"]
        # Send the onboarding message
        if (pyBot.bot_id == user_id):
            print ("Yes bot was invited to a channel!")
            pyBot.myChannels.add(channel_id)
        return make_response("", 200,)


    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/install", methods=["GET"])
def pre_install():
    """This route renders the installation page with 'Add to Slack' button."""
    # Since we've set the client ID and scope on our Bot object, we can change
    # them more easily while we're developing our app.
    client_id = pyBot.oauth["client_id"]
    scope = pyBot.oauth["scope"]
    # Our template is using the Jinja templating language to dynamically pass
    # our client id and scope
    return render_template("install.html", client_id=client_id, scope=scope)


@app.route("/thanks", methods=["GET", "POST"])
def thanks():
    """
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    """
    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')
    # The bot's auth method to handles exchanging the code for an OAuth token
    pyBot.auth(code_arg)
    return render_template("thanks.html")


#{'user_name': 'c.sanghvi',
#'response_url': 'https://hooks.slack.com/commands/T6S5C15LY/249218471651/wnHHhqOlr5NEatfFqIWVL1zR',
#'user_id': 'U6TT6QBK9',
#'channel_id': 'D7B6CGT0T',
#'token': 'c1BpEmuZPedxDOqTlVtKIh2B',
#'team_domain': 'tech-arch-group',
#'trigger_id': '250381124935.230182039712.54d5b49d07ba1a9638a726408f790fe6',
#'command': '/helpdesk', 'channel_name': 'directmessage', 'team_id': 'T6S5C15LY'}

#For slash commands
@app.route("/helpdesk", methods=["GET", "POST"])
def helpdesk():
    print ("In Helpdesk")
    secondtext = request.get_data().decode("utf-8")
    data = dict(parse_qsl(secondtext))
    pyBot.slash_command_handler(data)
    return make_response("", 200,)


@app.route("/tickets", methods=["GET", "POST"])
def tickets():



    secondtext = request.get_data().decode("utf-8")
    data = dict(parse_qsl(secondtext))

    if (data["text"] == "list"):


        count = len(pyBot.tickets.keys())
        print ("In Tickets {}".format(count))
        issues_red = {}
        issues_white = {}
        issues_blue = {}
        for key, value in pyBot.tickets.items():
            print ("key is {}".format(key))
            if (value.urgency == "High"):
                issues_red[key]=value.getAssignedTo()
                print ("Value is High {}".format(value.getAssignedTo()))

            elif (value.urgency == "Medium"):
                issues_blue[key]=value.getAssignedTo()
                print ("Value is Medium {}".format(value.getAssignedTo()))

            else :
                issues_white[key]=value.getAssignedTo()
                print ("Value is low {}".format(value.getAssignedTo()))




        print ("Red {}, Blue {}, White {}".format(len(issues_red.keys()),len(issues_blue.keys()),len(issues_white.keys())))
        text_count = "List of tickets is  {}".format(count)

        attach =  [
            {
                "fallback": "tickets in red",
                "color": "#ff0000",
                "title": "Tickets in Red",
                "fields": [{"title": key,"value": value, "short":False} for key,value in issues_red.items()]
            },
            {
                "fallback": "tickets in blue",
                "color": "#0000ff",
                "title": "Tickets in Blue",
                "fields": [{"title": key,"value": value, "short":False} for key,value in issues_blue.items()]
            },
            {
                "fallback": "tickets in white.",
                "color": "#f2f2f2",
                "title": "Tickets in White",
                "fields": [{"title": key,"value": value, "short":False} for key,value in issues_white.items()]
            }
        ]


        text = {
                "response_type": "ephemeral",
                "icon_url":"https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2017-03-10/153616747479_47b917939554a4acaac5_72.png",
                "text":text_count,
                "attachments":attach
                }

        return Response(json.dumps(text), mimetype='application/json')
    #return Response(, mimetype='application/json')

    elif (data["text"] == "unassigned"):
        issues_red = {}
        issues_white = {}
        issues_blue = {}
        for key, value in pyBot.tickets.items():
            print ("key is {}".format(key))
            if (value.urgency == "High"):
                if (value.getAssignedTo() == "None"):
                    issues_red[key]=value.getAssignedTo()
                    print ("Value is {}".format(value.getAssignedTo()))

            elif (value.urgency == "Medium"):
                if (value.getAssignedTo() == "None"):
                    issues_blue[key]=value.getAssignedTo()
                    print ("Value is {}".format(value.getAssignedTo()))

            else :
                if (value.getAssignedTo() == "None"):
                    issues_white[key]=value.getAssignedTo()
                    print ("Value is {}".format(value.getAssignedTo()))

        count = len(issues_red.keys()) + len(issues_blue.keys()) + len(issues_white.keys())
        text_count = "List of tickets is  {}".format(count)
        print ("Unassigned Red {}, Blue {}, White {}".format(len(issues_red.keys()),len(issues_blue.keys()),len(issues_white.keys())))

        attach =  [
            {
                "fallback": "tickets in red",
                "color": "#ff0000",
                "title": "Tickets in Red",
                "fields": [{"title": key,"value": value, "short":False} for key,value in issues_red.items()]
            },
            {
                "fallback": "tickets in blue",
                "color": "#0000ff",
                "title": "Tickets in Blue",
                "fields": [{"title": key,"value": value, "short":False} for key,value in  issues_blue.items()]
            },
            {
                "fallback": "tickets in white.",
                "color": "#f2f2f2",
                "title": "Tickets in White",
                "fields": [{"title": key,"value": value, "short":False} for key,value in issues_white.items()]
            }
        ]


        text = {
                "response_type": "ephemeral",
                "icon_url":"https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2017-03-10/153616747479_47b917939554a4acaac5_72.png",
                "text":text_count,
                "attachments":attach
                }
        return Response(json.dumps(text), mimetype='application/json')

    #pyBot.slash_command_handler(data)
    #return make_response("", 200,)

@app.route("/callback", methods=["GET","POST"])
def callback():
    rsp = {}
    secondtext = request.get_data().decode("utf-8")
    data = dict(parse_qsl(secondtext))
    print (data['payload'])
    payload = json.loads(data['payload'])
    #print (payload)
    mtype = payload["type"]
    callback_id =  payload["callback_id"]

    #handle interacgive call backs for buttons, message menus etc
    if mtype == "interactive_message":


        if callback_id=="select_assignee":
            #button processing
            #Buttons for us will be used when telling IT channel to assign the ticket to someone
            # If self or randomize selected, then subsequently start a dialog betn ticket creator and assignee
            #Finally if another user is to be assigned, that will be another callback
            team_id=payload["team"]["id"]

            ts = payload["original_message"]["ts"]
            channel = payload["channel"]["id"]
            text = payload["original_message"]["text"]
            values = payload["original_message"]["text"].split(" ")
            #tkt = int(values[2])
            tkt = values[2]
            by = values[5]
            print ("Lets process {} by {}".format(tkt, by))
            attachments = []
            pyBot.client.api_call("chat.update", ts=ts, channel=channel, text=text, attachments= attachments)

            if payload["actions"][0]["value"] == "self" :
                #Ticket assigned to self
                print (payload["response_url"])
                rsp = {
                        	"text":":white_check_mark: Sure, You can have the ticket.",
                        	"replace_original": False
                        }
                assigned_agent_id = payload["user"]["id"]
                assigned_agent_name = payload["user"]["name"]
                pyBot.tickets[str(tkt)].setAssignedTo(assigned_agent_name,assigned_agent_id)
                #ticket_created_by = payload["original_message"]["text"].split("Ticket Created by ")
                print("DM between agent {}, user {}".format(assigned_agent_id, by))
                #make_response(jsonify(rsp), 200,)
                #tempo = pyBot.(tkt)
                #make_response("", 200,)
                #temp =
                return Response(json.dumps(rsp), status=200, mimetype='application/json')
                #attachments=[]

            elif payload["actions"][0]["value"] == "someone":
                #ticket assigned to someone
                #rsp =   {
                        #    "text":":eyes: Sure, Lets assign it to someone.",
                        #    "replace_original": False
                        #    }
                #make_response(jsonify(rsp), 200,)
                #make_response("", 200,)
                #tempo =

                channel = payload["channel"]["id"]
                dm_id = pyBot.assign_someone(channel,tkt)
                return Response("", status=200, mimetype='application/json')


            elif payload["actions"][0]["value"] == "random":
                #randomize
                #attachments=[]
                text = ":white_check_mark: Sounds randomized & assigned to {}".format(payload["user"]["name"])
                rsp = {
                        "text":text,
                        "replace_original": False
                        }

                #"""Randomize the agent name here. Query users list in this channe.
                #Pick a random user. The ideal way would be to keep a running queue
                #for each agent and identify one with bandwidth"""

                assigned_agent_id = payload["user"]["id"]
                assigned_agent_name = payload["user"]["name"]
                pyBot.tickets[str(tkt)].setAssignedTo(assigned_agent_name,assigned_agent_id)
                #ticket_created_by = payload["original_message"]["text"].split("Ticket Created by ")
                print("DM between agent {}, user {}".format(assigned_agent_id, by))
                #make_response(jsonify(rsp), 200,)
                #tempo = pyBot.open_pvt(tkt)
                return Response(json.dumps(rsp), status=200, mimetype='application/json')


        elif callback_id=="ticket_assigned_to":
            values = payload["original_message"]["text"].split(" ")
            #tkt = int(values[2])
            tkt = values[2]
            by = values[5]
            winner = payload["actions"][0]["selected_options"][0]["value"]
            print ("time to assign to someone {}".format(winner))
            text=":white_check_mark: Assigning it to our Superman @{}".format(winner)
            rsp_msg = {
                        "text":text,
                        "replace_original": True
                       }
            pyBot.tickets[str(tkt)].setAssignedTo(payload["user"]["name"], winner)


            print("DM between agent {}, user {}".format(winner, by))
            #temp = pyBot.open_pvt(tkt)
            return Response(json.dumps(rsp_msg), mimetype='application/json')

    elif mtype == "dialog_submission":
        print ("ticket description is: {} ".format(payload["submission"]["description"]))
        thread = Thread(target = threaded_function,  args = (payload, ))
        thread.start()

    return make_response("",200,)

def threaded_function(payload):
    #Complete All JIRA ticket creation tasks
    tkt = pyBot.create_ticket(payload)
    print ("pybot ticket is {} and returned to me is {}".format(pyBot.tickets[str(tkt)].getNumber(), tkt))
    #pyBot.notify_IT(payload,tkt)
    return



@app.route("/listening", methods=["GET", "POST"])
def hears():
    """
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    """
    se = request.data.decode('utf-8')
    slack_event = json.loads(se)

    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

    # ============ Slack Token Verification =========== #
    # We can verify the request is coming from Slack by checking that the
    # verification token in the request matches our app's settings
    if pyBot.verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s \npyBot has: \
                   %s\n\n" % (slack_event["token"], pyBot.verification)
        # By adding "X-Slack-No-Retry" : 1 to our response headers, we turn off
        # Slack's automatic retries during development.
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    # ====== Process Incoming Events from Slack ======= #
    # If the incoming request is an Event we've subcribed to
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        # Then handle the event by event_type and have your bot respond
        return _event_handler(event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route('/')
def index():
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

    thread.join()
    print ("thread finished...exiting")
