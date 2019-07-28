from datetime import datetime, timedelta
import requests
import json

convert_date = lambda x: datetime.strptime(x.split(".")[0], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)

key = '3cee3147dab5e03add45994b5b88b864'
token = '7924a454c6c474f402b864006d30be1e2565a5400bd1c588cea8ea9a6d33462f'

boardId = '8rVqywnB'

url = "https://api.trello.com/1/boards/{}/members".format(boardId)
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


url = "https://api.trello.com/1/boards/{}/lists".format(boardId)
querystring = {"cards": "all", "card_fields": "all", "filter": "open", "fields": "all", "key": key, "token": token}
response = requests.request("GET", url, params=querystring).json()

for r in response:
    list_id = r['id']
    list_name = r['name']

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

        url = "https://api.trello.com/1/cards/{}/actions".format(card_id)
        card_actions = json.loads(requests.request("GET", url, params={"key": key, "token": token, "filter": 'all'}).content)
        
        for a in card_actions:
            date = convert_date(a['date'])
            if a['type'] == 'createCard':
                created_time = date
                creator = a['idMemberCreator']
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
            'miss_due_date': []
        }

        for a in card_actions:
            date = convert_date(a['date'])
            action_creator = a['memberCreator']['id']

            if a['type'] == 'updateCard':
                if action_creator != creator:
                    continue

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
                board[action_creator][current_month]['comments'].append([card_id, a['data']['text']])
                projects[list_id][current_month]['comments'].append([action_creator, card_id, a['data']['text']])

        if not card_info['complete']:
            if card['due'] is not None:
                due = convert_date(card['due'])
                if due < datetime.now():
                    card_info['miss_due_date'].append([1])

        for user_id in card['idMembers']:
            board[user_id][current_month]['cards'].append(card_info)
        
        projects[list_id][current_month]['cards'].append(card_info)

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

# with open('visiai.json', 'w') as outfile:
#     json.dump(board, outfile)

