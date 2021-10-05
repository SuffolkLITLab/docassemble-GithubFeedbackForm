# docassemble.GithubFeedbackForm

A package to gather feedback and then submit issues to Github.

  
1. Create a new GitHub user and create a personal access token on it. It does
 not need any special permissions; optionally, you can limit it. It will
 need to be able to make pull requests on the repos you want to add issues
 to. Public repos usually leave pull access open.
2. Edit your config, and create a block like this:

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
4. Optionally, create your own feedback.yml file. It should look like this,
   with whatever customizations you choose:

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