# YUZU.mix 정리 : 원본에서 남길 파일만 새 MPQ (v1) 로 옮겨 담기 (StormLib)
#   plan.tsv : R <경로> = 뺌 / M <옛 경로> <새 경로> = 새 이름으로 담음
#   사용 : python3 rebuild.py 원본.mix 새.mix plan.tsv
import ctypes, sys
lib = ctypes.CDLL('libstorm.so.9'); H = ctypes.c_void_p; U = ctypes.c_uint
def fn(name, args, res=ctypes.c_bool):
    f = getattr(lib, name); f.argtypes = args; f.restype = res; return f
OpenArc = fn('SFileOpenArchive', [ctypes.c_char_p, U, U, ctypes.POINTER(H)])
CreateArc = fn('SFileCreateArchive', [ctypes.c_char_p, U, U, ctypes.POINTER(H)])
CloseArc = fn('SFileCloseArchive', [H])
OpenFile = fn('SFileOpenFileEx', [H, ctypes.c_char_p, U, ctypes.POINTER(H)])
GetSize = fn('SFileGetFileSize', [H, ctypes.POINTER(U)], U)
ReadFile = fn('SFileReadFile', [H, ctypes.c_void_p, U, ctypes.POINTER(U), ctypes.c_void_p])
CloseFile = fn('SFileCloseFile', [H])
FindFirst = fn('SFileFindFirstFile', [H, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_char_p], H)
CreateFile = fn('SFileCreateFile', [H, ctypes.c_char_p, ctypes.c_ulonglong, U, U, U, ctypes.POINTER(H)])
WriteFile = fn('SFileWriteFile', [H, ctypes.c_void_p, U, U])
FinishFile = fn('SFileFinishFile', [H])
src_path, dst_path, plan = sys.argv[1], sys.argv[2], sys.argv[3]
enc = lambda s: s.encode('utf-8')
drop = set(); ren = {}
for line in open(plan, encoding='utf-8'):
    a = line.rstrip('\n').split('\t')
    if a[0] == 'R': drop.add(a[1].lower())
    elif a[0] == 'M': ren[a[1].lower()] = a[2]
src = H()
if not OpenArc(enc(src_path), 0, 0x100, ctypes.byref(src)) and not OpenArc(enc(src_path), 0, 0, ctypes.byref(src)):
    sys.exit('원본 열기 실패')
# 원본 목록 ((listfile) 읽기)
def read(h, name):
    f = H()
    if not OpenFile(h, enc(name), 0, ctypes.byref(f)): return None
    hi = U(0); size = GetSize(f, ctypes.byref(hi)); buf = ctypes.create_string_buffer(max(size, 1)); got = U(0)
    ReadFile(f, buf, size, ctypes.byref(got), None); CloseFile(f)
    return buf.raw[:got.value] if got.value == size else None
lst = read(src, '(listfile)').decode('utf-8', 'surrogateescape').replace('\r', '').split('\n')
names = []; seen = set()
for n in lst:
    if not n or n.startswith('(') or n.lower() in seen: continue
    seen.add(n.lower())
    if n.lower() in drop: continue
    names.append((n, ren.get(n.lower(), n)))
cnt = 1
while cnt < len(names) * 2 + 16: cnt *= 2
dst = H()
# MPQ_CREATE_LISTFILE 0x100000 | v1 (0)
if not CreateArc(enc(dst_path), 0x100000, cnt, ctypes.byref(dst)):
    sys.exit('새 파일 만들기 실패')
done = 0; fail = 0
for old, new in names:
    data = read(src, old)
    if data is None:
        fail += 1; print('읽기 실패', old); continue
    hf = H()
    # MPQ_FILE_COMPRESS 0x200 / MPQ_COMPRESSION_ZLIB 0x02
    if not CreateFile(dst, enc(new), 0, len(data), 0, 0x200, ctypes.byref(hf)):
        fail += 1; print('담기 실패', new); continue
    if len(data): WriteFile(hf, data, len(data), 0x02)
    FinishFile(hf); done += 1
CloseArc(dst); CloseArc(src)
print('담음', done, '실패', fail)
sys.exit(1 if fail else 0)
