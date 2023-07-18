import io
from pathlib import Path

from pyastgrep.files import get_encoding

from tests.utils import run_print

DIR = Path(__file__).parent / "examples" / "test_encodings"


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


def test_search():
    # Check that we can search for a unicode character, no matter the encoding
    # of the file, or whether it uses a literal unicode character or \x
    # encoding. The latter part is provided by the way that ast parsing converts
    # characters for us.
    windows_1252_file_data = b'# -*- coding: windows-1252 -*-\nE_acute = "\xc9"\nassert "\\xC9" == E_acute\n'
    output = run_print(DIR, './/Constant[@value="É"]', [io.BytesIO(windows_1252_file_data), "utf8.py"])
    assert (
        output.stdout
        == """
<stdin>:2:11:E_acute = "É"
<stdin>:3:8:assert "\\xC9" == E_acute
utf8.py:1:11:E_acute = "É"
utf8.py:2:8:assert "\\xC9" == E_acute
""".lstrip()
    )
