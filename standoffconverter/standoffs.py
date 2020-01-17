from lxml import etree
import json
from .utils import create_el_from_so, is_child_of


def get_closest_parent_of_interval_and_its_children(begin, end, depth, collection):
    
    closest_parent = None
    children = []
    for pair in __get_order_for_traversal(collection, key=lambda x: x.so):
        if __is_parent(begin, end, depth, pair.so):
            closest_parent = pair
            children = []
        else:
            if closest_parent is not None:
                if __is_parent(pair.so.begin, pair.so.end, pair.so.depth, closest_parent.so):
                    children.append(pair.so)
                else:
                    # if we already found a parent and currently `pair` is not a parent,
                    # then, we already found our closest parent and we can break
                    break

    return closest_parent, children
        

def __is_parent(begin, end, depth, so):
    return (
            (begin > so.begin and end <= so.end)
        or  (begin >= so.begin and end < so.end)
        or  (
                    (begin == so.begin and end == so.end)
                and (depth > so.depth)
            )   
    )


def __get_order_for_traversal(so, key=lambda x: x):
    return sorted(
        sorted(
            sorted(
                so,
                key=lambda x: key(x).depth
            ),
            key=lambda x:  (key(x).begin - key(x).end)
        ),
        key=lambda x: key(x).begin
    )


def standoff_to_tree(plain, collection):
    """convert the standoff representation to a etree representation

    arguments:
        plain -- plain text
        collection -- a list of so elements

    returns:
        tree -- the root element of the resulting tree
        new_collection (list) -- the new collection of pairs
    """
    order = __get_order_for_traversal(collection)

    pos_to_so = [[] for _ in range(len(plain))]
    new_collection = []

    for c_so in order:
        c_pair = AnnotationPair(c_so, None, None)
        
        new_collection.append(c_pair)
        
        c_pair.el = create_el_from_so(c_pair.so)

        for pos in range(c_pair.so.begin, c_pair.so.end):
            pos_to_so[pos].append(c_pair)
    
    for i in range(len(plain)):
        c_parents = pos_to_so[i]
        for i_parent in range(len(c_parents)-1):
            c_parent = c_parents[i_parent].el
            c_child = c_parents[i_parent+1].el
            if c_child not in c_parent:
                c_parent.append(c_child)
        if len(c_parents) > 0:
            if len(c_parents[-1].el) == 0:
                if c_parents[-1].el.text is None:
                    c_parents[-1].el.text = ""

                c_parents[-1].el.text += plain[i]
            else:
                if c_parents[-1].el[-1].tail is None:
                    c_parents[-1].el[-1].tail = ""
                c_parents[-1].el[-1].tail += plain[i]

    root = None
    for pos in pos_to_so:
        if len(pos) > 0:
            root = pos[0].el.getroottree().getroot()
    
    return root, new_collection


def tree_to_standoff(tree):
    """traverse the tree and create a standoff representation.

    arguments:
        tree -- the root element of an lxml etree

    returns:
        plain (str) -- the plain text of the tree
        collection (list) -- the list of standoff annotations
    """
    stand_off_props = {}
    plain = []

    def __traverse_and_parse(el, plain, stand_off_props, depth=0):
        
        dict_ = {
            "begin": len(plain),
            "tag": el.tag,
            "attrib": el.attrib,
            "depth": depth
        }

        so =  StandoffElement(dict_)
        
        stand_off_props[el] = so

        if el.text is not None:
            plain += [char for char in el.text]

        for gen in el:
            __traverse_and_parse(gen, plain, stand_off_props, depth=depth+1)

        depth -= 1
        stand_off_props[el].end = len(plain)

        if el.tail is not None:
            plain += [char for char in el.tail]

    __traverse_and_parse(tree, plain, stand_off_props)
    return "".join(plain), [(el,so) for el,so in stand_off_props.items()]


