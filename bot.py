# -*- coding: utf-8 -*-
"""
Python Slack Bot class for use with the pythOnBoarding app
"""
import os
import message
import urllib
import yaml
from urllib.parse import urlencode
import ticket

from slackclient import SlackClient

# To remember which teams have authorized your app and what tokens are
# associated with each team, we can store this information in memory on
# as a global object. When your bot is out of development, it's best to
# save this in a more persistant memory store.
authed_teams = {}


class Bot(object):
    """ Instanciates a Bot object to handle Slack onboarding interactions."""
    def __init__(self):
        super(Bot, self).__init__()
        self.name = "helpdesk"
        self.emoji = ":robot_face:"
        self.url="https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2017-03-10/153616747479_47b917939554a4acaac5_72.png"
        # When we instantiate a new bot object, we can access the app
        # credentials we set earlier in our local development environment.
        self.oauth = {"client_id": os.environ.get("CLIENT_ID"),
                      "client_secret": os.environ.get("CLIENT_SECRET"),
                      # Scopes provide and limit permissions to what our app
                      # can access. It's important to use the most restricted
                      # scope that your app will need.
                      "scope": "bot"}
        self.verification = os.environ.get("VERIFICATION_TOKEN")

        # NOTE: Python-slack requires a client connection to generate
        # an oauth token. We can connect to the client without authenticating
        # by passing an empty string as a token and then reinstantiating the
        # client with a valid OAuth token once we have one.
        self.client = SlackClient("")
        # We'll use this dictionary to store the state of each message object.
        # In a production envrionment you'll likely want to store this more
        # persistantly in  a database.
        self.messages = {}
        self.tickets = {}
        self.bot_id=""
        self.at_bot=""
        self.myChannels = set()


    def auth(self, code):
        """
        Authenticate with OAuth and assign correct scopes.
        Save a dictionary of authed team information in memory on the bot
        object.

        Parameters
        ----------
        code : str
            temporary authorization code sent by Slack to be exchanged for an
            OAuth token

        """
        # After the user has authorized this app for use in their Slack team,
        # Slack returns a temporary authorization code that we'll exchange for
        # an OAuth token using the oauth.access endpot
        auth_response = self.client.api_call(
                                "oauth.access",
                                client_id=self.oauth["client_id"],
                                client_secret=self.oauth["client_secret"],
                                code=code
                                )
        # To keep track of authorized teams and their associated OAuth tokens,
        # we will save the team ID and bot tokens to the global
        # authed_teams object
        team_id = auth_response["team_id"]
        authed_teams[team_id] = {"bot_token":
                                 auth_response["bot"]["bot_access_token"]}
        # Then we'll reconnect to the Slack Client with the correct team's
        # bot token
        self.client = SlackClient(authed_teams[team_id]["bot_token"])
        api_call = self.client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            #print (users)
            for user in users:
                if 'name' in user and user.get('name') == self.name:
                    print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
                    self.bot_id = user.get('id')
                    self.at_bot = "<@" + self.bot_id + ">"

                    print (self.at_bot)
                    #else:
                        #print("could not find bot user with the name " + user.get('name'))




    def open_dialog(self, trigger_id):
        with open('dialog.json') as json_file:
            json_dict = yaml.safe_load(json_file)

        callback = self.client.api_call("dialog.open",dialog=json_dict,trigger_id=trigger_id)
        print (callback)
        return callback


    def slash_command_handler(self, datadict):
        print (datadict)
        trigger_id = datadict["trigger_id"]
        if (datadict["command"] == "/helpdesk"):
            callback = self.open_dialog(trigger_id)
            return callback


        return


    def create_ticket (self, payload):


        userid = payload["user"]["id"]
        username = payload["user"]["name"]
        channel = self.open_dm(userid)
        tkt = ticket.Ticket()
        tkt.setCreatedBy(username,userid)
        tkt.setSummary(payload["submission"]["title"])
        tkt.setDescription(payload["submission"]["description"])
        tkt.setUrgency(payload["submission"]["urgency"])
        tkt.setDMID(channel)
        tkt_num = str(tkt.createTicket())
        #<http://www.foo.com|ISD-1>
        text = "I made your ticket at {} <{}|{}> where you can add more details for the IT team to help you out".format(tkt.color, tkt.slackjira.jira_base_url,tkt_num)

        timestamp = self.notify_user(tkt,channel,text)
        tkt.setCreatedAt(timestamp)
        self.tickets[str(tkt_num)] = tkt
        #We can use timestamp to track overall response time
        self.notify_IT(payload,str(tkt_num))

        return tkt_num

    def notify_user(self,tkt, channel, text):
        #text = "Hang Tight. Ticket id: {} <{}|{}> Help is on its way".format(tkt.color, tkt.slackjira.jira_base_url,tkt_num)
        print ("Channel is: {} & user is {}".format(channel, self.name))
        post_message = self.client.api_call("chat.postMessage",
                                            channel=channel,
                                            username=self.name,
                                            icon_url=self.url,
                                            text=text)

        timestamp = post_message["ts"]

        return timestamp


    def notify_IT(self,payload, tkt_num):
        username = payload["user"]["name"]
        userid = payload["user"]["id"]
        #get the urgency of this ticket
        color = self.tickets[tkt_num].color
        url = self.tickets[tkt_num].slackjira.jira_base_url


        tktext = "Please assign this {} ticket <{}|{}>".format(color,url, tkt_num)
        attachments = [{
                                "text": tktext,
                                "attachment_type": "default",
                                "callback_id": "select_assignee",
                                "fallback": "wowweee!",
                                "color": "#f44262",
                                "actions": [{
                                        "name": "part_1",
                                        "text": "Take it self",
                                        "type": "button",
                                        "value": "self"
                                        },{
                                        "name": "part_2",
                                        "text": "Assign to someone",
                                        "type": "button",
                                        "value": "someone"
                                        },
                                        {
                                        "name": "part_3",
                                        "text": "randomize",
                                        "type": "button",
                                        "value": "random"
                                        }
                                ]
                        }]
        #Get the IT channel, how?
        print("Notify IT in channel: {}".format(self.myChannels))
        #post message to the IT channel with ticket information
        for channel in self.myChannels:
            print ("Sending message to {}".format(channel))

            text = "Ticket {} {} Created by {}".format(color, tkt_num, username)

            post_message = self.client.api_call("chat.postMessage",
                                            channel=channel,
                                            username=self.name,
                                            icon_url=self.url,
                                            text=text,
                                            attachments = attachments

                                            )
        return

    def assign_someone(self,channel, tkt):


        text = "Ticket {} {} Created by {}".format(self.tickets[str(tkt)].color, tkt, self.tickets[str(tkt)].created_by_name)

        attachments =[
                        {
                        "text": "Who should the ticket be assigned to?",
                        #"fallback": "You could be telling the computer exactly what it can do with a lifetime supply of chocolate.",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "callback_id": "ticket_assigned_to",
                        "actions": [
                            {
                            "name": "users",
                            "text": "Please select",
                            "type": "select",
                            "data_source": "users"
                            }
                        ]
                        }
                     ]
        post_message = self.client.api_call("chat.postMessage",
                                                    channel=channel,
                                                    username=self.name,
                                                    icon_url=self.url,
                                                    text=text,
                                                    attachments = attachments

                                                )
        print (post_message)

        return post_message


    def open_pvt(self, tkt):
        """
        Open a pvt channel to activate communication between users
        recieved from Slack.

        Parameters
        ----------
        user_name : str
            name of the Slack user creating ticket
        agent_name : str
            name of the agent assigned to ticket

        Returns
        ----------
        id : str
            id of the  channel opened by this method
        """


        users = self.tickets[str(tkt)].assigned_id+ "," + self.tickets[str(tkt)].created_by_id + "," + self.bot_id
        print("DM between 3 users {}".format(users))
        new_dm = self.client.api_call("mpim.open", users = users)


        """Invite members to this channel"""
        print(new_dm)
        dm_id = new_dm["group"]["id"]
        text = "Connecting you two for the ticket {}".format(tkt)

        post_message = self.client.api_call("chat.postMessage",
                                                    channel=dm_id,
                                                    username=self.name,
                                                    icon_url=self.url,
                                                    text=text)


        self.tickets[str(tkt)].setGroupId(dm_id)

        return dm_id


    def open_dm(self, user_id):
        """
        Open a DM to send a confirm ticket creation.

        Parameters
        ----------
        user_id : str
            id of the Slack user associated with the 'team_join' event

        Returns
        ----------
        dm_id : str
            id of the DM channel opened by this method
        """
        new_dm = self.client.api_call("im.open",
                                      user=user_id)
        dm_id = new_dm["channel"]["id"]
        return dm_id

    def onboarding_message(self, team_id, user_id):
        """
        Create and send an onboarding welcome message to new users. Save the
        time stamp of this message on the message object for updating in the
        future.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        # We've imported a Message class from `message.py` that we can use
        # to create message objects for each onboarding message we send to a
        # user. We can use these objects to keep track of the progress each
        # user on each team has made getting through our onboarding tutorial.

        # First, we'll check to see if there's already messages our bot knows
        # of for the team id we've got.
        if self.messages.get(team_id):
            # Then we'll update the message dictionary with a key for the
            # user id we've recieved and a value of a new message object
            self.messages[team_id].update({user_id: message.Message()})
        else:
            # If there aren't any message for that team, we'll add a dictionary
            # of messages for that team id on our Bot's messages attribute
            # and we'll add the first message object to the dictionary with
            # the user's id as a key for easy access later.
            self.messages[team_id] = {user_id: message.Message()}
        message_obj = self.messages[team_id][user_id]
        # Then we'll set that message object's channel attribute to the DM
        # of the user we'll communicate with
        message_obj.channel = self.open_dm(user_id)
        # We'll use the message object's method to create the attachments that
        # we'll want to add to our Slack message. This method will also save
        # the attachments on the message object which we're accessing in the
        # API call below through the message object's `attachments` attribute.
        message_obj.create_attachments()
        post_message = self.client.api_call("chat.postMessage",
                                            channel=message_obj.channel,
                                            username=self.name,
                                            icon_url=self.url,
                                            text=message_obj.text,
                                            attachments=message_obj.attachments
                                            )
        timestamp = post_message["ts"]
        # We'll save the timestamp of the message we've just posted on the
        # message object which we'll use to update the message after a user
        # has completed an onboarding task.
        message_obj.timestamp = timestamp
