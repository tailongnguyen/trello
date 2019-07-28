from datetime import datetime
import pandas as pd
import requests
import json

key = '3cee3147dab5e03add45994b5b88b864'
token = '7924a454c6c474f402b864006d30be1e2565a5400bd1c588cea8ea9a6d33462f'

boardId = 'PHaQzsJc'

url = "https://api.trello.com/1/boards/{}/members".format(boardId)
response = json.loads(requests.request("GET", url, params={"key":key,"token":token}).content)
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

for user in list(users.keys()):
    users[user][current_month] = 0 

for card in done_list['cards']:
    last_active = card['dateLastActivity'].split(".")[0]
    date = datetime.strptime(last_active, '%Y-%m-%dT%H:%M:%S')
    
    if date.month != current_month:
        continue
    
    name = card['name']
    score = 0
    for label in card['labels']:
        score += int(label['name'].split(" ")[0])
    
    for user_id in card['idMembers']:
        user = board_users[user_id]
        if user not in users:
            users[user] = {}
            users[user][formated_date] = []

        users[user][formated_date].append([name, score])

for k, v in users.items():
    print("{}:\t{}".format(k, v))
        
with open('visiai.json', 'w') as outfile:
    json.dump(users, outfile)

# Creating a dictionary  
d = {'id':['1', '2', '3'], 
     'Task Name': [], 
     'Description': [], 
     'Column 1.3':[1, 4, 5], 
     'Column 2.1':[1, 2, 3], 
     'Column 2.2':[10, 10, 10], } 
  
# Converting dictionary into a data-frame  
df = pd.DataFrame(d) 
print(df) 