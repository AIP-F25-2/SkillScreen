## Backend – Resume Upload & Candidate Creation

- **Investigate Azure Postgres SSL EOF errors during candidate insert**
  - Symptom: `psycopg2.OperationalError: SSL SYSCALL error: EOF detected` when inserting into `candidates` during `/interview/resumes/upload`.
  - Impact: Candidate sometimes fails to save even though resume parsing succeeds; frontend now still gets a structured response with `candidate_save_error`, but persistence is unreliable.
  - Suggested follow-up: check DB connection pooling/timeout settings in `common-service` and network stability to Azure Postgres; consider automatic retry on transient `OperationalError`.

- **Align interview model nullability with DB constraints**
  - Symptom: `NOT NULL` violations on `template_id` and `mode` in `interviews` table when API omits these fields.
  - Current fix: API now defaults `template_id` to `1ef03eb1-4ba0-4e42-a27d-5b5a868640f4` and `mode` to `'chat'` in `send_invitation`.
  - Suggested follow-up: either (a) make these columns nullable in the DB if they are optional at the domain level or (b) formalize required defaults in schema/migrations so app+DB stay in sync.


