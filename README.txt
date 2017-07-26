ListFlow
============
Convert [Trello](https://trello.com) lists and cards into GitHub issues.

Setup
---------
You will need to [aquire a Trello API key](https://trello.com/app-key) and set the following environment variables

    export TRELLO_API_KEY=
    export TRELLO_API_SECRET=

Then you can run listflow.py and it will ask you to open a link. Copy the PIN into the terminal to get an oauth_token to use as your TRELLO_API_TOKEN.

    export TRELLO_API_TOKEN=

Likewise you will need a [GitHub Token](https://github.com/settings/tokens) and use the token as your GITHUB_PASSWORD

    export GITHUB_USER=
    export GITHUB_PASSWORD=

Finally, you should create a new virtualenv and install the requirements.

    createvenv venv
    pip install -r requirements.txt

Usage
-------
listflow will either import a Trello list or a single card.  Each card will coroposnse to a GitHub milestone and checklists on cards will be converted to Issues.
