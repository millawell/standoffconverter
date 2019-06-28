from lxml import etree
import standoffconverter

input_xml = b'''<?xml version='1.0' encoding='utf-8'?>
<W>
  <header>
    <date>
      2019
    </date>
    <location>
      Berlin, Germany
    </location>
  </header>
  <text type="a">
    Lorem ipsum dolor sit amet, <add>consetetur</add> sadipscing <del>elitr</del>, <note resp="David Lassner">sed</note> diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.
  </text>
</W>
'''

if __name__ == "__main__":
      
      print("INPUT XML:")
      print(input_xml.decode("utf-8"))
      
      tree = etree.fromstring(input_xml)
      
      plain, standoff = standoffconverter.tree_to_standoff(tree)
      
      t = "aliquyam"
      begin = plain.index(t)
      end = begin + len(t)
      standoff.append({
            "begin": begin,
            "end": end,
            "tag": "del",
            "depth": 0,
            "attrib": {"resp": "David Lassner"}
      })

      new_xml = standoffconverter.standoff_to_xml(plain, standoff)

      print("\n\n\n\n####\nOUTPUT XML")

      print(new_xml)