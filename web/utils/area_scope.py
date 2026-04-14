from __future__ import annotations


def _matches_area(
    target_area_id: str | None,
    target_area_code: str | None,
    candidate_area_id: str | None,
    candidate_area_code: str | None,
) -> bool:
    if target_area_id and candidate_area_id and str(target_area_id) == str(candidate_area_id):
        return True
    if target_area_code and candidate_area_code and str(target_area_code) == str(candidate_area_code):
        return True
    return False


def extract_area_context(record: dict | None) -> tuple[str | None, str | None]:
    if not isinstance(record, dict):
        return None, None

    area = record.get("area")
    if isinstance(area, dict):
        area_id = str(area["id"]) if area.get("id") else None
        return area_id, area.get("code")

    if record.get("area_id"):
        return str(record["area_id"]), None

    for key in (
        "equipment",
        "motor",
        "instrument",
        "removed_motor",
        "installed_motor",
        "removed_instrument",
        "installed_instrument",
        "target_equipment",
        "linked_user",
    ):
        nested_area_id, nested_area_code = extract_area_context(record.get(key))
        if nested_area_id or nested_area_code:
            return nested_area_id, nested_area_code

    return None, None


def record_matches_area(
    record: dict,
    *,
    target_area_id: str | None = None,
    target_area_code: str | None = None,
) -> bool:
    candidate_area_id, candidate_area_code = extract_area_context(record)
    return _matches_area(target_area_id, target_area_code, candidate_area_id, candidate_area_code)


def filter_records_for_area(
    records: list[dict],
    *,
    target_area_id: str | None = None,
    target_area_code: str | None = None,
) -> list[dict]:
    if target_area_id is None and target_area_code is None:
        return records
    return [
        record
        for record in records
        if record_matches_area(
            record,
            target_area_id=target_area_id,
            target_area_code=target_area_code,
        )
    ]

