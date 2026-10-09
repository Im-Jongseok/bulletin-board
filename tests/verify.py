"""표준 라이브러리와 Docker의 psql로 검증한다. 모든 데이터 변경 검사는 롤백한다."""
import pathlib
import subprocess
import sys

database, output_file = sys.argv[1:]
# ponytail: 이 실습 시드의 예상값만 검사한다. 데이터를 바꾸면 기대값도 함께 수정한다.
report = [f"B6-1 검증 / DB: {database}\n"]


def sql(statement):
    return subprocess.run(
        ["docker", "exec", "-i", "bulletin-board-db", "psql", "-X", "-U", "admin",
         "-d", database, "-v", "ON_ERROR_STOP=1", "-v", "VERBOSITY=verbose", "-At"],
        input=statement, text=True, capture_output=True, check=False,
    )


def expect(label, statement, expected):
    result = sql(statement)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected, (label, result.stdout, expected)
    report.append(f"PASS {label}\nSQL: {statement}\n결과:\n{result.stdout}")


def reject(label, statement, state):
    result = sql("BEGIN;\n" + statement + "\nROLLBACK;")
    assert result.returncode != 0 and f"ERROR:  {state}:" in result.stderr, (label, result)
    report.append(f"PASS {label} / 예상 SQLSTATE {state}\nSQL: {statement}\n{result.stderr}")


snapshot_sql = """
SELECT json_build_object(
 'member', (SELECT json_agg(t ORDER BY id) FROM member t),
 'board', (SELECT json_agg(t ORDER BY id) FROM board t),
 'post', (SELECT json_agg(t ORDER BY id) FROM post t),
 'comment', (SELECT json_agg(t ORDER BY id) FROM comment t));
"""
before = sql(snapshot_sql)
assert before.returncode == 0, before.stderr

