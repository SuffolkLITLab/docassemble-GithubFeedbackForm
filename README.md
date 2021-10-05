# docassemble.GithubFeedbackForm

A package that uses the GitHub API to gather feedback and then submit issues to Github that can be embedded
into a Docassemble interview. Makes it easy to collect per-page feedback.

This package is designed to support the following workflow:

1. Work is stored on a public GitHub repository, or at least, you setup a repository to collect feedback.
1. There is one package per "interview"/"app".
2. Each question block has a unique question ID.
3. Preferably--questions are triggered in an interview order block. If you use a series of `mandatory`
  blocks instead of a single mandatory block, the `variable` listed in the bug report may not be as useful.

## Getting started

1. Create a new GitHub user and create a personal access token on it. The personal access
   token needs minimal permissions. Specifically, it needs to be allowed to make pull requests.
   Pull request access is allowed for anyone by default when you create a new, public GitHub repository.
3. Edit your config, and create a block like this:

```yaml
github issues:
  username: "YOUR_NEW_DEDICATED_ISSUE_CREATION_ACCOUNT"
  token: "..." # A valid GitHub personal access token associated with the username above
  default repository owner: YOUR_GITHUB_USER_OR_ORG_HERE
  allowed repository owners: # List the repo that your account will be allowed to create issues on
    - YOUR_GITHUB_USER_OR_ORG_HERE 
    - SECOND_GITHUB_USER_OR_ORG
```

  Note that it is important to provide a list of allowed repository owners.
  This is used to prevent your form from being used to spam GitHub 
  repositories with feedback.
  
3. Add a link on each page, in the footer or `under` area.  
   You can use the `feedback_link()` function to add a link, like this:
   `[:comment-dots: Feedback](${ feedback_link(user_info()) } ){:target="_blank"}`
   
   Optional parameters:
    - `i`: the feedback form, like: docassemble.AssemblyLine:feedback.yml
    - `github_repo`: repo name, like: docassemble-AssemblyLine
    - `github_user`: owner of the repo, like: suffolklitlab
    - `variable`: variable being sought, like: intro
    - `question_id`:  id of the current question, like: intro
    - `package_version`: version number of the current package
    - `filename`: filename of the interview the user is providing feedback on.
    
    Each has a sensible default. Most likely, you will limit your custom
    parameters to the `github_repo` if you want feedback links to work
    from the docassemble playground.
    
    You will also need to include the `github_issue.py` module in your parent interview,
    like this: 
    ```yaml
    ---
    modules:
      - docassemble.GithubFeedbackForm.github_issue
    ```
    
4. Optionally, create your own feedback.yml file. If you want a custom feedback.yml,
   it should look like this, with whatever customizations you choose:

```yaml
include:
  - docassemble.GithubFeedbackForm:feedback.yml
---
code: |
  al_feedback_form_title = "Your title here"  
---
code: |
  # This email will be used ONLY if there is no valid GitHub config
  al_error_email = "your_email@yourdomain.com"
---
template: al_how_to_get_legal_help
content: |
  If you need more help, these are free resources:

  ... [INCLUDE STATE-SPECIFIC RESOURCES]      
```

You may also want to customize the metadata: title, exit url and override 
any specific questions, add a logo, etc.    

## Author

Quinten Steenhuis, qsteenhuis@suffolk.edu
