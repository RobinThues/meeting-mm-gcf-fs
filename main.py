import json
from datetime import datetime
from google.cloud import firestore

with open('config.json', 'r') as f:
    data = f.read()
config = json.loads(data)

db = firestore.Client()


def verify_web_hook(form: dict):
    if not form or form.get('token') != config['MATTERMOST_TOKEN']:
        raise ValueError('Invalid request/credentials.')


def handle_message(request):
    if request.method != 'POST':
        return 'Only POST requests are accepted', 405

    verify_web_hook(request.form)

    answer: str = parse_request(request.form['text'])
    return answer, 200


def parse_request(request_text: str) -> str:
    split = request_text.split(" ")
    if split[0] == '':
        return next_meeting()
    elif split[0] == 'add' and len(split) >= 3:
        return add_meeting(split[1], split[2])
    elif split[0] == 'list' and len(split) == 1:
        return list_future_meetings()
    else:
        return f'Diese Funktion steht nicht zur Verfügung.\n' \
               f'Versuch "/treffen" oder "/treffen list" stattdessen.'


def add_meeting(title: str, time: str) -> str:
    dt: datetime = str_to_time(time)
    title: str = title.replace('_', ' ')
    m = {
        'title': title,
        'time': time
    }
    db.collection('treffen').document(time).set(m)

    return f'Treffen {title} hinzugefügt für den {dt.isoformat().replace("T", " ")}'


def next_meeting() -> str:
    now = datetime.now()
    docs = db.collection('treffen').get()

    for doc in docs:
        if str_to_time(doc.get('time')) > now:
            return f'Der nächste Termin ist {doc.get("title")} an {doc.get("time").replace("T", " ")}.'
    return f'Kein Treffen gefunden'


def list_future_meetings() -> str:
    now: datetime = datetime.now()
    answer: str = f'Die nächsten Termine sind:\n'

    docs = db.collection('treffen').get()
    for d in docs:
        if str_to_time(d.get('time')) > now:
            answer += f'{d.get("title")}, {d.get("time").replace("T", " ")}\n'
    return answer


def str_to_time(time_string: str) -> datetime:
    return datetime.strptime(time_string, '%d.%m.%YT%H:%M')