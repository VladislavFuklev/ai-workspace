"""The error envelope.

One shape for every failure, matching what the web client already parses in
`apps/web/src/lib/api/errors.ts`: `code`, `message`, and for a 422 a `detail`
array of `{field, message}` that the form layer maps back onto its fields.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FieldError(BaseModel):
    field: str = Field(description="Dotted path to the offending field.")
    message: str


class ErrorResponse(BaseModel):
    code: str = Field(description="Stable, machine-readable. Clients branch on this.")
    message: str = Field(description="Safe to show a user.")
    detail: list[FieldError] | None = Field(
        default=None, description="Field-level problems, for a 422."
    )
    request_id: str | None = Field(
        default=None, description="Matches the X-Request-ID header; quote it in a bug report."
    )
