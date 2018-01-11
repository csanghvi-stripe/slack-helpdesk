'''
What can JIRA interface do?
1) Create Ticket
2) Search for Ticket
3) s
'''


from oauthlib.oauth1 import SIGNATURE_RSA
from requests_oauthlib import OAuth1Session
from jira.client import JIRA



class JiraSD(object):
    """ Instanciates a JIRA object to handle Issues Created."""
    def __init__(self):
        super(JiraSD, self).__init__()

        self.rsa_key = self.read("jirapvt.pem")

        self.jira_base_url = "https://slackdev.atlassian.net"

        self.request_token_url = self.jira_base_url+"/plugins/servlet/oauth/request-token"
        self.authorize_url = self.jira_base_url+"/plugins/servlet/oauth/authorize"
        self.access_token_url = self.jira_base_url + "/plugins/servlet/oauth/access-token"

        self.oauth_signing_type = 'RSA-SHA1'
        self.consumer_key = 'csanghvi'
        self.consumer_secret='dont_care'
        self.verifier = 'jira_verifier'

        self.oauth_token = "yrRisCkDUFK5GVeI1ppD22qU3Ua4tZ5c"
        self.oauth_token_secret = "b7fuJl94e4IJQmtck7gsr4rzPtbCy5Hw"
        self.jira = self.auth()
        print("JIRA SD Constructor")


    def read(self, file_path):
        """ Read a file and return it's contents. """
        with open(file_path) as f:
            #return serialization.load_pem_private_key(
            return f.read()


    # Now you can use the access tokens with the JIRA client. Hooray!

    def auth(self):
        return JIRA(options={'server': self.jira_base_url}, oauth={
        'access_token': self.oauth_token,
        'access_token_secret': self.oauth_token_secret,
        'consumer_key': self.consumer_key,
        'key_cert': self.rsa_key
    })


    def searchTickets(self):

        # print all of the project keys just as an exmaple
        for project in self.jira.projects():
            print(project.key)

        #jac = JIRA('https://jira.atlassian.com')
        #authed_jira = JIRA(basic_auth=('username', 'password'))
        #jira = JIRA('https://slackdev.atlassian.net', basic_auth=("csanghvi@slack-corp.com","CBSind55"))

        issue = self.jira.issue('ISD-3')
        print (issue.fields.project.key)             # 'JRA'
        print (issue.fields.issuetype.name)          # 'New Feature'
        print (issue.fields.reporter.displayName)    # 'Mike Cannon-Brookes [Atlassian]'


    def createTicket(self, description, summary, created_by_name, urgency):

        username='csanghvi+mr'
        #Get JIRA username of the user raising the ticket,
        #if not available create a ticket without default reporter
        #Requirement: Who should be allowed to raise, or on behalf of whom the ticket should be raised
        issue_dict = {
            'project': {'key': 'ISD'},
            'summary': summary,
            'description': description,
            'issuetype': {'name': 'Task'},
            'reporter':{'name':username},
        }

        new_issue = self.jira.create_issue(fields=issue_dict)

        print (new_issue)
        return new_issue