class AnnotationPair:
    """Contains a reference to the etree.Element object (self.el) and the corresponding StandoffElement object (self.so) to link the two representations.
    """
    def __init__(self, so, el, converter):
        """Create an AnnotationPair from a StandoffElement instance.
        
        arguments:
            so (StandoffElement): the StandoffElement instance.
            el (etree.Element): the etree.Element instance.
            converter (Converter): the Converter instance in which so is located.

        returns:
            (AnnotationPair): The created AnnotationPair instance.
        """
        self.so = so
        self.el = el
        self.converter = converter

    @classmethod
    def from_so(cls, so, converter):
        """Create an AnnotationPair from a StandoffElement instance.
        
        arguments:
            so (StandoffElement): the StandoffElement instance.
            converter (Converter): the Converter instance in which so is located.

        returns:
            (AnnotationPair): The created AnnotationPair instance.
        """
        el = create_el_from_so(so)
        so.etree_el = el
        return cls(so, el, converter)

    def xpath(self, *args, **kwargs):
        """Wrapper for `xpath` of the el

        returns
            (list): List of AnnotationPairs
        """
        found_els = self.el.xpath(*args, **kwargs)
        return [self.converter.el2pair[el] for el in found_els]

    def find(self, *args, **kwargs):
        """Wrapper for `find` of the el

        returns
            (AnnotationPairs): The found annotation pair
        """
        found_el = self.el.find(*args, **kwargs)
        return self.converter.el2pair[found_el]

    def get_text(self):
        """Get the text inside the annotation

        returns:
            (str): text within the annotation
        """
        return self.converter.plain[self.get_begin():self.get_end()]

    def get_so(self):
        """Get the so of the AnnotationPair

        returns:
            (StandoffElement): The created dictionary of standoff properties
        """
        return self.so

    def get_el(self):
        """Get the el of the AnnotationPair

        returns:
            (etree.Element): The created dictionary of standoff properties
        """
        return self.el

    def get_tag(self):
        """Get the tag of the StandoffElement

        returns:
            (str): The created dictionary of standoff properties
        """
        return self.so.tag

    def get_depth(self):
        """Get the depth of the StandoffElement

        returns:
            (int): The created dictionary of standoff properties
        """
        return self.so.depth

    def get_attrib(self):
        """Get the attrib of the StandoffElement

        returns:
            (dict): The created dictionary of standoff properties
        """
        return self.so.attrib

    def get_begin(self):
        """Get the begin of the StandoffElement

        returns:
            (int): The created dictionary of standoff properties
        """
        return self.so.begin

    def get_end(self):
        """Get the end of the StandoffElement

        returns:
            (int): The created dictionary of standoff properties
        """
        return self.so.end

    def get_dict(self):
        """Creates a new dictionary instance with the basic properties of the so element

        returns:
            (dict): The created dictionary of standoff properties
        """
        return {
            "begin": self.so.begin,
            "end": self.so.end,
            "attrib": self.so.attrib,
            "depth": self.so.depth,
            "tag": self.so.tag,
        }


class StandoffElement:
    """Wrapper class for the basic standoff properties."""
    def __init__(self, dict_):
        self.tag = dict_["tag"] if "tag" in dict_ else None
        self.attrib = dict(dict_["attrib"]) if "attrib" in dict_ else dict_
        self.begin = dict_["begin"] if "begin" in dict_ else None
        self.end = dict_["end"] if "end" in dict_ else None
        self.depth = dict_["depth"] if "depth" in dict_ else None


