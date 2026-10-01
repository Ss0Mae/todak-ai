import re


class ReplyExtractor:
    """스트림에서 '상담사 응답:' 마커 뒤 첫 줄만 통과시킨다.

    마커가 끝까지 안 나오면 finish()가 전체 텍스트를 돌려준다 (원 정규식의 폴백과 같은 동작).
    """
    MARK = re.compile(r"상담사\s*응답[:：]?\s*")

    def __init__(self):
        self.buf = ""
        self.started = False
        self.done = False
        self._lead = True

    def feed(self, chunk: str) -> str:
        if self.done:
            return ""
        self.buf += chunk
        if not self.started:
            m = self.MARK.search(self.buf)
            if not m:
                return ""
            self.started = True
            self.buf = self.buf[m.end():]
        out, self.buf = self.buf, ""
        if self._lead:
            out = out.lstrip()
            if out:
                self._lead = False
        nl = out.find("\n")
        if nl != -1:
            self.done = True
            out = out[:nl]
        return out

    def finish(self) -> str:
        if self.started or self.done:
            return ""
        out, self.buf = self.buf.strip(), ""
        return out