expect("PostgreSQL 18 이상", "SELECT current_setting('server_version_num')::integer >= 180000;", "t")
expect("테이블 4개", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';", "4")
expect("PK 4개 / FK 4개", "SELECT contype,COUNT(*) FROM pg_constraint WHERE connamespace='public'::regnamespace AND contype IN ('p','f') GROUP BY contype ORDER BY contype;", "f|4\np|4")
expect("전체 22개 컬럼 NOT NULL", "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='public' AND is_nullable='NO';", "22")
expect("샘플 행 수", "SELECT 'member',COUNT(*) FROM member UNION ALL SELECT 'board',COUNT(*) FROM board UNION ALL SELECT 'post',COUNT(*) FROM post UNION ALL SELECT 'comment',COUNT(*) FROM comment;", "member|10\nboard|10\npost|20\ncomment|30")
expect("빈 회원 2명 / 빈 게시판 1개 / 댓글 없는 글 4개", "SELECT (SELECT COUNT(*) FROM member m WHERE NOT EXISTS (SELECT 1 FROM post p WHERE p.member_id=m.id) AND NOT EXISTS (SELECT 1 FROM comment c WHERE c.member_id=m.id)), (SELECT COUNT(*) FROM board b WHERE NOT EXISTS (SELECT 1 FROM post p WHERE p.board_id=b.id)), (SELECT COUNT(*) FROM post p WHERE NOT EXISTS (SELECT 1 FROM comment c WHERE c.post_id=p.id));", "2|1|4")
expect("닉네임 중복 허용 샘플", "SELECT COUNT(*) FROM member WHERE nickname='새싹';", "2")
expect("자유 게시판 SUM / AVG", "SELECT SUM(p.view_count),ROUND(AVG(p.view_count),2) FROM post p JOIN board b ON b.id=p.board_id WHERE b.name='자유';", "30|10.00")
expect("전체 조회수 합계 / 평균", "SELECT SUM(view_count),ROUND(AVG(view_count),2) FROM post;", "1580|79.00")
expect("평균보다 조회수가 높은 글", "SELECT title,view_count FROM post WHERE view_count > (SELECT AVG(view_count) FROM post) ORDER BY view_count DESC,id DESC;", "SQL 자료|250\n인덱스 학습|200\nPostgreSQL 자료|180\nDB 설계 공유|150\nPostgreSQL 질문|120\n면접 SQL|110\n학습 계획|100\n이력서 질문|90\nDocker 접속 질문|80")
expect("건의 게시판 합계 0", "SELECT COALESCE(SUM(p.view_count),0) FROM board b LEFT JOIN post p ON p.board_id=b.id WHERE b.name='건의';", "0")
expect("회원별 글 수", "SELECT m.username,COUNT(p.id) FROM member m LEFT JOIN post p ON p.member_id=m.id GROUP BY m.id ORDER BY m.username;", "test_user|2\nuser02|3\nuser03|3\nuser04|3\nuser05|2\nuser06|2\nuser07|2\nuser08|3\nuser09|0\nuser10|0")
expect("INNER JOIN: 댓글 없는 글 제외", "SELECT p.title,c.id FROM post p INNER JOIN comment c ON c.post_id=p.id WHERE p.title='Docker 실습 후기';", "")
expect("LEFT JOIN: 댓글 없는 글 유지", "SELECT p.title,c.id FROM post p LEFT JOIN comment c ON c.post_id=p.id WHERE p.title='Docker 실습 후기';", "Docker 실습 후기|")
expect("Q07: COUNT(*)와 COUNT(c.id)의 차이", "SELECT p.title,COUNT(*),COUNT(c.id) FROM post p LEFT JOIN comment c ON c.post_id=p.id WHERE p.title IN ('SQL 기초','Docker 실습 후기') GROUP BY p.id ORDER BY p.title;", "Docker 실습 후기|1|0\nSQL 기초|5|5")

reject("중복 username", "INSERT INTO member(username,nickname,password_hash) VALUES('test_user','중복','demo');", "23505")
reject("중복 게시판 이름", "INSERT INTO board(name) VALUES('자유');", "23505")
reject("필수 nickname NULL", "UPDATE member SET nickname=NULL WHERE username='user02';", "23502")
reject("빈 nickname", "UPDATE member SET nickname='   ' WHERE username='user02';", "23514")
reject("username 최소 길이", "UPDATE member SET username='ab' WHERE username='user02';", "23514")
reject("username 앞뒤 공백", "UPDATE member SET username=' user02' WHERE username='user02';", "23514")
reject("username 최대 길이", "UPDATE member SET username=repeat('x',31) WHERE username='user02';", "22001")
reject("빈 password_hash", "UPDATE member SET password_hash='' WHERE username='user02';", "23514")
reject("빈 게시판 이름", "UPDATE board SET name='  ' WHERE name='질문';", "23514")
reject("post 없는 회원 참조", "UPDATE post SET member_id=-1 WHERE title='첫 글';", "23503")
reject("post 없는 게시판 참조", "UPDATE post SET board_id=-1 WHERE title='첫 글';", "23503")
reject("comment 없는 글 참조", "UPDATE comment SET post_id=-1 WHERE content='첫 댓글';", "23503")
reject("comment 없는 회원 참조", "UPDATE comment SET member_id=-1 WHERE content='첫 댓글';", "23503")
reject("빈 제목", "UPDATE post SET title=' ' WHERE title='첫 글';", "23514")
reject("빈 본문", "UPDATE post SET content='' WHERE title='첫 글';", "23514")
reject("빈 댓글", "UPDATE comment SET content=' ' WHERE content='첫 댓글';", "23514")
reject("음수 조회수", "UPDATE post SET view_count=-1 WHERE title='첫 글';", "23514")
reject("회원 삭제 RESTRICT", "DELETE FROM member WHERE username='test_user';", "23001")
reject("댓글만 작성한 회원 삭제 RESTRICT", "INSERT INTO member(username,nickname,password_hash) VALUES('comment_only','댓글회원','demo'); INSERT INTO comment(post_id,member_id,content) SELECT p.id,m.id,'삭제 제한 검증' FROM post p CROSS JOIN member m WHERE p.title='첫 글' AND m.username='comment_only'; DELETE FROM member WHERE username='comment_only';", "23001")
reject("게시판 삭제 RESTRICT", "DELETE FROM board WHERE name='자유';", "23001")

expect("댓글 삭제: 글 유지", "BEGIN; DELETE FROM comment WHERE content='첫 댓글'; SELECT COUNT(*) FROM post WHERE title='첫 글'; ROLLBACK;", "BEGIN\nDELETE 1\n1\nROLLBACK")
expect("글 삭제 CASCADE: 연결 댓글 3개만 삭제, 부모 유지", "BEGIN; DELETE FROM post WHERE title='첫 글'; SELECT (SELECT COUNT(*) FROM post),(SELECT COUNT(*) FROM comment),(SELECT COUNT(*) FROM member),(SELECT COUNT(*) FROM board); ROLLBACK;", "BEGIN\nDELETE 1\n19|27|10|10\nROLLBACK")
expect("정상 INSERT와 DEFAULT / RETURNING", "BEGIN; INSERT INTO board(name) VALUES('검증용') RETURNING description=''; INSERT INTO post(board_id,member_id,title,content) SELECT b.id,m.id,'검증 글','본문' FROM board b CROSS JOIN member m WHERE b.name='검증용' AND m.username='test_user' RETURNING view_count,created_at=updated_at; ROLLBACK;", "BEGIN\nt\nINSERT 0 1\n0|t\nINSERT 0 1\nROLLBACK")
expect("수정 시각 직접 갱신", "BEGIN; UPDATE post SET title='검증 수정',updated_at=CURRENT_TIMESTAMP WHERE title='첫 글' RETURNING updated_at>=created_at; UPDATE comment SET content='검증 수정',updated_at=CURRENT_TIMESTAMP WHERE content='첫 댓글' RETURNING updated_at>=created_at; ROLLBACK;", "BEGIN\nt\nUPDATE 1\nt\nUPDATE 1\nROLLBACK")
expect("보조 인덱스 4개", "SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public' AND indexname IN ('idx_post_board_created_at','idx_post_member_id','idx_comment_post_created_at','idx_comment_member_id');", "4")
expect("인덱스 컬럼과 정렬 방향", "SELECT indexdef FROM pg_indexes WHERE indexname='idx_post_board_created_at';", "CREATE INDEX idx_post_board_created_at ON public.post USING btree (board_id, created_at DESC, id DESC)")

after = sql(snapshot_sql)
assert after.returncode == 0 and before.stdout == after.stdout, "검증 전후 원본 데이터가 달라졌습니다."
report.append("PASS 검증 전후 네 테이블 전체 행과 컬럼 동일 (IDENTITY 시퀀스의 증가값은 비교하지 않음)\n")
pathlib.Path(output_file).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(output_file).write_text("\n".join(report), encoding="utf-8")
print(f"검증 {len(report)-1}개 통과: {output_file}")
