from datetime import datetime, timedelta
import requests
import json


def convert_date(x):
    if x is None:
        return None

    return datetime.strptime(x.split(".")[0], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)

key = '3cee3147dab5e03add45994b5b88b864'
token = '7924a454c6c474f402b864006d30be1e2565a5400bd1c588cea8ea9a6d33462f'

boardId = '8rVqywnB'

url = "https://api.trello.com/1/boards/{}/members".format(boardId)
response = requests.request("GET", url, params={"key": key, "token": token}).json()

board_users = {}
board_projects = {}

for r in response:
    if 'fullname' in r:
        board_users[r['id']] = r['fullname']
    else: 
        board_users[r['id']] = r['username']

board = {
    # 'Sample Person': {
    #     'sample month': {
    #         'cards': [],
    #         'comments': []
    #     }
    # }
}

projects = {
    # 'Sample project': {
    #     'sample month': {
    #         'cards': [],
    #         'comments': []
    #     }
    # }
}

current_month = "{}-{}".format(datetime.now().month, datetime.now().year)

for user_id, user_name in board_users.items():
    if user_name not in board:
        board[user_id] = {
            current_month: {
                'cards': [],
                'comments': [],
                'delete': 0
            }
        }
    else:
        board[user_id][current_month] = {
            'cards': [],
            'comments': [],
            'delete': 0
        }


url = "https://api.trello.com/1/boards/{}/lists".format(boardId)
querystring = {"cards": "all", "card_fields": "all", "filter": "open", "fields": "all", "key": key, "token": token}
lists = requests.request("GET", url, params=querystring).json()

for l in lists:
    list_id = l['id']
    list_name = l['name']
    print(list_name, list_id)

    board_projects[list_id] = list_name
    
    if list_name not in projects:
        projects[list_id] = {
            current_month: {
                'cards': [],
                'comments': []
            }
        }
    else:
        projects[list_id][current_month] = {
                'cards': [],
                'comments': []
            }

    url = "https://api.trello.com/1/lists/{}/actions".format(list_id)
    list_actions = requests.request("GET", url, params={"key": key, "token": token, "filter": 'all'}).json()

    cards = {
        # card_id: {
        #     'score': score,
        #     'name': card['name'],
        #     'description': card['desc'],
        #     'complete': card['dueComplete'],
        #     'change_due_date': [],
        #     'miss_due_date': [],
        #     'members': []
        # }
    }

    for a in list_actions[::-1]:
        date = convert_date(a['date'])
        if date.month != datetime.now().month or date.year != datetime.now().year:
            continue

        creator = a['idMemberCreator']
        
        if a['type'] == 'createCard':
            card_id = a['data']['card']['id']
            card_name = a['data']['card']['name']
            cards[card_id] = {
                'name': card_name,
                'description': "",
                'complete': False,
                'change_due_date': [],
                'miss_due_date': [],
                'members': [creator]
            }

        elif a['type'] == 'updateCard':
            card_id = a['data']['card']['id']

            if 'desc' in a['data']['old']:
                cards[card_id]['description'] = a['data']['old']['desc']
            
            if 'dueComplete' in a['data']['old']:
                cards[card_id]['complete'] = a['data']['old']['dueComplete']

            if 'due' in a['data']['old']:
                # related to due date
                if a['data']['old']['due'] is not None:
                    # change due date
                    new_date = convert_date(a['data']['card']['due'])
                    old_date = convert_date(a['data']['old']['due'])

                    if old_date < date:
                        # miss deadline
                        cards[card_id]['miss_due_date'].append([str(old_date), str(new_date), str(date)])
                    else:
                        cards[card_id]['change_due_date'].append([str(old_date), str(new_date), str(date)])

                else:
                    # create due date
                    pass

        elif a['type'] == 'commentCard':
            card_id = a['data']['card']['id']
            board[creator][current_month]['comments'].append([card_id, a['data']['text']])
            projects[list_id][current_month]['comments'].append([creator, card_id, a['data']['text']])

    for card_id, _ in cards.items():
        print(cards[card_id])
        url = "https://api.trello.com/1/cards/{}/".format(card_id)
        response = requests.request("GET", url, params={"key": key, "token": token, "fields": 'all'})

        if response.status_code == 404:
            # card has been deleted
            for user_id in cards[card_id]['members']:
                board[user_id][current_month]['delete'] += 1

            continue

        card_info = response.json()

        score = 0
        for label in card_info['labels']:
            score += int(label['name'].split(" ")[0])

        cards[card_id]['score'] = score

        if not card_info['dueComplete']:
            if card_info['due'] is not None:
                due = convert_date(card_info['due'])
                if due < datetime.now():
                    cards[card_id]['miss_due_date'].append([1])
            else:
                # there is no due date yet
                pass

        for user_id in cards[card_id]['members']:
            board[user_id][current_month]['cards'].append(cards[card_id])

        projects[list_id][current_month]['cards'].append(cards[card_id])

        print(cards[card_id])

print("USER")    
for user_id, user_data in board.items():
    print(board_users[user_id])
    for month, monthly_data in user_data.items():
        print("[{}]".format(month))
        total_score = 0
        total_change_due_date = 0
        total_miss_due_date = 0
        total_comments = len(monthly_data['comments'])
        
        for card in monthly_data['cards']:
            if card['complete'] and card['description'] != '':
                total_score += card['score']
            total_change_due_date += len(card['change_due_date'])
            total_miss_due_date += len(card['miss_due_date'])
        
        print("score:\t{}\nchange_due_date:\t{}\nmiss_due_date:\t{}\ncomments:\t{}\ndelete:\t{}".format(total_score, total_change_due_date, total_miss_due_date, total_comments, monthly_data['delete']))
        
    print("-"*20)

print("\nPROJECTS")
for pro_id, pro_data in projects.items():
    print(board_projects[pro_id])
    for month, monthly_data in pro_data.items():
        print("[{}]".format(month))
        total_score = 0
        total_change_due_date = 0
        total_miss_due_date = 0
        total_comments = len(monthly_data['comments'])
        for card in monthly_data['cards']:
            if card['complete'] and card['description'] != '':
                total_score += card['score']
            total_change_due_date += len(card['change_due_date'])
            total_miss_due_date += len(card['miss_due_date'])
        
        print("score:\t{}\nchange_due_date:\t{}\nmiss_due_date:\t{}\ncomments:\t{}".format(total_score, total_change_due_date, total_miss_due_date, total_comments))
        
    print("-"*20)

# with open('visiai.json', 'w') as outfile:
#     json.dump(board, outfile)

