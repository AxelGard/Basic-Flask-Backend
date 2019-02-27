import requests
import requests.exceptions
import json
import unittest
from flask_testing import TestCase
from server import db, app, User, Message, readby
import base64


link_heroku = "https:/your.herokuapp.com"
link_local = "http://localhost:4040"
link = link_local

local_server_online = True
heroku_server_online = True


try:
    requests.get(link_local)
except (requests.exceptions.ConnectionError):
    local_server_online = False

try:
    requests.get(link_heroku)
except (requests.exceptions.ConnectionError):
    heroku_server_online = False

class MyTest(TestCase):
    app.config['TESTING'] = True

    def create_app(self):
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def loginUser(self):
        r = self.client.post(link + "/user",
         data={"username": "Axel", "password": "1234"})
        assert r.status_code == 200


        r = self.client.post(link + "/user/login", data={"username": "Axel", "password": "1234"})
        token = json.loads(r.get_data(as_text=True))['access_token']
        assert r.status_code == 200

        return {"Authorization": "Bearer " + token}


class TestUserCreating(MyTest):
    def test_userCreation(self):
        r = self.client.post(link + "/user", data={"username": "Martin", "password": "1234"})
        assert r.status_code == 200
        r = self.client.post(link + "/user", data={"username": "Axel", "password": "SuperSecretVeyHardToCrackPasswordThatNeverWillBeCrackedByAnyoneInAnyTimeSoon"})
        assert r.status_code == 200

        r = self.client.post(link + "/user", data={"username": "Axel", "password": "SuperSecretVeyHardToCrackPasswordThatNeverWillBeCrackedByAnyoneInAnyTimeSoon"})
        assert r.status_code == 400


class TestUserLogin(MyTest):
    def test_user_login(self):
        r = self.client.post(link + "/user", data={"username": "Axel", "password": "1234"})
        assert r.status_code == 200

        r = self.client.post(link + "/user/login", data={"username": "Axel", "password": "1234"})
        assert r.status_code == 200

        r = self.client.post(link + "/user/login", data={"username": "Axel", "password": "WrongPassword"})
        assert r.status_code == 401

        r = self.client.post(link + "/user/login", data={"username": "WrongUsername", "password": "WrongPassword"})
        assert r.status_code == 401


class TestUserLogout(MyTest):
    def test_user_logout(self):
        r = self.client.post(link + "/user", data={"username": "Axel", "password": "1234"})
        assert r.status_code == 200

        r = self.client.post(link + "/user/login", data={"username": "Axel", "password": "1234"})
        token = json.loads(r.get_data(as_text=True))['access_token']
        assert r.status_code == 200

        r = self.client.post(link + "/user/logout", data={}, headers={
                "Authorization": "Bearer " + token})
        assert r.status_code == 200

        r = self.client.post(link + "/user/logout", data={}, headers={
                "Authorization": "Bearer " + token})
        assert r.status_code == 401


class HomepageTest(MyTest):
    def test_homepage(self):
        response = self.client.get("/")
        assert response.status_code == 200


class CreateMessageTest(MyTest):
    def test_message_creation(self):
        headers = self.loginUser()

        r = self.client.post(link + "/messages", data={"messagez": "NYTT MEDDELANDE"}, headers=headers)
        assert r.status_code == 400

        r = self.client.post(link + "/messages", data={"messages": "NEW MESSAGE THAT WILL CAUSE AND ERROR\
        BECAUSE MESSAGES LONGER THAN 140 CHARACTERAS ARE NOT ALLOWED AS MESSAGES\
        wdwdwdwdwdwdwwdwdwdwdwdwdwdwdwdwdwdwdwdwdwwdwwdwwdwdwdwdwdwwdwdwdww\
        wdwdwwwdwdwdwwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwdwwdwdwdw"}, headers=headers)
        assert r.status_code == 400

        r = self.client.post(link + "/messages", data={"message": "NYTT MEDDELANDE"}, headers=headers)
        assert r.status_code == 200


class GetMessageTest(MyTest):
    def test_get_one_message(self):
        r = self.client.post(link + "/user", data={"username": "Axel", "password": "1234"})
        assert r.status_code == 200

        r = self.client.post(link + "/user/login", data={"username": "Axel", "password": "1234"})
        token = json.loads(r.get_data(as_text=True))['access_token']
        assert r.status_code == 200

        headers = {"Authorization": "Bearer " + token}


        r = self.client.post(link + "/messages", data={"message": "SHOW THIS"}, headers = headers)
        assert r.status_code == 200
        id = json.loads(r.get_data(as_text=True))['id']
        assert id == 1
        r = self.client.get(link + "/messages/" + str(id))
        assert r.status_code == 200
        data = json.loads(r.get_data(as_text=True))
        assert data['message'] == "SHOW THIS"

class DeleteMessageTest(MyTest):
    def test_delete_messages(self):
        headers = self.loginUser()
        r = self.client.post(link + "/messages", data={"message": "TO DELETE"}, headers=headers)
        assert r.status_code == 200
        id = json.loads(r.get_data(as_text=True))['id']

        r = self.client.delete(link + "/messages/" + str(id), headers = headers)
        assert r.status_code == 200
        r = self.client.delete(link + "/messages/NotACorrectId", headers = headers)
        assert r.status_code == 400


class GetAllMessagesTest(MyTest):
    def test_get_all_messages(self):
        headers = self.loginUser()
        r = self.client.post(link + "/messages", data={"message": "Msg 1"}, headers=headers)
        assert r.status_code == 200
        r = self.client.post(link + "/messages", data={"message": "Msg 2"}, headers=headers)
        assert r.status_code == 200
        r = self.client.get(link + "/messages")
        assert r.status_code == 200
        data = json.loads(r.get_data(as_text=True))
        assert data == [{'id': 1, 'message': 'Msg 1', 'readBy': []},
                        {'id': 2, 'message': 'Msg 2', 'readBy': []}]


class MarkAsReadTest(MyTest):
    def test_mark_as_read(self):
        headers = self.loginUser()
        r = self.client.post(link + "/messages", data={"message": "Mark"}, headers=headers)
        assert r.status_code == 200
        r = self.client.post(link + "/messages/1/flag/1", headers = headers)
        assert r.status_code == 200
        r = self.client.get(link + "/messages/1")
        assert r.status_code == 200
        data = json.loads(r.get_data(as_text=True))
        assert data['readBy'] == [1]

        #Wrong id tests
        r = self.client.post(link + "/messages/1/flag/WrongID", headers = headers)
        assert r.status_code == 400
        r = self.client.post(link + "/messages/WrongID/flag/1", headers = headers)
        assert r.status_code == 400


class GetUserUnreadTest(MyTest):
    def test_get_unread_messages(self):
        headers = self.loginUser()

        r = self.client.post(link + "/messages", data={"message": "Unread message"}, headers = headers)
        assert r.status_code == 200
        r = self.client.post(link + "/messages", data={"message": "message"}, headers = headers)
        assert r.status_code == 200
        r = self.client.post(link + "/messages/2/flag/1", headers = headers)
        assert r.status_code == 200

        r = self.client.get(link + "/messages/unread/1", headers = headers)
        assert r.status_code == 200
        data = json.loads(r.get_data(as_text=True))
        assert data == [{'id': 1, 'message': 'Unread message', 'readBy': []}]

if __name__ == '__main__':
    if local_server_online:
        print("Running tests on local server")
        unittest.main()
    elif heroku_server_online:
        print("Running tests on heroku server")
        link = link_heroku
        unittest.main()
    else:
        print("No server could be found")
