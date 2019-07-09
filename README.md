# standoffconverter


I intended this package to be used in the following situation:
Given a bunch of XML files (e.g. standard TEI files), I would like to add new annotations (for example with an ML method). The workflow would then be

1. load the original TEI file with `lxml`

    `tree = etree.fromstring(INPUT)`

2. convert it with `tree_to_standoff` into a plain text str and a list of stand-off annotations
    ```
    so = standoffconverter.Standoff()
    so.from_lxml_tree(tree)
    ```

3. create new annotations (automatically) and add them to the original

    ```
    so.standoffs.append({
        "begin": 42, # character position in plain text str
        "end": 42, # character position in plain text str
        "tag": "SOMETAG",
        "depth": 0, # depth of the annotation wrt. to the other tags
        "attrib": {...} # dict of attrib as in etree.attrib elements
      })

4. convert the new annotations and the plain text back into an XML with `standoff_to_xml`

    `new_xml = so.to_xml()`

5. store the modified XML

     `open("...", "...").write(new_xml)`



      
      
      
      

      
