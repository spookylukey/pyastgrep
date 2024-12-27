import re
import sys
from pathlib import Path

import lxml.etree
from pyastgrep.asts import ast_to_xml
from pyastgrep.files import parse_python_file

from tests.utils import run_print

DIR = Path(__file__).parent / "examples" / "test_xml"


def test_literals():
    # We need a way to distinguish between different literals
    expr_int = './/Constant[@type="int"]'
    expr_string = './/Constant[@type="str"]'

    output_int = run_print(DIR, expr_int, print_xml=True).stdout
    output_string = run_print(DIR, expr_string, print_xml=True).stdout
    assert "assigned_int" in output_int
    assert "assigned_string" not in output_int

    assert "assigned_int" not in output_string
    assert "assigned_string" in output_string


def test_re_match():
    output = run_print(DIR, './/Name[re:match("assigned_.*", @id)]').stdout
    assert "assigned_int" in output
    assert "assigned_str" in output

    output2 = run_print(DIR, './/Name[re:match("sign", @id)]').stdout
    assert "assigned_int" not in output2


def test_re_search():
    output = run_print(DIR, './/Name[re:search("_.nt", @id)]').stdout
    assert "assigned_int" in output
    assert "assigned_str" not in output


def test_lower_case():
    output = run_print(DIR, './/ClassDef[lower-case(@name) = "myclass"]', xpath2=True).stdout
    assert "MyClass" in output


def test_attribute():
    """
    XPath expressions resolving to attributes don't return anything
    """
    output = run_print(DIR, ".//Name/@id")
    assert output.stdout == ""
    assert "XPath expression returned a value that is not an AST node: assigned_string" in output.stderr
    assert output.retval[0] == 0
    assert output.retval[1] > 0


def test_unicode():
    output = run_print(DIR, './/Name[@id="ß"]')
    assert "ß" in output.stdout
    output2 = run_print(DIR, './/Constant[contains(@value, "☺")]')
    assert "☺" in output2.stdout


def test_bytes():
    output = run_print(DIR, './/Constant[@type="bytes"]', ["bytes.py"])
    assert (
        output.stdout
        == """
bytes.py:1:11:MYBYTES = b"hello"
""".lstrip()
    )

    output2 = run_print(DIR, './/Constant[@value="hello"]', ["bytes.py"])
    assert (
        output2.stdout
        == """
bytes.py:1:11:MYBYTES = b"hello"
""".lstrip()
    )


def test_illegal_chars():
    # We have to strip the chars that are illegal in XML, but we should
    # not crash and we should still match on other parts of the string.
    output = run_print(DIR, './/Constant[contains(@value, "AB")]', ["xml_illegal.py"])
    assert (
        output.stdout
        == """
xml_illegal.py:2:13:NULPLUSAB = "\\x00AB"
xml_illegal.py:3:14:NULPLUSABb = b"\\x00AB"
xml_illegal.py:6:13:SURROGATE = "AB\\ud800"
""".lstrip()
    )


def _file_to_xml(path: Path):
    _, ast_node = parse_python_file(path.read_bytes(), str(path), auto_dedent=False)
    doc = ast_to_xml(ast_node, {})
    return lxml.etree.tostring(doc, pretty_print=True).decode("utf-8")


