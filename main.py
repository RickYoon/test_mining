#-*- coding: utf-8 -*-
#
# original:    https://github.com/yukuku/telebot
# modified by: Bak Yeon O @ https://bakyeono.net
# description: https://bakyeono.net/post/2015-08-24-using-telegram-bot-api.html
# github:      https://github.com/bakyeono/using-telegram-bot-api
#

# ���� �� ���� ���̺귯�� �ε�
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# URL, JSON, �α�, ����ǥ���� ���� ���̺귯�� �ε�
import urllib
import urllib2
import json
import logging
import re

# �� ��ū, �� API �ּ�
TOKEN = '137007641:AAFVXObeODnKcyDrbcBfEAHzYFGhcFeVlVk'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# ���� ������ ��ɾ�
CMD_START     = '/start'
CMD_STOP      = '/stop'
CMD_HELP      = '/help'
CMD_BROADCAST = '/broadcast'

# �� ���� & �޽���
USAGE = u"""[����] �Ʒ� ��ɾ �޽����� �����ų� ��ư�� �����ø� �˴ϴ�.
/start - (�� Ȱ��ȭ)
/stop  - (�� ��Ȱ��ȭ)
/help  - (�� ���� �����ֱ�)
"""
MSG_START = u'���� �����մϴ�.'
MSG_STOP  = u'���� �����մϴ�.'

# Ŀ���� Ű����
CUSTOM_KEYBOARD = [
        [CMD_START],
        [CMD_STOP],
        [CMD_HELP],
        ]

# ä�ú� �� Ȱ��ȭ ����
# ���� �� ������ Datastore(NDB)�� ���¸� �����ϰ� ����
# ����ڰ� /start ������ Ȱ��ȭ
# ����ڰ� /stop  ������ ��Ȱ��ȭ
class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(required=True, indexed=True, default=False,)

def set_enabled(chat_id, enabled):
    u"""set_enabled: �� Ȱ��ȭ/��Ȱ��ȭ ���� ����
    chat_id:    (integer) ���� Ȱ��ȭ/��Ȱ��ȭ�� ä�� ID
    enabled:    (boolean) ������ Ȱ��ȭ/��Ȱ��ȭ ����
    """
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = enabled
    es.put()

def get_enabled(chat_id):
    u"""get_enabled: �� Ȱ��ȭ/��Ȱ��ȭ ���� ��ȯ
    return: (boolean)
    """
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def get_enabled_chats():
    u"""get_enabled: ���� Ȱ��ȭ�� ä�� ����Ʈ ��ȯ
    return: (list of EnableStatus)
    """
    query = EnableStatus.query(EnableStatus.enabled == True)
    return query.fetch()

# �޽��� �߼� ���� �Լ���
def send_msg(chat_id, text, reply_to=None, no_preview=True, keyboard=None):
    u"""send_msg: �޽��� �߼�
    chat_id:    (integer) �޽����� ���� ä�� ID
    text:       (string)  �޽��� ����
    reply_to:   (integer) ~�޽����� ���� ����
    no_preview: (boolean) URL �ڵ� ��ũ(�̸�����) ����
    keyboard:   (list)    Ŀ���� Ű���� ����
    """
    params = {
        'chat_id': str(chat_id),
        'text': text.encode('utf-8'),
        }
    if reply_to:
        params['reply_to_message_id'] = reply_to
    if no_preview:
        params['disable_web_page_preview'] = no_preview
    if keyboard:
        reply_markup = json.dumps({
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False,
            'selective': (reply_to != None),
            })
        params['reply_markup'] = reply_markup
    try:
        urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode(params)).read()
    except Exception as e: 
        logging.exception(e)

def broadcast(text):
    u"""broadcast: ���� ���� �ִ� ��� ä�ÿ� �޽��� �߼�
    text:       (string)  �޽��� ����
    """
    for chat in get_enabled_chats():
        send_msg(chat.key.string_id(), text)

# �� ��� ó�� �Լ���
def cmd_start(chat_id):
    u"""cmd_start: ���� Ȱ��ȭ�ϰ�, Ȱ��ȭ �޽��� �߼�
    chat_id: (integer) ä�� ID
    """
    set_enabled(chat_id, True)
    send_msg(chat_id, MSG_START, keyboard=CUSTOM_KEYBOARD)

def cmd_stop(chat_id):
    u"""cmd_stop: ���� ��Ȱ��ȭ�ϰ�, ��Ȱ��ȭ �޽��� �߼�
    chat_id: (integer) ä�� ID
    """
    set_enabled(chat_id, False)
    send_msg(chat_id, MSG_STOP)

def cmd_help(chat_id):
    u"""cmd_help: �� ���� �޽��� �߼�
    chat_id: (integer) ä�� ID
    """
    send_msg(chat_id, USAGE, keyboard=CUSTOM_KEYBOARD)

def cmd_broadcast(chat_id, text):
    u"""cmd_broadcast: ���� Ȱ��ȭ�� ��� ä�ÿ� �޽��� ���
    chat_id: (integer) ä�� ID
    text:    (string)  ����� �޽���
    """
    send_msg(chat_id, u'�޽����� ����մϴ�.', keyboard=CUSTOM_KEYBOARD)
    broadcast(text)

def cmd_echo(chat_id, text, reply_to):
    u"""cmd_echo: ������� �޽����� ���� ����
    chat_id:  (integer) ä�� ID
    text:     (string)  ����ڰ� ���� �޽��� ����
    reply_to: (integer) ������ �޽��� ID
    """
    send_msg(chat_id, text, reply_to=reply_to)

def process_cmds(msg):
    u"""����� �޽����� �м��� �� ����� ó��
    chat_id: (integer) ä�� ID
    text:    (string)  ����ڰ� ���� �޽��� ����
    """
    msg_id = msg['message_id']
    chat_id = msg['chat']['id']
    text = msg.get('text')
    if (not text):
        return
    if CMD_START == text:
        cmd_start(chat_id)
        return
    if (not get_enabled(chat_id)):
        return
    if CMD_STOP == text:
        cmd_stop(chat_id)
        return
    if CMD_HELP == text:
        cmd_help(chat_id)
        return
    cmd_broadcast_match = re.match('^' + CMD_BROADCAST + ' (.*)', text)
    if cmd_broadcast_match:
        cmd_broadcast(chat_id, cmd_broadcast_match.group(1))
        return
    cmd_echo(chat_id, text, reply_to=msg_id)
    return

# �� ��û�� ���� �ڵ鷯 ����
# /me ��û��
class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

# /updates ��û��
class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

# /set-wehook ��û��
class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

# /webhook ��û�� (�ڷ��׷� �� API)
class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        self.response.write(json.dumps(body))
        process_cmds(body['message'])

# ���� �� ������ �� ��û �ڵ鷯 ����
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set-webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)