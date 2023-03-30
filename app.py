import os
from flask import Flask, request
from github import Github, GithubIntegration

app = Flask(__name__)

app_id = '311871'

# Read the bot certificate
with open(
        os.path.normpath(os.path.expanduser('bot_key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()
    
# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)

def issue_opened_event(repo, payload):
    issue = repo.get_issue(number=payload['issue']['number'])
    author = issue.user.login

    # Add labels to the issue
    issue.add_to_labels('needs triage')
    issue.add_to_labels('pending')

    
    response = f"Thanks for opening this issue, @{author}! " \
                f"The repository maintainers will look into it ASAP! :speech_balloon:"
    issue.create_comment(f"{response}")

def pull_request_accepted_event(repo, payload):
    pull_request = repo.get_pull(number=payload['pull_request']['number'])
    author = pull_request.user.login

    # add comment to pull request


    

    
    response = f"Thanks for opening this pull request, @{author}! " \
                f"The repository maintainers will look into it ASAP! :speech_balloon:"
    pull_request.create_issue_comment(f"{response}")

    #get branch name
    branch_name = pull_request.head.ref
    
    

    if (pull_request.merged):

        pull_request.create_issue_comment(f"Thanks for your contribution, @{author}! :tada:")
        print (branch_name)

        repo.get_git_ref(f"heads/{branch_name}").delete()
        
def pull_request_pending(repo, payload):
    pull_request = repo.get_pull(number=payload['pull_request']['number'])
    author = pull_request.user.login

    # add comment to pull request
    #get title of pull request
    title = pull_request.title.lower()

    pull_request.create_issue_comment(f"Test ")

    if "wip" in title or "work in progress" in title or "do not merge" in title :
        
        repo.get_commit(sha=pull_request.head.sha).create_status(state='pending', description='Work in progress', context='WIP')
        
    else :
        repo.get_commit(sha=pull_request.head.sha).create_status(state='success', description='Ready to merge', context='WIP')





@app.route("/", methods=['POST'])
def bot():
    payload = request.json

    if not 'repository' in payload.keys():
        return "", 204

    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']

    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    # Check if the event is a GitHub issue creation event
    if all(k in payload.keys() for k in ['action', 'issue']) and payload['action'] == 'opened':
        issue_opened_event(repo, payload)
    #check if pull request accepted
    elif all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'opened':
        pull_request_pending(repo, payload)
    elif all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'edited':
        pull_request_pending(repo, payload)
    elif all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'closed':
        pull_request_accepted_event(repo, payload)
    return "", 204

if __name__ == "__main__":
    app.run(debug=True, port=5000)
