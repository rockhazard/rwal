#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, patch, mock_open
from images import ImageSelector, ImageCollector


class TestImages(unittest.TestCase):
    selection = Mock(name='selector')
    selection.random.return_value = 'random'
    selection.next.return_value = 'next'
    selection.previous.return_value = 'previous'
    selection.first.return_value = 'first'
    selection.cli.return_value = 'commandline'
    ming = Mock(name='imghdr')
    ming.return_value = True

    @patch('images.ImageSelector.select_random_image', selection.random)
    def test_get_pic_random(self):
        selector = ImageSelector()
        call = selector.get_pic('random')
        self.assertEqual(call, 'random')

    @patch('images.ImageSelector.select_random_image', selection.random)
    def test_get_pic_random_scope(self):
        selector = ImageSelector()
        flag = 'random'

        def scope_test(switch):
            call = selector.get_pic(switch)
            return call

        call = scope_test(flag)
        self.assertEqual(call, 'random')

    @patch('images.ImageSelector.select_next_image', selection.next)
    def test_get_pic_next_scope(self):
        selector = ImageSelector()
        flag = 'next'

        def scope_test(switch='random'):
            call = selector.get_pic(switch)
            return call

        self.assertEqual(scope_test(flag), 'next')

    @patch('images.ImageSelector.select_next_image', selection.next)
    def test_get_pic_next(self):
        selector = ImageSelector()
        call = selector.get_pic('next')
        self.assertEqual(call, 'next')

    @patch('images.ImageSelector.select_previous_image', selection.previous)
    def test_get_pic_previous(self):
        selector = ImageSelector()
        call = selector.get_pic('previous')
        self.assertEqual(call, 'previous')

    @patch('images.ImageSelector.select_first_image', selection.first)
    def test_get_pic_first(self):
        selector = ImageSelector()
        call = selector.get_pic('first')
        self.assertEqual(call, 'first')

    @patch('images.ImageSelector.select_cli_image', selection.cli)
    def test_get_pic_cli(self):
        selector = ImageSelector()
        call = selector.get_pic('commandline')
        self.assertEqual(call, 'commandline')

    def test_get_pic_nomatch(self):
        selector = ImageSelector()
        with self.assertRaises(SystemExit) as cm:
            selector.get_pic('mock')
        self.assertEqual(cm.exception.code,
                         "ImageSelector received unknown action: value 'mock' "
                         "of type <class 'str'>")

    """"Test ImageCollector"""""

    @patch('images.ImageCollector.record_background')
    @patch('images.ImageCollector.index_background')
    @patch('images.ImageCollector.skip_image')
    @patch('images.imghdr.what', ming)
    @patch('images.ImageCollector.write_images_list_file')
    @patch('builtins.open', mock_open(read_data='/img/mock.jpg\n/img/mock.png'))
    def test_select_image_ImageSelector(self, mo, im, ind, rec):
        collector = ImageCollector()
        collector.set_state('list', True)
        collector.imageDirectory = '/img'
        # with open(mock_open(read_data='/img/mock.jpg\n/img/mock.png')):
        call = collector.select_image('first')
        print('Called: ', call)
        self.assertEqual(call, '/img/mock.jpg')


if __name__ == '__main__':
    unittest.main()
