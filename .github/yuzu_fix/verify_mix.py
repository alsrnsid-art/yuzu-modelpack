# 정리한 YUZU.mix 확인 : 기대 목록 (md5 / 이름) 의 파일이 모두 있고 내용이 같은지 + 그 밖의 파일이 없는지
import ctypes, sys, hashlib
lib = ctypes.CDLL('libstorm.so.9'); H = ctypes.c_void_p
lib.SFileOpenArchive.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(H)]; lib.SFileOpenArchive.restype = ctypes.c_bool
lib.SFileOpenFileEx.argtypes = [H, ctypes.c_char_p, ctypes.c_uint, ctypes.POINTER(H)]; lib.SFileOpenFileEx.restype = ctypes.c_bool
lib.SFileGetFileSize.argtypes = [H, ctypes.POINTER(ctypes.c_uint)]; lib.SFileGetFileSize.restype = ctypes.c_uint
lib.SFileReadFile.argtypes = [H, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p]; lib.SFileReadFile.restype = ctypes.c_bool
lib.SFileCloseFile.argtypes = [H]; lib.SFileCloseFile.restype = ctypes.c_bool
h = H()
if not lib.SFileOpenArchive(sys.argv[1].encode(), 0, 0, ctypes.byref(h)):
    sys.exit('열기 실패')
bad = 0; n = 0
for line in open(sys.argv[2], encoding='utf-8'):
    md, name = line.rstrip('\n').split('\t', 1)
    f = H()
    if not lib.SFileOpenFileEx(h, name.encode('utf-8'), 0, ctypes.byref(f)):
        bad += 1; print('없음', name); continue
    hi = ctypes.c_uint(0); size = lib.SFileGetFileSize(f, ctypes.byref(hi))
    buf = ctypes.create_string_buffer(max(size, 1)); got = ctypes.c_uint(0)
    lib.SFileReadFile(f, buf, size, ctypes.byref(got), None)
    lib.SFileCloseFile(f)
    if got.value != size or hashlib.md5(buf.raw[:size]).hexdigest() != md:
        bad += 1; print('다름', name)
    n += 1
print('확인', n, '문제', bad)
sys.exit(1 if bad else 0)
