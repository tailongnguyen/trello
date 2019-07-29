from datetime import datetime, timedelta
import requests
import json
import pandas as pd

def convert_date(x):
    if x is None:
        return None

    return datetime.strptime(x.split(".")[0], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)

key = '3cee3147dab5e03add45994b5b88b864'
token = '7924a454c6c474f402b864006d30be1e2565a5400bd1c588cea8ea9a6d33462f'

board_id = '8rVqywnB'

url = "https://api.trello.com/1/boards/{}/members".format(board_id)
response = json.loads(requests.request("GET", url, params={"key": key, "token": token}).content)

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
                'comments': []
            }
        }
    else:
        board[user_id][current_month] = {
            'cards': [],
            'comments': []
        }

current_month_cards = []

url = "https://api.trello.com/1/boards/{}/lists".format(board_id)
querystring = {"cards": "all", "card_fields": "all", "filter": "open", "fields": "all", "key": key, "token": token}
response = requests.request("GET", url, params=querystring).json()

for r in response:
    list_id = r['id']
    list_name = r['name']
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

    for card in r['cards']:
        card_id = card['id']
        print(card['name'])

        url = "https://api.trello.com/1/cards/{}/actions".format(card_id)
        card_actions = json.loads(requests.request("GET", url, params={"key": key, "token": token, "filter": 'all'}).content)
        
        for a in card_actions:
            date = convert_date(a['date'])
            if a['type'] == 'createCard':
                created_time = date
                break
        
        if created_time.month != datetime.now().month or created_time.year != datetime.now().year:
            continue
    
        score = 0
        for label in card['labels']:
            score += int(label['name'].split(" ")[0])

        card_info = {
            'score': score,
            'name': card['name'],
            'description': card['desc'],
            'complete': card['dueComplete'],
            'change_due_date': [],
            'miss_due_date': [],
            'members': card['idMembers']
        }

        for a in card_actions:
            print(a['type'])
            date = convert_date(a['date'])
            creator = a['idMemberCreator']

            if a['type'] == 'updateCard':
                if 'due' in a['data']['old']:
                    # related to due date
                    if a['data']['old']['due'] is not None:
                        # change due date
                        new_date = convert_date(a['data']['card']['due'])
                        old_date = convert_date(a['data']['old']['due'])

                        if old_date < date:
                            # miss deadline
                            card_info['miss_due_date'].append([str(old_date), str(new_date), str(date)])
                        else:
                            card_info['change_due_date'].append([str(old_date), str(new_date), str(date)])

                    else:
                        # create due date
                        pass

            elif a['type'] == 'commentCard':
                board[creator][current_month]['comments'].append([card_id, a['data']['text']])
                projects[list_id][current_month]['comments'].append([creator, card_id, a['data']['text']])

        if not card_info['complete']:
            if card['due'] is not None:
                due = convert_date(card['due'])
                if due < datetime.now():
                    card_info['miss_due_date'].append([1])

        for user_id in card['idMembers']:
            board[user_id][current_month]['cards'].append(card_info)
        
        projects[list_id][current_month]['cards'].append(card_info)
        current_month_cards.append(card_info)

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
        
        print("score:\t{}\nchange_due_date:\t{}\nmiss_due_date:\t{}\ncomments:\t{}".format(total_score, total_change_due_date, total_miss_due_date, total_comments))
        
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


df1 = {}
df1['Task'] = [''] + [card['name'] for card in current_month_cards]
df1['Điểm'] = [''] + [card['score'] for card in current_month_cards]
for user_id, user_name in board_users.items():
    if user_name in df1:
        user_name = user_name + '(1)'

    df1[user_name] = [''] * len(current_month_cards)
    total_score = 0
    for i, t in enumerate(current_month_cards):
        if user_id in current_month_cards[i]['members']:
            df1[user_name][i] = 'x'
            if current_month_cards[i]['complete'] and current_month_cards[i]['description'] != '':
                total_score += current_month_cards[i]['score']
    df1[user_name] = [total_score] + df1[user_name]

df2 = {
    '': ['total score', 'change due date', 'miss due date', 'comments']
}

for user_id, user_data in board.items():
    user_name = board_users[user_id]
    if user_name in df2:
        user_name = user_name + '(1)'
    
    monthly_data = user_data[current_month]

    total_score = 0
    total_change_due_date = 0
    total_miss_due_date = 0
    total_comments = len(monthly_data['comments'])
    
    for card in monthly_data['cards']:
        if card['complete'] and card['description'] != '':
            total_score += card['score']
        total_change_due_date += len(card['change_due_date'])
        total_miss_due_date += len(card['miss_due_date'])

    df2[user_name] = [total_score, total_change_due_date, total_miss_due_date, total_comments]

df3 = {
    '': ['total score', 'change due date', 'miss due date', 'comments']
}

for pro_id, pro_data in projects.items():
    pro_name = board_projects[pro_id]
    if pro_name in df3:
        pro_name = pro_name + '(1)'
    
    monthly_data = pro_data[current_month]

    total_score = 0
    total_change_due_date = 0
    total_miss_due_date = 0
    total_comments = len(monthly_data['comments'])
    
    for card in monthly_data['cards']:
        if card['complete'] and card['description'] != '':
            total_score += card['score']
        total_change_due_date += len(card['change_due_date'])
        total_miss_due_date += len(card['miss_due_date'])

    df3[pro_name] = [total_score, total_change_due_date, total_miss_due_date, total_comments]
    
with pd.ExcelWriter('{}.xlsx'.format(board_id)) as writer:
    pd.DataFrame(df1).to_excel(writer, encoding='utf-8', sheet_name='tasks')
    pd.DataFrame(df2).to_excel(writer, encoding='utf-8', sheet_name='users')
    pd.DataFrame(df3).to_excel(writer, encoding='utf-8', sheet_name='projects')


with open('{}.json'.format(board_id), 'w') as outfile:
    json.dump(board, outfile, indent=4)

