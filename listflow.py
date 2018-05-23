import os
import sys

from trello import TrelloClient
from trello.util import create_oauth_token
from github3 import login


class ListFlowError(Exception):
    """ Base Exception for listflow """

class ConfigurationError(RuntimeError):
    """ Missing environment settings """

class BoardNotFound(ListFlowError):
    """ No matching boards found """

class ListNotFound(ListFlowError):
    """ No matching Lists found """


TRELLO_API_KEY = os.environ.get('TRELLO_API_KEY')
if not TRELLO_API_KEY:
    print('Set TRELLO_API_KEY, from https://trello.com/app-key')
    sys.exit(1)

TRELLO_API_SECRET = os.environ.get('TRELLO_API_SECRET')
if not TRELLO_API_SECRET:
    print('Set TRELLO_API_SECRET from the bottom of https://trello.com/app-key')
    sys.exit(1)

TRELLO_API_TOKEN = os.environ.get('TRELLO_API_TOKEN')
if not TRELLO_API_TOKEN:
    create_oauth_token(expiration='1day', scope='read')


GITHUB_USER = os.environ.get('GITHUB_USER')
GITHUB_PASSWORD = os.environ.get('GITHUB_PASSWORD')
if not GITHUB_USER or not GITHUB_PASSWORD:
    print('Missing GitHub credentials, https://github.com/settings/tokens')
    sys.exit(1)


def get_board(trello, board):
    for b in trello.list_boards():
        if b.id == board:
            return b

        if b.name == board or b.url.endswith(board):
            return b

    raise BoardNotFound(board)

def get_list(trello, board, list_name):
    for l in board.open_lists():
        print(l, l.name, list_name)

        if l.name == list_name:
            return l

    raise ListNotFound(list_name)

def get_milestone(repo, title):
    for m in repo.milestones(state='open'):
        if m.title == title:
            return m


def get_issue(repo, title, milestone=None):
    for i in repo.issues(milestone=milestone):
        if i.title == title:
            return i


def create_milestone_for_card(repo, card, labels=None):
    print('Building Milestone:', card.name)
    milestone = get_milestone(repo, card.name)

    if milestone is None:
        description = '# [{}]({})\n'.format(card.name, card.short_url) + card.description
        milestone = repo.create_milestone(card.name, description=description)

    attachments = [a.name for a in card.get_attachments()]
    for cl in card.fetch_checklists():
        for cli in cl.items:
            name = cli['name']

            issue = get_issue(repo, name, milestone=card.name)
            # issue exists but isn't linked
            if issue and name not in attachments:
                print('\t x ', name)
                card.attach(name, url=issue.html_url)
                cl.delete_checklist_item(name)
                continue

            # existing issue should be skipped
            if issue:
                print('\t - ', name)
                continue

            print('\t + ', name)
            issue = repo.create_issue(name, milestone=milestone.number, labels=labels)
            card.attach(name, url=issue.html_url)
            cl.delete_checklist_item(name)

    print('')
    return milestone


def connect(repo_name):
    trello = TrelloClient(TRELLO_API_KEY, token=TRELLO_API_TOKEN)
    repo = login(GITHUB_USER, GITHUB_PASSWORD).repository(*repo_name.split('/', 1))

    return trello, repo


def convert_list(repo_name, board, list_name, labels=None):
    trello, repo = connect(repo_name)

    board = get_board(trello, board)
    tlist = get_list(trello, board, list_name)

    for card in tlist.list_cards():
        card.fetch()
        create_milestone_for_card(repo, card, labels=labels)


def convert_card(repo, card, labels=None):
    card.fetch()
    create_milestone_for_card(repo, card, labels=labels)


def listflow(*args):
    """
        listflow user/repo board/list [labels]
    """
    if len(args) < 3:
        print(args)
        print(listflow.__doc__)
        sys.exit(1)

    repo_name = args[0]
    board, list_name = args[1].split('/')
    labels = args[2:]

    convert_list(repo_name, board, list_name, labels)


def cardflow(*args):
    """
        cardflow user/repo card_id [labels]
    """
    if len(args) < 2:
        print(cardflow.__doc__)
        sys.exit(1)

    repo_name = args[0]
    card_id = args[1]
    labels = args[2:]

    trello, repo = connect(repo_name)

    card = trello.get_card(card_id)
    convert_card(repo, card, labels)


if __name__ == '__main__':
    if sys.argv[1] == 'list':
        listflow(*sys.argv[2:])
    elif sys.argv[1] == 'card':
        cardflow(*sys.argv[2:])
    else:
        cardflow(*sys.argv[1:])
