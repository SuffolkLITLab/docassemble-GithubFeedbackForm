# docassemble.GithubFeedbackForm

A package to gather feedback and then submit issues to Github.

Add a personal access token to a Github account with permissions to
create issues on your repository. Then add a section like this in your Docassemble configuration:

```
github issues:
  username: "suffolklitlab-issues"
  token: "xxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## Author

Quinten Steenhuis, qsteenhuis@suffolk.edu