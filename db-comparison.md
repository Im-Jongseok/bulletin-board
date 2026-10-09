# SQLite · MySQL · PostgreSQL · H2 비교

PostgreSQL 18, MySQL 8.4(InnoDB) 기준이다. 네 DB 모두 SQL·PK·FK·트랜잭션을 지원한다.

## 핵심 비교

| DB | 실행 방식 | 적합한 용도 | 핵심 특징 |
|---|---|---|---|
| [SQLite](https://www.sqlite.org/whentouse.html) | 앱 내부에서 실행, 별도 서버 불필요 | 로컬 도구·작은 앱·SQL 입문 | DB 파일 하나에 동시에 쓰는 트랜잭션은 1개 |
| [MySQL](https://dev.mysql.com/doc/refman/8.4/en/innodb-introduction.html) | 별도 서버 | 웹 서비스·기존 MySQL 환경 | 기본 저장 엔진은 InnoDB |
| [PostgreSQL](https://www.postgresql.org/docs/18/intro-whatis.html) | 별도 서버 | 웹 서비스·복잡한 데이터 처리 | 타입·인덱스·확장 기능을 활용 가능 |
| [H2](https://www.h2database.com/html/features.html) | Java 앱 내부 또는 서버 | Java 앱·빠른 테스트 | 파일·인메모리 저장 모두 지원 |

SQLite는 연결별로 FK 활성화 상태를 확인해야 한다. 일반 테이블의 `VARCHAR(n)`은 길이 제한을 강제하지 않는다. H2의 호환 모드는 실제 PostgreSQL·MySQL 전체를 재현하지 않는다. [SQLite FK](https://www.sqlite.org/foreignkeys.html#fk_enable), [타입](https://www.sqlite.org/datatype3.html), [H2 호환 모드](https://www.h2database.com/html/features.html#compatibility)

## PostgreSQL과 MySQL의 명확한 차이

| 항목 | PostgreSQL | MySQL / InnoDB |
|---|---|---|
| 기본 저장 방식 | heap 테이블 접근 방식 | InnoDB 저장 엔진 |
| PK와 실제 행 | 행과 PK 인덱스가 별도 저장 | PK 클러스터형 인덱스에 실제 행 저장 |
| 자식 FK 컬럼 인덱스 | 자동 생성하지 않음 | 필요한 인덱스가 없으면 자동 생성 |
| 일반 CREATE TABLE 롤백 | 트랜잭션 안에서 가능 | 암묵적 COMMIT으로 취소 불가 |

저장 방식: [PostgreSQL](https://www.postgresql.org/docs/18/runtime-config-client.html#GUC-DEFAULT-TABLE-ACCESS-METHOD), [행·인덱스](https://www.postgresql.org/docs/18/indexes-index-only-scans.html), [InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html). FK: [PostgreSQL](https://www.postgresql.org/docs/18/ddl-constraints.html#DDL-CONSTRAINTS-FK), [MySQL](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html). 롤백: [PostgreSQL](https://www.postgresql.org/docs/18/sql-rollback.html), [MySQL](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html).

`psql`과 `mysql`은 각 DB 서버에 접속하는 터미널 도구다. 저장 엔진이 아니다. [psql](https://www.postgresql.org/docs/18/app-psql.html), [mysql](https://dev.mysql.com/doc/refman/8.4/en/mysql.html)

## 현재 실습의 선택

PostgreSQL을 유지한다. Docker·SQL·검증 자료가 준비되어 있고, FK·삭제 정책·인덱스·트랜잭션을 실제 서버에서 학습하는 목표에 맞는다.

성능 우열은 쿼리·데이터·인덱스·동시 요청에 따라 달라진다. PostgreSQL의 선택 매력에는 JSONB와 pgvector 같은 기능·확장성도 있다. 인기가 곧 모든 작업에서의 속도 우위를 뜻하지 않는다. [JSONB](https://www.postgresql.org/docs/18/datatype-json.html), [pgvector](https://github.com/pgvector/pgvector)

실제 성능 비교와 다른 DB로의 SQL 이식은 수행하지 않았다.
