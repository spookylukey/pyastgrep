from pyastgrep.files import auto_dedent_code


def test_auto_dedent_code():
    # Dedent done
    assert auto_dedent_code(b"   xxx") == b"xxx"
    assert auto_dedent_code(b"\n   xxx") == b"\nxxx"
    assert auto_dedent_code(b"  \n   xxx") == b"\nxxx"
    assert auto_dedent_code(b"    xxx\n    yyy") == (b"xxx\nyyy")

    # No dedent done
    assert auto_dedent_code(b"xxx") == b"xxx"
    assert auto_dedent_code(b"    xx\n xxx") == b"    xx\n xxx"
