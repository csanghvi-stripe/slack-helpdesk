import os
import message
import urllib
import yaml
from urllib.parse import urlencode
from random import randint
import jirasd


from slackclient import SlackClient


class Ticket(object):
    """ Instanciates a Ticket object to handle Issues Created."""
    def __init__(self):
        super(Ticket, self).__init__()
        self.slackjira = jirasd.JiraSD()
        self.number = ''
        self.created_by_id = ''
        self.created_by_name = ''
        self.created_ts = ''
        self.assigned_id = ''
        self.description = ''
        self.urgency=''
        self.summary = ''
        self.assigned_name = "None"
        self.group_id = ""
        self.color = ""
        self.dmid = ""


    def setDMID(self, channel):
        self.dmid = channel
        
    def setNumber(self, ticket):
        self.number = ticket

    def getNumber(self):
        return self.number

    def createTicket(self):
        #number = randint(0, 999)
        self.number = self.slackjira.createTicket(self.description, self.summary, self.created_by_name, self.urgency)
        print ("Created number {}".format(self.number))
        return self.number

    def setCreatedBy(self,username, userid):
        self.created_by_id = userid
        self.created_by_name=username

    def setCreatedAt(self,ts):
        self.created_ts = ts

    def getCreatedBy(self):
        return self.created_by

    def getCreatedAt(self):
        return self.created_ts

    def setAssignedTo(self, username, userid):
        self.assigned_name = username
        self.assigned_id=userid

    def getAssignedTo(self):
        return self.assigned_name

    def setDescription(self, text):
        self.description=text

    def setSummary(self,summary):
        self.summary=summary

    def setUrgency(self,urgency):
        self.urgency=urgency
        self.setColor()

    def setGroupId(self, group_id):
        self.group_id = group_id

    def setColor(self):
        if (self.urgency == "High"):
            self.color = ":red_circle:"
        elif (self.urgency == "Medium"):
            self.color = ":large_blue_circle:"
        else:
            self.color = ":white_circle:"
