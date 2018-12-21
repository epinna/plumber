#!/usr/bin/env python3
import unittest
import requests

URL='http://plumber'

class TestPushIfNewwithPlainHTTPAPIs(unittest.TestCase):

    def test_multiple_push_if_new_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]
        requests.post(URL + '/1/flush')

        self.assertEqual(
                "3",
                requests.post(
                        URL + '/1/push?format=plain&push_if_new=true',
                        data = '\n'.join(data_list)
                        ).text
        )

        self.assertEqual(
                '\n'.join(data_list),
                requests.get(
                    URL + '/1/pop?format=plain&quantity=3'
                ).text
            )

        self.assertFalse(
                requests.get(
                    URL + '/1/pop?format=plain&quantity=3'
                ).text
            )

    def test_multiple_overpush_if_new_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                "3",
                requests.post(
                        URL + '/1/push?format=plain',
                        data = '\n'.join(data_list)
                        ).text
        )

        self.assertEqual(
                "0",
                requests.post(
                        URL + '/1/push?format=plain&push_if_new=true',
                        data = '\n'.join(data_list)
                        ).text
        )

        self.assertEqual(
                '\n'.join(data_list),
                requests.get(
                    URL + '/1/pop?format=plain&quantity=6'
                ).text
            )

        self.assertFalse(
                requests.get(
                    URL + '/1/pop?format=plain&quantity=1'
                ).text
            )

class TestPushIfNewwithJSONHTTPAPIs(unittest.TestCase):

    def test_multiple_push_if_new_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]
        requests.post(URL + '/1/flush')

        self.assertEqual(
                3,
                requests.post(
                        URL + '/1/push?push_if_new=true',
                        json = data_list
                        ).json()
        )

        self.assertEqual(
                data_list,
                requests.get(
                    URL + '/1/pop?quantity=3'
                ).json()
            )

        self.assertFalse(
                requests.get(
                    URL + '/1/pop?quantity=3'
                ).json()
            )

    def test_multiple_overpush_if_new_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                3,
                requests.post(
                        URL + '/1/push',
                        json = data_list
                        ).json()
        )

        self.assertEqual(
                0,
                requests.post(
                        URL + '/1/push?push_if_new=true',
                        json = data_list
                        ).json()
        )

        self.assertEqual(
                data_list,
                requests.get(
                    URL + '/1/pop?quantity=6'
                ).json()
            )

        self.assertFalse(
                requests.get(
                    URL + '/1/pop?quantity=1'
                ).json()
            )

if __name__ == '__main__':
    unittest.main()
