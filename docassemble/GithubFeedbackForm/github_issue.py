import requests
import json
from docassemble.base.util import log, get_config

# reference: https://gist.github.com/JeffPaine/3145490
# https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#create-an-issue

# Authentication for user filing issue (must have read/write access to
# repository to add issue to)
__all__ = ['valid_github_issue_config', 'make_github_issue']
USERNAME = get_config('github issues',{}).get('username')
TOKEN = get_config('github issues',{}).get('token')

def valid_github_issue_config():
  return bool(TOKEN)

def make_github_issue(repo_owner, repo_name, template=None, title=None, body=None):
    """
    Create a new Github issue and return the URL.
    """
    url = 'https://api.github.com/repos/%s/%s/issues' % (repo_owner, repo_name)
    # log(url)
    # Headers
    if not TOKEN:
      log("Error creating issues: No valid GitHub token provided.")
      return None
    
    headers = {
        "Authorization": "token %s" % TOKEN,
        "Accept": "application/vnd.github.v3+json"
    }
    
    if template:
      title = template.subject
      body = template.content
    # Create our issue
    data = {'title': title,
            'body': body,
           }

    payload = json.dumps(data)

    # Add the issue to our repository
    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code == 201:
        return response.json().get('html_url')
    else:
        log(f'Could not create Issue "{title}", results {response.content}')