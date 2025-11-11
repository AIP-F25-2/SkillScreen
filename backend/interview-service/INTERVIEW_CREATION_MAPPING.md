# Interview Creation - Field Mapping & Retrieval Plan

## Request Body Schema

### Mandatory Fields (Must be in request body)
- `user_id` (UUID/string) - The interviewer/creator
- `candidate_id` (UUID/string) - The candidate being interviewed
- `candidate_ids` (array of UUIDs, optional) - For bulk creation (alternative to candidate_id)

### Optional Fields (Can be in request body, with defaults)
- `organization_id` (UUID/string) - Will be looked up from user if not provided
- `job_position_id` (UUID/string) - Defaults to NULL or requires lookup
- `template_id` (UUID/string) - Will fetch default template if not provided
- `mode` (string: 'chat', 'audio', 'video', 'hybrid') - Defaults to 'video'
- `scheduled_at` (ISO datetime string) - Defaults to current time
- `settings` (JSON object) - Defaults to empty object `{}`

---

## Interviews Table Field Mapping

| Field Name | Type | Required in DB | Source | Retrieval Method | Default Value |
|------------|------|----------------|--------|------------------|---------------|
| **id** | UUID | ✅ | Auto-generated | `gen_random_uuid()` or `uuid.uuid4()` | N/A |
| **organization_id** | UUID | ✅ | Database Lookup | Query `users` table by `user_id` → get `organization_id` | Must retrieve, no default |
| **job_position_id** | UUID | ✅ | Request Body | `body.get("job_position_id")` | NULL (if allowed) OR raise error if not provided |
| **candidate_id** | UUID | ✅ | Request Body | `body.get("candidate_id")` or `body.get("candidate_ids")` | Must be provided |
| **interviewer_id** | UUID | ❌ Optional | Request Body | `body.get("user_id")` | Can be NULL |
| **template_id** | UUID | ✅ | Database Lookup | Query `interview_templates` for default template by `organization_id` | Get first active template for org |
| **status** | Enum | ✅ | Default | Map "created" → "scheduled" | `'scheduled'` |
| **mode** | Enum | ✅ | Request Body | `body.get("mode", "video")` | `'video'` |
| **scheduled_at** | timestamptz | ❌ Optional | Request Body | `body.get("scheduled_at")` or `datetime.now()` | Current timestamp |
| **started_at** | timestamptz | ❌ Optional | Auto | NULL initially | `NULL` |
| **completed_at** | timestamptz | ❌ Optional | Auto | NULL initially | `NULL` |
| **settings** | JSONB | ❌ Optional | Request Body | `body.get("settings", {})` | `{}` |
| **created_at** | timestamptz | ✅ | Auto-generated | `datetime.now(timezone.utc)` | Current timestamp |
| **updated_at** | timestamptz | ✅ | Auto-generated | `datetime.now(timezone.utc)` | Current timestamp |
| **deleted_at** | timestamptz | ❌ Optional | Auto | NULL initially | `NULL` |

---

## Detailed Retrieval Methods

### 1. organization_id (REQUIRED - Database Lookup)
**Query:**
```sql
SELECT organization_id FROM users WHERE id = :user_id AND deleted_at IS NULL;
```
**If not found:** Raise HTTPException 404 "User not found"
**If user has no organization_id:** Raise HTTPException 400 "User has no organization assigned"

### 2. template_id (REQUIRED - Database Lookup with Fallback)
**Priority:**
1. If provided in request body: Use `body.get("template_id")`
2. If not provided: Query for default template
   ```sql
   SELECT id FROM interview_templates 
   WHERE organization_id = :org_id 
     AND deleted_at IS NULL 
   ORDER BY created_at ASC 
   LIMIT 1;
   ```
**If no template found:** Raise HTTPException 400 "No interview template found for organization"

### 3. job_position_id (REQUIRED - Request Body)
**Options:**
- **Option A (Strict):** Must be provided in request body, raise error if missing
- **Option B (Flexible):** Allow NULL if interview doesn't require a job position
- **Option C (Lookup):** Query job_positions table for default/active job

