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


def get_board(trello, board_name):
    for b in trello.list_boards():
        if b.name == board_name or b.url.endswith(board_name):
            return b

    raise BoardNotFound(board_name)

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

    for cl in card.fetch_checklists():
        for cli in cl.items:
            name = cli['name']
            issue = get_issue(repo, name, milestone=card.name)
            if issue and 'https://github.com' not in name:
                print('\t - {} linking to Github'.format(name))
                cl.rename_checklist_item(name, '{} {}'.format(name, issue.html_url))
                continue

            print('\t - ', name)
            try:
                created_at = card.create_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            except IndexError:
                created_at = None

            description = '# [{}]({})'.format(card.name, card.short_url)
            issue = repo.import_issue(cli['name'], description, created_at, milestone=milestone.number, labels=labels)

            cl.rename_checklist_item(name, '{} {}'.format(name, issue.html_url))
    print('')
    return milestone


def connect(repo_name):
    trello = TrelloClient(TRELLO_API_KEY, token=TRELLO_API_TOKEN)
    repo = login(GITHUB_USER, GITHUB_PASSWORD).repository(*repo_name.split('/', 1))

    return trello, repo


def convert_list(repo_name, board_name, list_name, labels=None):
    trello, repo = connect(repo_name)

    board = get_board(trello, board_name)
    tlist = get_list(trello, board, list_name)

    for card in tlist.list_cards():
        card.fetch()
        create_milestone_for_card(repo, card, labels=labels)


def convert_card(repo, card, labels=None):
    card.fetch()
    create_milestone_for_card(repo, card, labels=labels)


def listflow(*args):
    """
        listflow board list user/repo [labels]
    """
    if len(args) < 4:
        print(args)
        print(listflow.__doc__)
        sys.exit(1)

    board_name = args[0]
    list_name = args[1]
    repo_name = args[2]
    labels = args[3:]

    convert_list(repo_name, board_name, list_name, labels)


def cardflow(*args):
    """
        cardflow card user/repo [labels]
    """
    if len(args) < 5:
        print(cardflow.__doc__)
        sys.exit(1)

    board_name = args[0]
    list_name = args[1]
    card_name = args[2]
    repo_name = args[3]
    labels = args[4:]

    trello, repo = connect(repo_name)

    board = get_board(trello, board_name)
    tlist = get_list(trello, board, list_name)
    for c in tlist.list_cards():
        if c.name == card_name:
            convert_card(repo, c, labels)
            break


if __name__ == '__main__':
#    listflow(*sys.argv[1:])
    cardflow(*sys.argv[1:])
