# backend/utils/tree_helpers.py
from backend.models import TreeVersion, UploadedTree
from flask import abort
from sqlalchemy.orm import Session

def get_latest_tree_version(db: Session, tree_id: int) -> TreeVersion:
    """
    Accepts either a TreeVersion ID or UploadedTree ID.
    First tries TreeVersion.id direct match. If not found, fall back to latest version by uploaded_tree_id.
    """
    # Try direct TreeVersion ID match
    version = db.query(TreeVersion).filter(TreeVersion.id == tree_id).first()
    if version:
        return version

    # Fall back to assuming it's an UploadedTree ID
    versions = (
        db.query(TreeVersion)
        .filter(TreeVersion.uploaded_tree_id == tree_id)
        .order_by(TreeVersion.version_number.desc())
        .all()
    )
    if versions:
        return versions[0]

    raise ValueError("Tree not found")