**Recommendation:** Make it required in request body for now

### 4. mode (REQUIRED - Request Body with Default)
```python
mode = body.get("mode", "video")
# Validate: mode must be in ['chat', 'audio', 'video', 'hybrid']
if mode not in ['chat', 'audio', 'video', 'hybrid']:
    raise HTTPException(400, "Invalid mode. Must be: chat, audio, video, or hybrid")
```

### 5. status (REQUIRED - Mapped)
```python
status = "scheduled"  # Map from "created" to "scheduled"
```

### 6. scheduled_at (Optional - Request Body with Default)
```python
if scheduled_at := body.get("scheduled_at"):
    scheduled_at = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
else:
    scheduled_at = datetime.now(timezone.utc)
```

---

## Example Request Body

### Single Interview Creation
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_id": "660e8400-e29b-41d4-a716-446655440001",
  "job_position_id": "770e8400-e29b-41d4-a716-446655440002",
  "template_id": "880e8400-e29b-41d4-a716-446655440003",  // Optional
  "mode": "video",  // Optional, defaults to "video"
  "scheduled_at": "2024-12-20T10:00:00Z",  // Optional, defaults to now
  "settings": {  // Optional
    "duration_minutes": 30,
    "max_questions": 10
  }
}
```

### Bulk Interview Creation
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_ids": [
    "660e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002",
    "660e8400-e29b-41d4-a716-446655440003"
  ],
  "job_position_id": "770e8400-e29b-41d4-a716-446655440002",
  "template_id": "880e8400-e29b-41d4-a716-446655440003",  // Optional
  "mode": "hybrid",  // Optional
  "scheduled_at": "2024-12-20T10:00:00Z"  // Optional
}
```

---

## Database Queries Needed

### 1. Get User Organization
```python
def get_user_organization(user_id: str) -> Optional[str]:
    query = select(users_table.c.organization_id).where(
        users_table.c.id == user_id,
        users_table.c.deleted_at.is_(None)
    )
    result = session.execute(query).scalar_one_or_none()
    return result
```

### 2. Get Default Template
```python
def get_default_template(organization_id: str) -> Optional[str]:
    query = select(interview_templates_table.c.id).where(
        interview_templates_table.c.organization_id == organization_id,
        interview_templates_table.c.deleted_at.is_(None)
    ).order_by(interview_templates_table.c.created_at.asc()).limit(1)
    result = session.execute(query).scalar_one_or_none()
    return result
```

### 3. Validate Candidate Exists
```python
def validate_candidate(candidate_id: str, organization_id: str) -> bool:
    query = select(candidates_table.c.id).where(
        candidates_table.c.id == candidate_id,
        candidates_table.c.organization_id == organization_id,
        candidates_table.c.deleted_at.is_(None)
    )
    result = session.execute(query).scalar_one_or_none()
    return result is not None
```

### 4. Validate Job Position Exists
```python
def validate_job_position(job_position_id: str, organization_id: str) -> bool:
    query = select(job_positions_table.c.id).where(
        job_positions_table.c.id == job_position_id,
        job_positions_table.c.organization_id == organization_id,
        job_positions_table.c.deleted_at.is_(None)
    )
    result = session.execute(query).scalar_one_or_none()
    return result is not None
```

---

## Implementation Summary

1. **Mandatory in Request:**
   - `user_id` ✅
   - `candidate_id` OR `candidate_ids` ✅
   - `job_position_id` ✅ (NEW - must add)

2. **Optional in Request (with defaults):**
   - `template_id` (lookup default if not provided)
   - `mode` (default: "video")
   - `scheduled_at` (default: now)
   - `settings` (default: {})

3. **Database Lookups:**
   - `organization_id` from `users` table
   - `template_id` from `interview_templates` (if not provided)

4. **Auto-generated:**
   - `id` (UUID)
   - `created_at`, `updated_at`
   - `started_at`, `completed_at` (NULL initially)
   - `deleted_at` (NULL initially)

5. **Mapped/Transformed:**
   - `status`: "created" → "scheduled"
   - `user_id` → `interviewer_id`

