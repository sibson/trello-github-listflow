import os
import sys

from trello import TrelloClient
from trello.util import create_oauth_token
from github3 import login


# https://trello.com/app-key
TRELLO_API_KEY = os.environ['TRELLO_API_KEY']
TRELLO_API_SECRET = os.environ['TRELLO_API_SECRET']
TRELLO_TOKEN = os.environ.get('TRELLO_TOKEN') or create_oauth_token(expiration='1day', scope='read')

GITHUB_USER = os.environ['GITHUB_USER']
GITHUB_PASSWORD = os.environ['GITHUB_PASSWORD']


def get_board(trello, board_name):
    for b in trello.list_boards():
        if b.name == board_name:
            return b


def get_list(trello, board, list_name):
    for l in board.open_lists():
        if l.name == list_name:
            return l


def get_milestone(repo, title):
    for m in repo.iter_milestones(state='open'):
        if m.title == title:
            return m


def get_issue(repo, title, milestone=None):
    for i in repo.issues(milestone=milestone):
        if i.title == title:
            return i


def create_milestone_for_card(repo, card, labels=None):
    print 'Building Milestone', card.name
    milestone = get_milestone(repo, card.name)
    if milestone is None:
        description = '# [{}]({})\n'.format(card.name, card.short_url) + card.description
        milestone = repo.create_milestone(card.name, description=description)

    card.fetch()  # need to fetch otherwise fetch_checklists will fail
    for cl in card.fetch_checklists():
        for cli in cl.items:
            if get_issue(repo, card.name, milestone=milestone):
                continue

            print 'Creating Issue', cli['name']
            description = '# [{}]({})'.format(card.name, card.short_url)
            repo.import_issue(cli['name'], description, card.create_date, milestone=milestone.number, labels=labels)

    return milestone


def convert_list(repo_name, board_name, list_name, labels=None):
    trello = TrelloClient(TRELLO_API_KEY, token=TRELLO_TOKEN)

    board = get_board(trello, board_name)
    tlist = get_list(trello, board, list_name)

    repo = login(GITHUB_USER, GITHUB_PASSWORD).repository(repo_name.split('/', 1))
    for card in tlist.list_cards():
        create_milestone_for_card(repo, card, labels=labels)


def main():
    repo_name = sys.argv[0]
    board_name = sys.argv[1]
    list_name = sys.argv[2]
    labels = sys.argv[3:]
    convert_list(repo_name, board_name, list_name, labels)


if __name__ == '__main__':
    main()
