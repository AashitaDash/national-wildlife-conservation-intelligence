import pathlib, sys
p = pathlib.Path(r"c:\\Users\\KIIT0001\\Downloads\\Wildlife_Conservation_Shareable\\nlp\\preprocessor.py")
data = p.read_bytes()
print('size', len(data))
print('null bytes', data.count(b'\x00'))

