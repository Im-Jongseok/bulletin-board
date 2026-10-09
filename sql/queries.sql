SET TIME ZONE 'Asia/Seoul';

-- Q01 [기본 조회] 최근 게시글 10개를 작성 시각과 ID 역순으로 조회한다.
SELECT id, title, view_count, created_at
FROM post ORDER BY created_at DESC, id DESC LIMIT 10;

-- Q02 [기본 조회] 제목에 SQL이 포함된 게시글을 찾는다.
SELECT id, title FROM post WHERE title LIKE '%SQL%' ORDER BY id;

-- Q03 [기본 조회] 자유 게시판의 글을 최신순으로 조회한다.
SELECT p.id, p.title, p.created_at
FROM post p WHERE p.board_id = (SELECT id FROM board WHERE name = '자유')
ORDER BY p.created_at DESC, p.id DESC;

-- Q04 [기본 조회] 조회수가 100 이상인 글을 조회수 순으로 최대 5개 조회한다.
SELECT id, title, view_count FROM post WHERE view_count >= 100
ORDER BY view_count DESC, id DESC LIMIT 5;

-- Q05 [조인] 게시글에 작성자의 닉네임을 붙인다.
SELECT p.id, p.title, m.nickname
FROM post p INNER JOIN member m ON m.id = p.member_id ORDER BY p.id;

-- Q06 [조인] 게시글에 소속 게시판 이름을 붙인다.
SELECT p.id, p.title, b.name AS board_name
FROM post p INNER JOIN board b ON b.id = p.board_id ORDER BY p.id;

-- Q07 [조인] 댓글 없는 글을 포함하여 글별 댓글 수를 계산한다.
SELECT p.id, p.title, COUNT(c.id) AS comment_count
FROM post p LEFT JOIN comment c ON c.post_id = p.id
GROUP BY p.id, p.title ORDER BY p.id;

-- Q08 [조인] 댓글에 글 제목과 댓글 작성자의 닉네임을 붙인다.
SELECT c.id, p.title, m.nickname, c.content
FROM comment c INNER JOIN post p ON p.id = c.post_id
INNER JOIN member m ON m.id = c.member_id ORDER BY c.id;

-- Q09 [집계] 글 없는 회원을 포함하여 회원별 작성 글 수를 계산한다.
SELECT m.username, m.nickname, COUNT(p.id) AS post_count
FROM member m LEFT JOIN post p ON p.member_id = m.id
GROUP BY m.id, m.username, m.nickname ORDER BY m.username;

-- Q10 [집계] 게시판별 조회수를 합산하고 글 없는 게시판은 0으로 표시한다.
SELECT b.name, COALESCE(SUM(p.view_count), 0) AS total_views
FROM board b LEFT JOIN post p ON p.board_id = b.id
GROUP BY b.id, b.name ORDER BY b.name;

-- Q11 [집계] 글이 있는 게시판의 평균 조회수를 소수점 둘째 자리까지 계산한다.
SELECT b.name, ROUND(AVG(p.view_count), 2) AS average_views
FROM board b INNER JOIN post p ON p.board_id = b.id
GROUP BY b.id, b.name ORDER BY b.name;

-- Q12 [서브쿼리] 전체 평균 조회수보다 조회수가 높은 글을 찾는다.
SELECT id, title, view_count FROM post
WHERE view_count > (SELECT AVG(view_count) FROM post)
ORDER BY view_count DESC, id DESC;

-- Q13 [인덱스] 게시판 ID로 범위를 줄인 뒤 작성 시각·ID 역순으로 최신 목록을 찾기 위해 생성한다.
CREATE INDEX IF NOT EXISTS idx_post_board_created_at ON post(board_id, created_at DESC, id DESC);

BEGIN;
-- Q14 [수정] 첫 글의 제목과 수정 시각을 갱신하고 바뀐 행을 확인한다.
UPDATE post SET title = '첫 글 (수정 실습)', updated_at = CURRENT_TIMESTAMP
WHERE id = (
    SELECT p.id FROM post p INNER JOIN member m ON m.id = p.member_id
    INNER JOIN board b ON b.id = p.board_id
    WHERE m.username = 'test_user' AND b.name = '자유' AND p.title = '첫 글'
    ORDER BY p.id LIMIT 1
)
RETURNING id, title, updated_at;

-- Q15 [삭제] 첫 댓글 한 개를 삭제하고 삭제된 행을 확인한다.
DELETE FROM comment WHERE id = (
    SELECT c.id FROM comment c INNER JOIN member m ON m.id = c.member_id
    INNER JOIN post p ON p.id = c.post_id
    WHERE m.username = 'test_user' AND p.title = '첫 글 (수정 실습)' AND c.content = '첫 댓글'
    ORDER BY c.id LIMIT 1
)
RETURNING id, post_id, content;
ROLLBACK;
