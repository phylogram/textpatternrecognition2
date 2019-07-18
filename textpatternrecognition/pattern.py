# -*- coding: utf-8 -*-

import re


class PotentialPattern:
    """
    Defines a PotentialPattern, which is not yet finished parsing.
    """

    def __init__(self, current_line_number, pattern_line_number, position, completed):
        """
        :param current_line_number: int
        :param pattern_line_number: int
        :param position: int
        :param completed: bool
        """
        self.current_line_number = current_line_number
        self.pattern_line_number = pattern_line_number
        self.position = position
        self.completed = completed


class PatternParser:
    """
    Parses a pattern and provides method parse_text to find patterns in a list of lines (from file iteration)
    """

    # TO DO: add Flags support
    def __init__(self, search_pattern, use_regex=False):
        """
        Initialises  PatternParser with new pattern

        :param search_pattern: str either not compiled regex or simple string
        :param use_regex: bool whether to escape the string for use in regex or not
        """

        self.use_regex = use_regex

        self.potential_patterns = dict()
        self.found_patterns = set()
        self.current_text_line = ''
        self.current_text_line_number = 0

        self.search_pattern_lines = search_pattern.splitlines()
        self.number_of_search_pattern_lines = len(self.search_pattern_lines) - 1  # indexing

        # We will use regex for search anyway, so escape it if it is not meant to be a regex
        if not self.use_regex:
            self.search_pattern_lines = [re.escape(search_pattern_line) for search_pattern_line in
                                         self.search_pattern_lines]
        self._create_search_objects()
        self.current_text_line_number = 0

    def reset(self):
        """
        Use, if you start new text

        :return:
        """
        self.potential_patterns = dict()
        self.found_patterns = set()
        self.current_text_line = ''

    def _create_search_objects(self):
        """
        Method that creates pattern objects like re.compile and sets self.search_pattern_lines to it

        Overwrite in child classes, if you wish different behavior.
        See cls._evaluate_search_objects and cls._parse_first_line before!

        :return:
        """
        self.search_pattern_lines = [re.compile(search_pattern_line) for search_pattern_line in
                                     self.search_pattern_lines]

    def _evaluate_search_objects(self, text, pattern_line_number, position):
        """
        Method that evaluates text + search object, for example re.compile('a').match('a')

        You can use this method to override the default search functionality in child classes.

        Be aware, that if you do so, you may need to change cls._create_search_objects and cls._parse_first_line as well

        :param text: str The string unit aka line to be searched for
        :param pattern_line_number: int The line number of the current PotentialPattern
        :param position: int The position in text where to look
        :return: Bool or None. None: The patterns is not continuing. None: The patterns is not finished
        """

        search_object = self.search_pattern_lines[pattern_line_number]
        match_object = search_object.match(text, position)

        if match_object is None:
            return False  # The patterns is not continuing
        if pattern_line_number < self.number_of_search_pattern_lines and match_object:
            return None  # The patterns is not finished
        if pattern_line_number is self.number_of_search_pattern_lines and match_object:
            return True  # The patterns is completed
        else:
            raise Exception(u"Error in Logic. Please go debugging")  # No clue what is going on – debug!
            # TO DO: Add more meaningful exception

    def _parse_first_lines(self):
        """
        Finds occurrences of first line of pattern and populates self.potential_patterns with PotentialPatterns

        Works first come first save – so with pattern

        x
        y
        x

        and text

        x
        y
        x
        y
        x

        only one (the first) occurrence will be found

        x
        y
        x  x
           y
           x

        will work however

        """

        first_line_pattern = self.search_pattern_lines[0]
        start = 0
        while True:
            match = first_line_pattern.search(self.current_text_line, start)
            if match is None:
                break
            position = match.start()
            if position not in self.potential_patterns:  # Assuming First come, first serve
                self.potential_patterns[position] = PotentialPattern(
                    current_line_number=self.current_text_line_number,
                    pattern_line_number=0,
                    position=position,
                    completed=None,
                )
            start = match.end()

    def _continue_parsing_potential_objects(self):
        """
        Takes the outcome of cls._evaluate_search_objects and administers it
        :return: int found completed patterns
        """

        positions_to_remove = set()
        found = 0

        for position, potential_pattern in self.potential_patterns.items():

            result = self._evaluate_search_objects(
                text=self.current_text_line,
                pattern_line_number=potential_pattern.pattern_line_number,
                position=potential_pattern.position
            )

            if result is False:
                positions_to_remove.add(position)  # Pattern did not continue - remove
                continue
            if result is None:
                potential_pattern.pattern_line_number += 1
                continue  # Go up one line in pattern
            if result is True:
                potential_pattern.completed = True
                found += 1
                positions_to_remove.add(position)  # pattern is finished - count and free slot
                self.found_patterns.add(position)  # log
                continue

        self.potential_patterns = {position: self.potential_patterns[position] for position in
                                   self.potential_patterns.keys() if position not in positions_to_remove}

        return found

    def parse_text(self, text_line):
        """
        Use to parse line from the text, where you are searching your patterns in it.
        :param text_line: the unit of text to look in
        :return: int found completed patterns
        """
        self.current_text_line = text_line
        self._parse_first_lines()
        found = self._continue_parsing_potential_objects()
        self.current_text_line_number += 1
        return found
