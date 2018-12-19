#!/usr/bin/env python3
import unittest
import requests

URL='http://plumber'

class TestPushwithPlainHTTPAPIs(unittest.TestCase):

    def test_plain_single_push_and_pop(self):

        for i in range(3):
            self.assertEqual(
                    "1",
                    requests.post(
                URL + '/1/push?format=plain',
                data = str(i)
                    ).text
                )

        for i in range(3):
            self.assertEqual(
                    str(i),
                    requests.get(
                        URL + '/1/pop?format=plain'
                    ).text
                )

    def test_multiple_push_and_pop(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                "3",
                requests.post(
                        URL + '/1/push?format=plain',
                        data = '\n'.join(data_list)
                        ).text
        )

        self.assertEqual(
                '\n'.join(data_list),
                requests.get(
                    URL + '/1/pop?format=plain&quantity=3'
                ).text
            )

    def test_multiple_push_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                "3",
                requests.post(
                        URL + '/1/push?format=plain',
                        data = '\n'.join(data_list)
                        ).text
                )

        self.assertEqual(
                '\n'.join(data_list),
                requests.get(
                    URL + '/1/pop?format=plain&quantity=100'
                ).text
            )


    def test_multiple_push_and_pop_without_any_left(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                "3",
                requests.post(
                        URL + '/1/push?format=plain',
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
        
    def test_flush(self):

        self.assertEqual(
                "1",
                requests.post(
                        URL + '/1/push?format=plain',
                        data = '1'
                        ).text
        )

        self.assertEqual(
            requests.post(
                URL + '/1/flush',
                ).status_code, 
            200
            )

        self.assertFalse(
                requests.get(
                    URL + '/1/pop?format=plain&quantity=3'
                ).text
            )

class TestPushwithJSONHTTPAPIs(unittest.TestCase):

    def test_json_single_push_and_pop(self):

        for i in range(3):
            self.assertEqual(
                    1,
                    requests.post(
                URL + '/1/push',
                json = [ i ]
                    ).json()
                )

        for i in range(3):
            self.assertEqual(
                    [ i ],
                    requests.get(
                        URL + '/1/pop'
                    ).json()
                )

    def test_multiple_push_and_pop(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                3,
                requests.post(
                        URL + '/1/push',
                        json = data_list
                        ).json()
        )

        self.assertEqual(
                data_list,
                requests.get(
                    URL + '/1/pop?quantity=3'
                ).json()
            )

    def test_multiple_push_and_overpop(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                3,
                requests.post(
                        URL + '/1/push',
                        json = data_list
                        ).json()
                )

        self.assertEqual(
                data_list,
                requests.get(
                    URL + '/1/pop?quantity=100'
                ).json()
            )


    def test_multiple_push_and_pop_without_any_left(self):

        data_list = [ str(i) for i in range(3) ]

        self.assertEqual(
                3,
                requests.post(
                        URL + '/1/push',
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
        
    def test_flush(self):

        self.assertEqual(
                1,
                requests.post(
                        URL + '/1/push?format=json',
                        json = [ 1 ]
                        ).json()
        )

        self.assertEqual(
            requests.post(
                URL + '/1/flush',
                ).status_code, 
            200
            )

        self.assertFalse(
                requests.get(
                    URL + '/1/pop?quantity=3'
                ).json()
            )
if __name__ == '__main__':
    unittest.main()