def test_xml_everything():
    # Smoke test to check we didn't break anything.
    EXPECTED = """
<Module>
  <body>
    <FunctionDef lineno="2" col_offset="0" type="str" name="function">
      <args>
        <arguments>
          <posonlyargs/>
          <args>
            <arg lineno="2" col_offset="13" type="str" arg="arg"/>
          </args>
          <kwonlyargs/>
          <kw_defaults/>
          <defaults/>
        </arguments>
      </args>
      <body>
        <Expr lineno="3" col_offset="4">
          <value>
            <Constant lineno="3" col_offset="4" type="str" value="Docstring"/>
          </value>
        </Expr>
        <Assign lineno="4" col_offset="4">
          <targets>
            <Name lineno="4" col_offset="4" type="str" id="assigned_string">
              <ctx>
                <Store/>
              </ctx>
            </Name>
          </targets>
          <value>
            <Constant lineno="4" col_offset="22" type="str" value="string_literal"/>
          </value>
        </Assign>
        <Assign lineno="5" col_offset="4">
          <targets>
            <Name lineno="5" col_offset="4" type="str" id="assigned_int">
              <ctx>
                <Store/>
              </ctx>
            </Name>
          </targets>
          <value>
            <Constant lineno="5" col_offset="19" type="int" value="123"/>
          </value>
        </Assign>
        <Assign lineno="6" col_offset="4">
          <targets>
            <Name lineno="6" col_offset="4" type="str" id="assigned_float">
              <ctx>
                <Store/>
              </ctx>
            </Name>
          </targets>
          <value>
            <Constant lineno="6" col_offset="21" type="float" value="3.14"/>
          </value>
        </Assign>
        <Assign lineno="7" col_offset="4">
          <targets>
            <Name lineno="7" col_offset="4" type="str" id="assigned_bool">
              <ctx>
                <Store/>
              </ctx>
            </Name>
          </targets>
          <value>
            <Constant lineno="7" col_offset="20" type="bool" value="True"/>
          </value>
        </Assign>
      </body>
      <decorator_list/>
      <type_params/>
    </FunctionDef>
    <FunctionDef lineno="10" col_offset="0" type="str" name="function_kwarg">
      <args>
        <arguments>
          <posonlyargs/>
          <args>
            <arg lineno="10" col_offset="19" type="str" arg="kwarg_arg"/>
          </args>
          <kwonlyargs/>
          <kw_defaults/>
          <defaults>
            <Constant lineno="10" col_offset="29" type="str" value=""/>
          </defaults>
        </arguments>
      </args>
      <body>
        <Pass lineno="11" col_offset="4"/>
      </body>
      <decorator_list/>
      <type_params/>
    </FunctionDef>
    <FunctionDef lineno="14" col_offset="0" type="str" name="function_star_args">
      <args>
        <arguments>
          <posonlyargs/>
          <args/>
          <vararg>
            <arg lineno="14" col_offset="24" type="str" arg="args"/>
          </vararg>
          <kwonlyargs/>
          <kw_defaults/>
          <defaults/>
        </arguments>
      </args>
      <body>
        <Pass lineno="15" col_offset="4"/>
      </body>
      <decorator_list/>
      <type_params/>
    </FunctionDef>
    <FunctionDef lineno="18" col_offset="0" type="str" name="function_star_kwargs">
      <args>
        <arguments>
          <posonlyargs/>
          <args/>
          <kwonlyargs/>
          <kw_defaults/>
          <kwarg>
            <arg lineno="18" col_offset="27" type="str" arg="kwargs"/>
          </kwarg>
          <defaults/>
        </arguments>
      </args>
      <body>
        <Pass lineno="19" col_offset="4"/>
      </body>
      <decorator_list/>
      <type_params/>
    </FunctionDef>
    <FunctionDef lineno="22" col_offset="0" type="str" name="function_pos_kw_only">
      <args>
        <arguments>
          <posonlyargs>
            <arg lineno="22" col_offset="25" type="str" arg="a"/>
          </posonlyargs>
          <args/>
          <kwonlyargs>
            <arg lineno="22" col_offset="34" type="str" arg="b"/>
          </kwonlyargs>
          <kw_defaults>
            <item></item>
          </kw_defaults>
          <defaults/>
        </arguments>
      </args>
      <body>
        <Pass lineno="23" col_offset="4"/>
      </body>
      <decorator_list/>
      <type_params/>
    </FunctionDef>
    <FunctionDef lineno="26" col_offset="0" type="str" name="function_all">
      <args>
        <arguments>
          <posonlyargs/>
          <args>
            <arg lineno="26" col_offset="17" type="str" arg="a"/>
          </args>
          <vararg>
            <arg lineno="26" col_offset="21" type="str" arg="args"/>
          </vararg>
          <kwonlyargs>
            <arg lineno="26" col_offset="27" type="str" arg="b"/>
            <arg lineno="26" col_offset="30" type="str" arg="c"/>
          </kwonlyargs>
          <kw_defaults>
            <item></item>
            <Constant lineno="26" col_offset="32" type="str" value=""/>
          </kw_defaults>
          <kwarg>
            <arg lineno="26" col_offset="38" type="str" arg="kwargs"/>
          </kwarg>
          <defaults/>
        </arguments>
      </args>
      <body>
        <Pass lineno="27" col_offset="4"/>
      </body>
      <decorator_list/>
      <type_params/>
    </FunctionDef>
    <ClassDef lineno="30" col_offset="0" type="str" name="MyClass">
      <bases/>
      <keywords/>
      <body>
        <Pass lineno="31" col_offset="4"/>
      </body>
      <decorator_list/>
      <type_params/>
    </ClassDef>
    <FunctionDef lineno="34" col_offset="0" type="str" name="function_ann">
      <args>
        <arguments>
          <posonlyargs/>
          <args>
            <arg lineno="34" col_offset="17" type="str" arg="a">
              <annotation>
                <Name lineno="34" col_offset="20" type="str" id="str">
                  <ctx>
                    <Load/>
                  </ctx>
                </Name>
              </annotation>
            </arg>
            <arg lineno="34" col_offset="25" type="str" arg="b">
              <annotation>
                <Name lineno="34" col_offset="28" type="str" id="bool">
                  <ctx>
                    <Load/>
                  </ctx>
                </Name>
              </annotation>
            </arg>
          </args>
          <kwonlyargs/>
          <kw_defaults/>
          <defaults>
            <Constant lineno="34" col_offset="35" type="bool" value="False"/>
          </defaults>
        </arguments>
      </args>
      <body>
        <AnnAssign lineno="35" col_offset="4" type="int" simple="1">
          <target>
            <Name lineno="35" col_offset="4" type="str" id="c">
              <ctx>
                <Store/>
              </ctx>
            </Name>
          </target>
          <annotation>
            <Name lineno="35" col_offset="7" type="str" id="int">
              <ctx>
                <Load/>
              </ctx>
            </Name>
          </annotation>
        </AnnAssign>
        <AnnAssign lineno="36" col_offset="4" type="int" simple="1">
          <target>
            <Name lineno="36" col_offset="4" type="str" id="d">
              <ctx>
                <Store/>
              </ctx>
            </Name>
          </target>
          <annotation>
            <Subscript lineno="36" col_offset="7">
              <value>
                <Name lineno="36" col_offset="7" type="str" id="list">
                  <ctx>
                    <Load/>
                  </ctx>
                </Name>
              </value>
              <slice>
                <Name lineno="36" col_offset="12" type="str" id="int">
                  <ctx>
                    <Load/>
                  </ctx>
                </Name>
              </slice>
              <ctx>
                <Load/>
              </ctx>
            </Subscript>
          </annotation>
          <value>
            <List lineno="36" col_offset="19">
              <elts>
                <Constant lineno="36" col_offset="20" type="int" value="1"/>
              </elts>
              <ctx>
                <Load/>
              </ctx>
            </List>
          </value>
        </AnnAssign>
      </body>
      <decorator_list/>
      <returns>
        <Name lineno="34" col_offset="45" type="str" id="str">
          <ctx>
            <Load/>
          </ctx>
        </Name>
      </returns>
      <type_params/>
    </FunctionDef>
    <Assign lineno="39" col_offset="0">
      <targets>
        <Name lineno="39" col_offset="0" type="str" id="&#223;">
          <ctx>
            <Store/>
          </ctx>
        </Name>
      </targets>
      <value>
        <Constant lineno="39" col_offset="5" type="str" value="&#9786;"/>
      </value>
    </Assign>
    <Assign lineno="40" col_offset="0">
      <targets>
        <Name lineno="40" col_offset="0" type="str" id="myellipsis">
          <ctx>
            <Store/>
          </ctx>
        </Name>
      </targets>
      <value>
        <Constant lineno="40" col_offset="13" type="ellipsis" value="Ellipsis"/>
      </value>
    </Assign>
  </body>
  <type_ignores/>
</Module>
""".lstrip()

    # Hacks for different Python versios, we may need to just have a dictionary
    # of different outputs
    if sys.version_info < (3, 12):
        EXPECTED = re.subn(r" *<type_params/>\n", "", EXPECTED)[0]

    assert _file_to_xml(DIR / "everything.py") == EXPECTED
