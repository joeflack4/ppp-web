#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests."""
import os
import unittest
from copy import copy
from glob import glob
from subprocess import call

from webui.app import create_app

TEST_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
TEST_STATIC_DIR = TEST_DIR + 'static/'


class PppWebTest(unittest.TestCase):
    """Base class for PPP web package tests."""

    @classmethod
    def files_dir(cls):
        """Return name of test class."""
        return TEST_STATIC_DIR + cls.__name__

    def input_path(self):
        """Return path of input file folder for test class."""
        return self.files_dir() + '/input/'

    def output_path(self):
        """Return path of output file folder for test class."""
        return self.files_dir() + '/output/'

    def input_files(self):
        """Return paths of input files for test class."""
        all_files = glob(self.input_path() + '*')
        # With sans_temp_files, you can have XlsForms open while testing.
        sans_temp_files = [x for x in all_files
                           if not x[len(self.input_path()):].startswith('~$')]
        return sans_temp_files

    def output_files(self):
        """Return paths of input files for test class."""
        return glob(self.output_path() + '*')

    def convert(self, command):
        """Converts input/* --> output/*. Returns n files each."""
        in_files = self.input_files()
        out_dir = self.output_path()

        call(['rm', '-rf', out_dir])
        os.makedirs(out_dir)
        call(command)

        expected = 'N files: ' + str(len(in_files))
        actual = 'N files: ' + str(len(self.output_files()))
        return expected, actual

    def standard_conversion_test(self, command):
        """Checks standard convert success."""
        expected, actual = self.convert(command)
        self.assertEqual(expected, actual)


class TestRoutes(unittest.TestCase):
    """Test routes."""

    ignore_routes = ('/static/<path:filename>',)
    ignore_end_patterns = ('>',)

    def setUp(self):
        """Set up: Put Flask app in test mode."""
        app = create_app()
        self.initial_app = copy(app)
        app.testing = True
        self.app = app.test_client()

    @staticmethod
    def valid_route(route):
        """Validate route.

        Args:
            route (str): Route url pattern.

        Returns:
            bool: True if valid, else False.
        """
        if route in TestRoutes.ignore_routes \
                or route.endswith(TestRoutes.ignore_end_patterns):
            return False
        return True

    def test_routes(self):
        """Smoke test routes to ensure no runtime errors."""
        routes = [route.rule for route in self.initial_app.url_map.iter_rules()
                  if self.valid_route(route.rule)]
        for route in routes:
            self.app.get(route)


class TestCommand(PppWebTest):
    """Test command."""

    def test_standard(self):
        """Test command"""
        self.standard_conversion_test(
            ['python3', '-m', 'ppp'] + self.input_files() + [
             '--language', 'English',
             '--format', 'doc',
             '--preset', 'minimal',
             '--template', 'old',
             '--outpath', self.output_path()])


if __name__ == '__main__':
    from test.utils.doctest_unittest_runner import doctest_unittest_runner
    TEST_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
    doctest_unittest_runner(test_dir=TEST_DIR, relative_path_to_root='../',
                            package_names=['webui', 'test'])
