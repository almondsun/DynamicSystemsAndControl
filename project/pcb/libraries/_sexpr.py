"""Small lossless-value S-expression reader for local KiCad audit, no evaluation."""
import json,re
class Quoted(str):pass
def parse(text):
 tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text.lstrip('\ufeff'))
 stack=[];roots=[]
 for t in tokens:
  if t=='(':
   node=[]
   if stack:stack[-1].append(node)
   else:roots.append(node)
   stack.append(node)
  elif t==')':
   if not stack:raise ValueError('Unexpected closing parenthesis')
   stack.pop()
  else:
   if not stack:raise ValueError('Token outside root')
   stack[-1].append(Quoted(json.loads(t)) if t.startswith('"') else t)
 if stack or len(roots)!=1:raise ValueError('Unbalanced or multiple roots')
 return roots[0]
def dump(node,level=0):
 if isinstance(node,Quoted):return json.dumps(str(node),ensure_ascii=False)
 if not isinstance(node,list):return str(node)
 if not any(isinstance(v,list) for v in node):return '('+' '.join(dump(v) for v in node)+')'
 head=[];tail=[]
 for value in node:
  (tail if isinstance(value,list) else head).append(value)
 return '('+' '.join(dump(v) for v in head)+''.join('\n'+'  '*(level+1)+dump(v,level+1) for v in tail)+'\n'+'  '*level+')'
def children(node,key):return [v for v in node if isinstance(v,list) and v and v[0]==key]
def first(node,key):return next((v for v in node if isinstance(v,list) and v and v[0]==key),None)
def walk(node,key):
 if isinstance(node,list):
  if node and node[0]==key:yield node
  for v in node:
   if isinstance(v,list):yield from walk(v,key)
def prop(node,key):return next((v for v in children(node,'property') if v[1]==key),None)
def pin_signature(node):
 return sorted((str(first(p,'number')[1]),str(first(p,'name')[1]),str(p[1]),str(p[2])) for p in walk(node,'pin'))
