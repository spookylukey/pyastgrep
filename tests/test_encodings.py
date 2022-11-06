from pyastgrep.files import get_encoding


def test_empty():
    assert get_encoding(b"") == "utf-8"


def test_coding_first_line():
    assert get_encoding(b'# -*- coding: windows-1252 -*-\n\nX = "\x85"\n') == "windows-1252"
    assert get_encoding(b"# -*- coding: windows-1252 -*-\n") == "windows-1252"
    assert get_encoding(b"# -*- coding: windows-1252 -*-") == "windows-1252"


def test_coding_second_line():
    assert get_encoding(b'#!/usr/bin/env python\n# -*- coding: windows-1252 -*-\n\nX = "\x85"\n') == "windows-1252"
    assert get_encoding(b"#!/usr/bin/env python\n# -*- coding: windows-1252 -*-\n") == "windows-1252"
    assert get_encoding(b"#!/usr/bin/env python\n# -*- coding: windows-1252 -*-") == "windows-1252"
