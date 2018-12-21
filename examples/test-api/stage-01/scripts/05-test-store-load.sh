#!/usr/bin/env python3
import unittest
import json
import requests
import time

URL='http://plumber'

class TestLoadandStorewithPlainHTTPAPIs(unittest.TestCase):

    def test_store_and_load_by_id(self):

        data_list = [ str(i) for i in range(3) ]

        id_result = requests.post(
                URL + '/1/store?format=plain',
                data = '\n'.join(data_list)
              ).text

        self.assertEqual(
          24,
          len(id_result)
        )

        self.assertEqual(
          '\n'.join(data_list),
          requests.get(
              URL + '/1/load?format=plain&filter={"_id":"%s"}' % (id_result),
          ).text)

    def test_store_and_load_and_delete_by_id(self):

        data_list = [ str(i) for i in range(3) ]

        id_result = requests.post(
                URL + '/1/store?format=plain',
                data = '\n'.join(data_list)
              ).text

        self.assertEqual(
          24,
          len(id_result)
        )

        self.assertEqual(
          '\n'.join(data_list),
          requests.get(
              URL + '/1/load?format=plain&filter={"_id":"%s"}&delete=true' % (id_result),
          ).text)

        self.assertEqual(
          '',
          requests.get(
              URL + '/1/load?format=plain&filter={"_id":"%s"}' % (id_result),
          ).text)

    def test_store_and_load_and_delete_by_content(self):

        data_string = "TESTINGDATA"

        id_result = requests.post(
                URL + '/1/store?format=plain',
                data = data_string
              ).text

        self.assertEqual(
          24,
          len(id_result)
        )

        self.assertEqual(
          data_string,
          requests.get(
              URL + '/1/load?format=plain&filter={"data":"%s"}&delete=true' % (data_string),
          ).text)

        self.assertEqual(
          '',
          requests.get(
              URL + '/1/load?format=plain&filter={"data":"%s"}&delete=true' % (data_string),
          ).text)

class TestLoadandStorewithJSONHTTPAPIs(unittest.TestCase):

    def test_store_and_load_by_id(self):

        data_list = [ str(i) for i in range(3) ]

        id_result = requests.post(
                URL + '/1/store',
                json = data_list
                ).json()

        self.assertEqual(
          24,
          len(id_result)
        )

        self.assertEqual(
          data_list,
          requests.get(
              URL + '/1/load?format=json&filter={"_id":"%s"}' % (id_result),
              ).json())

    def test_store_and_load_and_delete_by_id(self):

        data_list = [ str(i) for i in range(3) ]

        id_result = requests.post(
                URL + '/1/store?format=json',
                json = data_list
                ).json()

        self.assertEqual(
          24,
          len(id_result)
        )

        self.assertEqual(
          data_list,
          requests.get(
              URL + '/1/load?format=json&filter={"_id":"%s"}&delete=true' % (id_result),
              ).json())

        self.assertEqual(
        {},
          requests.get(
              URL + '/1/load?format=json&filter={"_id":"%s"}' % (id_result),
              ).json())

    def test_store_and_load_and_delete_by_content(self):

        data_string = { 'testing': 'data' }

        id_result = requests.post(
                URL + '/1/store',
                json = data_string
                ).json()

        self.assertEqual(
          24,
          len(id_result)
        )

        self.assertEqual(
          data_string,
          requests.get(
          URL + '/1/load?filter={"data":%s}&delete=true' % (json.dumps(data_string)),
              ).json())

        self.assertEqual(
        {},
          requests.get(
              URL + '/1/load?filter={"data":"%s"}&delete=true' % (data_string),
              ).json())

if __name__ == '__main__':
    unittest.main()
