import importlib
import json
import requests
from typing import Dict, Optional, List, Union, Any
from urllib.parse import urlencode, quote_plus
from docassemble.base.util import log, get_config, interview_url
import re

try:
    import google.generativeai as genai
except ImportError:
    pass

# reference: https://gist.github.com/JeffPaine/3145490
# https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#create-an-issue

# Authentication for user filing issue (must have read/write access to
# repository to add issue to)
__all__ = [
    "valid_github_issue_config",
    "make_github_issue",
    "feedback_link",
    "is_likely_spam",
    "is_likely_spam_from_genai",
    "prefill_github_issue_url",
]
USERNAME = get_config("github issues", {}).get("username")


def _get_token() -> Optional[str]:
    return (get_config("github issues") or {}).get("token")


def _get_allowed_repo_owners() -> List[str]:
    github_config = get_config("github issues") or {}
    repo_owners = github_config.get("allowed repository owners")
    if not repo_owners:
        default_owner = github_config.get("default reporitory owner")
        repo_owners = [default_owner] if default_owner else []
    if not repo_owners:
        repo_owners = ["suffolklitlab", "suffolklitlab-issues"]
    return [owner.lower() for owner in repo_owners]


def valid_github_issue_config():
    return bool(_get_token())


def feedback_link(
    user_info_object: Optional[Any] = None,
    i: Optional[str] = None,
    github_repo: Optional[str] = None,
    github_user: Optional[str] = None,
    variable: Optional[str] = None,
    question_id: Optional[str] = None,
    package_version: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """
    Constructs a URL that when visited will open the feedback interview with the correct context, including
    the destination repository for the feedback and information about the user's current position in the interview.

    The feedback interview needs to know the URL to the github repository where the feedback will be made, and
    uses a few alternative methods to determine the two components of that url - the owner of the repository and the name of the repository.
    For example, suppose you want to see the issues when you visit https://github.com/suffolklitlab/docassemble-AssemblyLine/issues:

    To determine the feedback destination repository's name, e.g., docassemble-AssemblyLine:

    1. It tries using the output of current_context() (formerly user_info()), if passed as the user_info_object parameter,
       to retrieve the package's name. It also tries to get the variable, question_id,
       filename, and session ID from the user_info_object. Note if you want to test the feedback from during development, the package name is not available
       when running from the playground.
    2. It uses the value of the github_repo parameter.
    3. It defaults to the demo repository on the suffolklitlab-issues organization.

    To determine the feedback destination repository's owner, e.g., suffolklitlab:

    1. It uses the value of the github_user parameter.
    2. It tries to get the default repository owner from the Docassemble config, at github issues: default repository owner.
    3. It defaults to suffolklitlab-issues.

    The variable, question_id, package_version, and filename parameters can also be passed in manually rather than retrieved from the
    user_info_object parameter.

    Args:
        user_info_object (str, optional): the output of the current_context() function, which might contain enough information to create the link.
                                          (Name is historical as the current_context() function replaces the former user_info() function)
        i (str, optional): path to the feedback interview file, e.g., docassemble.GithubFeedbackForm:feedback.yml
        github_repo (str, optional): GitHub repository name where issue feedback will be made. E.g, docassemble-AssemblyLine
        github_user (str, optional): GitHub user or organization name where issue feedback will be made. E.g, suffolklitlab
        variable (str, optional): the variable name that the feedback is about
        question_id (str, optional): the question ID that the feedback is about
        package_version (str, optional): the version of the package that the feedback is about
        filename (str, optional): the YAML interview filename that the feedback is about

    Returns:
        str: a URL to the feedback form that includes the public URL parameters for the feedback interview

    Example:
        feedback_link(current_context(), i="docassemble.GithubFeedbackForm:feedback.yml") # github_user is taken from the config and github_repo inferred from output of current_context()

        The package name isn't available from the user_info_object when you run from the playground, so it is better to pass in the github_repo parameter manually
        for better interactive testing:

        feedback_link(current_context(), github_repo="docassemble-AssemblyLine", github_user="suffolklitlab", variable="my_variable", question_id="my_question", package_version="1.0.0", filename="my_file.py", i="docassemble.GithubFeedbackForm:feedback.yml")
    """
    if user_info_object:
        package_name = str(user_info_object.package)
        # TODO: maybe we can use the packages table or /api/packages to get the exact GitHub URL, which would include the owner
        if package_name and not package_name.startswith("docassemble-playground"):
            _github_repo = package_name.replace(".", "-")
        else:
            _github_repo = "demo"  # default repo on GitHub of suffolklitlab-issues/demo for documentation purposes
        _variable = user_info_object.variable
        _question_id = user_info_object.question_id
        _filename = user_info_object.filename
        try:
            _package_version = str(
                importlib.import_module(user_info_object.package).__version__
            )
        except:
            _package_version = "playground"
        if get_config("github issues", {}).get("default repository owner"):
            _github_user = get_config("github issues", {}).get(
                "default repository owner"
            )
        _session_id = user_info_object.session
    else:
        _session_id = None

    # Allow keyword params to override any info from the current_context() object
    # We will try pulling the repo owner name from the Docassemble config
    if github_repo and github_user:
        _github_repo = github_repo
        _github_user = github_user
    elif (
        get_config("github issues", {}).get("default repository owner") and github_repo
    ):
        log(
            "No github_user provided, using default repository owner from config to get the feedback"
        )
        _github_user = get_config("github issues", {}).get("default repository owner")
        _github_repo = github_repo
    else:
        _github_repo = "demo"
        _github_user = "suffolklitlab-issues"
        log(
            "No github_repo provided, using default demo repository to get the feedback"
        )
    if variable:
        _variable = variable
    if question_id:
        _question_id = question_id
    if package_version:
        _package_version = package_version
    if filename:
        _filename = filename

    if not i:
        i = "docassemble.GithubFeedbackForm:feedback.yml"
        log("No feedback interview file provided, using default feedback interview")

    return interview_url(
        i=i,
        github_repo=_github_repo,
        github_user=_github_user,
        variable=_variable,
        question_id=_question_id,
        package_version=_package_version,
        filename=_filename,
        session_id=_session_id,
        local=False,
        reset=1,
    )


def is_likely_spam_from_genai(
    body: Optional[str],
    context: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    model="gemini-2.0-flash-exp",
) -> bool:
    """
    Check if the body of the issue is likely spam with the help of Google Gemini Flash experimental.

    Args:
        body (Optional[str]): the body of the issue
        context (Optional[str]): the context of the issue to help rate it as spam or not, defaults to a guided interview in the legal context
        gemini_api_key (Optional[str]): the API key for the Google Gemini Flash API, can be specified in the global config as `google gemini api key`
        model (Optional[str]): the model to use for the spam detection, defaults to "gemini-2.0-flash-exp", can be specified in the global config
            as `github issues: spam model`
    """
    if not body:
        return False

    model = model or get_config("github issues", {}).get(
        "spam model", "gemini-2.0-flash-exp"
    )
    gemini_api_key = gemini_api_key or get_config("google gemini api key")

    if not gemini_api_key:  # not passed as a parameter OR in the global config
        log("Not using Google Gemini Flash to check for spam: no API key provided")
        return False

    if context is None:  # empty string is a valid input
        context = "a guided interview in the legal context"

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(
            model_name=model,
            system_instruction=f"""
                You are reviewing a feedback form for {context}. Your job is to allow as many
                relevant feedback responses as possible while filtering out irrelevant and spam feedback,
                especially targeted advertising that isn't pointing out a problem on the guided interview.

                Rate the user's feedback as 'spam' or 'not spam' based on the context of the guided interview.
                Answer only with the exact keywords: 'spam' or 'not spam'.
                """,
        )

        response = model.generate_content(body)
        if response.text.strip() == "spam":
            return True
    except NameError:
        log(
            f"Error using Google Gemini Flash: the `google.generativeai` module is not available"
        )
    except Exception as e:
        log(f"Error using Google Gemini Flash: {e}")
        return False
    return False


def is_likely_spam(
    body: Optional[str],
    keywords: Optional[List[str]] = None,
    filter_urls: bool = True,
    model: Optional[str] = None,
) -> bool:
    """
    Check if the body of the issue is likely spam based on a set of keywords and URLs.

    Some keywords are hardcoded, but additional keywords can be added to the global config
    or passed as parameters, or both.

    Args:
        body (Optional[str]): the body of the issue
        keywords (Optional[List[str]]): a list of additional keywords that are likely spam, defaults to a set of keywords
            from the global configuration under the `github issues: spam keywords` key
    """

    _urls = ["leadgeneration.com", "leadmagnet.com"]
    _keywords = [
        "100 times more effective",
        "adult dating",
        "backlink",
        "backlinks",
        "binary options",
        "bitcoin investment",
        "cheap hosting",
        "cheap meds",
        "cialis",
        "credit repair fast",
        "earn money online",
        "email me",
        "escort service",
        "forex trading",
        "free gift cards",
        "free trial",
        "get rich quick",
        "increase website traffic",
        "international long distance calling",
        "keep this info confidential",
        "lead feature",
        "lead generation",
        "lottery winner",
        "market your business",
        "nigerian prince",
        "online casino",
        "payment/deposit handler",
        "reliable business representative",
        "remote job opportunity",
        "results are astounding",
        "send an email",
        "seo services",
        "split the funds",
        "turkish bank",
        "unsubscribe",
        "viagra",
        "visit this link",
        "web lead",
        "web visitors",
        "work from home",
        "your late relative",
    ]

    if not keywords:
        keywords = []
    keywords += _keywords + _urls

    keywords += get_config("github issues", {}).get("spam keywords", [])

    if not body:
        return False
    body = body.lower()
    if any([keyword in body for keyword in keywords]):
        return True

    if filter_urls:
        url_regex = re.compile(r"(https?:\/\/[^\s]+)", flags=re.IGNORECASE)
        if re.search(url_regex, body):
            return True

    return is_likely_spam_from_genai(body, model=model)


def prefill_github_issue_url(
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    template=None,
    title=None,
    body=None,
    label=None,
) -> Optional[str]:
    """
    Makes a URL that when visited, pre-fills part of the Github issue. It doesn't automatically make a Github issue for you.

    template - the docassemble template for the github issue. Overrides `title` and `body` if provided.
    title - the title for the github issue
    body - the body of the github issue
    """
    if not repo_owner:
        repo_owner = (
            get_config("github issues", {}).get("default repository owner")
            or "suffolklitlab"
        )
    if not repo_name:
        repo_name = "docassemble-AssemblyLine"  # TODO(brycew): should this be the default repo? it is in `feedback.yml`
    # TODO(brycew): this function doesn't make issues: do we still want to prevent making URLs for other repos?
    if repo_owner.lower() not in _get_allowed_repo_owners():
        log(
            f"Error creating issue: this form is not permitted to add issues to repositories owned by {repo_owner}. Check your config and see https://github.com/SuffolkLITLab/docassemble-GithubFeedbackForm#getting-started"
        )
        return None

    if template:
        title = template.subject
        body = template.content

    payload = {"title": title, "body": body}
    url_params = urlencode(payload, quote_via=quote_plus)

    return f"https://github.com/{repo_owner}/{repo_name}/issues/new?{url_params}"


def make_github_issue(
    repo_owner: str,
    repo_name: str,
    template=None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    label: Optional[str] = None,
) -> Optional[str]:
    """
    Create a new GitHub issue and return the URL.

    Args:
        template: a docassemble template that overrides `title` and `body`
        title: the title for the GitHub issue
        body: the body of the GitHub issue
        label: optional label to add *if* we can verify or create it

    At least one of template, title, and body is required.

    Returns:
        str, the URL for the label if it exists, or None if the issue could not be created
    """
    make_issue_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

    # Abort early if the configuration or repo owner is invalid
    if not valid_github_issue_config():
        log(
            "Error creating issue: No valid GitHub token provided. "
            "See https://github.com/SuffolkLITLab/docassemble-GithubFeedbackForm#getting-started"
        )
        return None
    if repo_owner.lower() not in _get_allowed_repo_owners():
        log(
            f"Error creating issue: repositories owned by {repo_owner} are not permitted. "
            "See https://github.com/SuffolkLITLab/docassemble-GithubFeedbackForm#getting-started"
        )
        return None

    headers = {
        "Authorization": f"token {_get_token()}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Abort early for private repos
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    repo_resp = requests.get(repo_url, headers=headers)

    if repo_resp.status_code != 200:
        log(
            f"Cannot access repo {repo_owner}/{repo_name}: "
            f"{repo_resp.status_code} {repo_resp.text}. Maybe it is a private repo?"
            "Check that the PAT has the correct scopes and that the user can write to the repo."
        )
        return None

    # ------------------------------------------------------------------
    # 1. Figure out whether we can safely apply the label
    # ------------------------------------------------------------------
    apply_label = False  # only set to True when we're sure it exists

    if label:
        make_labels_url = (
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/labels"
        )
        get_labels_url = f"{make_labels_url}/{label}"
        has_label_resp = requests.get(get_labels_url, headers=headers)

        if has_label_resp.status_code == 200:
            # Label already exists in the repo
            apply_label = True

        elif has_label_resp.status_code == 404:
            # Try to create the label; this may fail if the token lacks permission
            label_data = {
                "name": label,
                "description": "Feedback from a Docassemble Interview",
                "color": "002E60",
            }
            make_label_resp = requests.post(
                make_labels_url,
                data=json.dumps(label_data),
                headers=headers,
            )
            if make_label_resp.status_code == 201:
                log(
                    f"Created the '{label}' label for the "
                    f"{repo_owner}/{repo_name} repository"
                )
                apply_label = True
            else:
                log(
                    f"Could not create label '{label}': {make_label_resp.status_code} "
                    f"{make_label_resp.text}"
                )
        else:
            # 403, 422, etc. → most likely a permissions issue; skip using the label
            log(
                f"Unable to verify label '{label}': {has_label_resp.status_code} "
                f"{has_label_resp.text}"
            )

    # ------------------------------------------------------------------
    # 2. Derive title/body from a template, if supplied
    # ------------------------------------------------------------------
    if template:
        if hasattr(template, "subject"):
            title = template.subject
        if hasattr(template, "body"):
            body = template.content

    if not title and not body:
        return None

    if not body:
        body = ""

    if not title:
        title = "User feedback"

    # Reject obvious spam before calling GitHub
    if is_likely_spam(body):
        log("Error creating issue: the body of the issue was classified as spam")
        return None

    # ------------------------------------------------------------------
    # 3. Assemble and POST the issue
    # ------------------------------------------------------------------
    data: Dict[str, Union[str, List[str]]] = {
        "title": title,
        "body": body,
    }
    if apply_label and label is not None:
        data["labels"] = [label]

    response = requests.post(make_issue_url, data=json.dumps(data), headers=headers)

    if response.status_code == 201:
        return response.json().get("html_url")
    else:
        log(f'Could not create issue "{title}": {response.status_code} {response.text}')
        return None
