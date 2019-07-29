from datetime import datetime, timedelta
import pandas as pd
import requests
import json


def convert_date(x):
    if x is None:
        return None

    return datetime.strptime(x.split(".")[0], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)

key = '3cee3147dab5e03add45994b5b88b864'
token = '7924a454c6c474f402b864006d30be1e2565a5400bd1c588cea8ea9a6d33462f'

boardId = 'PHaQzsJc'

url = "https://api.trello.com/1/boards/{}/members".format(boardId)
response = json.loads(requests.request("GET", url, params={"key": key,"token": token}).content)
board_users = {}
for r in response:
    if 'fullname' in r:
        board_users[r['id']] = r['fullname']
    else: 
        board_users[r['id']] = r['username']

url = "https://api.trello.com/1/boards/{}/lists".format(boardId)

querystring = {"cards":"all","card_fields":"all","filter":"open","fields":"all","key":key, "token":token}

response = requests.request("GET", url, params=querystring).json()
done_list = None
for r in response:
    if r['name'] == 'Done':
        done_list = r
        break

if done_list is None:
    assert("You should have a list named 'Done'")

users = {}
current_month = datetime.now().month
formated_date = "{}-{}".format(current_month, datetime.now().year)

for card in done_list['cards']:
    card_id = card['id']
    print(card_id)
    url = "https://api.trello.com/1/cards/{}/actions".format(card_id)
    card_actions = json.loads(requests.request("GET", url, params={"key": key, "token": token, "filter": 'all'}).content)
    
    for a in card_actions:
        date = convert_date(a['date'])
        if a['type'] == 'createCard':
            created_time = date
            break
    try:
        if created_time.month != datetime.now().month or created_time.year != datetime.now().year:
            continue
    except:
        continue
    
    name = card['name']
    score = 0
    for label in card['labels']:
        score += int(label['name'].split(" ")[0])
    
    for user_id in card['idMembers']:
        user = board_users[user_id]
        if user not in users:
            users[user] = []

        users[user].append([name, score])

cards = {}
for k, v in users.items():
    for card in v:
        if card[0] not in cards:
            cards[card[0]] = {
                'score': card[1],
                'members': [k]
            }
        else:
            cards[card[0]]['members'].append(k)

    # print("{}:\t{}".format(k, v))

# print(cards)
tasks = list(cards.keys())
tmp = {}
tmp['Task'] = [t.replace('\t', " ") for t in tasks]
tmp['Điểm'] = [cards[t]['score'] for t in tasks]
for u in list(users.keys()):
    tmp[u] = [''] * len(tasks)
    for i, t in enumerate(tasks):
        if u in cards[t]['members']:
            tmp[u][i] = 'x'


# Converting dictionary into a data-frame  
df = pd.DataFrame(tmp) 
df.to_excel('blah.xlsx', encoding='utf-8')
# print(df) 