class Converter:
    """Home class that manages the representations of the document. 
    """
    def __init__(self, collection=None, plain=None, tree=None, so2pair=None, el2pair=None):
        """
        arguments:
            collection (list): annotations in list format.
            tree (etree.Element): root element of all annotations in tree format.
            plain (str): plain text without annotations.
            so2pair (dict): a dictionary to lookup self.collection items given a StandoffElement
            el2pair (dict): a dictionary to lookup self.collection items given a etree.Element

        returns:
            (AnnotationPair): The created AnnotationPair instance.
        """
        
        if collection is None:
            self.collection = []
        else:
            self.collection = collection

        self.plain = plain
        self.tree = tree
        if so2pair is None or el2pair is None:
            self.so2pair, self.el2pair = self.__get_lookups()
        
        if self.tree is not None:
            self.root_ap = self.el2pair[self.tree]

    @classmethod
    def from_tree(cls, tree):
        """create a standoff representation from an lxml tree.

        arguments:
            tree: the lxml object
        """
        self = cls()
        plain, collection = tree_to_standoff(tree)
        collection = [AnnotationPair(so, el, self) for el, so in collection]
        self.tree = tree
        self.plain = plain
        self.collection = collection
        self.so2pair, self.el2pair = self.__get_lookups()
        self.root_ap = self.el2pair[self.tree]

        return self

    def to_tree(self):
        """
        returns:
            (etree.Element): Root element of the tree representation.
        """
        return self.tree

    def to_json(self):
        """
        returns:
            (str): JSON representation.
        """
        return json.dumps(
            [it.get_dict() for it in self.collection]
        )

    def __iter__(self):
        for attr in self.collection:
            yield attr, self.plain[attr.begin:attr.end]

    def __len__(self):
        return len(self.collection)

    def __get_lookups(self):
        
        so2pair = {}
        el2pair = {}
        
        for it_pair in self.collection:
            so, el = it_pair.get_so(), it_pair.get_el()
            so2pair[so] = it_pair
            el2pair[el] = it_pair

        return so2pair, el2pair

    def add_annotation(self, begin=None, end=None, tag=None, depth=0, attribute=None, unique=True):
        """add a standoff annotation.

        arguments:
            begin (int): the beginning character index
            end (int): the ending character index
            tag (str): the name of the xml tag
            depth (int): tree depth of the attribute. for the same begin and end, a lower depth annotation includes a higher depth annotation
            attribute (dict): attrib of the lxml
            unique (bool): whether to allow for duplicate annotations
        """
        if not unique or not self.__is_duplicate_annotation(begin, end, tag, attribute):

            parent, children = get_closest_parent_of_interval_and_its_children(
                            begin, end, depth, self.collection)

            if parent is None:
                raise NotImplementedError("currently not possible to add root element.")
            elif parent.el.getparent() is None:
                raise NotImplementedError("currently not possible to add direct children of root elements.")
            else:
                
                dict_ = {
                    "begin": begin,
                    "end": end,
                    "tag": tag,
                    "attrib": attribute,
                    "depth": depth
                }
                
                so = StandoffElement(dict_)

                tree, new_collection = standoff_to_tree(self.plain, children + [so, parent.so])
                new_parent = new_collection[0]
                new_parent.el.tail = parent.el.tail
                # replace subtree
                parent.el.getparent().replace(parent.el, new_parent.el)
                
                # remove old items from collection
                for it in children + [parent.so]:
                    self.collection.remove(self.so2pair[it])

                # add new items to collection
                for pair in new_collection:
                    pair.converter = self
                    self.collection.append(pair)

                self.so2pair, self.el2pair = self.__get_lookups()


    def remove_annotation(self, pair):
        '''remove a standoff annotation

        arguments:
            so (StandoffElement): that is to be removed.
        '''

        if pair not in self.collection:
            raise ValueError("Annotation not in collection")
        
        parent, children = get_closest_parent_of_interval_and_its_children(
                            pair.so.begin, pair.so.end, pair.so.depth, self.collection)

        if parent is None:
            raise NotImplementedError("currently not possible to remove root element.")
        elif parent.el.getparent() is None:
            raise NotImplementedError("currently not possible to remove direct children of root elements.")
        else:
            children.remove(pair.so)

            tree, new_collection = standoff_to_tree(self.plain, children + [parent.so])
            
            new_parent = new_collection[0]
            new_parent.el.tail = parent.el.tail
            # replace subtree
            parent.el.getparent().replace(parent.el, new_parent.el)

            for it in children + [parent.so]:
                self.collection.remove(self.so2pair[it])

            self.collection.remove(pair)

            for pair in new_collection:
                pair.converter = self
                self.collection.append(pair)

            self.so2pair, self.el2pair = self.__get_lookups()
    
    def __is_duplicate_annotation(self, begin, end, tag, attribute):
        """check whether this annotation already in self.collection
        
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

        for item_pair in self.collection:
            if (item_pair.get_begin() == begin
                and item_pair.get_end() == end
                and item_pair.get_tag() == tag
                and attrs_equal(attribute, item_pair.get_attrib())):
                return True
        return False
