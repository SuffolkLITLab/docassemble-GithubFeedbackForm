import os
import sys
from setuptools import setup, find_packages
from fnmatch import fnmatchcase
from distutils.util import convert_path

standard_exclude = ('*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info')
def find_package_data(where='.', package='', exclude=standard_exclude, exclude_directories=standard_exclude_directories):
    out = {}
    stack = [(convert_path(where), '', package)]
    while stack:
        where, prefix, package = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                        stack.append((fn, '', new_package))
                else:
                    stack.append((fn, prefix + name + '/', package))
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out

setup(name='docassemble.GithubFeedbackForm',
      version='0.0.1',
      description=('A docassemble extension.'),
      long_description='# docassemble.GithubFeedbackForm\r\n\r\nA package to gather feedback and then submit issues to Github.\r\n\r\n  \r\n1. Create a new GitHub user and create a personal access token on it. It does\r\n not need any special permissions; optionally, you can limit it. It will\r\n need to be able to make pull requests on the repos you want to add issues\r\n to. Public repos usually leave pull access open.\r\n2. Edit your config, and create a block like this:\r\n\r\n```yaml\r\ngithub issues:\r\n  username: "YOUR_NEW_DEDICATED_ISSUE_CREATION_ACCOUNT"\r\n  token: "..." # A valid GitHub personal access token associated with the username above\r\n  default repository owner: YOUR_GITHUB_USER_OR_ORG_HERE\r\n  allowed repository owners: # List the repo that your account will be allowed to create issues on\r\n    - YOUR_GITHUB_USER_OR_ORG_HERE \r\n    - SECOND_GITHUB_USER_OR_ORG\r\n```\r\n\r\n  Note that it is important to provide a list of allowed repository owners.\r\n  This is used to prevent your form from being used to spam GitHub \r\n  repositories with feedback.\r\n3. Add a link on each page, in the footer or `under` area.  \r\n   You can use the `feedback_link()` function to add a link, like this:\r\n   `[:comment-dots: Feedback](${ feedback_link(user_info()) } ){:target="_blank"}`\r\n   \r\n   Optional parameters:\r\n    - `i`: the feedback form, like: docassemble.AssemblyLine:feedback.yml\r\n    - `github_repo`: repo name, like: docassemble-AssemblyLine\r\n    - `github_user`: owner of the repo, like: suffolklitlab\r\n    - `variable`: variable being sought, like: intro\r\n    - `question_id`:  id of the current question, like: intro\r\n    - `package_version`: version number of the current package\r\n    - `filename`: filename of the interview the user is providing feedback on.\r\n    \r\n    Each has a sensible default. Most likely, you will limit your custom\r\n    parameters to the `github_repo` if you want feedback links to work\r\n    from the docassemble playground.\r\n4. Optionally, create your own feedback.yml file. It should look like this,\r\n   with whatever customizations you choose:\r\n\r\n```yaml\r\ninclude:\r\n  - docassemble.GithubFeedbackForm:feedback.yml\r\n---\r\ncode: |\r\n  al_feedback_form_title = "Your title here"  \r\n---\r\ncode: |\r\n  # This email will be used ONLY if there is no valid GitHub config\r\n  al_error_email = "your_email@yourdomain.com"\r\n---\r\ntemplate: al_how_to_get_legal_help\r\ncontent: |\r\n  If you need more help, these are free resources:\r\n\r\n  ... [INCLUDE STATE-SPECIFIC RESOURCES]      \r\n```\r\n\r\nYou may also want to customize the metadata: title, exit url and override \r\nany specific questions, add a logo, etc.    \r\n\r\n## Author\r\n\r\nQuinten Steenhuis, qsteenhuis@suffolk.edu',
      long_description_content_type='text/markdown',
      author='System Administrator',
      author_email='admin@admin.com',
      license='The MIT License (MIT)',
      url='https://docassemble.org',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=['docassemble.MAVirtualCourt>=1.0.22'],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/GithubFeedbackForm/', package='docassemble.GithubFeedbackForm'),
     )

