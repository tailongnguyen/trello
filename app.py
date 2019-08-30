from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_cors import CORS
from datetime import datetime, timedelta

import signal
import sys, os
import requests
import json
import pandas as pd

def convert_date(x):
    if x is None:
        return None

    return datetime.strptime(x.split(".")[0], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)

app = Flask(__name__)
CORS(app)
   
def exit_signal_handler(sig, frame):
    print('You pressed Ctrl+C.')
    sys.exit()


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# @app.route('/get_file', methods=['GET'])
# def get_file():
#     return send_file("8rVqywnB.xlsx", as_attachment=True)

@app.route('/process/<lists_ids>-<key>-<token>-<board_id>', methods=['GET'])
def process(lists_ids, key, token, board_id):
    lists = lists_ids.split("_")

    url = "https://api.trello.com/1/boards/{}/members".format(board_id)
    response = json.loads(requests.request("GET", url, params={"key": key, "token": token}).content)

    if os.path.isfile("{}.json".format(board_id)):
        board_all = json.load(open("{}.json".format(board_id)))
    else:
        board_all = {
            'users': {
                # 'Sample Person': {
                #     'sample month': {
                #         'cards': [],
                #         'comments': []
                #     }
                # }
            },
            'projects': {
                # 'Sample project': {
                #     'sample month': {
                #         'cards': [],
                #         'comments': []
                #     }
                # }
            }
        }

    board_users = {}
    board_projects = {}

    for r in response:
        if 'fullname' in r:
            board_users[r['id']] = r['fullname']
        else: 
            board_users[r['id']] = r['username']

    users = board_all['users']
    projects = board_all['projects']

    current_month = "{}-{}".format(datetime.now().month, datetime.now().year)
    for user_id, user_name in board_users.items():
        if user_name not in users:
            users[user_id] = {
                current_month: {
                    'cards': [],
                    'comments': []
                }
            }
        else:
            users[user_id][current_month] = {
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
        board_projects[list_id] = list_name

        if list_id not in lists:
            continue

        print(list_name, list_id)
        
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
            
            created_time = None
            for a in card_actions:
                date = convert_date(a['date'])
                if a['type'] == 'createCard':
                    created_time = date
                    break
            if created_time is None:
                # card is deleted
                continue
                        
            if created_time.month != datetime.now().month or created_time.year != datetime.now().year:
                continue
        
            score = 0
            for label in card['labels']:
                score += int(label['name'].split(" ")[0])

            card_info = {
                'score': score,
                'name': '{}_{}'.format(list_name, card['name']),
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
                    users[creator][current_month]['comments'].append([card_id, a['data']['text']])
                    projects[list_id][current_month]['comments'].append([creator, card_id, a['data']['text']])

            if not card_info['complete']:
                if card['due'] is not None:
                    due = convert_date(card['due'])
                    if due < datetime.now():
                        card_info['miss_due_date'].append([1])

            for user_id in card['idMembers']:
                users[user_id][current_month]['cards'].append(card_info)
            
            projects[list_id][current_month]['cards'].append(card_info)
            current_month_cards.append(card_info)

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
                if 'Seminar' in current_month_cards[i]['name'] or 'seminar' in current_month_cards[i]['name']:
                    current_month_cards[i]['description'] = '[seminar]'

                if current_month_cards[i]['complete'] and current_month_cards[i]['description'] != '':
                    total_score += current_month_cards[i]['score']
        df1[user_name] = [total_score] + df1[user_name]

    df2 = {
        '': ['total score', 'change due date', 'miss due date', 'comments']
    }

    for user_id, user_data in users.items():
        try:
            user_name = board_users[user_id]
        except KeyError:
            continue

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

    print(list(projects.keys()))
    for pro_id, pro_data in projects.items():
        try:
            pro_name = board_projects[pro_id]
        except KeyError:
            continue

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
        json.dump(board_all, outfile, indent=4)

    # excelDownload = open("sample.xlsx",'rb').read()
    # return Response(
    #     excelDownload,
    #     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #     headers={"Content-disposition":
    #              "attachment; filename=sample.xlsx"})

    return send_file('{}.xlsx'.format(board_id), as_attachment=True)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_signal_handler)
    app.run(port=5050, debug=False)
