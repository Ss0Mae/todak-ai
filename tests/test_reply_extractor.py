"""스트리밍 응답 필터의 최소 검증. 실행: python3 -m pytest tests/ 또는 python3 tests/test_reply_extractor.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from agents.reply_extractor import ReplyExtractor


def run(chunks):
    ex = ReplyExtractor()
    out = "".join(ex.feed(c) for c in chunks)
    return out + ex.finish()


def test_marker_split_across_chunks_and_first_line_only():
    assert run(["상담사 응", "답: 오늘 ", "힘들었구나.\n분석: 불안"]) == "오늘 힘들었구나."


def test_leading_space_after_marker_is_stripped():
    assert run(["상담사 응답:", " 괜찮아."]) == "괜찮아."


def test_no_marker_falls_back_to_whole_text():
    assert run(["그냥 ", "본문만 왔다 "]) == "그냥 본문만 왔다"


def test_colon_and_newline_arrive_after_marker_in_later_chunks():
    # 실제 gpt-4o-mini 출력: "상담사 응답:  \n본문" 이 청크 "상담사 응답" / ":" / "  \n요즘…" 으로 쪼개져 온다
    assert run(["상담사 응답", ":", "  \n요즘 힘들지.", "\n분석: 슬픔"]) == "요즘 힘들지."


def test_markdown_bold_marker():
    assert run(["**상담사 응답**: 괜찮아.\n"]) == "괜찮아."


def test_nothing_after_done():
    ex = ReplyExtractor()
    ex.feed("상담사 응답: 끝\n")
    assert ex.feed("더 오는 글") == "" and ex.finish() == ""


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
