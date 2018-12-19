#!/usr/bin/env python3
import unittest
import requests
import time

URL='http://plumber'

class TestPushIfOlderThanwithPlainHTTPAPIs(unittest.TestCase):

    def test_multiple_push_if_new_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]
        requests.post(URL + '/1/flush')

        self.assertEqual(
                "3",
                requests.post(
                        URL + '/1/push?format=plain&push_if_older_than=1',
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
                        URL + '/1/push?format=plain&push_if_older_than=1',
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

    def test_multiple_push_and_pop_with_age(self):

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
                        URL + '/1/push?format=plain&push_if_older_than=1',
                        data = '\n'.join(data_list)
                        ).text
        )

        time.sleep(3)

        self.assertEqual(
                "3",
                requests.post(
                        URL + '/1/push?format=plain&push_if_older_than=2',
                        data = '\n'.join(data_list)
                        ).text
        )

        self.assertEqual(
                '\n'.join(data_list*2),
                requests.get(
                    URL + '/1/pop?format=plain&quantity=6'
                ).text
            )

class TestPushIfOlderThanwithJSONHTTPAPIs(unittest.TestCase):

    def test_multiple_push_if_new_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]
        requests.post(URL + '/1/flush')

        self.assertEqual(
                3,
                requests.post(
                        URL + '/1/push?push_if_older_than=1',
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
                        URL + '/1/push?push_if_older_than=1',
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

    def test_multiple_push_and_pop_with_age(self):

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
                        URL + '/1/push?push_if_older_than=1',
                        json = data_list
                        ).json()
        )

        time.sleep(3)

        self.assertEqual(
                3,
                requests.post(
                        URL + '/1/push?push_if_older_than=2',
                        json = data_list
                        ).json()
        )

        self.assertEqual(
                data_list*2,
                requests.get(
                    URL + '/1/pop?quantity=6'
                ).json()
            )

if __name__ == '__main__':
    unittest.main()
