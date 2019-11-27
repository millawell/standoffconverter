import unittest
import os
from lxml import etree

import standoffconverter

input_xml1 = b'''<W><text type="a">A B C</text></W>'''
input_xml2 = b'''<W><text type="a">The answer is 42.</text></W>'''
input_xml3 = b'''<W>
    <text type="a">
        <p type="b">The answer<del> not this</del> is 42.</p>
        <p type="b">The answer is 43.</p>
        <p type="b">The answer is 44.</p>
        <p type="b">The answer is 45.</p>
    </text>
    <text type="a">
        <p type="b">The answer is 46.</p>
        <p type="b">The answer is 47.</p>
        <p type="b">The answer is 48.</p>
    </text>
</W>'''

file_xml1 = os.path.join(os.path.dirname(__file__), 'xml1.xml')
file_xml2 = os.path.join(os.path.dirname(__file__), 'xml2.xml')

class TestStandoffConverter(unittest.TestCase):

    def test_load(self):
        with open(file_xml1, "rb") as fin:
            so = standoffconverter.load(fin)
            self.assertTrue(so.plain == "A B C")

    def test_save(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        
        with open(file_xml2, "wb") as fout:
            so.save(fout)
        
        with open(file_xml2) as fin:
            tree = etree.fromstring(fin.read())
        so2 = standoffconverter.Standoff.from_lxml_tree(tree)    

        self.assertTrue(so.plain == so2.plain)

    def test_from_lxml_tree_plain(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        self.assertTrue(so.plain == "A B C")
    
    def test_from_lxml_tree_standoff(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        self.assertTrue(so.standoffs[0]["begin"] == 0)
        self.assertTrue(so.standoffs[-1]["begin"] == 0)
        self.assertTrue(so.standoffs[0]["end"] == len(so.plain))
        self.assertTrue(so.standoffs[-1]["end"] == len(so.plain))

    def test_add_annotation_1(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        so.add_annotation(0,1,"xx",0,{"resp":"machine"})
        output_xml = etree.tostring(so.tree).decode("utf-8")
        expected_out = '<W><text type="a"><xx resp="machine">A</xx> B C</text></W>'
        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_2(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        so.add_annotation(0,1,"xx",0,{"resp":"machine"})
        so.add_annotation(2,3,"xx",0,{"resp":"machine"})
        output_xml = etree.tostring(so.tree).decode("utf-8")
        expected_out = '<W><text type="a"><xx resp="machine">A</xx> <xx resp="machine">B</xx> C</text></W>'
        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_3(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        # so.add_annotation(0,1,"xx",0,{"resp":"machine"})
        so.add_annotation(2,3,"xx",0,{"resp":"machine"})
        output_xml = etree.tostring(so.tree).decode("utf-8")
        expected_out = '<W><text type="a">A <xx resp="machine">B</xx> C</text></W>'
        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_4(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        # so.add_annotation(0,1,"xx",0,{"resp":"machine"})
        so.add_annotation(2,3,"xx",0,{"resp":"machine"})
        so.add_annotation(2,3,"vv",1,{"resp":"machine"})
        output_xml = etree.tostring(so.tree).decode("utf-8")
        expected_out = '<W><text type="a">A <xx resp="machine"><vv resp="machine">B</vv></xx> C</text></W>'
        self.assertTrue(expected_out == output_xml)

    def test_is_duplicate_annotation(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        self.assertTrue(
            so.is_duplicate_annotation(0,len(so.plain), "W", {})
        )

    def test_find(self):
        tree = etree.fromstring(input_xml3)
        so = standoffconverter.Standoff.from_lxml_tree(tree)

        filterset = standoffconverter.Filter(so)
        filterset.find("text").find("p")


        for text, standoff in filterset:
            attrib = standoff["attrib"]
            self.assertTrue(
                text == "The answer not this is 42."
            )

            self.assertTrue(
                attrib["type"] == "b"
            )
            break

    def test_find_exclude(self):

        tree = etree.fromstring(input_xml3)
        so = standoffconverter.Standoff.from_lxml_tree(tree)

        filterset = standoffconverter.Filter(so)
        filterset.find("text").find("p").exclude("del")


        for text, standoff in filterset:
            attrib = standoff["attrib"]
            self.assertTrue(
                text == "The answer is 42."
            )

            self.assertTrue(
                attrib["type"] == "b"
            )
            break

    def test_find_first(self):

        tree = etree.fromstring(input_xml3)
        so = standoffconverter.Standoff.from_lxml_tree(tree)

        filterset = standoffconverter.Filter(so).find("del")

        text, _ = filterset.first()

        self.assertTrue(
            text == " not this"
        )


    def test_filter_copy(self):
        tree = etree.fromstring(input_xml3)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        
        filterset = standoffconverter.Filter(so)
        filterset2 = filterset.copy().exclude("del").find("p")
        filterset=filterset.find("p")



        for el1, el2 in zip(filterset, filterset2):
            break

        self.assertTrue(el1[0] == "The answer not this is 42.")
        self.assertTrue(el2[0] == "The answer is 42.")


if __name__ == '__main__':
    unittest.main()