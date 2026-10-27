"""Span-preserving S-expression reader for KiCad files (no evaluation).

Each list node is a `Node` (a Python list subclass) that remembers the
character offsets of its opening and closing parentheses in the source text,
so callers can replace exactly one node without reformatting the file.
"""
import json
import re

TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+')


class Quoted(str):
    """A token that was written between double quotes."""


class Node(list):
    start = 0
    end = 0

    def children(self, key):
        return [v for v in self if isinstance(v, Node) and v and v[0] == key]

    def first(self, key):
        return next((v for v in self if isinstance(v, Node) and v and v[0] == key), None)

    def walk(self, key):
        if self and self[0] == key:
            yield self
        for v in self:
            if isinstance(v, Node):
                yield from v.walk(key)

    def prop(self, name):
        return next((p for p in self.children("property") if p[1] == name), None)

    def at(self):
        at = self.first("at")
        return tuple(float(v) for v in at[1:]) if at else None


def parse(text):
    stack, roots = [], []
    for match in TOKEN.finditer(text):
        tok = match.group(0)
        if tok == "(":
            node = Node()
            node.start = match.start()
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif tok == ")":
            if not stack:
                raise ValueError(f"unexpected ')' at {match.start()}")
            stack.pop().end = match.end()
        else:
            if not stack:
                raise ValueError("token outside root")
            stack[-1].append(Quoted(json.loads(tok)) if tok.startswith('"') else tok)
    if stack or len(roots) != 1:
        raise ValueError("unbalanced or multiple roots")
    return roots[0]


def q(value):
    """Quote a string the way KiCad writes it."""
    return json.dumps(str(value), ensure_ascii=False)


def replace_spans(text, edits):
    """Apply (start, end, replacement) edits; spans must not overlap."""
    out, pos = [], 0
    for start, end, new in sorted(edits):
        if start < pos:
            raise ValueError("overlapping edits")
        out.append(text[pos:start])
        out.append(new)
        pos = end
    out.append(text[pos:])
    return "".join(out)
