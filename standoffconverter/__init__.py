import numpy as np
from lxml import etree

from .tree_to_standoff import tree_to_standoff as tts
from .standoff_to_tree import standoff_to_tree as stt


def load(fp):
    """read from file handler and create an lxml tree from it. 
    Then create a standoff object and instantiate it.

    arguments:
        fp: file handler
    """
    tree = etree.fromstring(fp.read())
    return Standoff.from_lxml_tree(tree)


class Filter:

    def __init__(self, so, namespace=""):
        self.so = so
        self.find_state = [so.tree]
        self.exclude_map = np.zeros(len(so.plain))
        self.namespace = namespace

    def find(self, tag):
        new_find_state = []

        for it in self.find_state:
            new_find_state += [jt for jt in it.iterfind(".//{}{}".format(self.namespace, tag))]

        self.find_state = new_find_state
        return self

    def first(self):
        for plain, standoff in self.__iter__():
            return plain, standoff

    def exclude(self, tag):
        for it in self.find_state:
            for jt in it.iterfind(".//{}{}".format(self.namespace, tag)):
                standoff = self.so.tree_standoff_link[jt]
                self.exclude_map[standoff["begin"]:standoff["end"]] = 1

        return self

    def __iter__(self):
        for el in self.find_state:
            standoff = self.so.tree_standoff_link[el]
            filtered_string = (
                "".join(
                    char for ichar, char in enumerate(self.so.plain[standoff["begin"]:standoff["end"]])
                                                if self.exclude_map[ichar + standoff["begin"]] == 0
                )
            )
            yield filtered_string, standoff

    def __len__(self):
        return len(self.find_state)

    def copy(self):
        '''
        create a copy of the filter set by retaining the original standoff and namespace
        also retaining
        '''
        new_obj = Filter(self.so, self.namespace)    
        new_obj.exclude_map = np.copy(self.exclude_map)
        new_obj.find_state = [el for el in self.find_state]
        return new_obj

class Standoff:
    
    def __init__(self, standoffs=None, plain=None, tree=None, tree_standoff_link=None):
        self.standoffs = [] if standoffs is None else standoffs
        self.plain = plain
        self.tree = tree
        self.tree_standoff_link = tree_standoff_link

    @classmethod
    def from_lxml_tree(cls, tree):
        """create a standoff representation from an lxml tree.

        arguments:
            tree: the lxml object
        """
        plain, standoffs, link = tts(tree)
        return cls(standoffs, plain, tree, link)

    def __iter__(self):
        for attr in self.standoffs:
            yield attr, self.plain[attr["begin"]:attr["end"]]

    def __synchronize_representations(self, reference):

        if reference == "standoff":
            self.tree, self.tree_standoff_link = stt(self)
        elif reference == "tree":
            self.plain, self.standoffs, self.tree_standoff_link = tts(self.tree)
        else:
            raise ValueError("reference unknown.")

    def add_annotation(self, begin=None, end=None, tag=None, depth=None, attribute=None, unique=True):
        """add a standoff annotation.

        arguments:
            begin (int): the beginning character index
            end (int): the ending character index
            tag (str): the name of the xml tag
            depth (int): tree depth of the attribute. for the same begin and end, a lower depth annotation includes a higher depth annotation
            attribute (dict): attrib of the lxml
            unique (bool): whether to allow for duplicate annotations
        """
        if not unique or not self.is_duplicate_annotation(begin, end, tag, attribute):
            self.standoffs.append({
                "begin": begin,
                "end": end,
                "tag": tag,
                "attrib": attribute,
                "depth": depth if depth is not None else 0
            })
        self.__synchronize_representations(reference="standoff")

    def remove_annotation(self):
        '''remove a standoff annotation
        '''
        raise NotImplementedError()

    def is_duplicate_annotation(self, begin, end, tag, attribute):
        """check whether this annotation already in self.standoffs
        
        arguments:
            begin (int): the beginning character index
            end (int): the ending character index
            tag (str): the name of the xml tag
            attribute (dict): attrib of the lxml

        returns:
            bool: True if annotation already exists
        """

        def attrs_equal(attr_a, attr_b):
            shared_items = {}
            for k in attr_a:
                if k in attr_b and attr_a[k] == attr_b[k]:
                    shared_items[k] = attr_a[k]

            return len(attr_a) == len(attr_b) == len(shared_items)

        for standoff in self.standoffs:
            if (standoff["begin"] == begin
                and standoff["end"] == end
                and standoff["tag"] == tag
                and attrs_equal(attribute, standoff["attrib"])):
                return True
        return False
     
    def save(self, fp):
        """save the current self.tree as XML String to the file handler.

        arguments:
            fp: file handler
        """
        fp.write(etree.tostring(self.tree))

    
        