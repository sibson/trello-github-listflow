import os
import sys

from trello import TrelloClient
from trello.util import create_oauth_token
from github3 import login


class ConfigurationError(Exception):
    pass

TRELLO_API_KEY = os.environ.get('TRELLO_API_KEY')
if not TRELLO_API_KEY:
    raise ConfigurationError('Get a API KEY from https://trello.com/app-key')

TRELLO_API_SECRET = os.environ.get('TRELLO_API_SECRET')
if not TRELLO_API_SECRET:
    raise ConfigurationError('Get an OAUTH SECRET from https://trello.com/app-key')

TRELLO_API_TOKEN = os.environ.get('TRELLO_API_TOKEN')
if not TRELLO_API_TOKEN:
    create_oauth_token(expiration='1day', scope='read')


GITHUB_USER = os.environ.get('GITHUB_USER')
GITHUB_PASSWORD = os.environ.get('GITHUB_PASSWORD')
if not GITHUB_USER or not GITHUB_PASSWORD:
    raise ConfigurationError('Missing GitHub credentials, https://github.com/settings/tokens')


def get_board(trello, board_name):
    for b in trello.list_boards():
        if b.name == board_name or b.url.endswith(board_name):
            return b


def get_list(trello, board, list_name):
    for l in board.open_lists():
        if l.name == list_name:
            return l


def get_milestone(repo, title):
    for m in repo.milestones(state='open'):
        if m.title == title:
            return m


def get_issue(repo, title, milestone=None):
    for i in repo.issues(milestone=milestone):
        if i.title == title:
            return i


def create_milestone_for_card(repo, card, labels=None):
    print 'Building Milestone:', card.name
    milestone = get_milestone(repo, card.name)

    if milestone is None:
        description = '# [{}]({})\n'.format(card.name, card.short_url) + card.description
        milestone = repo.create_milestone(card.name, description=description)

    for cl in card.fetch_checklists():
        for cli in cl.items:
            if get_issue(repo, card.name, milestone=card.name):
                continue

            print '\t - ', cli['name']
            try:
                created_at = card.create_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            except IndexError:
                created_at = None

            description = '# [{}]({})'.format(card.name, card.short_url)
            repo.import_issue(cli['name'], description, created_at, milestone=milestone.number, labels=labels)

    print ''
    return milestone


def convert_list(repo_name, board_name, list_name, labels=None):
    trello = TrelloClient(TRELLO_API_KEY, token=TRELLO_API_TOKEN)

    board = get_board(trello, board_name)
    tlist = get_list(trello, board, list_name)

    repo = login(GITHUB_USER, GITHUB_PASSWORD).repository(*repo_name.split('/', 1))
    for card in tlist.list_cards():
        card.fetch()
        create_milestone_for_card(repo, card, labels=labels)


def usage():
    print 'listflow board list user/repo [labels]'


def main():
    if len(sys.argv) < 4:
        usage()
        sys.exit(1)

    board_name = sys.argv[1]
    list_name = sys.argv[2]
    repo_name = sys.argv[3]
    labels = sys.argv[4:]

    convert_list(repo_name, board_name, list_name, labels)


if __name__ == '__main__':
    main()
